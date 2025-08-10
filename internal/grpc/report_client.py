import asyncio

from grpc import aio

import internal.grpc.pb.report_pb2 as report_pb2
import internal.grpc.pb.report_pb2_grpc as report_pb2_grpc


async def run():
    async with aio.insecure_channel("0.0.0.0:50052") as channel:
        stub = report_pb2_grpc.ReportServiceStub(channel)
        response = await stub.CreateReport(
            report_pb2.ReportRequest(
                user_id="5e60fb4c-8c82-467b-954c-945c5d01135a",
                year_month="2025-8",
            )
        )
    print(response.report_id)


if __name__ == "__main__":
    asyncio.run(run())
