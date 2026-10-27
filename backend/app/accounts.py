from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any

from .models import BirthData


class AccountConfigurationError(RuntimeError):
    pass


class AccountAuthError(RuntimeError):
    pass


def _norm_email(value: str) -> str:
    email = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise AccountAuthError("Please enter a valid email address.")
    return email


def _hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if len(password) < 8:
        raise AccountAuthError("Password must be at least 8 characters.")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return salt.hex(), digest.hex()


def _verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    try:
        _, candidate = _hash_password(password, bytes.fromhex(salt_hex))
    except Exception:
        return False
    return hmac.compare_digest(candidate, hash_hex)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AccountStore:
    def __init__(self) -> None:
        self.url = os.getenv("DATABASE_URL", "").strip()
        self.environment = os.getenv("ENVIRONMENT", "production").lower()
        if not self.url:
            if self.environment != "development":
                raise AccountConfigurationError("User accounts require DATABASE_URL.")
            self.url = f"sqlite:///{Path(__file__).resolve().parents[1] / 'data' / 'accounts-dev.sqlite3'}"
        self._ensure_schema()

    def _is_postgres(self) -> bool:
        return self.url.startswith("postgres://") or self.url.startswith("postgresql://")

    def _connect(self):
        if self._is_postgres():
            try:
                import psycopg
            except ImportError as exc:
                raise AccountConfigurationError("psycopg is required for PostgreSQL account storage") from exc
            return psycopg.connect(self.url)
        path = self.url.removeprefix("sqlite:///")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(path)

    def _execute(self, conn, sql_sqlite: str, sql_pg: str, args: tuple[Any,...] = ()):
        return conn.cursor().execute(sql_pg if self._is_postgres() else sql_sqlite, args)

    def _ensure_schema(self) -> None:
        with closing(self._connect()) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS astromyla_users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
                    password_salt TEXT NOT NULL, password_hash TEXT NOT NULL, created_at BIGINT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS astromyla_sessions (
                    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at BIGINT NOT NULL,
                    expires_at BIGINT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS astromyla_saved_charts (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, label TEXT NOT NULL,
                    birth_json TEXT NOT NULL, created_at BIGINT NOT NULL, updated_at BIGINT NOT NULL
                )
            """)
            conn.commit()

    def register(self, email: str, password: str, display_name: str) -> tuple[dict[str,Any], str]:
        email = _norm_email(email)
        display_name = " ".join(display_name.split())[:80] or email.split("@",1)[0]
        salt, digest = _hash_password(password)
        user_id = "usr_" + secrets.token_urlsafe(12)
        now = int(time.time())
        try:
            with closing(self._connect()) as conn:
                self._execute(conn,
                    "INSERT INTO astromyla_users (id,email,display_name,password_salt,password_hash,created_at) VALUES (?,?,?,?,?,?)",
                    "INSERT INTO astromyla_users (id,email,display_name,password_salt,password_hash,created_at) VALUES (%s,%s,%s,%s,%s,%s)",
                    (user_id,email,display_name,salt,digest,now))
                conn.commit()
        except Exception as exc:
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
                raise AccountAuthError("An account with this email already exists.") from exc
            raise
        token = self._new_session(user_id)
        return {"id":user_id,"email":email,"display_name":display_name}, token

    def login(self, email: str, password: str) -> tuple[dict[str,Any], str]:
        email = _norm_email(email)
        with closing(self._connect()) as conn:
            cur = self._execute(conn,
                "SELECT id,email,display_name,password_salt,password_hash FROM astromyla_users WHERE email=?",
                "SELECT id,email,display_name,password_salt,password_hash FROM astromyla_users WHERE email=%s", (email,))
            row = cur.fetchone()
        if not row or not _verify_password(password, str(row[3]), str(row[4])):
            raise AccountAuthError("Email or password is incorrect.")
        token = self._new_session(str(row[0]))
        return {"id":str(row[0]),"email":str(row[1]),"display_name":str(row[2])}, token

    def _new_session(self, user_id: str) -> str:
        token = secrets.token_urlsafe(36)
        now = int(time.time())
        expiry = now + 60*60*24*14
        with closing(self._connect()) as conn:
            self._execute(conn,
                "INSERT INTO astromyla_sessions (token_hash,user_id,created_at,expires_at) VALUES (?,?,?,?)",
                "INSERT INTO astromyla_sessions (token_hash,user_id,created_at,expires_at) VALUES (%s,%s,%s,%s)",
                (_token_hash(token),user_id,now,expiry))
            conn.commit()
        return token

    def user_for_token(self, token: str) -> dict[str,Any] | None:
        now = int(time.time())
        with closing(self._connect()) as conn:
            cur = self._execute(conn,
                "SELECT u.id,u.email,u.display_name,s.expires_at FROM astromyla_sessions s JOIN astromyla_users u ON u.id=s.user_id WHERE s.token_hash=?",
                "SELECT u.id,u.email,u.display_name,s.expires_at FROM astromyla_sessions s JOIN astromyla_users u ON u.id=s.user_id WHERE s.token_hash=%s",
                (_token_hash(token),))
            row = cur.fetchone()
        if not row or int(row[3]) <= now:
            return None
        return {"id":str(row[0]),"email":str(row[1]),"display_name":str(row[2])}

    def logout(self, token: str) -> None:
        with closing(self._connect()) as conn:
            self._execute(conn, "DELETE FROM astromyla_sessions WHERE token_hash=?", "DELETE FROM astromyla_sessions WHERE token_hash=%s", (_token_hash(token),))
            conn.commit()

    def list_charts(self, user_id: str) -> list[dict[str,Any]]:
        with closing(self._connect()) as conn:
            cur = self._execute(conn,
                "SELECT id,label,birth_json,created_at,updated_at FROM astromyla_saved_charts WHERE user_id=? ORDER BY updated_at DESC",
                "SELECT id,label,birth_json,created_at,updated_at FROM astromyla_saved_charts WHERE user_id=%s ORDER BY updated_at DESC", (user_id,))
            rows = cur.fetchall()
        return [{"id":r[0],"label":r[1],"birth":json.loads(r[2]),"created_at":r[3],"updated_at":r[4]} for r in rows]

    def save_chart(self, user_id: str, label: str, birth: BirthData) -> dict[str,Any]:
        chart_id = "cht_" + secrets.token_urlsafe(10)
        now = int(time.time())
        label = " ".join(label.split())[:80] or birth.name or "Saved chart"
        birth_json = json.dumps(birth.model_dump(mode="json"), ensure_ascii=False)
        with closing(self._connect()) as conn:
            self._execute(conn,
                "INSERT INTO astromyla_saved_charts (id,user_id,label,birth_json,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                "INSERT INTO astromyla_saved_charts (id,user_id,label,birth_json,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s)",
                (chart_id,user_id,label,birth_json,now,now))
            conn.commit()
        return {"id":chart_id,"label":label,"birth":json.loads(birth_json),"created_at":now,"updated_at":now}

    def delete_chart(self, user_id: str, chart_id: str) -> bool:
        with closing(self._connect()) as conn:
            cur = self._execute(conn,
                "DELETE FROM astromyla_saved_charts WHERE id=? AND user_id=?",
                "DELETE FROM astromyla_saved_charts WHERE id=%s AND user_id=%s", (chart_id,user_id))
            conn.commit()
            return bool(cur.rowcount)
