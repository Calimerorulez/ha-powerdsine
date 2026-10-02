"""Small asynchronous SNMP client used by PowerDsine."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    USM_AUTH_HMAC128_SHA224,
    USM_AUTH_HMAC192_SHA256,
    USM_AUTH_HMAC256_SHA384,
    USM_AUTH_HMAC384_SHA512,
    USM_AUTH_HMAC96_MD5,
    USM_AUTH_HMAC96_SHA,
    USM_AUTH_NONE,
    USM_PRIV_CBC168_3DES,
    USM_PRIV_CBC56_DES,
    USM_PRIV_CFB128_AES,
    USM_PRIV_CFB192_AES,
    USM_PRIV_CFB256_AES,
    USM_PRIV_NONE,
    get_cmd,
    set_cmd,
)
from pysnmp.proto.rfc1902 import Integer32
from pysnmp.proto.rfc1905 import EndOfMibView, NoSuchInstance, NoSuchObject


class PowerDsineSnmpError(Exception):
    """Raised when an SNMP operation fails."""


AUTH_PROTOCOLS = {
    "none": USM_AUTH_NONE,
    "MD5": USM_AUTH_HMAC96_MD5,
    "SHA": USM_AUTH_HMAC96_SHA,
    "SHA224": USM_AUTH_HMAC128_SHA224,
    "SHA256": USM_AUTH_HMAC192_SHA256,
    "SHA384": USM_AUTH_HMAC256_SHA384,
    "SHA512": USM_AUTH_HMAC384_SHA512,
}

PRIV_PROTOCOLS = {
    "none": USM_PRIV_NONE,
    "DES": USM_PRIV_CBC56_DES,
    "3DES": USM_PRIV_CBC168_3DES,
    "AES128": USM_PRIV_CFB128_AES,
    "AES192": USM_PRIV_CFB192_AES,
    "AES256": USM_PRIV_CFB256_AES,
}


@dataclass(slots=True)
class SnmpConfig:
    """Connection parameters."""

    host: str
    port: int = 161
    version: str = "2c"
    community: str = "public"
    write_community: str | None = None
    username: str | None = None
    auth_protocol: str = "none"
    auth_key: str | None = None
    priv_protocol: str = "none"
    priv_key: str | None = None
    timeout: float = 2.0
    retries: int = 1


class PowerDsineSnmpClient:
    """Async PySNMP wrapper that uses numeric OIDs only."""

    def __init__(self, config: SnmpConfig) -> None:
        self.config = config
        self._engine = SnmpEngine()
        self._target: UdpTransportTarget | None = None

    async def async_initialize(self) -> None:
        """Create the reusable UDP target."""
        self._target = await UdpTransportTarget.create(
            (self.config.host, self.config.port),
            timeout=self.config.timeout,
            retries=self.config.retries,
        )

    def _auth(self, *, write: bool = False) -> CommunityData | UsmUserData:
        if self.config.version == "2c":
            community = (
                self.config.write_community
                if write and self.config.write_community
                else self.config.community
            )
            return CommunityData(community, mpModel=1)

        if not self.config.username:
            raise PowerDsineSnmpError("SNMPv3 username is missing")

        auth_protocol = AUTH_PROTOCOLS[self.config.auth_protocol]
        priv_protocol = PRIV_PROTOCOLS[self.config.priv_protocol]
        return UsmUserData(
            self.config.username,
            authKey=self.config.auth_key or None,
            privKey=self.config.priv_key or None,
            authProtocol=auth_protocol,
            privProtocol=priv_protocol,
        )

    @staticmethod
    def _value(value: Any) -> Any | None:
        if isinstance(value, (NoSuchObject, NoSuchInstance, EndOfMibView)):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return value.prettyPrint() if hasattr(value, "prettyPrint") else str(value)

    async def async_get_many(self, oids: Iterable[str]) -> dict[str, Any | None]:
        """Read multiple OIDs in one request."""
        if self._target is None:
            await self.async_initialize()

        oid_list = list(oids)
        if not oid_list:
            return {}

        error_indication, error_status, error_index, var_binds = await get_cmd(
            self._engine,
            self._auth(),
            self._target,
            ContextData(),
            *(ObjectType(ObjectIdentity(oid)) for oid in oid_list),
            lookupMib=False,
        )
        if error_indication:
            raise PowerDsineSnmpError(str(error_indication))
        if error_status:
            bad_oid = oid_list[int(error_index) - 1] if error_index else "unknown"
            raise PowerDsineSnmpError(f"{error_status.prettyPrint()} at {bad_oid}")

        result: dict[str, Any | None] = {}
        for requested_oid, var_bind in zip(oid_list, var_binds, strict=False):
            result[requested_oid] = self._value(var_bind[1])
        return result

    async def async_get(self, oid: str) -> Any | None:
        """Read one OID."""
        return (await self.async_get_many([oid])).get(oid)

    async def async_get_many_tolerant(
        self, oids: Iterable[str]
    ) -> dict[str, Any | None]:
        """Read OIDs while treating per-OID PDU failures as unavailable."""
        oid_list = list(oids)
        if not oid_list:
            return {}
        try:
            return await self.async_get_many(oid_list)
        except PowerDsineSnmpError as err:
            message = str(err).lower()
            transport_markers = (
                "timeout",
                "timed out",
                "no snmp response",
                "unknown user",
                "wrong digest",
                "authentication",
                "decryption",
            )
            if any(marker in message for marker in transport_markers):
                raise
            if len(oid_list) == 1:
                return {oid_list[0]: None}
            middle = len(oid_list) // 2
            left = await self.async_get_many_tolerant(oid_list[:middle])
            right = await self.async_get_many_tolerant(oid_list[middle:])
            return {**left, **right}

    async def async_set_int(self, oid: str, value: int) -> None:
        """Write one integer OID."""
        if self._target is None:
            await self.async_initialize()

        error_indication, error_status, error_index, _ = await set_cmd(
            self._engine,
            self._auth(write=True),
            self._target,
            ContextData(),
            ObjectType(ObjectIdentity(oid), Integer32(value)),
            lookupMib=False,
        )
        if error_indication:
            raise PowerDsineSnmpError(str(error_indication))
        if error_status:
            raise PowerDsineSnmpError(
                f"{error_status.prettyPrint()} at index {int(error_index) if error_index else 0}"
            )

    async def async_close(self) -> None:
        """Close PySNMP dispatcher resources."""
        close = getattr(self._engine, "close_dispatcher", None)
        if close is not None:
            close()
