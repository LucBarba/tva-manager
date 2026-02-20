from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InvoiceCreate(BaseModel):
    date:      Optional[str]  = None
    client:    Optional[str]  = None
    number:    Optional[str]  = None
    desc:      Optional[str]  = None
    amount_ht: float          = Field(..., ge=0)
    vat_rate:  float          = Field(20.0, ge=0, le=100)
    is_paid:   bool           = False


class InvoiceUpdate(BaseModel):
    date:      Optional[str]   = None
    client:    Optional[str]   = None
    number:    Optional[str]   = None
    desc:      Optional[str]   = None
    amount_ht: Optional[float] = None
    vat_rate:  Optional[float] = None
    is_paid:   Optional[bool]  = None


class InvoiceOut(BaseModel):
    id:         int
    date:       Optional[str]      = None
    client:     Optional[str]      = None
    number:     Optional[str]      = None
    desc:       Optional[str]      = None
    amount_ht:  float
    vat_rate:   float
    is_paid:    bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    date:      Optional[str]  = None
    supplier:  Optional[str]  = None
    number:    Optional[str]  = None
    desc:      Optional[str]  = None
    amount_ht: float          = Field(..., ge=0)
    vat_rate:  float          = Field(20.0, ge=0, le=100)
    category:  Optional[str]  = "Autre"


class ExpenseUpdate(BaseModel):
    date:      Optional[str]   = None
    supplier:  Optional[str]   = None
    number:    Optional[str]   = None
    desc:      Optional[str]   = None
    amount_ht: Optional[float] = None
    vat_rate:  Optional[float] = None
    category:  Optional[str]   = None


class ExpenseOut(BaseModel):
    id:         int
    date:       Optional[str]      = None
    supplier:   Optional[str]      = None
    number:     Optional[str]      = None
    desc:       Optional[str]      = None
    amount_ht:  float
    vat_rate:   float
    category:   Optional[str]      = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
