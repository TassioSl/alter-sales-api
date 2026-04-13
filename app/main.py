from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials

from .config import settings
from .db import DatabaseConnectionError, test_connection
from .live_sales import build_live_envelope_today, live_sales_enabled
from .logging_setup import configure_logging, logger
from .schemas import (
    AlterPerHourPreview,
    AlterPerStorePreview,
    SalesIntakeRequest,
    SalesIntakeResponse,
    StoredSalesEnvelope,
)
from .security import require_basic_auth, security
from .service import build_intake_response, build_per_hour_preview, build_per_store_preview
from .storage import load_latest_sales, save_latest_sales


configure_logging()
app = FastAPI(title="Alter Sales API", version="0.1.0")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    t0 = perf_counter()
    request_id = uuid4().hex[:8]
    try:
        response = await call_next(request)
        elapsed = (perf_counter() - t0) * 1000
        logger.info(
            "[{}] {} {} -> {} ({:.1f} ms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        response.headers["X-Request-Id"] = request_id
        return response
    except Exception:  # noqa: BLE001
        elapsed = (perf_counter() - t0) * 1000
        logger.exception(
            "[{}] {} {} -> ERROR ({:.1f} ms)",
            request_id,
            request.method,
            request.url.path,
            elapsed,
        )
        raise


def _require_auth(credentials: HTTPBasicCredentials | None) -> None:
    require_basic_auth(credentials)


def _active_payload_or_404() -> SalesIntakeRequest:
    if live_sales_enabled():
        try:
            payload = build_live_envelope_today().payload
        except DatabaseConnectionError as exc:
            raise HTTPException(status_code=503, detail=f"Falha ao consultar banco: {exc}") from exc
        if not payload.sales:
            raise HTTPException(status_code=404, detail="Nenhuma venda encontrada no banco para hoje")
        return payload
    latest = load_latest_sales()
    if latest is None:
        raise HTTPException(status_code=404, detail="Nenhum lote de vendas armazenado")
    return latest.payload


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP {} em {} {}: {}", exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: BLE001
    logger.exception("Erro inesperado em {} {}", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno inesperado"})


@app.get("/api/health")
def health() -> dict:
    latest = load_latest_sales()
    db_status = test_connection() if live_sales_enabled() else {"ok": False, "error": "Variaveis SQL_* ausentes"}
    return {
        "status": "ok",
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "disable_inbound_auth": settings.disable_inbound_auth,
        "inbound_auth_configured": bool(settings.inbound_api_username and settings.inbound_api_password),
        "live_sales_enabled": live_sales_enabled(),
        "live_store_code": settings.live_store_code,
        "live_store_alias_id": settings.live_store_alias_id,
        "db_status": db_status,
        "latest_sales_loaded": latest is not None,
    }


@app.post("/api/sales/intake", response_model=SalesIntakeResponse)
def sales_intake(
    payload: SalesIntakeRequest,
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    _require_auth(credentials)
    if not payload.sales:
        raise HTTPException(status_code=400, detail="sales nao pode ser vazio")
    logger.info("Recebido lote com {} vendas para intake", len(payload.sales))
    save_latest_sales(payload)
    return build_intake_response(payload)


@app.get("/api/sales/latest", response_model=StoredSalesEnvelope)
def sales_latest(credentials: HTTPBasicCredentials | None = Depends(security)):
    _require_auth(credentials)
    if live_sales_enabled():
        try:
            envelope = build_live_envelope_today()
        except DatabaseConnectionError as exc:
            raise HTTPException(status_code=503, detail=f"Falha ao consultar banco: {exc}") from exc
        if not envelope.payload.sales:
            raise HTTPException(status_code=404, detail="Nenhuma venda encontrada no banco para hoje")
        return envelope
    latest = load_latest_sales()
    if latest is None:
        raise HTTPException(status_code=404, detail="Nenhum lote de vendas armazenado")
    return latest


@app.post("/api/alter/preview/per-hour", response_model=AlterPerHourPreview)
def preview_per_hour(
    payload: SalesIntakeRequest,
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    _require_auth(credentials)
    if not payload.sales:
        raise HTTPException(status_code=400, detail="sales nao pode ser vazio")
    logger.info("Gerando preview por hora com {} vendas", len(payload.sales))
    return build_per_hour_preview(payload)


@app.post("/api/alter/preview/per-store", response_model=AlterPerStorePreview)
def preview_per_store(
    payload: SalesIntakeRequest,
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    _require_auth(credentials)
    if not payload.sales:
        raise HTTPException(status_code=400, detail="sales nao pode ser vazio")
    try:
        logger.info("Gerando preview por loja com {} vendas", len(payload.sales))
        return build_per_store_preview(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/alter/feed/per-hour", response_model=AlterPerHourPreview)
def feed_per_hour(credentials: HTTPBasicCredentials | None = Depends(security)):
    _require_auth(credentials)
    payload = _active_payload_or_404()
    logger.info("Entregando feed por hora com {} vendas", len(payload.sales))
    return build_per_hour_preview(payload)


@app.get("/api/alter/feed/per-store", response_model=AlterPerStorePreview)
def feed_per_store(credentials: HTTPBasicCredentials | None = Depends(security)):
    _require_auth(credentials)
    try:
        payload = _active_payload_or_404()
        logger.info("Entregando feed por loja com {} vendas", len(payload.sales))
        return build_per_store_preview(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
