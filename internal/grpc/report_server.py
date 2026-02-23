import asyncio
import uuid

from grpc import aio

from dependencies import get_dependency, initialize_dependencies
from internal.databases.database import get_db
from internal.grpc.pb import report_pb2, report_pb2_grpc
from internal.logger.logger import logger
from internal.schemas.kafka_message_schema import KafkaFillReportMessage
from internal.schemas.report_schema import BlankReportSchema
from internal.services.report_service import ReportService
from internal.transport.producer import Producer

# Coroutines to be invoked when the event loop is shutting down.
_cleanup_coroutines = []


class ReportServiceServicer(report_pb2_grpc.ReportServiceServicer):
    def __init__(self, report_service: ReportService, kafka_producer: Producer) -> None:
        self.report_service = report_service
        self.kafka_producer = kafka_producer

    async def CreateReport(
        self,
        request: report_pb2.ReportRequest,
        context: aio.ServicerContext,
    ) -> report_pb2.ReportResponse:
        logger.info("Received request")

        blank_report = BlankReportSchema(
            report_id=uuid.uuid4(),
            user_id=uuid.UUID(request.user_id),
            report_year_month=request.year_month,
        )
        async for db in get_db():
            await self.report_service.create_report(db, blank_report)

        kafka_message = KafkaFillReportMessage(report_id=blank_report.report_id)
        await self.kafka_producer.produce_create_report_message(kafka_message)
        return report_pb2.ReportResponse(report_id=str(blank_report.report_id))


async def serve() -> None:
    kafka_producer = Producer()
    await kafka_producer.report_producer.start()

    resources = {}
    await initialize_dependencies(resources)
    report_service: ReportService = await get_dependency("report_service", resources)

    server = aio.server()
    report_pb2_grpc.add_ReportServiceServicer_to_server(
        ReportServiceServicer(report_service, kafka_producer),
        server,
    )
    listen_address: str = "0.0.0.0:50052"
    server.add_insecure_port(listen_address)
    logger.info("Starting grpc server on %s", listen_address)
    await server.start()

    async def server_graceful_shutdown():
        logger.info("Starting graceful shutdown...")
        await kafka_producer.report_producer.stop()
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(serve())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
