import requests
import json
import uuid
from rabbitmq_client import RabbitMQClient


def run_test(question, api_url="http://localhost:8080"):
    thread_id = f"test_{uuid.uuid4()}"

    response = requests.post(
        f"{api_url}/ask_async",
        json={
            "threadId": thread_id,
            "question": question
        },
        stream=True
    )

    if not response.ok:
        raise Exception(f"API request failed: {response.status_code} {response.text}")

    final_answer = ""
    context = ""

    for line in response.iter_lines():
        if line:
            line_text = line.decode('utf-8')

            if line_text.startswith('data: '):
                json_data = line_text[6:]
                try:
                    data = json.loads(json_data)

                    if data.get("content"):
                        final_answer += data["content"]

                    if data.get("additional_kwargs", {}).get("context"):
                        context = data["additional_kwargs"]["context"]

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    continue

    conversation_response = requests.get(f"{api_url}/conversation/{thread_id}")

    if not conversation_response.ok:
        raise Exception(f"Failed to fetch conversation: {conversation_response.status_code} {conversation_response.text}")

    conversation_data = conversation_response.json()
    messages = conversation_data[0].get("messages", [])

    tool_calls = []
    tool_call_map = {}

    for message in messages:
        if message.get("type") == "ai" and "tool_calls" in message:
            for tool_call in message.get("tool_calls", []):
                tool_call_map[tool_call["id"]] = {
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "response": None
                }

        elif message.get("type") == "tool":
            tool_call_id = message.get("tool_call_id")
            if tool_call_id in tool_call_map:
                tool_call_map[tool_call_id]["response"] = message.get("content")

    tool_calls = list(tool_call_map.values())

    return {
        "answer": final_answer,
        "context": context if context else None,
        "tool_calls": tool_calls
    }


def run_tests(questions, api_url="http://localhost:8080", rabbitmq_host="localhost", rabbitmq_port=5672, rabbitmq_user="guest", rabbitmq_password="guest"):
    test_run_id = str(uuid.uuid4())
    print(f"Starting test run with ID: {test_run_id}")

    rabbitmq_client = RabbitMQClient(
        host=rabbitmq_host,
        port=rabbitmq_port,
        user=rabbitmq_user,
        password=rabbitmq_password
    )

    rabbitmq_client.connect()
    rabbitmq_client.declare_queue('tests_results', durable=True)

    for question_data in questions:
        question = question_data.get("question", "")
        reference_answer = question_data.get("reference_answer")

        print(f"Running test for question: {question}")

        result = run_test(question, api_url)

        test_result = {
            "test_run_id": test_run_id,
            "question": question,
            "reference_answer": reference_answer,
            "answer": result["answer"],
            "context": result["context"],
            "tool_calls": result["tool_calls"]
        }

        rabbitmq_client.send_message('tests_results', test_result, persistent=True)

        print(f"Result sent to queue for question: {question}")

    rabbitmq_client.close()
    print(f"All {len(questions)} tests completed and sent to queue")
    print(f"Test run ID: {test_run_id}")


if __name__ == "__main__":
    import glob
    from pathlib import Path

    # Get all JSON files from data folder
    data_folder = Path(__file__).parent.parent / "data"
    json_files = glob.glob(str(data_folder / "*.json"))

    test_questions = []

    # Read all JSON files and extract questions
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            questions_data = data.get("questions", [])

            for q in questions_data:
                test_questions.append({
                    "question": q.get("question", ""),
                    "reference_answer": q.get("answer", "")
                })

    print(f"Loaded {len(test_questions)} questions from {len(json_files)} JSON files")

    run_tests(test_questions)
