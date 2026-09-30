import pytest

from backend.nfc import NfcError, read_card_uid


def test_nfc_disabled_fails_closed(monkeypatch):
    monkeypatch.setenv("KIOSK_NFC", "disabled")
    with pytest.raises(NfcError) as exc:
        read_card_uid()
    assert exc.value.code == "NFC_READER_OFFLINE"
    assert exc.value.retryable is False


def test_nfc_mock_is_deterministic(monkeypatch):
    monkeypatch.setenv("KIOSK_NFC", "mock")
    monkeypatch.setenv("KIOSK_NFC_MOCK_UID", "04:aa:bb:cc")
    assert read_card_uid() == "04AABBCC"
    assert read_card_uid() == "04AABBCC"
