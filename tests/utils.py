import random
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def generate_user(
    username: str = None,
    password: str = None,
) -> dict[str, str]:
    return {
        "username": username or f"test_username_{random.randint(1000, 999999)}",
        "password": password or f"password{random.randint(1000, 999999)}",
    }


def generate_category(
    category_name: str = f"name_{random.randint(100, 1000)}",
    category_description: str = f"description_{random.randint(100, 1000)}",
    category_type: str = random.choice(["expenses", "income"]),
) -> dict[str, str]:
    return {
        "category_name": category_name,
        "category_description": category_description,
        "category_type": category_type,
    }


def generate_transaction(
    client: TestClient,
    category_id: str,
    transaction_value: float = round(random.uniform(0.01, 10000.00), 2),
    transaction_description: str = f"description_{random.randint(100, 1000)}",
    transaction_date: str = (
        datetime.now(tz=UTC) + timedelta(days=random.randint(-365, 365))
    )
    .isoformat()
    .replace("+00:00", "Z"),
) -> dict[str, str | float]:
    category: dict[str, str] = client.get(f"api/v1/categories/{category_id}").json()

    return {
        "transaction_type": category["category_type"],
        "transaction_value": transaction_value,
        "transaction_date": transaction_date,
        "transaction_description": transaction_description,
        "category_id": category_id,
    }


def authorize(client: TestClient, user_data: dict[str, str]) -> dict[str, str]:
    token = client.post("api/v1/signin", data=user_data).json()
    return {"Authorization": f"{token['token_type']} {token['access_token']}"}


def get_user_id(client: TestClient, user_data: dict[str, str]) -> str:
    headers: dict[str, str] = authorize(client, user_data)
    return client.get(
        "api/v1/verify",
        headers=headers,
    ).json()["user_id"]


def get_last_category_id(client: TestClient, user_data: dict[str, str]) -> str:
    headers: dict[str, str] = authorize(client, user_data)
    return client.get(
        "api/v1/categories",
        headers=headers,
    ).json()[-1]["category_id"]


def get_last_transaction_id(client: TestClient, user_data: dict[str, str]) -> str:
    headers: dict[str, str] = authorize(client, user_data)
    return client.get(
        "api/v1/transactions",
        headers=headers,
    ).json()[-1]["transaction_id"]


def get_all_transaction_ids(client: TestClient, headers: dict[str, str]) -> list[str]:
    return [
        category["transaction_id"]
        for category in client.get(
            "api/v1/transactions",
            headers=headers,
        ).json()
    ]


def get_all_category_ids(client: TestClient, headers: dict[str, str]) -> list[str]:
    return [
        category["category_id"]
        for category in client.get(
            "api/v1/categories",
            headers=headers,
        ).json()
    ]
