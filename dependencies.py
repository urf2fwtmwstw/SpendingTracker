from internal.auth.repository import UsersRepository
from internal.categories.repository import CategoriesRepository
from internal.reports.repository import ReportsRepository
from internal.services.category_service import CategoryService
from internal.services.report_service import ReportService
from internal.services.transaction_service import TransactionService
from internal.services.user_service import UserService
from internal.transactions.repository import TransactionsRepository


async def get_dependency(dependency_name: str, resource):
    dependency = resource.get(f"{dependency_name}", None)
    if dependency is None:
        raise ModuleNotFoundError(f'"{dependency_name}" was not initialized')
    return dependency


async def initialize_repositories(resources) -> None:
    resources["user_repository"] = UsersRepository()
    resources["category_repository"] = CategoriesRepository()
    resources["transaction_repository"] = TransactionsRepository()
    resources["report_repository"] = ReportsRepository()


async def initialize_services(resources) -> None:
    resources["user_service"] = UserService(
        await get_dependency("user_repository", resources)
    )
    resources["category_service"] = CategoryService(
        await get_dependency("category_repository", resources)
    )
    resources["transaction_service"] = TransactionService(
        await get_dependency("transaction_repository", resources)
    )
    resources["report_service"] = ReportService(
        await get_dependency("report_repository", resources),
        await get_dependency("transaction_service", resources),
        await get_dependency("user_service", resources),
    )


async def initialize_dependencies(resources) -> None:
    await initialize_repositories(resources)
    await initialize_services(resources)
