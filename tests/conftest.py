from asyncio import Queue
from typing import AsyncIterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from internal.application.routers import handlers
from main import app


@pytest.fixture(scope="session", autouse=True)
def mock_kafka():
    queue = Queue()
    
    class MockMessage:
        def __init__(self, value):
            self.value: dict[str, str] = value

    class MockProducer:
        def __init__(self, *args, **kwargs):
            self.queue: Queue = queue

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

        async def send(self, topic, value: dict[str, str]) -> None :
            message: MockMessage = MockMessage(value)
            await self.queue.put(message)
    
    class MockConsumer:
        def __init__(self, *args, **kwargs):
            self.queue: Queue = queue

        async def start(self) -> None:
            pass

        async def stop(self) -> None:
            pass

        def __aiter__(self) -> AsyncIterator[MockMessage]:
            return self

        async def __anext__(self) -> MockMessage:
            return await self.queue.get()


    with patch(
        "internal.transport.producer.producer.AIOKafkaProducer",
        new=MockProducer,
    ), patch(
        "internal.transport.consumer.consumer.AIOKafkaConsumer",
        new=MockConsumer,
    ):
        yield


@pytest.fixture(scope="session")
def client():
    handlers(app)
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="module")
def registered_test_user_data() -> dict[str, str]:
    return {"username": "test_username", "password": "password123"}
