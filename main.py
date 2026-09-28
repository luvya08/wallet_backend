"""
Entry point of the app. Run this with:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs in your browser to test everything.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from typing import List

from database import Base, engine, get_db, SessionLocal
from models import User, Item, Transaction
from schemas import (
    UserRegister, UserLogin, Token,
    SpendRequest, BalanceResponse,
    ItemResponse, TransactionResponse,
    AdminItemCreate, AdminCreditRequest,
)
from auth import hash_password, verify_password, create_access_token, get_current_user,require_admin

# This line looks at every class that inherits from Base (User, Item,
# Transaction in models.py) and creates the matching tables in MySQL
# if they don't already exist. Make sure the "wallet_db" database itself
# already exists in MySQL first (CREATE DATABASE wallet_db;).
Base.metadata.create_all(bind=engine)


def seed_items():
    """
    Runs once when the server starts. If the items table is empty,
    it fills it with a few starter items so /items isn't empty and
    there's something to buy. Safe to run every restart since it
    checks "if empty" first.
    """
    db = SessionLocal()
    try:
        if db.query(Item).count() == 0:
            starter_items = [
                Item(name="Book", price=50, stock=10),
                Item(name="Pen", price=10, stock=50),
                Item(name="Notebook", price=30, stock=20),
                Item(name="Water Bottle", price=80, stock=15),
                Item(name="Sticker Pack", price=20, stock=30),
            ]
            db.add_all(starter_items)
            db.commit()
    finally:
        db.close()


seed_items()

app = FastAPI(title="Virtual Wallet API")


@app.get("/")
def root():
    return {"message": "Wallet API is running. Visit /docs to test endpoints."}


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Check username isn't already taken
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        wallet_balance=100,  # everyone starts with ₹100
        role="user",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}


@app.post("/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    # Check both "user doesn't exist" and "wrong password" the same way,
    # so attackers can't tell which one failed.
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # "sub" (subject) is the standard JWT field for "who this token is about"
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)


# ============================================================
# WALLET ENDPOINTS
# Notice these all take `current_user: User = Depends(get_current_user)`.
# That one line means: "this endpoint requires a valid JWT token in the
# Authorization header, and give me the User object it belongs to."
# ============================================================

@app.get("/wallet/balance", response_model=BalanceResponse)
def get_balance(current_user: User = Depends(get_current_user)):
    return BalanceResponse(username=current_user.username, wallet_balance=current_user.wallet_balance)


@app.post("/wallet/spend", response_model=BalanceResponse)
def spend_money(
    payload: SpendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if payload.amount > current_user.wallet_balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    current_user.wallet_balance -= payload.amount

    # Log this as a transaction with no linked item (a plain spend)
    txn = Transaction(user_id=current_user.id, item_id=None, amount=payload.amount, type="purchase")
    db.add(txn)
    db.commit()
    db.refresh(current_user)

    return BalanceResponse(username=current_user.username, wallet_balance=current_user.wallet_balance)


# ============================================================
# ITEMS ENDPOINTS
# ============================================================

@app.get("/items", response_model=List[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).all()


@app.post("/items/buy/{item_id}", response_model=BalanceResponse)
def buy_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.stock <= 0:
        raise HTTPException(status_code=400, detail="Item out of stock")
    if item.price > current_user.wallet_balance:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Deduct balance, reduce stock, log the transaction
    current_user.wallet_balance -= item.price
    item.stock -= 1
    txn = Transaction(user_id=current_user.id, item_id=item.id, amount=item.price, type="purchase")
    db.add(txn)
    db.commit()
    db.refresh(current_user)

    return BalanceResponse(username=current_user.username, wallet_balance=current_user.wallet_balance)


# ============================================================
# TRANSACTION HISTORY (bonus points feature)
# ============================================

@app.get("/wallet/transactions", response_model=List[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

# ============================================================
# ADMIN ENDPOINTS (bonus points feature)
# Notice these use `Depends(require_admin)` instead of `Depends(get_current_user)`.
# require_admin (in auth.py) does everything get_current_user does, PLUS
# checks current_user.role == "admin", rejecting anyone else with a 403.
# ============================================================

@app.post("/admin/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def admin_add_item(
    payload: AdminItemCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    new_item = Item(name=payload.name, price=payload.price, stock=payload.stock)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@app.post("/admin/wallet/credit", response_model=BalanceResponse)
def admin_credit_wallet(
    payload: AdminCreditRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    target_user.wallet_balance += payload.amount

    # type="credit" distinguishes admin top-ups from user purchases
    txn = Transaction(user_id=target_user.id, item_id=None, amount=payload.amount, type="credit")
    db.add(txn)
    db.commit()
    db.refresh(target_user)

    return BalanceResponse(username=target_user.username, wallet_balance=target_user.wallet_balance)