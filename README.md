# Virtual Wallet API

A backend for a virtual wallet system built with **FastAPI**, **MySQL** and **JWT authentication**. Users can register, log in, check their balance, spend money and buy items from a small shop. Admins can add items and credit user wallets.

## Tech Stack

- **FastAPI**: web framework
- **MySQL**: database
- **SQLAlchemy** + **PyMySQL**: talking to MySQL from Python
- **python-jose**: creating and verifying JWT tokens
- **passlib (bcrypt)**: password hashing

## Features

**Core**
- Register and login with hashed passwords (bcrypt)
- JWT-based authentication on protected endpoints
- Every new user starts with a wallet balance of ₹100
- Check balance, spend money, buy items
- Data persisted in MySQL (users, items, transactions)

**Bonus**
- Role-based access (`user` / `admin`)
- Admin endpoints to add items and credit wallets
- Transaction history per user (purchases and credits are tracked separately)
- Input validation (no negative or zero amounts, insufficient balance, out-of-stock items)

## Project Structure

```
wallet_backend/
├── main.py           # All API endpoints
├── auth.py           # Password hashing, JWT creation/verification, admin check
├── models.py         # Database tables (User, Item, Transaction)
├── schemas.py        # Request/response shapes (Pydantic)
├── database.py       # MySQL connection setup
├── requirements.txt  # Python dependencies
└── .env.example      # Template for environment variables
```

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd wallet_backend
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `pip` is blocked on your machine, use `python -m pip install -r requirements.txt` instead.

### 4. Create the MySQL database

Open MySQL and run:

```sql
CREATE DATABASE wallet_db;
```

Tables are created automatically the first time the server starts.

### 5. Configure environment variables

Copy `.env.example` to a new file named `.env` and fill in your values:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=wallet_db

JWT_SECRET_KEY=any_long_random_string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### 6. Run the server

```bash
python -m uvicorn main:app --reload
```

The API is now running at `http://127.0.0.1:8000`.
Interactive docs (Swagger UI) are at **http://127.0.0.1:8000/docs**.

On first start, 5 starter items are added to the shop automatically (Book, Pen, Notebook, Water Bottle, Sticker Pack).

## Using the API

Protected endpoints need this header:

```
Authorization: Bearer <your_access_token>
```

In Swagger UI, log in through `/auth/login`, copy the `access_token`, click **Authorize**, and paste it in.

### Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | No | Create an account (starts with ₹100) |
| POST | `/auth/login` | No | Log in, returns a JWT |
| GET | `/wallet/balance` | User | View your balance |
| POST | `/wallet/spend` | User | Spend a custom amount |
| GET | `/wallet/transactions` | User | View your transaction history |
| GET | `/items` | No | List shop items |
| POST | `/items/buy/{item_id}` | User | Buy an item |
| POST | `/admin/items` | Admin | Add a new item |
| POST | `/admin/wallet/credit` | Admin | Add money to a user's wallet |

### Examples

**Register**

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "bob12345"}'
```

Response:

```json
{ "message": "User registered successfully", "user_id": "3f2a..." }
```

**Login**

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "password": "bob12345"}'
```

Response:

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

**Check balance**

```bash
curl http://127.0.0.1:8000/wallet/balance \
  -H "Authorization: Bearer <token>"
```

Response:

```json
{ "username": "bob", "wallet_balance": 100 }
```

**Spend money**

```bash
curl -X POST http://127.0.0.1:8000/wallet/spend \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 30}'
```

**List items**

```bash
curl http://127.0.0.1:8000/items
```

**Buy an item**

```bash
curl -X POST http://127.0.0.1:8000/items/buy/<item_id> \
  -H "Authorization: Bearer <token>"
```

Response: your updated balance.

### Error responses

| Status | Meaning |
|---|---|
| 400 | Invalid amount, insufficient balance, out of stock, or username already taken |
| 401 | Missing/invalid token, or wrong username/password |
| 403 | Admin access required |
| 404 | Item or user not found |

## Creating an Admin

For safety, everyone registers as a normal `user`. To promote someone to admin, run this in MySQL:

```sql
UPDATE users SET role='admin' WHERE username='your_username';
```

Then log in again to get a fresh token. Admin example:

```bash
curl -X POST http://127.0.0.1:8000/admin/items \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Eraser", "price": 5, "stock": 25}'
```

```bash
curl -X POST http://127.0.0.1:8000/admin/wallet/credit \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<user_id>", "amount": 50}'
```

## Design Notes

- **Passwords** are hashed with bcrypt and never stored in plain text.
- **JWTs** are signed with a secret from `.env` and expire after 60 minutes (configurable).
- **Secrets** live in `.env`, which is excluded from Git via `.gitignore`.
- **Transactions** record every purchase and admin credit, so the balance can always be traced.