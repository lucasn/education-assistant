import pika
import json


class RabbitMQClient:
    def __init__(self, host="localhost", port=5672, user="guest", password="guest"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None

    def connect(self):
        credentials = pika.PlainCredentials(self.user, self.password)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials
            )
        )
        self.channel = self.connection.channel()

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

    def close(self):
        if self.connection:
            self.connection.close()
