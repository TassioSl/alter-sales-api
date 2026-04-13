from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .config import settings
from .db import fetch_all_dict, sql_is_configured
from .schemas import SaleIn, SalesIntakeRequest, StoredSalesEnvelope


REAL_SALES_SQL = """
SELECT
    TRY_CAST(LEFT(V.NomeFilialFranqueada, 4) AS INT) AS codigo_filial,
    V.NomeFilialFranqueada AS nome_filial,
    CAST(V.Hora AS datetime) AS data_hora,
    V.DocumentoNumero AS documento_numero,
    MAX(V.IdTransacao) AS id_transacao,
    MAX(V.Transacao) AS nome_transacao,
    MAX(V.AnaliseVendas) AS analise_vendas,
    SUM(V.VLiquido) AS valor_liquido,
    SUM(V.QItem) AS qtde_itens,
    MAX(V.VendedorCodigo) AS vendedor_codigo,
    MAX(V.VendedorNome) AS vendedor_nome,
    CAST(NULL AS varchar(50)) AS return_id
FROM dbo.V_BIO_FATO_VENDA_PRODUTO V
WHERE
    V.Movimento >= ?
    AND V.Movimento < ?
    AND TRY_CAST(LEFT(V.NomeFilialFranqueada, 4) AS INT) = ?
    AND (
        TRY_CAST(LEFT(V.NomeFilialFranqueada, 4) AS INT) NOT BETWEEN 26 AND 99
        OR TRY_CAST(LEFT(V.NomeFilialFranqueada, 4) AS INT) = 27
    )
GROUP BY
    TRY_CAST(LEFT(V.NomeFilialFranqueada, 4) AS INT),
    V.NomeFilialFranqueada,
    CAST(V.Hora AS datetime),
    V.DocumentoNumero
ORDER BY data_hora DESC;
"""


def live_sales_enabled() -> bool:
    return sql_is_configured()


def _movement_type(row: dict) -> str:
    analysis = str(row.get("analise_vendas") or "").upper()
    transaction_name = str(row.get("nome_transacao") or "").upper()
    total_amount = float(row.get("valor_liquido") or 0)
    if "DEVOL" in analysis or "DEVOL" in transaction_name or total_amount < 0:
        return "devolucao"
    return "venda"


def _should_include_row(row: dict) -> bool:
    analysis = str(row.get("analise_vendas") or "").upper()
    transaction_name = str(row.get("nome_transacao") or "").upper()
    if "INVALID" in analysis:
        return False
    if "CANCELADA" in transaction_name or "CANCELADO" in transaction_name:
        return False
    return True


def fetch_live_payload(start_date: date, end_date: date) -> SalesIntakeRequest:
    rows = fetch_all_dict(
        REAL_SALES_SQL,
        (
            start_date,
            end_date + timedelta(days=1),
            settings.live_store_code,
        ),
    )

    sales: list[SaleIn] = []
    for row in rows:
        if not _should_include_row(row):
            continue
        sold_at = row.get("data_hora")
        if isinstance(sold_at, str):
            sold_at_str = sold_at
        elif isinstance(sold_at, datetime):
            sold_at_str = sold_at.isoformat()
        else:
            sold_at_str = str(sold_at)

        documento = str(row.get("documento_numero") or "sem-documento").strip()
        movement_type = _movement_type(row)
        sales.append(
            SaleIn(
                sale_id=f"{settings.live_store_code}-{documento}-{sold_at_str}",
                coupon_number=documento,
                movement_type=movement_type,
                sales_analysis=str(row.get("analise_vendas") or "").strip() or None,
                transaction_id=int(row["id_transacao"]) if row.get("id_transacao") is not None else None,
                transaction_name=str(row.get("nome_transacao") or "").strip() or None,
                store_id=str(row.get("nome_filial") or f"{settings.live_store_code:03d}"),
                store_alias_id=settings.live_store_alias_id,
                sold_at=sold_at_str,
                total_amount=row.get("valor_liquido") or 0,
                items_count=int(float(row.get("qtde_itens") or 0)),
                seller_code=str(row.get("vendedor_codigo") or "0"),
                seller_name=str(row.get("vendedor_nome") or "NAO INFORMADO").strip(),
                return_id=documento if movement_type == "devolucao" else row.get("return_id"),
            )
        )
    return SalesIntakeRequest(sales=sales)


def fetch_live_payload_today() -> SalesIntakeRequest:
    today = date.today()
    return fetch_live_payload(today, today)


def build_live_envelope(start_date: date, end_date: date) -> StoredSalesEnvelope:
    return StoredSalesEnvelope(
        created_at=datetime.now(timezone.utc),
        payload=fetch_live_payload(start_date, end_date),
    )


def build_live_envelope_today() -> StoredSalesEnvelope:
    return build_live_envelope(date.today(), date.today())
