"""Binary sensors for PowerDsine PoE."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PowerDsineCoordinator
from .entity import PowerDsineEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PowerDsineCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PowerDsinePsuProblem(coordinator, "internal_psu", "Internal power supply"),
            PowerDsinePsuProblem(coordinator, "external_psu", "External power supply"),
        ]
    )


class PowerDsinePsuProblem(PowerDsineEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{name} problem"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}_problem"

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data["chassis"].get(self._key)
        if value in (None, 3):
            return None
        return value == 2
