"""Number entities for PowerDsine PoE."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    PRIVATE_MAIN_POWER_BUDGET,
    PRIVATE_PORT_MAX_POWER,
    main_oid,
    port_oid,
)
from .coordinator import PowerDsineCoordinator
from .entity import PowerDsineEntity, PowerDsinePortEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PowerDsineCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = [PowerDsineBudgetNumber(coordinator)]
    if coordinator.product.port_max_power_writable:
        entities.extend(
            PowerDsinePortMaxPowerNumber(coordinator, port)
            for port in range(1, coordinator.product.ports + 1)
        )
    async_add_entities(entities)


class PowerDsineBudgetNumber(PowerDsineEntity, NumberEntity):
    _attr_name = "Power budget limit"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 10
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_power_budget"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data["chassis"].get("power_budget")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.async_set_int(main_oid(PRIVATE_MAIN_POWER_BUDGET), int(value))
        await self.coordinator.async_request_refresh()


class PowerDsinePortMaxPowerNumber(PowerDsinePortEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 1
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, port: int) -> None:
        super().__init__(coordinator, port)
        self._attr_name = f"Port {port:02d} maximum power"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_port_{port}_max_power"
        self._attr_native_max_value = coordinator.product.port_max_power_limit

    @property
    def native_value(self) -> float | None:
        return self.port_data.get("max_power")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.async_set_int(
            port_oid(PRIVATE_PORT_MAX_POWER, self.port), int(value)
        )
        await self.coordinator.async_request_refresh()
