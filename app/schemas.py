from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class SaleIn(BaseModel):
    sale_id: str = Field(..., min_length=1)
    coupon_number: str | None = None
    store_id: str = Field(..., min_length=1)
    store_alias_id: int | None = Field(default=None, gt=0)
    sold_at: datetime
    total_amount: Decimal
    items_count: int = Field(..., ge=0)
    seller_code: str = Field(..., min_length=1)
    seller_name: str = Field(..., min_length=1)
    return_id: str | None = None

    @field_validator("seller_code", "seller_name", "sale_id", "store_id", "coupon_number")
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @model_validator(mode="after")
    def validate_return_consistency(self) -> "SaleIn":
        if self.return_id and self.total_amount > 0:
            raise ValueError("return_id informado exige total_amount negativo ou zero")
        return self


class SalesIntakeRequest(BaseModel):
    sales: list[SaleIn] = Field(default_factory=list)


class IntakeSummary(BaseModel):
    total_sales: int
    total_stores: int
    total_amount: Decimal
    returns_count: int


class SalesIntakeResponse(BaseModel):
    summary: IntakeSummary
    sales: list[SaleIn]


class StoredSalesEnvelope(BaseModel):
    created_at: datetime
    payload: SalesIntakeRequest


class AlterPerHourItem(BaseModel):
    date: str
    hour: int
    total: Decimal
    nbItems: int
    nbSales: int


class AlterPerHourPreview(BaseModel):
    store_ids: list[str]
    payload: list[AlterPerHourItem]


class AlterPerStoreSaleItem(BaseModel):
    localDate: str
    total: Decimal
    couponNumber: str | None = None


class AlterPerStorePreviewItem(BaseModel):
    store_alias_id: int
    sales: list[AlterPerStoreSaleItem]


class AlterPerStorePreview(BaseModel):
    stores: list[AlterPerStorePreviewItem]


class AlterSendResult(BaseModel):
    target: str
    status_code: int
    response_body: str
