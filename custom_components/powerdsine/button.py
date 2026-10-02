"""Buttons for PowerDsine PoE."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_POWER_CYCLE_DELAY, DOMAIN, OPT_POWER_CYCLE_DELAY, RFC_PORT_ADMIN, port_oid
from .coordinator import PowerDsineCoordinator
from .entity import PowerDsinePortEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PowerDsineCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PowerDsinePowerCycleButton(coordinator, port)
        for port in range(1, coordinator.product.ports + 1)
    )


class PowerDsinePowerCycleButton(PowerDsinePortEntity, ButtonEntity):
    """Power-cycle one PoE port."""

    def __init__(self, coordinator, port: int) -> None:
        super().__init__(coordinator, port)
        self._attr_name = f"Port {port:02d} power cycle"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_port_{port}_power_cycle"
        self._attr_icon = "mdi:restart"

    async def async_press(self) -> None:
        delay = self.coordinator.entry.options.get(
            OPT_POWER_CYCLE_DELAY, DEFAULT_POWER_CYCLE_DELAY
        )
        oid = port_oid(RFC_PORT_ADMIN, self.port)
        await self.coordinator.client.async_set_int(oid, 2)
        await asyncio.sleep(delay)
        await self.coordinator.client.async_set_int(oid, 1)
        await self.coordinator.async_request_refresh()
