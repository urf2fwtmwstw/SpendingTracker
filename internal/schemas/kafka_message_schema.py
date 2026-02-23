from pydantic import BaseModel

from internal.schemas.report_schema import ReportID


class KafkaFillReportMessage(BaseModel):
    report_id: ReportID
