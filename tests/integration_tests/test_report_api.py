import datetime
import time

from fastapi.testclient import TestClient

from tests.utils import (
    authorize,
    generate_category,
    generate_transaction,
    get_all_category_ids,
    get_all_transaction_ids,
)


def get_report_id(
    client: TestClient,
    registered_test_user_data: dict[str, str],
    report_year: int = datetime.datetime.now(tz=datetime.UTC).year,
    report_month: int = datetime.datetime.now(tz=datetime.UTC).month,
) -> str:
    headers: dict[str, str] = authorize(client, registered_test_user_data)
    return client.post(
        "api/v1/create_report",
        json={
            "report_year": report_year,
            "report_month": report_month,
        },
        headers=headers,
    ).json()["report_id"]


def create_categories_for_report(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    for _ in range(6):
        client.post(
            "api/v1/categories",
            json=generate_category(category_type="expenses"),
            headers=headers,
        )

    client.post(
        "api/v1/categories",
        json=generate_category(category_type="income"),
        headers=headers,
    )


def create_transactions_for_report(
    client: TestClient,
    headers: dict[str, str],
) -> None:
    category_ids: list[str] = get_all_category_ids(client, headers)
    for category_id in category_ids:
        transaction = generate_transaction(
            client,
            category_id,
            transaction_date=datetime.datetime.now(tz=datetime.UTC).isoformat(),
        )
        client.post("api/v1/transactions", json=transaction, headers=headers)


def generate_test_data_for_report(
    client: TestClient,
    registered_test_user_data: dict[str, str],
) -> None:
    headers: dict[str, str] = authorize(client, registered_test_user_data)
    create_categories_for_report(client, headers)
    create_transactions_for_report(client, headers)


def get_expected_report_data(
    client: TestClient,
    registered_test_user_data: dict[str, str],
) -> dict[str, float | str]:
    headers: dict[str, str] = authorize(client, registered_test_user_data)
    total_transactions: list[dict[str, float | str]] = client.get(
        "api/v1/transactions",
        headers=headers,
    ).json()
    expense_transactions: list[dict[str, float | str]] = [
        transaction
        for transaction in total_transactions
        if transaction["transaction_type"] == "expenses"
    ]
    income: float = 0
    expenses: float = 0
    balance: float = 0
    most_expensive_categories = ", ".join(
        [
            transaction["category_id"]
            for transaction in sorted(
                expense_transactions,
                key=lambda transaction: transaction["transaction_value"],
                reverse=True,
            )
        ][:5]
    )
    for transaction in total_transactions:
        match transaction["transaction_type"]:
            case "income":
                income += transaction["transaction_value"]
                balance += transaction["transaction_value"]
            case "expenses":
                expenses += transaction["transaction_value"]
                balance -= transaction["transaction_value"]
    return {
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "balance": round(balance, 2),
        "most_expensive_categories": most_expensive_categories,
    }


def delete_test_data_for_reports(
    client: TestClient,
    registered_test_user_data: dict[str, str],
) -> None:
    headers: dict[str, str] = authorize(client, registered_test_user_data)
    transaction_ids: list[str] = get_all_transaction_ids(client, headers)
    [
        client.delete(f"api/v1/transactions/{transaction_id}", headers=headers)
        for transaction_id in transaction_ids
    ]
    category_ids: list[str] = [
        category["category_id"]
        for category in client.get(
            "api/v1/categories",
            headers=headers,
        ).json()
    ]
    [
        client.delete(f"api/v1/categories/{category_id}", headers=headers)
        for category_id in category_ids
    ]


def test_create_report(
    client: TestClient,
    registered_test_user_data: dict[str, str],
) -> None:
    headers: dict[str, str] = authorize(client, registered_test_user_data)
    response = client.post(
        "api/v1/create_report",
        json={
            "report_year": datetime.datetime.now(datetime.UTC).year,
            "report_month": datetime.datetime.now(datetime.UTC).month,
        },
        headers=headers,
    )
    report_id = response.json()["report_id"]
    client.delete(
        "api/v1/delete_report",
        params={"report_id": report_id},
    )
    assert response.status_code == 200
    assert isinstance(report_id, str)
    assert len(report_id) == 36


def test_get_report(
    client: TestClient,
    registered_test_user_data: dict[str, str],
) -> None:
    generate_test_data_for_report(client, registered_test_user_data)
    expected_report_data: dict[str, float | str] = get_expected_report_data(
        client,
        registered_test_user_data,
    )
    report_id: str = get_report_id(client, registered_test_user_data)
    time.sleep(5)
    response = client.get(
        "api/v1/get_report",
        params={"report_id": report_id},
    )
    report = response.json()
    delete_test_data_for_reports(client, registered_test_user_data)
    assert response.status_code == 200
    assert report["month_income"] == expected_report_data["income"]
    assert report["month_expenses"] == expected_report_data["expenses"]
    assert report["balance"] == expected_report_data["balance"]
    assert (
        report["most_expensive_categories"]
        == expected_report_data["most_expensive_categories"]
    )
    assert report["status"] == "GENERATED"


def test_delete_report(
    client: TestClient,
    registered_test_user_data: dict[str, str],
) -> None:
    report_id: str = get_report_id(client, registered_test_user_data)
    response = client.delete(
        "api/v1/delete_report",
        params={"report_id": report_id},
    )
    delete_test_data_for_reports(client, registered_test_user_data)
    assert response.status_code == 204
