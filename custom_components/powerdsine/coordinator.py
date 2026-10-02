"""Data coordinator for PowerDsine PoE midspans."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BACKUP_STATUS,
    DETECTION_STATUS,
    MAIN_STATUS,
    OID_SYS_DESCR,
    OID_SYS_NAME,
    OID_SYS_OBJECT_ID,
    POWER_CLASS,
    POWERDSINE_SYSOBJECT_PREFIX,
    PORT_PRIORITY,
    PRIVATE_MAIN_BACKUP_STATUS,
    PRIVATE_MAIN_EXTERNAL_PSU,
    PRIVATE_MAIN_INTERNAL_PSU,
    PRIVATE_MAIN_MAX_POWER,
    PRIVATE_MAIN_POWER_BUDGET,
    PRIVATE_MAIN_VOLTAGE,
    PRIVATE_PORT_CONSUMPTION,
    PRIVATE_PORT_MAX_POWER,
    PRODUCTS,
    PSU_STATUS,
    RFC_MAIN_CONSUMPTION,
    RFC_MAIN_POWER,
    RFC_MAIN_STATUS,
    RFC_PORT_ADMIN,
    RFC_PORT_CLASS,
    RFC_PORT_DETECTION,
    RFC_PORT_OVERLOAD,
    RFC_PORT_POWER_DENIED,
    RFC_PORT_PRIORITY,
    RFC_PORT_SHORT,
    main_oid,
    port_oid,
)
from .snmp import PowerDsineSnmpClient, PowerDsineSnmpError

_LOGGER = logging.getLogger(__name__)
BATCH_SIZE = 32


@dataclass(slots=True)
class ProductInfo:
    """Detected PowerDsine product information."""

    sys_object_id: str
    product_leaf: int
    model: str
    ports: int
    port_max_power_writable: bool
    port_max_power_limit: int


class PowerDsineCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll a PowerDsine midspan."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: PowerDsineSnmpClient,
        product: ProductInfo,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"PowerDsine {entry.title}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client
        self.product = product
        self.entry = entry

    @staticmethod
    def product_from_sys_object_id(sys_object_id: str) -> ProductInfo:
        """Decode the Microsemi private sysObjectID."""
        normalized = str(sys_object_id).lstrip(".")
        if not normalized.startswith(POWERDSINE_SYSOBJECT_PREFIX):
            raise ValueError(f"Not a PowerDsine sysObjectID: {sys_object_id}")
        leaf = int(normalized.rsplit(".", 1)[1])
        if leaf not in PRODUCTS:
            raise ValueError(f"Unsupported PowerDsine product id {leaf}")
        model, ports, writable, max_power = PRODUCTS[leaf]
        return ProductInfo(normalized, leaf, model, ports, writable, max_power)

    @staticmethod
    async def async_detect(client: PowerDsineSnmpClient) -> tuple[ProductInfo, dict[str, Any]]:
        """Detect and validate a PowerDsine device without an SNMP walk."""
        values = await client.async_get_many([OID_SYS_OBJECT_ID, OID_SYS_NAME, OID_SYS_DESCR])
        raw_oid = values.get(OID_SYS_OBJECT_ID)
        if raw_oid is None:
            raise PowerDsineSnmpError("sysObjectID returned no value")
        product = PowerDsineCoordinator.product_from_sys_object_id(str(raw_oid))
        return product, values

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll only the OIDs we need."""
        chassis_oids = {
            "sys_name": OID_SYS_NAME,
            "sys_descr": OID_SYS_DESCR,
            "nominal_power": main_oid(RFC_MAIN_POWER),
            "oper_status": main_oid(RFC_MAIN_STATUS),
            "total_consumption": main_oid(RFC_MAIN_CONSUMPTION),
            "voltage": main_oid(PRIVATE_MAIN_VOLTAGE),
            "power_budget": main_oid(PRIVATE_MAIN_POWER_BUDGET),
            "max_power": main_oid(PRIVATE_MAIN_MAX_POWER),
            "backup_status": main_oid(PRIVATE_MAIN_BACKUP_STATUS),
            "internal_psu": main_oid(PRIVATE_MAIN_INTERNAL_PSU),
            "external_psu": main_oid(PRIVATE_MAIN_EXTERNAL_PSU),
        }

        port_fields = {
            "admin": RFC_PORT_ADMIN,
            "detection": RFC_PORT_DETECTION,
            "priority": RFC_PORT_PRIORITY,
            "class": RFC_PORT_CLASS,
            "power_denied": RFC_PORT_POWER_DENIED,
            "overload": RFC_PORT_OVERLOAD,
            "short": RFC_PORT_SHORT,
            "consumption": PRIVATE_PORT_CONSUMPTION,
            "max_power": PRIVATE_PORT_MAX_POWER,
        }

        reverse: dict[str, tuple[str, int | None]] = {}
        all_oids: list[str] = []

        for key, oid in chassis_oids.items():
            reverse[oid] = (key, None)
            all_oids.append(oid)

        for port in range(1, self.product.ports + 1):
            for field, base in port_fields.items():
                oid = port_oid(base, port)
                reverse[oid] = (field, port)
                all_oids.append(oid)

        raw: dict[str, Any | None] = {}
        try:
            for pos in range(0, len(all_oids), BATCH_SIZE):
                raw.update(await self.client.async_get_many_tolerant(all_oids[pos : pos + BATCH_SIZE]))
        except PowerDsineSnmpError as err:
            raise UpdateFailed(f"SNMP update failed: {err}") from err

        chassis: dict[str, Any] = {}
        ports: dict[int, dict[str, Any]] = {
            port: {} for port in range(1, self.product.ports + 1)
        }
        for oid, value in raw.items():
            field, port = reverse[oid]
            if port is None:
                chassis[field] = value
            else:
                ports[port][field] = value

        if chassis.get("oper_status") is not None:
            chassis["oper_status_text"] = MAIN_STATUS.get(chassis["oper_status"], "unknown")
        if chassis.get("backup_status") is not None:
            chassis["backup_status_text"] = BACKUP_STATUS.get(chassis["backup_status"], "unknown")
        for key in ("internal_psu", "external_psu"):
            if chassis.get(key) is not None:
                chassis[f"{key}_text"] = PSU_STATUS.get(chassis[key], "unknown")

        for data in ports.values():
            if data.get("detection") is not None:
                data["detection_text"] = DETECTION_STATUS.get(data["detection"], "unknown")
            if data.get("priority") is not None:
                data["priority_text"] = PORT_PRIORITY.get(data["priority"], "unknown")
            if data.get("class") is not None:
                data["class_text"] = POWER_CLASS.get(data["class"], "unknown")

        return {"chassis": chassis, "ports": ports}
