from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class InvoiceDB(Base):
    __tablename__ = "invoices"

    id         = Column(Integer, primary_key=True, index=True)
    date       = Column(String(10),  nullable=True)
    client     = Column(String(200), nullable=True)
    number     = Column(String(100), nullable=True)
    desc       = Column(String(500), nullable=True)
    amount_ht  = Column(Float,   nullable=False, default=0.0)
    vat_rate   = Column(Float,   nullable=False, default=20.0)
    is_paid    = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExpenseDB(Base):
    __tablename__ = "expenses"

    id         = Column(Integer, primary_key=True, index=True)
    date       = Column(String(10),  nullable=True)
    supplier   = Column(String(200), nullable=True)
    number     = Column(String(100), nullable=True)
    desc       = Column(String(500), nullable=True)
    amount_ht  = Column(Float,   nullable=False, default=0.0)
    vat_rate   = Column(Float,   nullable=False, default=20.0)
    category   = Column(String(100), nullable=True, default="Autre")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
