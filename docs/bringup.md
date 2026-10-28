# SIGMIDI Foot Controller v0.1 — Build and first hardware bring-up

## Firmware status

This is the first compiled prototype, not hardware-qualified firmware. PlatformIO espressif32 6.9.0 provides ESP-IDF 5.3.1. The generic ESP32-C6 board definition is overridden to use 4 MB flash and the project's partition table for DFR1075. GPIO assignments are in `docs/hardware.md` and `src/hardware.cpp`.

Implemented: standard BLE MIDI service with timestamped CC/PC notifications, subscription readiness, independent press/release sequences and delays, ADC ladder debounce, two pedal converters with filtering/hysteresis, ST7789V2 280×240 SPI display, encoder menus, persistent validated configuration, WPA2 setup access point, browser editor, calibration capture, explicit MIDI sequence tests, optional WS2811 RGB switch feedback, and JSON backups.

Initial limits: 32 messages per edge, 128 messages total, 16 outstanding switch jobs, 10 seconds maximum delay per message, 32 KiB maximum web/import request. Empty MIDI mappings and disabled pedal transmission are the factory defaults. The BLE peripheral currently does not implement persistent pairing/bonding; establish its MIDI connection through the iPad app. Automatic paired reconnection is not implemented.

## Build

Install PlatformIO Core and a C++17 host compiler. ESP-IDF requires paths without spaces. The build helper copies source into a temporary directory and keeps disposable compiler outputs in `build/` and publishes firmware and installer releases to `distribution/`:

```sh
python3 scripts/build.py
```

Set `PIO` if PlatformIO is not on PATH. Its package cache must also resolve to a path without spaces. On the development machine used for the initial build:

```sh
PIO=/Users/ab/.platformio/penv/bin/pio \
PLATFORMIO_CORE_DIR=/tmp/midi-foot-toolchain \
python3 scripts/build.py
```

The temporary package cache may be removed by the OS; use a persistent space-free cache for ongoing development. In a checkout without spaces, normal `pio run` also works. The native ESP-IDF CMake project embeds the same editor HTML.

Host tests:

```sh
scripts/test.sh
```

If `IDF_PATH` or `PLATFORMIO_CORE_DIR` points to the installed ESP-IDF sources, this also runs configuration serialization tests using IDF's cJSON. Set `NODE` to a modern Node executable to include browser JavaScript syntax checking.

## Browser flash

The build also packages a complete USB browser installer. Run `python3 scripts/serve_flasher.py`, open **http://localhost:8766/** in desktop Chrome or Edge, connect the controller, and choose **Connect & install**. Leave Erase device unchecked when updating a compatible SIGMIDI Foot Controller layout. See [web flasher and saved-settings behavior](web-flasher.md). The portable ZIP and HTTPS hosting instructions are included there.

## Command-line flash

Confirm the board and wiring before flashing. Use esptool with the board's actual serial port, substituting `PORT`:

```sh
python -m esptool --chip esp32c6 --port PORT --baud 460800 write_flash \
  0x0 distribution/firmware/bootloader.bin \
  0x8000 distribution/firmware/partitions.bin \
  0x20000 distribution/firmware/firmware.bin
```

The Python environment needs esptool installed. ESP-IDF/PlatformIO installs a compatible version in its tools environment. This command does not erase the whole flash; a different existing partition layout may require separate recovery. No hardware has been flashed by this implementation task.

## First run

1. Start with USB power, LCD, encoder, and ladder. Verify LCD orientation and idle plus all installed ladder levels before connecting pedals. Firmware disables analog interpretation if ADC calibration cannot initialize.
2. Turn the encoder and check one menu step per physical detent. The default decoder uses four valid transitions per detent. If the selected 20-detent encoder uses half-cycle detents, compile with `-DEDGES_PER_DETENT=2`. Reverse A/B if direction is reversed.
3. With all switches released, click for setup. Set **EDIT CONFIG → Switch count** to the installed total (4/6/8/10 in Modular wiring mode), or use **Settings → Number of footswitches** in the Wi-Fi editor. New defaults use the Left enclosure variant, Modular wiring and ten switches. Select four for the base alone. Old backups migrate in Linear mode. Hidden physical mappings and measured centers are retained when reducing the count. Save and exit to apply. Rotate to choose, click to select or edit, hold for 700 ms to cancel/back. Configuration fields are organized as a tree: switches, press/release message lists, pedals, ladder centers, and global settings. String editing advances one character per click; hold cancels. Message type is shown as CC or PC; turning the encoder while editing selects only these two choices. PC messages show Program and hide Value; CC messages show Controller and Value. JSON backups retain numeric type values (0 = CC, 1 = PC). Message lists have Append Message and Test; message objects have Delete/Move Up/Move Down. Save & Exit persists; Discard & Exit restores the last saved configuration.
4. Choose Wi-Fi Setup. Join the displayed `SIGMIDI-xxxx` network, open `http://192.168.4.1` in Safari, and enter the displayed Wi-Fi password again to acquire the editor session. Wi-Fi has no internet. A password is generated each time Wi-Fi starts. Use the direct browser address rather than expecting a captive portal.
5. On Calibration, capture idle and every switch individually. Adjust acceptance half-width only after examining measured gaps and noise. Save only a configuration with non-overlapping windows.
6. Configure a single CC action and connect the iPad MIDI application to **SIGMIDI Foot Controller v0.1** through its BLE MIDI interface. Explicit Test buttons work only while BLE notifications are subscribed. Verify the receiving MIDI monitor before controlling instruments.
7. Save & Exit to turn off Wi-Fi and resume footswitch/pedal transmission. A browser or local edit does not transmit MIDI by itself. Normal setup entry waits for outstanding switch actions to finish.

The browser and encoder share a validated draft. A browser owns editing while its 60-second lease is refreshed by status polling. Holding the encoder during browser editing revokes the lease and discards that draft. Saved settings survive power cycles; unsaved browser typing does not. Use Reload Draft after conflicts. JSON backups exclude network credentials.

## Pedal calibration and remaining bench checks

Electrical mode changes apply when leaving setup, not immediately while editing. Unplug the pedal, save the desired mode and exit, reconnect, then reopen setup for calibration. Live readings during setup therefore reflect the last applied mode. Potentiometer heel/toe capture is supported in the browser. Resistor mode currently uses the nominal 3.3 V / 10 kΩ divider model and configured maximum resistance; measured reference/tolerance correction and nonzero minimum-resistance calibration remain future refinements.

PC numbers in the initial editor are shown and stored as wire values 0–127. The reserved display-offset field does not yet change the UI rendering. The LCD uses an original 5×7 bitmap font at multiple sizes, with seven scrolling menu rows, highlighted selection/edit state, PC/CC colors and pedal bars. Browser names may contain characters the uppercase LCD font cannot render.

Verify LCD remap/orientation, encoder direction/detents, measured ladder noise, pedal endpoints, hot-plug protection, configuration recovery, BLE reconnect behavior, and end-to-end MIDI latency on the assembled board. Wi-Fi/BLE share the radio; setup tests do not establish performance latency. Browser JavaScript has syntax checks; a live Safari/UI test and device HTTP integration test remain outstanding.

## Editing action lists

Each of the ten switches has an independent **Press** list and **Release** list. Both may contain a mixture of PC and CC messages, each with its own MIDI channel and optional delay. Empty lists send nothing. Limits are 32 messages per list and 128 messages across the controller.

On the LCD, open Edit Config → switches → switch number → press or release. Use Append Message repeatedly, then select each compact message entry to edit it. Delete, Move Up and Move Down are inside each message. On Wi-Fi, each switch exposes On press and On release sections with Append message and reorder controls. Test actions send the selected complete list.

Action lists initially show compact summaries such as `PC24/2` and `CC17:127/3`. Select an LCD entry for Edit, Insert Before, or Delete; Append Message adds at the end. Long press returns to the list. In the browser, expand a compact entry to edit, insert before it, delete, or reorder. Appending or inserting opens the new message editor.

Newly appended or inserted MIDI messages default to a 5 ms delay before transmission in both editors. Existing configured delays, including zero, are retained.

Configuration schema version 4 adds `ladderLayout` to `switchCount`, global LED settings and per-tap assignments. Modular totals are 4/6/8/10; displayed labels run A–E from left to right in the upper row and 1–5 from left to right in the lower row for the preferred Left enclosure; Right reverses each row. Arrays remain in permanent tap order so expansion retains actions, LEDs and calibration on their physical switches. V1–3 data migrates in Linear mode, preserving its original meaning. Test coverage includes all modular totals, legacy counts, migration, inactive-input rejection, mapped LCD/browser edits, calibration, MIDI tests and ADC-to-MIDI/LED behavior. [Ladder details](resistor-ladders.md).

## Waveshare 24382 assembly and display check

Use the revised screen cutout and four 16.1 mm hollow supports in the current print package. The factory rear M2 standoffs rest on these supports; fasten with four **M2×5 countersunk screws from the underside**, with their heads recessed into the hollow supports through Ø2.6 clearance bores. The head seats are at Z−9.51 mm, with Ø4.4 mm nominal tool access. The factory holes are blind: do not substitute longer screws. Nominal thread engagement is 1.39 mm; check actual hardware and seating before tightening.

After flashing, confirm the full 280×240 landscape area, rounded corners, RGB color order, BLE badge, pedal bars, scrolling and PC/CC message forms. Compare with `previews/display-preview.png`; PC shows Program and no Value, while CC shows Control and Value. Parameter values share one vertical column; menu actions are purple and the value being edited is amber. Test the actual display and iPad before relying on the controller in performance.

## Optional Pololu 2535 LED chain

Use the specified [Pololu 2535](https://www.pololu.com/product/2535) 5 mm diffused LEDs. Follow [lead orientation, wiring and commissioning](leds.md): GPIO16/TX → 5 V AHCT buffer → 330 Ω → first pixel DIN, with regulated 5 V LED power and shared ground. Select **RGB** order and **2535** protocol (800 kbit/s). Ten LEDs need approximately 0.5 A at full white; provide at least 1 A LED capacity plus controller/display headroom. These LEDs power up blue until a color command; firmware sends black at initialization and refreshes the chain every 250 ms. The feature starts disabled. Set ENABLED, BRIGHTNESS, RGB ORDER and PROTOCOL in **EDIT CONFIG → LED CHAIN**, or in Wi-Fi Settings; edit each switch's **LED NO.** / **LED assignment** if needed. Save before testing.

LEDs change to white/yellow at the first successfully queued MIDI message of a press/release phase and retain that color. Empty lists do not change the LED. Verify actual LEDs, power and timing under BLE/Wi-Fi traffic; the compiled firmware and host tests have not been bench-tested on a physical chain.

## Enclosure variant

For the enclosure with the screen on the left, select Wi-Fi **Settings → Enclosure variant → Left · Screen on left**, then **Save**. Alternatively choose **EDIT CONFIG → ENCLOSURE → LEFT** on the encoder, click, hold back to setup and **SAVE & EXIT**. Left combines 180° screen rotation with mirrored switch/calibration list order. MIDI actions, names, measured voltages and LED assignments retain their physical tap identities.

Choose **Right** for the original screen-on-right enclosure. The selected variant persists across restarts. Older saved 180° orientation settings migrate to Left; older records without an orientation setting retain Right. New configurations default to Left. Verify that pressing A selects A and drives its assigned LED after installation.
