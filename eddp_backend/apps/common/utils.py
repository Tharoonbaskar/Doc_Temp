from __future__ import annotations

import os
import secrets
import string
import uuid
from datetime import datetime

from django.utils import timezone


def generate_uuid(*, as_string: bool = True) -> str | uuid.UUID:
    value = uuid.uuid4()
    return str(value) if as_string else value


def generate_code(
    prefix: str,
    length: int = 12,
    *,
    separator: str = "_",
) -> str:
    if length <= 0:
        raise ValueError("length must be a positive integer")

    alphabet = string.ascii_uppercase + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(length))

    normalized_prefix = prefix.strip().upper()
    if not normalized_prefix:
        return token

    if separator:
        return f"{normalized_prefix}{separator}{token}"
    return f"{normalized_prefix}{token}"


def current_timestamp(*, as_iso: bool = False, localtime: bool = False) -> datetime | str:
    now = timezone.localtime(timezone.now()) if localtime else timezone.now()
    return now.isoformat() if as_iso else now