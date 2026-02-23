from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from internal.databases.models import Report as ReportModel
from internal.databases.models import ReportStatus
from internal.schemas.report_schema import BlankReportSchema, ReportSchema


class ReportsRepository:
    @staticmethod
    async def add_report(
        async_session: async_sessionmaker[AsyncSession],
        report_data: BlankReportSchema,
    ) -> None:
        async with async_session() as session:
            report = ReportModel(
                report_id=report_data.report_id,
                report_year_month=report_data.report_year_month,
                user_id=report_data.user_id,
                status=report_data.status,
            )
            session.add(report)
            await session.commit()

    @staticmethod
    async def get_created_reports(
        async_session: async_sessionmaker[AsyncSession],
    ) -> list[ReportSchema]:
        async with async_session() as session:
            statement = select(ReportModel).filter(
                ReportModel.status == ReportStatus.created
            )
            result = await session.execute(statement)
            created_reports: list[ReportSchema] = [
                ReportSchema.model_validate(created_report)
                for created_report in result.scalars()
            ]
            return created_reports

    @staticmethod
    async def get_report(
        async_session: async_sessionmaker[AsyncSession],
        report_id: str,
    ) -> ReportSchema:
        async with async_session() as session:
            statement = select(ReportModel).filter(ReportModel.report_id == report_id)
            result = await session.execute(statement)
            reportDB: ReportModel = result.scalars().one()
            report = ReportSchema.model_validate(reportDB)
            return report

    @staticmethod
    async def update_report(
        async_session: async_sessionmaker[AsyncSession],
        report_data: ReportSchema,
    ):
        async with async_session() as session:
            statement = (
                update(ReportModel)
                .where(ReportModel.report_id == report_data.report_id)
                .values(
                    month_income=report_data.month_income,
                    month_expenses=report_data.month_expenses,
                    balance=report_data.balance,
                    most_expensive_categories=report_data.most_expensive_categories,
                    status=report_data.status,
                )
            )
            await session.execute(statement)
            await session.commit()

    @staticmethod
    async def delete_report(
        async_session: async_sessionmaker[AsyncSession],
        report_id: str,
    ) -> None:
        async with async_session() as session:
            statement = delete(ReportModel).where(ReportModel.report_id == report_id)
            await session.execute(statement)
            await session.commit()
