# PowerDsine PoE for Home Assistant

Home Assistant custom integration for managed PowerDsine / Microsemi PoE midspans using SNMP.

The integration is based on the IETF POWER-ETHERNET-MIB (RFC 3621) plus Microsemi's `POE-PRIVATE-MIB-V2-02`. It does **not** run an SNMP walk. During setup it reads only `sysObjectID`, `sysName` and `sysDescr`, identifies the product, then polls a fixed list of documented OIDs.

## Primary target

Developed for the PowerDsine **PD-90xxG** family, including the 24-port PD-9024G. The private MIB also describes a number of older/newer PowerDsine families and the integration can identify those product IDs as well.

## Features

- UI configuration (config flow)
- SNMP v2c and v3
- Automatic product/port-count detection using PowerDsine `sysObjectID`
- Per port:
  - PoE enable/disable switch
  - actual power consumption
  - detection/delivery status
  - PoE class
  - power priority selector
  - configurable maximum port power where the private MIB defines it as writable
  - diagnostic fault counters
  - power-cycle button
- Chassis:
  - total PoE consumption
  - available/maximum PoE power
  - PSE voltage
  - PSE operational state
  - power backup state
  - internal/external PSU problem sensors
  - configurable overall power-budget percentage
- Device information: management software version and serial number on the device page
- Diagnostic sensors: management software version, boot version, serial number, system name and management uptime
- Diagnostics with SNMP secrets redacted
- English and Dutch translations

## Installation with HACS

1. In HACS, open **Integrations** → menu → **Custom repositories**.
2. Add `https://github.com/Calimerorulez/ha-powerdsine` and choose category **Integration**.
3. Install **PowerDsine PoE**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration** and search for **PowerDsine PoE**.

## Manual installation

Copy:

```text
custom_components/powerdsine/
```

to:

```text
/config/custom_components/powerdsine/
```

and restart Home Assistant.

## SNMP permissions

Read-only SNMP credentials are enough for sensors. To use PoE switches, priority, power limits and power-cycle buttons, the SNMP identity/community must have **SET** permission for the corresponding RFC3621/private MIB objects.

For SNMP v2c you can configure a separate write community. If it is left blank, the read community is also used for SET operations.

## OID indexing

Both supplied MIB tables use a two-part index for PoE ports:

```text
{ groupIndex, portIndex }
```

For a standalone midspan `groupIndex` is `1`, so port 7 for `pethPsePortAdminEnable` is:

```text
1.3.6.1.2.1.105.1.1.1.3.1.7
```

The private measured port-power OID for port 7 is:

```text
1.3.6.1.4.1.7428.1.2.1.1.1.3.1.7
```

## Notes

- The PD-90xxG private MIB defines per-port `portMaxPower` as read/write and describes up to 30/36 W for this family.
- Temperature is intentionally not exposed for PD-90xxG because the supplied private MIB says that object applies only to the 95xxG family.
- Fault counters are disabled by default in the entity registry to keep the entity list manageable.
- Default polling interval: 30 seconds (configurable from Integration options).
- Default power-cycle off time: 5 seconds (configurable from Integration options).

## Development status

This implementation (`0.1.2`) built from the supplied MIB definitions. The code is designed so the first real device test requires no `snmpwalk`; unsupported optional OIDs simply return no value.

If your exact firmware rejects a documented SET operation, Home Assistant will log the SNMP error and the device remains unchanged.

## Device information

The management software version, boot version and serial number are parsed from
explicit `App Ver=`, `BOOT Ver=` and `Unit S/N=` labels in SNMP `sysDescr`.
Serial numbers retain leading zeroes. Missing or unrecognized fields remain unknown.
The full description is available as an attribute on the management software sensor.
The device registry is updated when the reported software version changes.

Management uptime uses `sysUpTime.0` (hundredths of a second, converted to seconds).
This measures the SNMP management subsystem, not the time PoE has been supplying power,
and the 32-bit counter wraps after approximately 497 days.

The separate PoE controller firmware version, exact part number, flash size and
production number are not supplied by this private MIB or the observed `sysDescr`;
they are not inferred from the web interface or hardcoded for a particular device.
