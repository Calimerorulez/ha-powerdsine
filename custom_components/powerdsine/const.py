"""Constants for the PowerDsine PoE integration."""

from __future__ import annotations

DOMAIN = "powerdsine"
PLATFORMS = ["sensor", "binary_sensor", "switch", "button", "select", "number"]

CONF_SNMP_VERSION = "snmp_version"
CONF_WRITE_COMMUNITY = "write_community"
CONF_USERNAME = "username"
CONF_AUTH_PROTOCOL = "auth_protocol"
CONF_AUTH_KEY = "auth_key"
CONF_PRIV_PROTOCOL = "priv_protocol"
CONF_PRIV_KEY = "priv_key"

OPT_SCAN_INTERVAL = "scan_interval"
OPT_POWER_CYCLE_DELAY = "power_cycle_delay"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_POWER_CYCLE_DELAY = 5
DEFAULT_PORT = 161

OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
OID_SYS_OBJECT_ID = "1.3.6.1.2.1.1.2.0"
OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"

RFC_PORT_ADMIN = "1.3.6.1.2.1.105.1.1.1.3"
RFC_PORT_DETECTION = "1.3.6.1.2.1.105.1.1.1.6"
RFC_PORT_PRIORITY = "1.3.6.1.2.1.105.1.1.1.7"
RFC_PORT_CLASS = "1.3.6.1.2.1.105.1.1.1.10"
RFC_PORT_POWER_DENIED = "1.3.6.1.2.1.105.1.1.1.12"
RFC_PORT_OVERLOAD = "1.3.6.1.2.1.105.1.1.1.13"
RFC_PORT_SHORT = "1.3.6.1.2.1.105.1.1.1.14"

RFC_MAIN_POWER = "1.3.6.1.2.1.105.1.3.1.1.2"
RFC_MAIN_STATUS = "1.3.6.1.2.1.105.1.3.1.1.3"
RFC_MAIN_CONSUMPTION = "1.3.6.1.2.1.105.1.3.1.1.4"
RFC_MAIN_THRESHOLD = "1.3.6.1.2.1.105.1.3.1.1.5"

PRIVATE_PORT_CONSUMPTION = "1.3.6.1.4.1.7428.1.2.1.1.1.3"
PRIVATE_PORT_MAX_POWER = "1.3.6.1.4.1.7428.1.2.1.1.1.4"
PRIVATE_PORT_TYPE = "1.3.6.1.4.1.7428.1.2.1.1.1.5"

PRIVATE_MAIN_VOLTAGE = "1.3.6.1.4.1.7428.1.2.2.1.1.2"
PRIVATE_MAIN_DETECTION_METHOD = "1.3.6.1.4.1.7428.1.2.2.1.1.3"
PRIVATE_MAIN_POWER_BUDGET = "1.3.6.1.4.1.7428.1.2.2.1.1.4"
PRIVATE_MAIN_MAX_POWER = "1.3.6.1.4.1.7428.1.2.2.1.1.5"
PRIVATE_MAIN_LEGACY_PD = "1.3.6.1.4.1.7428.1.2.2.1.1.6"
PRIVATE_MAIN_EXTENDED_POWER = "1.3.6.1.4.1.7428.1.2.2.1.1.7"
PRIVATE_MAIN_BACKUP_STATUS = "1.3.6.1.4.1.7428.1.2.2.1.1.8"
PRIVATE_MAIN_INTERNAL_PSU = "1.3.6.1.4.1.7428.1.2.2.1.1.9"
PRIVATE_MAIN_EXTERNAL_PSU = "1.3.6.1.4.1.7428.1.2.2.1.1.10"

POWERDSINE_SYSOBJECT_PREFIX = "1.3.6.1.4.1.7428.1.1.1."

DETECTION_STATUS = {1: "disabled", 2: "searching", 3: "delivering_power", 4: "fault", 5: "test", 6: "other_fault"}
PORT_PRIORITY = {1: "critical", 2: "high", 3: "low"}
PORT_PRIORITY_REVERSE = {v: k for k, v in PORT_PRIORITY.items()}
POWER_CLASS = {1: "class_0", 2: "class_1", 3: "class_2", 4: "class_3", 5: "class_4"}
MAIN_STATUS = {1: "on", 2: "off", 3: "faulty"}
BACKUP_STATUS = {1: "stand_alone", 2: "power_backup_by_rps", 3: "power_backup_by_midspan", 4: "incompatible_power_backup_device"}
PSU_STATUS = {1: "ok", 2: "fail", 3: "not_supported"}

PRODUCTS: dict[int, tuple[str, int, bool, int]] = {
    2: ("6-port AC", 6, True, 17), 3: ("6-port AC/DC", 6, True, 17),
    4: ("12-port AC", 12, True, 17), 5: ("12-port AC/DC", 12, True, 17),
    6: ("24-port AC", 24, True, 17), 7: ("24-port AC/DC", 24, True, 17),
    8: ("48-port AC", 48, True, 17), 9: ("48-port AC/DC", 48, True, 17),
    10: ("6-port High Power AC", 6, False, 99), 11: ("6-port High Power AC/DC", 6, False, 99),
    12: ("12-port High Power AC", 12, False, 99), 13: ("12-port High Power AC/DC", 12, False, 99),
    14: ("Gigabit 6-port AC", 6, True, 17), 15: ("Gigabit 12-port AC", 12, True, 17),
    16: ("Gigabit 24-port AC", 24, True, 17), 17: ("HiPoE Gigabit 6-port AC", 6, True, 30),
    18: ("HiPoE Gigabit 12-port AC", 12, True, 30), 19: ("HiPoE Gigabit 24-port AC", 24, True, 30),
    20: ("90xxG HiPoE AT Gigabit 6-port", 6, True, 36),
    21: ("90xxG HiPoE AT Gigabit 12-port AC/DC", 12, True, 36),
    22: ("90xxG HiPoE AT Gigabit 24-port AC/DC", 24, True, 36),
    23: ("4-pair AT Gigabit 6-port AC/DC", 6, True, 72),
    24: ("4-pair AT Gigabit 12-port AC/DC", 12, True, 72),
    25: ("HiPoE AT Gigabit 6-port DC", 6, True, 36),
    26: ("HiPoE AT Gigabit 12-port DC", 12, True, 36),
    27: ("HiPoE AT Gigabit 24-port DC", 24, True, 36),
    28: ("4-pair AT Gigabit 24-port AC/DC", 24, True, 72),
    29: ("EEPoE Gigabit 24-port AC/DC", 24, True, 72),
    30: ("PoH Gigabit 6-port AC/DC", 6, True, 99),
    31: ("PoH Gigabit 12-port AC/DC", 12, True, 99),
    32: ("PoH Gigabit 24-port AC/DC", 24, True, 99),
}

def port_oid(base: str, port: int, group: int = 1) -> str:
    return f"{base}.{group}.{port}"

def main_oid(base: str, group: int = 1) -> str:
    return f"{base}.{group}"
