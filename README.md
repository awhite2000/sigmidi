# SIGMIDI Foot Controller v0.1

<img src="design/branding/sigmidi-mark.svg" width="96" alt="SIGMIDI logotype">

SIGMIDI is a programmable BLE MIDI foot controller built around the DFRobot DFR1075 FireBeetle 2 ESP32-C6 and Waveshare 24382 color LCD. It sends MIDI to an iPad and provides encoder menus and a Wi-Fi configuration editor.

## Features

- A four-switch base with up to three two-switch extensions: 4, 6, 8 or 10 momentary switches, detected individually through one resistor ladder.
- Independent ordered press and release lists of PC and CC messages, with channels 1–16 and a delay per message. PC supports STATIC, INCR and DECR with independent persistent counters. Added messages default to 5 ms. Per-switch Toggle mode alternates the two lists on successive presses.
- Two pedal inputs, independently selectable as two-wire resistors or three-wire potentiometers, with maximum resistance up to 10 kΩ, calibration, linear/log response and CC output.
- A 280 × 240 landscape LCD and a 20-detent encoder with click for local setup.
- An offline Wi-Fi editor for configuration, calibration, MIDI tests and JSON backups.
- Optional Pololu 2535 indicators, one per switch: white for a performed press action and yellow for release in momentary mode; white/off in Toggle mode.
- USB power and an optional 9 V center-negative input through a Pololu S13V10F5 regulator.

## Enclosures and switch identity

**Left is the preferred enclosure and firmware default.** Its display and encoder are on the left, with modular extensions added on the right. Left labels read **A B C D E / 1 2 3 4 5** across the upper/lower rows. Right has the electronics on the right and reverses each row.

Select **Settings → Enclosure variant** in the Wi-Fi editor or **EDIT CONFIG → ENCLOSURE** on the LCD. Left combines 180° LCD rotation with Left list order; Right uses 0°. MIDI actions, names, LED assignments and calibration belong to permanent electrical taps, independently of the selected variant or installed switch count.

The main enclosure measures **350 × 92 × 54 mm**, with a 30 mm raised row, 65 mm horizontal pitch, 32.5 mm stagger and 53 mm row spacing. The Left electronics shell has a 25 mm-wide icon raised 0.6 mm between A and B. Main and modular assemblies are available for both variants.

## Install and configure

Use the preserved [release bundles](distribution/README.md). From the project root:

```sh
python3 scripts/serve_flasher.py
```

Open **http://localhost:8766/** in desktop Chrome or Edge, connect the DFR1075 over USB-C and choose **Connect & install**. Leave **Erase device** unchecked to keep compatible saved settings. The flasher serves the complete local installer from `distribution/web-flasher/`.

On the controller, enter **Wi-Fi Setup**, join the displayed `SIGMIDI-xxxx` network, and open **http://192.168.4.1/**. Choose the enclosure, ladder wiring and installed switch count, calibrate the inputs, configure MIDI actions and save. Normal performance runs with Wi-Fi off. The BLE name is **SIGMIDI Foot Controller v0.1**.

## Documentation and files

| Area | Guide |
|---|---|
| Electrical wiring and GPIO | [Hardware](docs/hardware.md) |
| Editable electrical schematic | [KiCad project](design/kicad/README.md) |
| Modular taps and resistor values | [Resistor ladder](docs/resistor-ladders.md) |
| Menus, configuration and MIDI behavior | [Firmware](docs/firmware.md) |
| Building and commissioning | [Bring-up](docs/bringup.md) |
| Browser installation and hosting | [Web flasher](docs/web-flasher.md) |
| LED wiring and configuration | [LEDs](docs/leds.md) |
| Power wiring and load budget | [Power](docs/power.md) |
| CAD and manufacturing files | [Design](design/README.md) |
| Screenshots and enclosure renders | [Previews](previews/README.md) |

The [complete Fusion model](design/fusion/sigmidi-foot-controller-0.1.f3d) contains the native component hierarchy for all four assemblies and the modular part libraries. Firmware source is in `src/`, the embedded editor in `web/`, and tests in `tests/`. Release binaries and installers are in `distribution/`; `build/` contains disposable compiler outputs when a build is run.

## Validation status

The ESP-IDF 5.3.1 firmware compiles for ESP32-C6. Host tests cover configuration, MIDI scheduling, UI navigation, display mapping, switch identity and LED feedback. CAD, mesh and slicer checks accompany the manufacturing files. Physical USB flashing, iPad interoperability, printed fit/load strength and sustained thermal operation require validation on the assembled hardware.

![SIGMIDI preferred Left enclosure](previews/sigmidi-left-main.png)

## License

SIGMIDI is licensed under the [Apache License 2.0](LICENSE). Third-party materials carry their own license notices.
