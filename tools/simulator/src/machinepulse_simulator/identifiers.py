"""Validation helpers for canonical MachinePulse entity identifiers."""

import re
from typing import Annotated

from pydantic import BeforeValidator

_CANONICAL_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", re.ASCII)


def require_canonical_ulid(value: object) -> str:
    """Require the 26-character uppercase MachinePulse ULID profile.

    Args:
        value: Input value supplied for a device or asset identifier.

    Returns:
        The input ULID unchanged.

    Raises:
        ValueError: If the value is not in canonical MachinePulse ULID form.
    """
    if not isinstance(value, str) or _CANONICAL_ULID.fullmatch(value) is None:
        raise ValueError("must be a canonical uppercase ULID")
    return value


type CanonicalULID = Annotated[str, BeforeValidator(require_canonical_ulid)]
