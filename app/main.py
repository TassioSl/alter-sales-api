from time import perf_counter
from uuid import uuid4
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials

from .config import settings
from .db import DatabaseConnectionError, test_connection
from .live_sales import build_live_envelope, build_live_envelope_today, live_sales_enabled
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
from .service import summarize_payload
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


def _latest_saved_payload_or_none() -> SalesIntakeRequest | None:
    latest = load_latest_sales()
    if latest is None:
        return None
    return latest.payload


def _active_payload_or_404() -> SalesIntakeRequest:
    if live_sales_enabled():
        try:
            payload = build_live_envelope_today().payload
            summary = summarize_payload(payload)
            logger.info(
                "Usando payload ao vivo do banco | total_sales={} total_stores={} total_amount={} coupons_count={}",
                summary["total_sales"],
                summary["total_stores"],
                summary["total_amount"],
                summary["coupons_count"],
            )
        except DatabaseConnectionError as exc:
            fallback_payload = _latest_saved_payload_or_none()
            if fallback_payload is not None:
                summary = summarize_payload(fallback_payload)
                logger.warning(
                    "Banco indisponivel ({}). Usando ultimo lote salvo via intake | total_sales={} total_stores={} total_amount={} coupons_count={}",
                    exc,
                    summary["total_sales"],
                    summary["total_stores"],
                    summary["total_amount"],
                    summary["coupons_count"],
                )
                return fallback_payload
            raise HTTPException(status_code=503, detail=f"Falha ao consultar banco: {exc}") from exc
        if not payload.sales:
            raise HTTPException(status_code=404, detail="Nenhuma venda encontrada no banco para hoje")
        return payload
    fallback_payload = _latest_saved_payload_or_none()
    if fallback_payload is None:
        raise HTTPException(status_code=404, detail="Nenhum lote de vendas armazenado")
    summary = summarize_payload(fallback_payload)
    logger.info(
        "Usando payload salvo | total_sales={} total_stores={} total_amount={} coupons_count={}",
        summary["total_sales"],
        summary["total_stores"],
        summary["total_amount"],
        summary["coupons_count"],
    )
    return fallback_payload


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP {} em {} {}: {}", exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):  # noqa: BLE001
    logger.exception("Erro inesperado em {} {}", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno inesperado"})


@app.get("/")
def root() -> dict:
    return {
        "name": "Alter Sales API",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "endpoints": [
            "/api/health",
            "/api/sales/latest",
            "/api/sales/latest?start_date=2026-04-01&end_date=2026-04-10",
            "/api/alter/feed/per-hour",
            "/api/alter/feed/per-store",
        ],
    }


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
    summary = summarize_payload(payload)
    logger.info(
        "Recebido lote para intake | total_sales={} total_stores={} total_amount={} coupons_count={}",
        summary["total_sales"],
        summary["total_stores"],
        summary["total_amount"],
        summary["coupons_count"],
    )
    save_latest_sales(payload)
    return build_intake_response(payload)


@app.get("/api/sales/latest", response_model=StoredSalesEnvelope)
def sales_latest(
    start_date: date | None = None,
    end_date: date | None = None,
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    _require_auth(credentials)
    if (start_date is None) ^ (end_date is None):
        raise HTTPException(status_code=400, detail="Informe start_date e end_date juntos")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date nao pode ser maior que end_date")
    if live_sales_enabled():
        try:
            if start_date and end_date:
                envelope = build_live_envelope(start_date, end_date)
            else:
                envelope = build_live_envelope_today()
            summary = summarize_payload(envelope.payload)
            logger.info(
                "Retornando sales/latest do banco | start_date={} end_date={} total_sales={} total_stores={} total_amount={} coupons_count={}",
                start_date,
                end_date,
                summary["total_sales"],
                summary["total_stores"],
                summary["total_amount"],
                summary["coupons_count"],
            )
        except DatabaseConnectionError as exc:
            if start_date and end_date:
                raise HTTPException(status_code=503, detail=f"Falha ao consultar banco: {exc}") from exc
            latest = load_latest_sales()
            if latest is not None:
                summary = summarize_payload(latest.payload)
                logger.warning(
                    "Banco indisponivel ({}). Retornando ultimo lote salvo via intake | total_sales={} total_stores={} total_amount={} coupons_count={}",
                    exc,
                    summary["total_sales"],
                    summary["total_stores"],
                    summary["total_amount"],
                    summary["coupons_count"],
                )
                return latest
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
