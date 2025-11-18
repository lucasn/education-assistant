import signal
import sys
import os
from judge import Judge
from rabbitmq_client import RabbitMQClient
import json
from pymongo import MongoClient
from datetime import datetime


class Evaluator:
    def __init__(self, rabbitmq_host="localhost", rabbitmq_port=5672, rabbitmq_user="guest", rabbitmq_password="guest",
                 mongo_host="localhost", mongo_port=27017, mongo_user="root", mongo_password="root"):
        self.rabbitmq_client = RabbitMQClient(
            host=rabbitmq_host,
            port=rabbitmq_port,
            user=rabbitmq_user,
            password=rabbitmq_password
        )
        self.is_running = True
        self.judge = Judge()

        # Initialize MongoDB client
        mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/"
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client["education"]
        self.evaluation_collection = self.db["evaluation"]

    def process_message(self, message):
        print(f"\n{'='*80}")
        print(f"Processing test result...")
        print(f"{'='*80}")

        test_run_id = message.get("test_run_id", "N/A")
        question = message.get("question", "")
        answer = message.get("answer", "")
        context = message.get("context")
        tool_calls = message.get("tool_calls", [])

        search_documents_content = self.extract_search_documents(tool_calls)

        self.print_test(test_run_id, question, answer, context, tool_calls)

        correctness_input = f"QUESTION: {question}\nRESPONSE: {answer}"
        correctness = self.judge.evaluate_correctness({"input": correctness_input})

        groundedness_input = f"QUESTION: {question}\nCONTEXT: {search_documents_content}\nRESPONSE: {answer}"
        groundedness = self.judge.evaluate_groundedness({"input": groundedness_input})

        evaluation_summary = {
            "test_run_id": test_run_id,
            "question": question,
            "answer": answer,
            "search_documents_content": search_documents_content,
            "correctness": correctness,
            "groundedness": groundedness,
            "timestamp": datetime.now()
        }

        print(evaluation_summary)

        # Save to MongoDB
        try:
            result = self.evaluation_collection.insert_one(evaluation_summary)
            print(f"\nSaved to MongoDB with ID: {result.inserted_id}")
        except Exception as e:
            print(f"\n[ERROR] Failed to save to MongoDB: {e}")

        print(f"\n{'='*80}")
        print(f"Evaluation completed!")
        print(f"{'='*80}\n")

    def extract_search_documents(self, tool_calls):
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

        return search_documents_content

    def print_test(self, test_run_id, question, answer, context, tool_calls):
        print(f"\nTest Run ID: {test_run_id}")
        print(f"Question: {question}")
        print(f"Answer: {answer[:100]}..." if len(answer) > 100 else f"Answer: {answer}")
        print(f"Context available: {context is not None}")
        print(f"Tool calls: {len(tool_calls)} - [{[tool_call["name"] for tool_call in tool_calls]}]")

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
            self.mongo_client.close()
            print("Evaluator stopped.")


def main():
    print("=" * 80)
    print("Starting Evaluator Service")
    print("=" * 80)

    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")

    mongo_host = os.getenv("MONGO_HOST", "localhost")
    mongo_port = int(os.getenv("MONGO_PORT", "27017"))
    mongo_user = os.getenv("MONGO_USER", "root")
    mongo_password = os.getenv("MONGO_PASSWORD", "root")

    print(f"Configuration:")
    print(f"  RabbitMQ Host: {rabbitmq_host}")
    print(f"  RabbitMQ Port: {rabbitmq_port}")
    print(f"  RabbitMQ User: {rabbitmq_user}")
    print(f"  MongoDB Host: {mongo_host}")
    print(f"  MongoDB Port: {mongo_port}")
    print(f"  MongoDB User: {mongo_user}")
    print("=" * 80)

    evaluator = Evaluator(
        rabbitmq_host=rabbitmq_host,
        rabbitmq_port=rabbitmq_port,
        rabbitmq_user=rabbitmq_user,
        rabbitmq_password=rabbitmq_password,
        mongo_host=mongo_host,
        mongo_port=mongo_port,
        mongo_user=mongo_user,
        mongo_password=mongo_password
    )

    evaluator.start()


if __name__ == "__main__":
    main()
