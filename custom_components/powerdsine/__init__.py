"""PowerDsine PoE integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    CONF_USERNAME,
    CONF_WRITE_COMMUNITY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OPT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import PowerDsineCoordinator
from .snmp import PowerDsineSnmpClient, SnmpConfig


def _snmp_config(entry: ConfigEntry) -> SnmpConfig:
    data = entry.data
    return SnmpConfig(
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, 161),
        version=data.get(CONF_SNMP_VERSION, "2c"),
        community=data.get("community", "public"),
        write_community=data.get(CONF_WRITE_COMMUNITY) or None,
        username=data.get(CONF_USERNAME),
        auth_protocol=data.get(CONF_AUTH_PROTOCOL, "none"),
        auth_key=data.get(CONF_AUTH_KEY) or None,
        priv_protocol=data.get(CONF_PRIV_PROTOCOL, "none"),
        priv_key=data.get(CONF_PRIV_KEY) or None,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PowerDsine from a config entry."""
    client = PowerDsineSnmpClient(_snmp_config(entry))
    await client.async_initialize()
    try:
        product, _ = await PowerDsineCoordinator.async_detect(client)
    except Exception as err:
        await client.async_close()
        raise ConfigEntryNotReady(f"PowerDsine is not reachable: {err}") from err

    coordinator = PowerDsineCoordinator(
        hass,
        entry,
        client,
        product,
        entry.options.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: PowerDsineCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.async_close()
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
