from datetime import datetime
from enum import Enum
from uuid import UUID as ReportID

from pydantic import BaseModel, ConfigDict

from internal.schemas.user_schema import UserID


class ReportStatus(str, Enum):
    created = "CREATED"
    generated = "GENERATED"
    failed = "FAILED"


class ReportCreateSchema(BaseModel):
    report_year: int
    report_month: int


class BlankReportSchema(BaseModel):
    report_id: ReportID
    user_id: UserID
    report_year_month: str
    status: ReportStatus = ReportStatus.created


class ReportSchema(BaseModel):
    report_id: ReportID
    report_created: datetime | None
    report_year_month: str
    month_income: float | None
    month_expenses: float | None
    balance: float | None
    most_expensive_categories: str | None
    user_id: ReportID
    status: ReportStatus

    model_config = ConfigDict(from_attributes=True)
