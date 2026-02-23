import asyncio
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Annotated

from aiokafka.errors import BrokerNotAvailableError, KafkaError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import app
from internal.controllers.auth import get_auth_user_info
from internal.databases.database import get_db
from internal.logger.logger import logger
from internal.services.report_service import ReportService
from internal.schemas.kafka_message_schema import KafkaFillReportMessage
from internal.schemas.report_schema import (
    BlankReportSchema,
    ReportCreateSchema,
    ReportSchema,
)
from internal.schemas.user_schema import UserSchema
from internal.transport.consumer import Consumer
from internal.transport.producer import KafkaProducerError, Producer

resources = {}

@asynccontextmanager
async def lifespan(router: APIRouter):
    # Initialize Kafka producer and consumer
    try:
        producer = Producer()
        await producer.report_producer.start()
        resources["kafka_producer"] = producer
        kafka_consumer = Consumer(app.resources["report_service"])
        await kafka_consumer.report_consumer.start()
        asyncio.create_task(kafka_consumer.consume_create_report_message())
    except KafkaError as e:
        raise BrokerNotAvailableError(e)

    yield

    await producer.report_producer.stop()
    resources.clear()


router = APIRouter(lifespan=lifespan)


def get_report_service() -> ReportService:
    report_service = app.resources.get("report_service", None)
    if report_service is None:
        raise ModuleNotFoundError('"report_service" was not initialized')
    return report_service


def get_kafka_producer() -> Producer:
    kafka_producer = resources.get("kafka_producer", None)
    if kafka_producer is None:
        raise ModuleNotFoundError('"kafka_producer" was not initialized')
    return kafka_producer

@app.app.exception_handler(KafkaProducerError)
async def kafka_consumer_exception_handler(request: Request, e: KafkaProducerError):
    logger.error(f"HTTP exception: {e.message}")
    return HTTPException(
        status_code=500,
        detail={"error": e.error_code, "message": e.message},
    )


@router.post("/create_report")
async def create_report(
    report_data: ReportCreateSchema,
    service: Annotated[ReportService, Depends(get_report_service)],
    producer: Annotated[Producer, Depends(get_kafka_producer)],
    db: Annotated[async_sessionmaker[AsyncSession], Depends(get_db)],
    background_tasks: BackgroundTasks,
    user: UserSchema = Depends(get_auth_user_info),
) -> dict[str, str]:
    blank_report = BlankReportSchema(
        report_id=uuid.uuid4(),
        user_id=user.user_id,
        report_year_month=str(report_data.report_year)
        + "-"
        + str(report_data.report_month),
    )
    kafka_message = KafkaFillReportMessage(report_id=blank_report.report_id)
    await service.create_report(db, blank_report)
    background_tasks.add_task(producer.produce_create_report_message, kafka_message)
    return {"report_id": str(blank_report.report_id)}


@router.get("/get_report", response_model=ReportSchema)
async def get_report(
    report_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    db: Annotated[async_sessionmaker[AsyncSession], Depends(get_db)],
) -> ReportSchema:
    report: ReportSchema = await service.get_report(db, report_id)
    return report


@router.delete("/delete_report", status_code=HTTPStatus.NO_CONTENT)
async def delete_report(
    report_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    db: Annotated[async_sessionmaker[AsyncSession], Depends(get_db)],
) -> None:
    await service.delete_report(db, report_id)
