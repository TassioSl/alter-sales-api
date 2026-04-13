from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import settings
from .logging_setup import logger
from .schemas import SalesIntakeRequest, StoredSalesEnvelope
from .service import summarize_payload


def save_latest_sales(payload: SalesIntakeRequest) -> StoredSalesEnvelope:
    envelope = StoredSalesEnvelope(
        created_at=datetime.now(timezone.utc),
        payload=payload,
    )
    try:
        settings.data_file.parent.mkdir(parents=True, exist_ok=True)
        settings.data_file.write_text(
            envelope.model_dump_json(indent=2),
            encoding="utf-8",
        )
        summary = summarize_payload(payload)
        logger.info(
            "Lote salvo em {} | total_sales={} total_stores={} total_amount={} coupons_count={}",
            settings.data_file,
            summary["total_sales"],
            summary["total_stores"],
            summary["total_amount"],
            summary["coupons_count"],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao salvar lote em {}", settings.data_file)
        raise RuntimeError(f"Falha ao salvar lote em {settings.data_file}: {exc}") from exc
    return envelope


def load_latest_sales() -> StoredSalesEnvelope | None:
    try:
        if not settings.data_file.exists():
            return None
        raw = settings.data_file.read_text(encoding="utf-8")
        if not raw.strip():
            return None
        envelope = StoredSalesEnvelope.model_validate(json.loads(raw))
        summary = summarize_payload(envelope.payload)
        logger.debug(
            "Lote carregado de {} | total_sales={} total_stores={} total_amount={} coupons_count={}",
            settings.data_file,
            summary["total_sales"],
            summary["total_stores"],
            summary["total_amount"],
            summary["coupons_count"],
        )
        return envelope
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao ler lote salvo em {}", settings.data_file)
        raise RuntimeError(f"Falha ao ler lote salvo em {settings.data_file}: {exc}") from exc
