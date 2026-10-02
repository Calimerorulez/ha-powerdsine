"""Select entities for PowerDsine PoE."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PORT_PRIORITY_REVERSE, RFC_PORT_PRIORITY, port_oid
from .coordinator import PowerDsineCoordinator
from .entity import PowerDsinePortEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PowerDsineCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PowerDsinePrioritySelect(coordinator, port)
        for port in range(1, coordinator.product.ports + 1)
    )


class PowerDsinePrioritySelect(PowerDsinePortEntity, SelectEntity):
    """PoE priority for a port."""

    _attr_options = ["critical", "high", "low"]
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, port: int) -> None:
        super().__init__(coordinator, port)
        self._attr_name = f"Port {port:02d} priority"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_port_{port}_priority"

    @property
    def current_option(self) -> str | None:
        return self.port_data.get("priority_text")

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.async_set_int(
            port_oid(RFC_PORT_PRIORITY, self.port), PORT_PRIORITY_REVERSE[option]
        )
        await self.coordinator.async_request_refresh()
