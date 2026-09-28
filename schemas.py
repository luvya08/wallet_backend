"""
Pydantic models define the SHAPE of data coming in (requests) and going out
(responses). FastAPI uses these to automatically validate incoming JSON and
to convert Python objects into JSON responses.

Think of these as separate from models.py: models.py = database tables,
schemas.py = what the API accepts/returns over HTTP.
"""

from pydantic import BaseModel
from datetime import datetime


# ---------- Auth ----------

class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Wallet ----------

class SpendRequest(BaseModel):
    amount: int


class BalanceResponse(BaseModel):
    username: str
    wallet_balance: int


# ---------- Items ----------

class ItemResponse(BaseModel):
    id: str
    name: str
    price: int
    stock: int

    class Config:
        from_attributes = True  # lets Pydantic read SQLAlchemy objects directly
# ---------- Admin ----------

class AdminItemCreate(BaseModel):
    name: str
    price: int
    stock: int


class AdminCreditRequest(BaseModel):
    user_id: str
    amount: int


# ---------- Transactions ----------

class TransactionResponse(BaseModel):
    id: str
    item_id: str | None
    amount: int
    type: str
    timestamp: datetime

    class Config:
        from_attributes = True
