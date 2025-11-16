import pika
import json
import time


class RabbitMQClient:
    def __init__(self, host="localhost", port=5672, user="guest", password="guest"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None

    def connect(self, max_retries=10, retry_delay=2):
        credentials = pika.PlainCredentials(self.user, self.password)
        print(f"Attempting to connect to RabbitMQ at {self.host}:{self.port}")

        for attempt in range(max_retries):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.host,
                        port=self.port,
                        credentials=credentials
                    )
                )
                self.channel = self.connection.channel()
                print(f"Successfully connected to RabbitMQ at {self.host}:{self.port}")
                return
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.ConnectionClosedByBroker) as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Failed to connect to RabbitMQ after {max_retries} attempts")
                    raise

    def declare_queue(self, queue_name, durable=True):
        if not self.channel:
            raise Exception("Not connected to RabbitMQ. Call connect() first.")
        self.channel.queue_declare(queue=queue_name, durable=durable)

    def send_message(self, queue_name, message, persistent=True):
        if not self.channel:
            raise Exception("Not connected to RabbitMQ. Call connect() first.")

        properties = None
        if persistent:
            properties = pika.BasicProperties(delivery_mode=2)

        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=properties
            )
        except (pika.exceptions.StreamLostError, pika.exceptions.ConnectionClosedByBroker, pika.exceptions.AMQPConnectionError) as e:
            print(f"Connection lost, reconnecting... Error: {e}")
            self.connect()
            self.declare_queue(queue_name, durable=True)
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=properties
            )

    def consume_messages(self, queue_name, callback, auto_ack=False):
        if not self.channel:
            raise Exception("Not connected to RabbitMQ. Call connect() first.")

        def message_callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=message_callback,
            auto_ack=auto_ack
        )

        print(f"Waiting for messages from queue '{queue_name}'. To exit press CTRL+C")
        self.channel.start_consuming()

    def stop_consuming(self):
        if self.channel:
            self.channel.stop_consuming()

    def close(self):
        if self.connection:
            self.connection.close()
