"""PoE port switches for PowerDsine."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, RFC_PORT_ADMIN, port_oid
from .coordinator import PowerDsineCoordinator
from .entity import PowerDsinePortEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PowerDsineCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PowerDsinePortSwitch(coordinator, port)
        for port in range(1, coordinator.product.ports + 1)
    )


class PowerDsinePortSwitch(PowerDsinePortEntity, SwitchEntity):
    """Enable or disable PoE on one port."""

    def __init__(self, coordinator, port: int) -> None:
        super().__init__(coordinator, port)
        self._attr_name = f"Port {port:02d} PoE"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_port_{port}_poe"

    @property
    def is_on(self) -> bool | None:
        value = self.port_data.get("admin")
        return None if value is None else value == 1

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.client.async_set_int(port_oid(RFC_PORT_ADMIN, self.port), 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.client.async_set_int(port_oid(RFC_PORT_ADMIN, self.port), 2)
        await self.coordinator.async_request_refresh()
