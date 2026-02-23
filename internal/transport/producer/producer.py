import json

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from internal.config.config import settings
from internal.schemas.kafka_message_schema import KafkaFillReportMessage


class KafkaProducerError(Exception):
    def __init__(self, message: str, error_code: str = "KAFKA_PRODUCER_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class Producer:
    def __init__(self):
        self.report_producer = AIOKafkaProducer(
            bootstrap_servers=[settings.KAFKA_URL],
            value_serializer=lambda message: json.dumps(message).encode("utf-8"),
        )

    async def produce_create_report_message(
        self, message: KafkaFillReportMessage
    ) -> None:
        try:
            await self.report_producer.send(
                "report_tasks",
                {"report_id": str(message.report_id)},
            )
        except KafkaError as e:
            raise KafkaProducerError(f"Kafka producer failed: {str(e)}")
