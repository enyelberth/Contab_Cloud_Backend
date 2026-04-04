from datetime import datetime

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    unit_price: float = Field(default=0, ge=0)
    cost_price: float = Field(default=0, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    unit_price: float | None = Field(default=None, ge=0)
    cost_price: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
