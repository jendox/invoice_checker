from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import async_session_factory
from app.routers import exports, rules, statements, transactions, web, web_reference
from app.services.seed_reference_data import seed_reference_data
from app.services.seed_rules import seed_default_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_factory() as session:
        await seed_reference_data(session)
        await seed_default_rules(session)
    yield


app = FastAPI(
    title="Invoice Checker",
    description="Bank statement analyzer for invoice tracking",
    version="0.1.0",
    lifespan=lifespan,
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(web.router)
app.include_router(web_reference.router)
app.include_router(statements.router)
app.include_router(transactions.router)
app.include_router(exports.router)
app.include_router(rules.router)

# Alias: GET /invoice-requests (spec endpoint)
from app.routers.transactions import invoice_requests as _invoice_requests  # noqa: E402

app.add_api_route(
    "/invoice-requests",
    _invoice_requests,
    methods=["GET"],
    tags=["transactions"],
    response_model=list,
)


@app.get("/health")
async def health():
    return {"status": "ok"}
