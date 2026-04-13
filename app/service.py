from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from .schemas import (
    AlterPerHourItem,
    AlterPerHourPreview,
    AlterPerStorePreview,
    AlterPerStorePreviewItem,
    AlterPerStoreSaleItem,
    IntakeSummary,
    SaleIn,
    SalesIntakeRequest,
    SalesIntakeResponse,
)


def build_intake_response(payload: SalesIntakeRequest) -> SalesIntakeResponse:
    total_amount = sum((sale.total_amount for sale in payload.sales), start=Decimal("0"))
    returns_count = sum(1 for sale in payload.sales if sale.return_id or sale.total_amount <= 0)
    total_stores = len({sale.store_id for sale in payload.sales})
    return SalesIntakeResponse(
        summary=IntakeSummary(
            total_sales=len(payload.sales),
            total_stores=total_stores,
            total_amount=total_amount,
            returns_count=returns_count,
        ),
        sales=payload.sales,
    )


def summarize_payload(payload: SalesIntakeRequest) -> dict[str, int | Decimal]:
    total_amount = sum((sale.total_amount for sale in payload.sales), start=Decimal("0"))
    returns_count = sum(1 for sale in payload.sales if sale.return_id or sale.total_amount <= 0)
    total_stores = len({sale.store_id for sale in payload.sales})
    coupons_count = sum(1 for sale in payload.sales if sale.coupon_number)
    return {
        "total_sales": len(payload.sales),
        "total_stores": total_stores,
        "total_amount": total_amount,
        "returns_count": returns_count,
        "coupons_count": coupons_count,
    }


def build_per_hour_preview(payload: SalesIntakeRequest) -> AlterPerHourPreview:
    grouped: dict[tuple[str, int], dict[str, Decimal | int]] = defaultdict(
        lambda: {"total": Decimal("0"), "nbItems": 0, "nbSales": 0}
    )

    for sale in payload.sales:
        local_date = sale.sold_at.date().isoformat()
        key = (local_date, sale.sold_at.hour)
        grouped[key]["total"] += sale.total_amount
        grouped[key]["nbItems"] += sale.items_count
        grouped[key]["nbSales"] += 1

    items = [
        AlterPerHourItem(
            date=local_date,
            hour=hour,
            total=values["total"],
            nbItems=int(values["nbItems"]),
            nbSales=int(values["nbSales"]),
        )
        for (local_date, hour), values in sorted(grouped.items())
    ]

    return AlterPerHourPreview(
        store_ids=sorted({sale.store_id for sale in payload.sales}),
        payload=items,
    )


def build_per_store_preview(payload: SalesIntakeRequest) -> AlterPerStorePreview:
    grouped: dict[int, list[AlterPerStoreSaleItem]] = defaultdict(list)

    for sale in payload.sales:
        if sale.store_alias_id is None:
            raise ValueError(f"sale_id={sale.sale_id} está sem store_alias_id para envio por loja")
        grouped[sale.store_alias_id].append(
            AlterPerStoreSaleItem(
                localDate=sale.sold_at.isoformat(),
                total=sale.total_amount,
                couponNumber=sale.coupon_number,
            )
        )

    stores = [
        AlterPerStorePreviewItem(store_alias_id=store_alias_id, sales=sales)
        for store_alias_id, sales in sorted(grouped.items(), key=lambda item: item[0])
    ]
    return AlterPerStorePreview(stores=stores)


def alter_per_hour_body(payload: SalesIntakeRequest) -> list[dict]:
    preview = build_per_hour_preview(payload)
    return [item.model_dump() for item in preview.payload]


def alter_per_store_bodies(payload: SalesIntakeRequest) -> list[tuple[int, list[dict]]]:
    preview = build_per_store_preview(payload)
    return [
        (store.store_alias_id, [sale.model_dump() for sale in store.sales])
        for store in preview.stores
    ]
