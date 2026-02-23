from contextlib import asynccontextmanager

from fastapi import FastAPI
from internal.scheduler.scheduled_jobs import create_scheduled_jobs, scheduler

from dependencies import get_dependency, initialize_dependencies

resources = {}


# OS signals handling
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing resources...")
    await initialize_dependencies(resources)
    await create_scheduled_jobs(await get_dependency("report_service", resources))
    resources["message"] = "Initialized"
    yield
    print("Cleaning up resources...")
    resources.clear()
    scheduler.shutdown()


# entry point
app = FastAPI(lifespan=lifespan, docs_url="/docs")


# root endpoint
@app.get("/")
async def root():
    return {"message": resources.get("message", "Resource not initialized")}
