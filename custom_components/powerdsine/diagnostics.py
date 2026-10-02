"""Diagnostics support for PowerDsine."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

REDACT = {"community", "write_community", "auth_key", "priv_key"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return safe diagnostics."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    config = {key: ("**REDACTED**" if key in REDACT else value) for key, value in entry.data.items()}
    return {
        "config": config,
        "options": dict(entry.options),
        "product": {
            "sys_object_id": coordinator.product.sys_object_id,
            "product_leaf": coordinator.product.product_leaf,
            "model": coordinator.product.model,
            "ports": coordinator.product.ports,
        },
        "data": coordinator.data,
    }
