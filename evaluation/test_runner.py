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

    for question in questions:
        print(f"Running test for question: {question}")

        result = run_test(question, api_url)

        test_result = {
            "test_run_id": test_run_id,
            "question": question,
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
    test_questions = [
        'O que é neurodivergência e como ela se diferencia do modelo médico de "deficiência"?',
        'Quais são os principais tipos de neurodivergência e suas características? Discuta a possibilidade de ocorrência de comorbidades e suas implicações.',
        'Quais são as barreiras mais comuns enfrentadas por neurodivergentes eu seu dia a dia? Elenque alguns exemplos, de preferência reais, como os registrados em noticiário.',
        'O que significa o conceito de "Nothing About Us Without Us" (Nada sobre nós sem nós) e por que é um princípio ético fundamental ao se projetar qualquer produto ou serviço para comunidades neurodivergentes?',
        'Como a patologização de condições neurodivergentes (vê-las apenas como "doenças a serem curadas") impacta a forma como a sociedade enxerga as necessidades e potenciais dessas pessoas?',
        'Quais são os perigos do ableism (ou capacitismo) no trato com pessoas neurodivergentes? Como podemos identificar e evitar vieses inconscientes que assumem que todos possuem as mesmas condições de atuação em face dos desafios cotidianos?',
        'A neurodiversidade é frequentemente representada de forma estereotipada na mídia e na cultura popular. Como esses estereótipos podem influenciar negativamente a visão de pessoas neurodivergentes?',
        'Como podemos, enquanto futuros profissionais, advogar pela inclusão da neurodiversidade, não apenas nos serviços e produtos, mas também nos processos de desenvolvimento e de gestão promovidos em todas as organizações sociais e do mercado produtivo?'
    ]

    run_tests(test_questions)
