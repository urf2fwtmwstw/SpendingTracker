from datetime import UTC, datetime

from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from internal.databases.database import get_db
from internal.services.report_service import ReportService

jobstores = {"default": MemoryJobStore()}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=UTC)


async def create_scheduled_jobs(report_service: ReportService) -> None:
    @scheduler.scheduled_job("cron", day=20, hour=14, minute=26, second=0)
    async def create_reports(service=report_service):
        date = datetime.now(tz=UTC)
        if date.month != 1:
            month = date.month - 1
            year = date.year
        else:
            month = 12
            year = date.year - 1
        async for db in get_db():
            await service.async_report_generation(db, year, month)

    @scheduler.scheduled_job("cron", minute="*/1")
    async def fill_created_reports(service=report_service):
        async for db in get_db():
            await service.fill_created_reports(db)

    scheduler.start()
