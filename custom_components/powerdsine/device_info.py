"""Parse explicitly labelled metadata from the SNMP system description."""

from __future__ import annotations

import re

_PATTERNS = {
    "serial_number": r"\bUnit\s+S/N\s*=\s*([A-Za-z0-9-]+)",
    "software_version": r"\bApp\s+Ver\s*=\s*(\d+(?:\.\d+)+)(?=\s|,|$)",
    "boot_version": r"\bBOOT\s+Ver\s*=\s*(\d+(?:\.\d+)+)(?=\s|,|$)",
}


def parse_system_description(description: object) -> dict[str, str]:
    """Extract known fields without guessing versions from build dates."""
    if not isinstance(description, str):
        return {}
    result = {}
    for key, pattern in _PATTERNS.items():
        if match := re.search(pattern, description, re.IGNORECASE):
            result[key] = match.group(1)
    return result
