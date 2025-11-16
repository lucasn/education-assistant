import signal
import sys
import os
from judge import Judge
from rabbitmq_client import RabbitMQClient
import json


class Evaluator:
    def __init__(self, rabbitmq_host="localhost", rabbitmq_port=5672, rabbitmq_user="guest", rabbitmq_password="guest"):
        self.rabbitmq_client = RabbitMQClient(
            host=rabbitmq_host,
            port=rabbitmq_port,
            user=rabbitmq_user,
            password=rabbitmq_password
        )
        self.is_running = True
        self.judge = Judge()

    def process_message(self, message):
        """
        Process a single test result message from the queue.
        """
        print(f"\n{'='*80}")
        print(f"Processing test result...")
        print(f"{'='*80}")

        test_run_id = message.get("test_run_id", "N/A")
        question = message.get("question", "")
        answer = message.get("answer", "")
        context = message.get("context")
        tool_calls = message.get("tool_calls", [])

        # Extract search_documents content
        search_documents_content = ""
        for tool_call in tool_calls:
            if tool_call.get("name") == "search_documents":
                response = tool_call.get("response", "")
                try:
                    documents = json.loads(response)
                    contents = [doc.get("content", "") for doc in documents if isinstance(doc, dict)]
                    search_documents_content = "\n\n".join(contents)
                except json.JSONDecodeError as e:
                    print(f"[WARNING] Failed to parse search_documents response: {e}")
                break

        print(f"\nTest Run ID: {test_run_id}")
        print(f"Question: {question}")
        print(f"Answer: {answer[:100]}..." if len(answer) > 100 else f"Answer: {answer}")
        print(f"Context available: {context is not None}")
        print(f"Tool calls: {len(tool_calls)}")
        print(f"Search documents content length: {len(search_documents_content)} characters")

        groundedness_input = f"QUESTION: {question}\nCONTEXT: {search_documents_content}\nRESPONSE: {answer}"
        groundedness = self.judge.evaluate_groundedness({"input": groundedness_input})

        print(groundedness)

        # In production, you might want to store these results in a database
        # or send them to another queue for further processing
        evaluation_summary = {
            "test_run_id": test_run_id,
            "question": question,
            "answer": answer,
            "search_documents_content": search_documents_content,
            # "correctness": correctness_result,
            # "groundedness": groundedness
        }

        print(f"\n{'='*80}")
        print(f"Evaluation completed!")
        print(f"{'='*80}\n")

        return evaluation_summary

    def start(self):
        """
        Start consuming messages from the RabbitMQ queue.
        """
        def signal_handler(sig, frame):
            print("\n\nStopping evaluator...")
            self.is_running = False
            self.rabbitmq_client.stop_consuming()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            print("Connecting to RabbitMQ...")
            self.rabbitmq_client.connect()

            print("Declaring queue 'tests_results'...")
            self.rabbitmq_client.declare_queue('tests_results', durable=True)

            print("Starting to consume messages...")
            self.rabbitmq_client.consume_messages('tests_results', self.process_message, auto_ack=False)

        except KeyboardInterrupt:
            print("\nStopping evaluator...")
        finally:
            self.rabbitmq_client.close()
            print("Evaluator stopped.")


def main():
    print("=" * 80)
    print("Starting Evaluator Service")
    print("=" * 80)

    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")

    print(f"Configuration:")
    print(f"  RabbitMQ Host: {rabbitmq_host}")
    print(f"  RabbitMQ Port: {rabbitmq_port}")
    print(f"  RabbitMQ User: {rabbitmq_user}")
    print("=" * 80)

    evaluator = Evaluator(
        rabbitmq_host=rabbitmq_host,
        rabbitmq_port=rabbitmq_port,
        rabbitmq_user=rabbitmq_user,
        rabbitmq_password=rabbitmq_password
    )

    evaluator.start()


if __name__ == "__main__":
    main()
