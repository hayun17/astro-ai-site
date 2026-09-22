from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PRODUCTS = {
    "personalized_reading": {"tier": "personalized", "label": "Personalized Reading", "price_env": "PAID_READING_PRICE_TRY"},
    "deep_reading": {"tier": "deep", "label": "Deep Personal Reading", "price_env": "DEEP_READING_PRICE_TRY"},
}


class PaymentConfigurationError(RuntimeError):
    pass


class PaymentProviderError(RuntimeError):
    pass


def _price_for(product: str) -> Decimal:
    meta = PRODUCTS.get(product)
    if not meta:
        raise PaymentConfigurationError("Unknown product")
    raw = os.getenv(str(meta["price_env"]), "").strip()
    if not raw:
        raise PaymentConfigurationError(f"{meta['price_env']} is not configured")
    try:
        price = Decimal(raw).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise PaymentConfigurationError(f"Invalid configured price for {product}") from exc
    if price <= 0:
        raise PaymentConfigurationError("Configured price must be positive")
    return price


def public_catalog() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for product, meta in PRODUCTS.items():
        try:
            price = _price_for(product)
            out[product] = {"configured": True, "label": meta["label"], "price": f"{price:.2f}", "currency": "TRY"}
        except PaymentConfigurationError:
            out[product] = {"configured": False, "label": meta["label"], "price": None, "currency": "TRY"}
    return out


def payment_ready() -> bool:
    if not (os.getenv("IYZICO_API_KEY", "").strip() and os.getenv("IYZICO_SECRET_KEY", "").strip() and os.getenv("DATABASE_URL", "").strip()):
        return False
    try:
        _price_for("personalized_reading")
        _price_for("deep_reading")
    except PaymentConfigurationError:
        return False
    return True


def _iyzico_options() -> dict[str, str]:
    api_key = os.getenv("IYZICO_API_KEY", "").strip()
    secret_key = os.getenv("IYZICO_SECRET_KEY", "").strip()
    base_url = os.getenv("IYZICO_BASE_URL", "https://sandbox-api.iyzipay.com").strip().rstrip("/")
    if not api_key or not secret_key:
        raise PaymentConfigurationError("iyzico credentials are not configured")
    return {"api_key": api_key, "secret_key": secret_key, "base_url": base_url}


@dataclass
class Order:
    id: str
    public_token: str
    product: str
    tier: str
    amount: str
    currency: str
    email: str
    status: str
    payment_token: str | None
    payment_id: str | None
    request_json: str
    created_at: int
    paid_at: int | None


class OrderStore:
    """Small persistence adapter.

    Production payments require DATABASE_URL. PostgreSQL is used on Render.
    SQLite is accepted only in development/tests to keep local setup simple.
    """

    def __init__(self) -> None:
        self.url = os.getenv("DATABASE_URL", "").strip()
        self.environment = os.getenv("ENVIRONMENT", "production").lower()
        if not self.url:
            if self.environment != "development":
                raise PaymentConfigurationError("DATABASE_URL is required for production payment orders")
            self.url = f"sqlite:///{Path(__file__).resolve().parents[1] / 'data' / 'orders-dev.sqlite3'}"
        self._ensure_schema()

    def _is_postgres(self) -> bool:
        return self.url.startswith("postgres://") or self.url.startswith("postgresql://")

    def _connect(self):
        if self._is_postgres():
            try:
                import psycopg
            except ImportError as exc:
                raise PaymentConfigurationError("psycopg is required for PostgreSQL payment storage") from exc
            return psycopg.connect(self.url)
        path = self.url.removeprefix("sqlite:///")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            if self._is_postgres():
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS astromyla_orders (
                        id TEXT PRIMARY KEY, public_token TEXT UNIQUE NOT NULL, product TEXT NOT NULL,
                        tier TEXT NOT NULL, amount TEXT NOT NULL, currency TEXT NOT NULL, email TEXT NOT NULL,
                        status TEXT NOT NULL, payment_token TEXT, payment_id TEXT, request_json TEXT NOT NULL,
                        created_at BIGINT NOT NULL, paid_at BIGINT, report_pdf BYTEA, report_filename TEXT
                    )
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS astromyla_orders (
                        id TEXT PRIMARY KEY, public_token TEXT UNIQUE NOT NULL, product TEXT NOT NULL,
                        tier TEXT NOT NULL, amount TEXT NOT NULL, currency TEXT NOT NULL, email TEXT NOT NULL,
                        status TEXT NOT NULL, payment_token TEXT, payment_id TEXT, request_json TEXT NOT NULL,
                        created_at INTEGER NOT NULL, paid_at INTEGER, report_pdf BLOB, report_filename TEXT
                    )
                """)
            conn.commit()

    def create(self, *, product: str, tier: str, amount: str, email: str, request_payload: dict[str, Any]) -> Order:
        order = Order(
            id="ord_" + secrets.token_urlsafe(12), public_token=secrets.token_urlsafe(28), product=product, tier=tier,
            amount=amount, currency="TRY", email=email, status="created", payment_token=None, payment_id=None,
            request_json=json.dumps(request_payload, ensure_ascii=False), created_at=int(time.time()), paid_at=None,
        )
        with self._connect() as conn:
            conn.cursor().execute(
                "INSERT INTO astromyla_orders (id,public_token,product,tier,amount,currency,email,status,payment_token,payment_id,request_json,created_at,paid_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
                if not self._is_postgres() else
                "INSERT INTO astromyla_orders (id,public_token,product,tier,amount,currency,email,status,payment_token,payment_id,request_json,created_at,paid_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (order.id, order.public_token, order.product, order.tier, order.amount, order.currency, order.email, order.status, None, None, order.request_json, order.created_at, None),
            )
            conn.commit()
        return order

    def _row_to_order(self, row) -> Order | None:
        return Order(*row) if row else None

    def get_public(self, public_token: str) -> Order | None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id,public_token,product,tier,amount,currency,email,status,payment_token,payment_id,request_json,created_at,paid_at FROM astromyla_orders WHERE public_token=?" if not self._is_postgres() else "SELECT id,public_token,product,tier,amount,currency,email,status,payment_token,payment_id,request_json,created_at,paid_at FROM astromyla_orders WHERE public_token=%s", (public_token,))
            return self._row_to_order(cur.fetchone())

    def get_id(self, order_id: str) -> Order | None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id,public_token,product,tier,amount,currency,email,status,payment_token,payment_id,request_json,created_at,paid_at FROM astromyla_orders WHERE id=?" if not self._is_postgres() else "SELECT id,public_token,product,tier,amount,currency,email,status,payment_token,payment_id,request_json,created_at,paid_at FROM astromyla_orders WHERE id=%s", (order_id,))
            return self._row_to_order(cur.fetchone())

    def get_report(self, order_id: str) -> tuple[bytes, str] | None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT report_pdf, report_filename FROM astromyla_orders WHERE id=?" if not self._is_postgres() else "SELECT report_pdf, report_filename FROM astromyla_orders WHERE id=%s", (order_id,))
            row = cur.fetchone()
            if not row or row[0] is None:
                return None
            return bytes(row[0]), str(row[1] or "astromyla-premium-reading.pdf")

    def save_report(self, order_id: str, content: bytes, filename: str) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE astromyla_orders SET report_pdf=?, report_filename=? WHERE id=?" if not self._is_postgres() else "UPDATE astromyla_orders SET report_pdf=%s, report_filename=%s WHERE id=%s", (content, filename, order_id))
            conn.commit()

    def set_payment_token(self, order_id: str, token: str) -> None:
        self._update(order_id, status="pending", payment_token=token)

    def mark_paid(self, order_id: str, payment_id: str | None) -> None:
        self._update(order_id, status="paid", payment_id=payment_id, paid_at=int(time.time()))

    def mark_failed(self, order_id: str) -> None:
        self._update(order_id, status="failed")

    def _update(self, order_id: str, **fields: Any) -> None:
        if not fields:
            return
        allowed = {"status", "payment_token", "payment_id", "paid_at"}
        fields = {k: v for k, v in fields.items() if k in allowed}
        with self._connect() as conn:
            cur = conn.cursor()
            if self._is_postgres():
                set_sql = ",".join(f"{k}=%s" for k in fields)
                cur.execute(f"UPDATE astromyla_orders SET {set_sql} WHERE id=%s", (*fields.values(), order_id))
            else:
                set_sql = ",".join(f"{k}=?" for k in fields)
                cur.execute(f"UPDATE astromyla_orders SET {set_sql} WHERE id=?", (*fields.values(), order_id))
            conn.commit()


def initialize_checkout(*, order: Order, buyer: dict[str, Any], client_ip: str, callback_url: str) -> dict[str, Any]:
    try:
        import iyzipay
    except ImportError as exc:
        raise PaymentConfigurationError("iyzipay SDK is not installed") from exc

    options = _iyzico_options()
    full_name = " ".join(str(buyer.get("full_name") or "").split())
    bits = full_name.split(" ", 1)
    first, last = bits[0], bits[1] if len(bits) > 1 else bits[0]
    address = {
        "contactName": full_name,
        "city": str(buyer["city"]),
        "country": str(buyer.get("country") or "Turkey"),
        "address": str(buyer["address"]),
    }
    req = {
        "locale": "tr",
        "conversationId": order.id,
        "price": order.amount,
        "paidPrice": order.amount,
        "currency": "TRY",
        "basketId": order.id,
        "paymentGroup": "PRODUCT",
        "callbackUrl": callback_url,
        "buyer": {
            "id": order.id,
            "name": first,
            "surname": last,
            "gsmNumber": str(buyer["phone"]),
            "email": str(buyer["email"]),
            "identityNumber": str(buyer["identity_number"]),
            "registrationAddress": str(buyer["address"]),
            "ip": client_ip or "127.0.0.1",
            "city": str(buyer["city"]),
            "country": str(buyer.get("country") or "Turkey"),
        },
        "shippingAddress": address,
        "billingAddress": address,
        "basketItems": [{
            "id": order.product,
            "name": PRODUCTS[order.product]["label"],
            "category1": "Digital Astrology Reading",
            "itemType": "VIRTUAL",
            "price": order.amount,
        }],
    }
    resource = iyzipay.CheckoutFormInitialize()
    response = json.load(resource.create(req, options))
    if response.get("status") != "success":
        raise PaymentProviderError(str(response.get("errorMessage") or "iyzico checkout initialization failed"))
    # Official SDK exposes signature verification for conversationId + token.
    sig = response.get("signature")
    token = response.get("token")
    if sig and token and not resource.verify_signature([response.get("conversationId"), token], options["secret_key"], sig):
        raise PaymentProviderError("iyzico initialize signature verification failed")
    return response


def retrieve_checkout(*, token: str, conversation_id: str) -> dict[str, Any]:
    try:
        import iyzipay
    except ImportError as exc:
        raise PaymentConfigurationError("iyzipay SDK is not installed") from exc
    options = _iyzico_options()
    resource = iyzipay.CheckoutForm()
    response = json.load(resource.retrieve({"locale": "tr", "conversationId": conversation_id, "token": token}, options))
    if response.get("status") != "success":
        raise PaymentProviderError(str(response.get("errorMessage") or "iyzico checkout verification failed"))
    sig = response.get("signature")
    if sig:
        values = [
            response.get("paymentStatus"), response.get("paymentId"), response.get("currency"), response.get("basketId"),
            response.get("conversationId"), resource.strip_zero(str(response.get("paidPrice"))),
            resource.strip_zero(str(response.get("price"))), response.get("token"),
        ]
        if not resource.verify_signature(values, options["secret_key"], sig):
            raise PaymentProviderError("iyzico retrieve signature verification failed")
    return response
