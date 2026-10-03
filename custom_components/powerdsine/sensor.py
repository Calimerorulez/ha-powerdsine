"""Sensors for PowerDsine PoE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PowerDsineCoordinator
from .entity import PowerDsineEntity, PowerDsinePortEntity


@dataclass(frozen=True, kw_only=True)
class PowerDsineSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


CHASSIS_SENSORS = (
    PowerDsineSensorDescription(
        key="software_version",
        name="Management software version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
        value_fn=lambda d: d.get("software_version"),
    ),
    PowerDsineSensorDescription(
        key="boot_version",
        name="Boot version",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
        value_fn=lambda d: d.get("boot_version"),
    ),
    PowerDsineSensorDescription(
        key="serial_number",
        name="Serial number",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:identifier",
        value_fn=lambda d: d.get("serial_number"),
    ),
    PowerDsineSensorDescription(
        key="sys_name",
        name="System name",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:label",
        value_fn=lambda d: d.get("sys_name"),
    ),
    PowerDsineSensorDescription(
        key="uptime",
        name="Management uptime",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda d: d.get("uptime"),
    ),
    PowerDsineSensorDescription(
        key="total_consumption",
        name="Total PoE power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("total_consumption"),
    ),
    PowerDsineSensorDescription(
        key="max_power",
        name="Maximum PoE power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda d: d.get("max_power"),
    ),
    PowerDsineSensorDescription(
        key="voltage",
        name="PSE voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("voltage"),
    ),
    PowerDsineSensorDescription(
        key="oper_status",
        name="PSE status",
        value_fn=lambda d: d.get("oper_status_text"),
    ),
    PowerDsineSensorDescription(
        key="backup_status",
        name="Power backup status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("backup_status_text"),
    ),
)

PORT_SENSORS = (
    PowerDsineSensorDescription(
        key="consumption",
        name="Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("consumption"),
    ),
    PowerDsineSensorDescription(
        key="detection",
        name="Status",
        value_fn=lambda d: d.get("detection_text"),
    ),
    PowerDsineSensorDescription(
        key="class",
        name="Class",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("class_text"),
    ),
    PowerDsineSensorDescription(
        key="power_denied",
        name="Power denied counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("power_denied"),
    ),
    PowerDsineSensorDescription(
        key="overload",
        name="Overload counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("overload"),
    ),
    PowerDsineSensorDescription(
        key="short",
        name="Short counter",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("short"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: PowerDsineCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        PowerDsineChassisSensor(coordinator, description) for description in CHASSIS_SENSORS
    ]
    for port in range(1, coordinator.product.ports + 1):
        entities.extend(
            PowerDsinePortSensor(coordinator, port, description) for description in PORT_SENSORS
        )
    async_add_entities(entities)


class PowerDsineChassisSensor(PowerDsineEntity, SensorEntity):
    entity_description: PowerDsineSensorDescription

    def __init__(self, coordinator, description) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data["chassis"])


    @property
    def extra_state_attributes(self):
        """Expose the raw description without the sensor state length limit."""
        if self.entity_description.key == "software_version":
            return {"system_description": self.coordinator.data["chassis"].get("sys_descr")}
        return None


class PowerDsinePortSensor(PowerDsinePortEntity, SensorEntity):
    entity_description: PowerDsineSensorDescription

    def __init__(self, coordinator, port: int, description) -> None:
        super().__init__(coordinator, port)
        self.entity_description = description
        self._attr_name = f"Port {port:02d} {description.name.lower()}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_port_{port}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.port_data)
