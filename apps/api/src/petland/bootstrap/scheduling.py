from fastapi import FastAPI
from sqlalchemy.engine import Engine

from petland.modules.identity.public.http import HttpIdentity
from petland.modules.scheduling.application.service import Scheduling
from petland.modules.scheduling.infrastructure.store import schedule_store
from petland.modules.scheduling.presentation.http import scheduling_router


def include_scheduling(app: FastAPI, engine: Engine, auth: HttpIdentity) -> None:
    app.include_router(scheduling_router(Scheduling(lambda: schedule_store(engine)), auth))
