"""
This file sets up the connection to MySQL using SQLAlchemy.

SQLAlchemy is an ORM (Object-Relational Mapper). Instead of writing raw SQL
strings like "SELECT * FROM users WHERE id = 5", we define Python classes
(in models.py) and SQLAlchemy translates our Python code into SQL for us.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from the .env file into the environment
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "wallet_db")

# This is the connection string SQLAlchemy uses to reach MySQL.
# Format: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# The "engine" is the actual connection pool to the database.
engine = create_engine(DATABASE_URL, echo=False)

# A "session" is a single conversation with the database (used per-request).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All our model classes (User, Item, Transaction) will inherit from this.
Base = declarative_base()


def get_db():
    """
    FastAPI calls this for every request that needs DB access.
    It opens a session, hands it to the endpoint function, then
    always closes it afterward (even if an error happens).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
