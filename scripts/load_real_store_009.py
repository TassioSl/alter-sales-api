from __future__ import annotations

import argparse
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
    AND V.IdTransacao NOT IN (3, 6, 7, 8, 10)
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


def build_payload(start_date: date, end_date: date, store_code: int) -> dict:
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
        sales.append(
            {
                "sale_id": f"{store_code}-{documento}-{sold_at_str}",
                "store_id": str(row.get("nome_filial") or f"{store_code:03d}"),
                "store_alias_id": None,
                "sold_at": sold_at_str,
                "total_amount": float(row.get("valor_liquido") or 0),
                "items_count": int(float(row.get("qtde_itens") or 0)),
                "seller_code": str(row.get("vendedor_codigo") or "0"),
                "seller_name": str(row.get("vendedor_nome") or "NAO INFORMADO").strip(),
                "return_id": None,
            }
        )
    return {"sales": sales}


def post_json(url: str, payload: dict) -> str:
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
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
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8091")
    parser.add_argument("--mode", choices=["payload", "intake"], default="payload")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    payload = build_payload(start_date, end_date, args.store_code)
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

    print(post_json(f"{args.api_base_url}/api/sales/intake", payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
