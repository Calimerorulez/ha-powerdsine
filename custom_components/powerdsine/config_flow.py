"""Config flow for PowerDsine PoE."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.config_entries import ConfigFlowResult

from .const import (
    CONF_AUTH_KEY,
    CONF_AUTH_PROTOCOL,
    CONF_PRIV_KEY,
    CONF_PRIV_PROTOCOL,
    CONF_SNMP_VERSION,
    CONF_USERNAME,
    CONF_WRITE_COMMUNITY,
    DEFAULT_PORT,
    DEFAULT_POWER_CYCLE_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    OPT_POWER_CYCLE_DELAY,
    OPT_SCAN_INTERVAL,
)
from .coordinator import PowerDsineCoordinator
from .snmp import PowerDsineSnmpClient, PowerDsineSnmpError, SnmpConfig


class PowerDsineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._connection: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect address and protocol version."""
        if user_input is not None:
            self._connection = user_input
            if user_input[CONF_SNMP_VERSION] == "3":
                return await self.async_step_v3()
            return await self.async_step_community()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_SNMP_VERSION, default="2c"): vol.In(["2c", "3"]),
                }
            ),
        )

    async def async_step_community(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect SNMP v2c credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**self._connection, **user_input}
            try:
                title = await self._async_validate(data)
            except (PowerDsineSnmpError, ValueError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(data[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="community",
            data_schema=vol.Schema(
                {
                    vol.Required("community", default="public"): str,
                    vol.Optional(CONF_WRITE_COMMUNITY, default=""): str,
                }
            ),
            errors=errors,
        )

    async def async_step_v3(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Collect SNMPv3 credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**self._connection, **user_input}
            auth = data[CONF_AUTH_PROTOCOL]
            priv = data[CONF_PRIV_PROTOCOL]
            if auth != "none" and len(data.get(CONF_AUTH_KEY, "")) < 8:
                errors[CONF_AUTH_KEY] = "key_too_short"
            elif priv != "none" and len(data.get(CONF_PRIV_KEY, "")) < 8:
                errors[CONF_PRIV_KEY] = "key_too_short"
            elif priv != "none" and auth == "none":
                errors[CONF_AUTH_PROTOCOL] = "auth_required_for_privacy"
            else:
                try:
                    title = await self._async_validate(data)
                except (PowerDsineSnmpError, ValueError):
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(data[CONF_HOST])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="v3",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_AUTH_PROTOCOL, default="SHA"): vol.In(
                        ["none", "MD5", "SHA", "SHA224", "SHA256", "SHA384", "SHA512"]
                    ),
                    vol.Optional(CONF_AUTH_KEY, default=""): str,
                    vol.Required(CONF_PRIV_PROTOCOL, default="none"): vol.In(
                        ["none", "DES", "3DES", "AES128", "AES192", "AES256"]
                    ),
                    vol.Optional(CONF_PRIV_KEY, default=""): str,
                }
            ),
            errors=errors,
        )

    async def _async_validate(self, data: dict[str, Any]) -> str:
        client = PowerDsineSnmpClient(
            SnmpConfig(
                host=data[CONF_HOST],
                port=data[CONF_PORT],
                version=data[CONF_SNMP_VERSION],
                community=data.get("community", "public"),
                write_community=data.get(CONF_WRITE_COMMUNITY) or None,
                username=data.get(CONF_USERNAME),
                auth_protocol=data.get(CONF_AUTH_PROTOCOL, "none"),
                auth_key=data.get(CONF_AUTH_KEY) or None,
                priv_protocol=data.get(CONF_PRIV_PROTOCOL, "none"),
                priv_key=data.get(CONF_PRIV_KEY) or None,
            )
        )
        try:
            await client.async_initialize()
            product, values = await PowerDsineCoordinator.async_detect(client)
        finally:
            await client.async_close()
        sys_name = values.get("1.3.6.1.2.1.1.5.0")
        return str(sys_name) if sys_name else f"PowerDsine {product.model}"

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return PowerDsineOptionsFlow()


class PowerDsineOptionsFlow(config_entries.OptionsFlow):
    """Options for polling and power cycling."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPT_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                    vol.Required(
                        OPT_POWER_CYCLE_DELAY,
                        default=self.config_entry.options.get(
                            OPT_POWER_CYCLE_DELAY, DEFAULT_POWER_CYCLE_DELAY
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                }
            ),
        )
