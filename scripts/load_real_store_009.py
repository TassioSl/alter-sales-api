from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib import error as urllib_error
from urllib import request as urllib_request


ROOT = Path(__file__).resolve().parents[1]


def _find_dashboard_backend(start: Path) -> Path:
    for base in [start, *start.parents]:
        candidate = base / "dashboard-app" / "backend"
        if candidate.exists():
            return candidate
        sibling_candidate = base.parent / "dashboard-app" / "backend"
        if sibling_candidate.exists():
            return sibling_candidate
    raise RuntimeError("Nao foi possivel localizar dashboard-app/backend a partir do script atual.")


DASHBOARD_BACKEND = _find_dashboard_backend(ROOT)
if str(DASHBOARD_BACKEND) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_BACKEND))

from app.db import fetch_all_dict  # type: ignore  # noqa: E402


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
    AND (
        UPPER(COALESCE(V.AnaliseVendas, '')) LIKE '%VENDA%'
        OR UPPER(COALESCE(V.AnaliseVendas, '')) LIKE '%DEVOL%'
        OR UPPER(COALESCE(V.Transacao, '')) LIKE '%DEVOL%'
    )
GROUP BY
    TRY_CAST(LEFT(V.NomeFilialFranqueada, 4) AS INT),
    V.NomeFilialFranqueada,
    CAST(V.Hora AS datetime),
    V.DocumentoNumero
ORDER BY data_hora DESC;
"""


def _movement_type(row: dict) -> str:
    analysis = str(row.get("analise_vendas") or "").upper()
    transaction_name = str(row.get("nome_transacao") or "").upper()
    total_amount = float(row.get("valor_liquido") or 0)
    if "DEVOL" in analysis or "DEVOL" in transaction_name or total_amount < 0:
        return "devolucao"
    return "venda"


def build_payload(start_date: date, end_date: date, store_code: int, store_alias_id: int | None = None) -> dict:
    rows = fetch_all_dict(
        REAL_SALES_SQL,
        (
            start_date,
            end_date + timedelta(days=1),
            store_code,
        ),
    )

    sales: list[dict] = []
    for row in rows:
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
            {
                "sale_id": f"{store_code}-{documento}-{sold_at_str}",
                "coupon_number": documento,
                "movement_type": movement_type,
                "sales_analysis": str(row.get("analise_vendas") or "").strip() or None,
                "transaction_id": int(row["id_transacao"]) if row.get("id_transacao") is not None else None,
                "transaction_name": str(row.get("nome_transacao") or "").strip() or None,
                "store_id": str(row.get("nome_filial") or f"{store_code:03d}"),
                "store_alias_id": store_alias_id,
                "sold_at": sold_at_str,
                "total_amount": float(row.get("valor_liquido") or 0),
                "items_count": int(float(row.get("qtde_itens") or 0)),
                "seller_code": str(row.get("vendedor_codigo") or "0"),
                "seller_name": str(row.get("vendedor_nome") or "NAO INFORMADO").strip(),
                "return_id": documento if movement_type == "devolucao" else None,
            }
        )
    return {"sales": sales}


def post_json(url: str, payload: dict, username: str = "", password: str = "") -> str:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if username and password:
        pair = f"{username}:{password}".encode("ascii")
        headers["Authorization"] = "Basic " + base64.b64encode(pair).decode("ascii")
    req = urllib_request.Request(
        url,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=60) as response:
            return response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    today = date.today().isoformat()
    parser.add_argument("--start-date", default=today)
    parser.add_argument("--end-date", default=today)
    parser.add_argument("--store-code", type=int, default=9)
    parser.add_argument("--store-alias-id", type=int, default=9)
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8091")
    parser.add_argument("--api-username", default="")
    parser.add_argument("--api-password", default="")
    parser.add_argument("--mode", choices=["payload", "intake"], default="payload")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    payload = build_payload(start_date, end_date, args.store_code, args.store_alias_id)
    if not payload["sales"]:
        print(
            json.dumps(
                {
                    "status": "empty",
                    "message": "Nenhuma venda encontrada para a data informada.",
                    "store_code": args.store_code,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.mode == "payload":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(post_json(f"{args.api_base_url}/api/sales/intake", payload, args.api_username, args.api_password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
