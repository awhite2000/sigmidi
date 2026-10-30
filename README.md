# SIGMIDI Foot Controller v0.1

<img src="design/branding/sigmidi-mark.svg" width="96" alt="SIGMIDI logotype">

SIGMIDI is a programmable USB and BLE MIDI foot controller built around the Arduino Nano ESP32 (ESP32-S3, 16 MB flash) and Waveshare 24382 color LCD. It sends PC/CC messages over native USB MIDI and BLE MIDI simultaneously when both links are ready, including to an iPad and provides encoder menus and a Wi-Fi configuration editor.

## Features

- A four-switch base with up to three two-switch extensions: 4, 6, 8 or 10 momentary switches, detected individually through one resistor ladder.
- Independent ordered press and release lists of PC and CC messages, with channels 1–16 and a delay per message. PC supports STATIC, INCR and DECR with independent persistent counters. Added messages default to 5 ms. Per-switch Toggle mode alternates the two lists on successive presses.
- Two pedal inputs, independently selectable as two-wire resistors or three-wire potentiometers, with maximum resistance up to 10 kΩ, calibration, linear/log response and CC output.
- A 280 × 240 landscape LCD and a 20-detent encoder with click for local setup.
- An offline Wi-Fi editor for configuration, calibration, MIDI tests and JSON backups.
- Optional Pololu 2535 indicators, one per switch: white for a performed press action and yellow for release in momentary mode; white/off in Toggle mode.
- Native class-compliant USB MIDI plus BLE MIDI output. USB power or an optional 9 V center-negative input to Nano VIN; Pololu S13V10F5 supplies the optional LED rail.

## Enclosures and switch identity

**Left is the preferred enclosure and firmware default.** Its display and encoder are on the left, with modular extensions added on the right. Left labels read **A B C D E / 1 2 3 4 5** across the upper/lower rows. Right has the electronics on the right and reverses each row.

Select **Settings → Enclosure variant** in the Wi-Fi editor or **EDIT CONFIG → ENCLOSURE** on the LCD. Left combines 180° LCD rotation with Left list order; Right uses 0°. MIDI actions, names, LED assignments and calibration belong to permanent electrical taps, independently of the selected variant or installed switch count.

The main enclosure measures **350 × 92 × 54 mm**, with a 30 mm raised row, 65 mm horizontal pitch, 32.5 mm stagger and 53 mm row spacing. The Left electronics shell has a 25 mm-wide icon raised 0.6 mm between A and B. Main and modular assemblies are available for both variants.

The Nano mounts component-side up directly on four reinforced posts in each electronics base. See the [direct Nano mounting guide](design/fusion/nano-esp32/README.md). Use the [Nano pin/power map](docs/hardware.md), [electrical diagrams](design/electrical/README.md) and [editable KiCad schematic](design/kicad/README.md).

## Install and configure

Use the preserved [release bundles](distribution/README.md). From the project root:

```sh
python3 scripts/serve_flasher.py
```

Open **http://localhost:8766/** in desktop Chrome or Edge, connect the Nano over USB-C in ROM download mode (jumper B1 to GND, tap RST, remove the jumper) and choose **Connect & install**. Leave **Erase device** unchecked to keep compatible saved settings. The flasher serves the complete local installer from `distribution/web-flasher/`.

On the controller, enter **Wi-Fi Setup**, join the displayed `SIGMIDI-xxxx` network, and open **http://192.168.4.1/**. Choose the enclosure, ladder wiring and installed switch count, calibrate the inputs, configure MIDI actions and save. Normal performance runs with Wi-Fi off. The BLE name is **SIGMIDI Foot Controller v0.1**.

## Documentation and files

| Area | Guide |
|---|---|
| Step-by-step assembly, wiring and first power-up | [Assembly guide PDF](output/pdf/sigmidi-foot-controller-0.1-assembly-guide.pdf) · [Editable source](docs/assembly-guide.md) |
| USB/BLE connections, performance and editing; HX Stomp example in Appendix A | [User manual PDF](output/pdf/sigmidi-foot-controller-0.1-user-manual.pdf) · [Editable source](docs/user-manual.md) |
| Parts, hardware and enclosure quantities | [Bill of materials PDF](output/pdf/sigmidi-foot-controller-0.1-bill-of-materials.pdf) · [Shopping CSV](docs/bill-of-materials.csv) · [Document source](docs/bill-of-materials.md) |
| Electrical wiring and GPIO | [Hardware](docs/hardware.md) |
| Editable electrical schematic | [KiCad project](design/kicad/README.md) |
| Modular taps and resistor values | [Resistor ladder](docs/resistor-ladders.md) |
| Menus, configuration and MIDI behavior | [Firmware](docs/firmware.md) |
| Building and commissioning | [Bring-up](docs/bringup.md) |
| Browser installation and hosting | [Web flasher](docs/web-flasher.md) |
| LED wiring and configuration | [LEDs](docs/leds.md) |
| Power wiring and load budget | [Power](docs/power.md) |
| CAD and manufacturing files | [Design](design/README.md) |
| Arduino Nano ESP32 components-up mounting | [Direct base mounting](design/fusion/nano-esp32/README.md) |
| Screenshots and enclosure renders | [Previews](previews/README.md) |

The [complete Fusion model](design/fusion/sigmidi-foot-controller-0.1.f3d) contains the native component hierarchy for all four assemblies and the modular part libraries. Firmware source is in `src/`, the embedded editor in `web/`, and tests in `tests/`. Release binaries and installers are in `distribution/`; `build/` contains disposable compiler outputs when a build is run.

## Validation status

The firmware targets ESP-IDF 5.3.1 on ESP32-S3. Host tests cover configuration, MIDI scheduling, UI navigation, display mapping, switch identity and LED feedback. CAD, mesh and slicer checks accompany the manufacturing files. Physical USB flashing, iPad interoperability, printed fit/load strength and sustained thermal operation require validation on the assembled hardware.

![SIGMIDI preferred Left enclosure](previews/sigmidi-left-main.png)

## License

SIGMIDI is licensed under the [Apache License 2.0](LICENSE). Third-party materials carry their own license notices.
