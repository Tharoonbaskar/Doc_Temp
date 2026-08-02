from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from django.core.exceptions import ValidationError


def validate_uuid(value: Any) -> str:
    if value is None:
        raise ValidationError("UUID value is required.")
    try:
        parsed = UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError("Invalid UUID format.") from exc
    return str(parsed)


def validate_json(value: Any) -> Any:
    if value is None:
        raise ValidationError("JSON value is required.")

    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError("Invalid JSON payload.") from exc

    raise ValidationError("Value must be a JSON string, object, or array.")


def validate_file_extension(
    value: Any,
    allowed_extensions: Iterable[str] | None = None,
) -> str:
    if value is None:
        raise ValidationError("File is required.")

    filename = getattr(value, "name", value)
    if not isinstance(filename, str) or not filename.strip():
        raise ValidationError("Invalid filename.")

    extension = Path(filename).suffix.lower().lstrip(".")
    if not extension:
        raise ValidationError("File must have an extension.")

    normalized_allowed = {
        ext.lower().lstrip(".")
        for ext in (allowed_extensions or [])
    }
    if normalized_allowed and extension not in normalized_allowed:
        allowed_str = ", ".join(sorted(normalized_allowed))
        raise ValidationError(
            f"Unsupported file extension '{extension}'. Allowed: {allowed_str}."
        )

    return extension