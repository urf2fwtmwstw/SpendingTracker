import json

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from internal.config.config import settings
from internal.databases.database import get_db
from internal.schemas.kafka_message_schema import KafkaFillReportMessage
from internal.services.report_service import ReportService


class KafkaConsumerError(Exception):
    def __init__(self, message: str, error_code: str = "KAFKA_CONSUMER_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class Consumer:
    def __init__(self, report_service: ReportService):
        self.KAFKA_BOOTSTRAP_SERVERS = settings.KAFKA_URL
        self.report_service = report_service
        self.report_consumer = AIOKafkaConsumer(
            "report_tasks",
            bootstrap_servers=self.KAFKA_BOOTSTRAP_SERVERS,
            group_id="report_consumer_group",
            auto_offset_reset="earliest",
            value_deserializer=lambda message: json.loads(message.decode("utf-8")),
        )

    async def consume_create_report_message(self):
        try:
            async for message in self.report_consumer:
                try:
                    report_data = KafkaFillReportMessage(**message.value)
                    async for db in get_db():
                        await self.report_service.fill_report(
                            db,
                            report_data.report_id,
                        )
                except KafkaError as e:
                    raise KafkaConsumerError(f"Kafka consumer failed: {str(e)}")
        finally:
            await self.report_consumer.stop()
