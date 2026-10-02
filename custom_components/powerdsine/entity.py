"""Shared entity helpers."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PowerDsineCoordinator


class PowerDsineEntity(CoordinatorEntity[PowerDsineCoordinator]):
    """Base entity for the PowerDsine chassis."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PowerDsineCoordinator) -> None:
        super().__init__(coordinator)
        product = coordinator.product
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            manufacturer="PowerDsine / Microsemi",
            model=product.model,
            name=coordinator.entry.title,
            configuration_url=f"http://{coordinator.entry.data['host']}",
        )


class PowerDsinePortEntity(PowerDsineEntity):
    """Base entity tied to one PoE port."""

    def __init__(self, coordinator: PowerDsineCoordinator, port: int) -> None:
        super().__init__(coordinator)
        self.port = port

    @property
    def port_data(self):
        return self.coordinator.data["ports"].get(self.port, {})
