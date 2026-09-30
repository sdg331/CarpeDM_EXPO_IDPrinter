"""ACR1252U access boundary.

Production hardware is accessed through PC/SC (`KIOSK_NFC=pcsc`). The default is
`disabled`, so a missing reader can never be mistaken for a successful NFC write.

The current exhibition MVP binds the card's immutable UID to a local session in
SQLite. It does not claim to write visitor data into card memory. This keeps card
payload minimal and makes reuse/revocation explicit in the local database.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class NfcError(Exception):
    code: str
    retryable: bool
    detail: str = ""

    def __str__(self) -> str:
        return self.detail or self.code


def backend_name() -> str:
    return os.getenv("KIOSK_NFC", "disabled").strip().lower()


def nfc_status() -> dict[str, Any]:
    backend = backend_name()
    if backend == "disabled":
        return {
            "backend": backend,
            "ready": False,
            "detail": "KIOSK_NFC=pcsc 또는 개발용 mock 설정 필요",
        }
    if backend == "mock":
        return {"backend": backend, "ready": True, "detail": "deterministic mock UID"}
    if backend != "pcsc":
        return {"backend": backend, "ready": False, "detail": "unknown NFC backend"}

    try:
        from smartcard.System import readers
    except ImportError:
        return {
            "backend": backend,
            "ready": False,
            "detail": "pyscard 미설치",
        }

    try:
        found = list(readers())
    except Exception as exc:
        return {"backend": backend, "ready": False, "detail": f"PC/SC 오류: {exc}"}
    return {
        "backend": backend,
        "ready": bool(found),
        "readers": [str(r) for r in found],
        "detail": "reader detected" if found else "reader not detected",
    }


def read_card_uid(timeout_seconds: float = 10.0) -> str:
    backend = backend_name()
    if backend == "disabled":
        raise NfcError(
            "NFC_READER_OFFLINE",
            False,
            "NFC backend is disabled",
        )
    if backend == "mock":
        uid = os.getenv("KIOSK_NFC_MOCK_UID", "04A1B2C3D4E5F6")
        return _normalize_uid(uid)
    if backend != "pcsc":
        raise NfcError("NFC_READER_OFFLINE", False, f"unknown NFC backend: {backend}")
    return _read_pcsc_uid(timeout_seconds)


def _normalize_uid(value: str) -> str:
    uid = "".join(ch for ch in value.upper() if ch in "0123456789ABCDEF")
    if len(uid) < 4 or len(uid) % 2:
        raise NfcError("NFC_READ_FAILED", True, "invalid card UID")
    return uid


def _read_pcsc_uid(timeout_seconds: float) -> str:
    try:
        from smartcard.Exceptions import CardConnectionException, NoCardException
        from smartcard.System import readers
    except ImportError as exc:
        raise NfcError("NFC_READER_OFFLINE", False, "pyscard is not installed") from exc

    try:
        available = list(readers())
    except Exception as exc:
        raise NfcError("NFC_READER_OFFLINE", True, f"PC/SC reader query failed: {exc}") from exc
    if not available:
        raise NfcError("NFC_READER_OFFLINE", True, "ACR1252U reader not detected")

    get_uid_apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    deadline = time.monotonic() + max(0.1, timeout_seconds)
    last_error = ""

    while time.monotonic() < deadline:
        for reader in available:
            connection = reader.createConnection()
            try:
                connection.connect()
                data, sw1, sw2 = connection.transmit(get_uid_apdu)
                if sw1 == 0x90 and sw2 == 0x00 and data:
                    return _normalize_uid("".join(f"{b:02X}" for b in data))
                last_error = f"UID APDU failed: SW={sw1:02X}{sw2:02X}"
            except (NoCardException, CardConnectionException):
                continue
            except Exception as exc:
                last_error = str(exc)
            finally:
                try:
                    connection.disconnect()
                except Exception:
                    pass
        time.sleep(0.2)

    raise NfcError(
        "NFC_TIMEOUT",
        True,
        last_error or "card was not presented before timeout",
    )
