"""
Each class here becomes a table in MySQL. SQLAlchemy creates the actual
tables for us based on these class definitions (see main.py's startup code).
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    wallet_balance = Column(Integer, default=100, nullable=False)
    role = Column(String(10), default="user", nullable=False)  # "user" or "admin"

    transactions = relationship("Transaction", back_populates="user")


class Item(Base):
    __tablename__ = "items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=10, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=True)
    amount = Column(Integer, nullable=False)
    type = Column(String(20), default="purchase", nullable=False)  # "purchase" or "credit"
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
