import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from internal.reports.repository import ReportsRepository
from internal.schemas.report_schema import (
    BlankReportSchema,
    ReportSchema,
    ReportStatus,
)
from internal.schemas.transaction_schema import TransactionSchema
from internal.schemas.user_schema import UserSchema
from internal.services.transaction_service import TransactionService
from internal.services.user_service import UserService


class ReportService:
    def __init__(
        self,
        repo: ReportsRepository,
        transaction_service: TransactionService,
        user_service: UserService = None,
    ):
        self.repo = repo
        self.transaction_service = transaction_service
        self.user_service = user_service

    @staticmethod
    async def __get_month_dependant_attributes(
        report_month_transactions: list[TransactionSchema],
    ) -> dict[str, float | dict[str, float]]:
        month_income: float = 0
        month_expenses: float = 0
        expenses_in_category: dict[str, float] = {}
        for transaction in report_month_transactions:
            if transaction.transaction_type == "income":
                month_income += transaction.transaction_value
            else:
                expense_value: float = transaction.transaction_value
                month_expenses += expense_value
                category_id = str(transaction.category_id)
                expenses_in_category[category_id] = (
                    expenses_in_category.get(category_id, 0) + expense_value
                )
        return {
            "month_income": month_income,
            "month_expenses": month_expenses,
            "expenses_in_category": expenses_in_category,
        }

    @staticmethod
    async def __get_balance(transactions: list[TransactionSchema]) -> float:
        balance: float = 0
        for transaction in transactions:
            if transaction.transaction_type == "income":
                balance += transaction.transaction_value
            elif transaction.transaction_type == "expenses":
                balance -= transaction.transaction_value
        return balance

    # sort dictionary of {category_id: expenses} by value and return a string with ids of the most expensive categories
    @staticmethod
    async def __sort_category_dict(expense_categories: dict[str, float]) -> str:
        most_expensive_categories_ids = [
            str(category_id)
            for category_id, expenses in sorted(
                expense_categories.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ][:5]
        return ", ".join(most_expensive_categories_ids)

    async def create_report(
        self,
        session: async_sessionmaker[AsyncSession],
        blank_report: BlankReportSchema,
    ) -> None:
        await self.repo.add_report(session, blank_report)

    async def fill_report(
        self,
        session: async_sessionmaker[AsyncSession],
        report_id: str,
    ):
        report: ReportSchema = await self.get_report(session, report_id)
        try:
            await self.generate_report(session, report)
        except Exception:
            report.status = ReportStatus.failed
            await self.repo.update_report(session, report)

    async def generate_report(
        self,
        session: async_sessionmaker[AsyncSession],
        report: ReportSchema,
    ) -> None:
        user_id: str = str(report.user_id)
        report_year_month: list[int] = list(
            map(int, report.report_year_month.split("-"))
        )
        report_year: int = report_year_month[0]
        report_month: int = report_year_month[1]
        transactions: list[
            TransactionSchema
        ] = await self.transaction_service.get_transactions(session, user_id)
        report_month_transactions = [
            transaction
            for transaction in transactions
            if transaction.transaction_date.year == report_year
            and transaction.transaction_date.month == report_month
        ]
        month_dependant_attributes = await self.__get_month_dependant_attributes(
            report_month_transactions
        )
        month_income: float = month_dependant_attributes["month_income"]
        month_expenses: float = month_dependant_attributes["month_expenses"]
        expenses_in_category: dict[str, float] = month_dependant_attributes[
            "expenses_in_category"
        ]
        most_expensive_categories: str = await self.__sort_category_dict(
            expenses_in_category
        )
        balance: float = await self.__get_balance(transactions)

        report.month_income = month_income
        report.month_expenses = month_expenses
        report.balance = balance
        report.most_expensive_categories = most_expensive_categories
        report.status = ReportStatus.generated

        await self.repo.update_report(session, report)

    async def async_report_generation(
        self,
        session: async_sessionmaker[AsyncSession],
        report_year: int,
        report_month: int,
    ) -> None:
        async_tasks = []
        users: list[UserSchema] = await self.user_service.get_users(session)

        for user in users:
            report_data = BlankReportSchema(
                user_id=user.user_id,
                report_id=uuid.uuid4(),
                report_year_month=str(report_year) + "-" + str(report_month),
            )
            task = asyncio.create_task(
                self.create_report(
                    session,
                    report_data,
                )
            )
            async_tasks.append(task)
        await asyncio.gather(*async_tasks)

    async def fill_created_reports(
        self,
        session: async_sessionmaker[AsyncSession],
    ) -> None:
        async_tasks = []
        created_reports: list[ReportSchema] = await self.repo.get_created_reports(
            session
        )
        for report in created_reports:
            task = asyncio.create_task(
                self.fill_report(
                    session,
                    str(report.report_id),
                ),
            )
            async_tasks.append(task)
        await asyncio.gather(*async_tasks)

    async def get_report(
        self,
        session: async_sessionmaker[AsyncSession],
        report_id: str,
    ) -> ReportSchema:
        report: ReportSchema = await self.repo.get_report(session, report_id)
        return report

    async def delete_report(
        self,
        session: async_sessionmaker[AsyncSession],
        report_id,
    ) -> None:
        await self.repo.delete_report(session, report_id)
