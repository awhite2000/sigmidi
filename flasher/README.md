# SIGMIDI Foot Controller v0.1 USB firmware installer

Use **desktop Google Chrome or Microsoft Edge** and a USB-C **data** cable to install firmware on the DFRobot DFR1075 / FireBeetle 2 ESP32-C6 (4 MB). This firmware is a compiled prototype; physical controller and iPad validation remain to be done.

## Run the portable package

Extract all files from `sigmidi-foot-controller-0.1-web-flasher.zip` into one directory, then serve that directory:

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open **http://localhost:8766/** in desktop Chrome or Edge. Opening `index.html` directly from disk will not work. All installer scripts and firmware are included; the local server needs no internet connection. A local development server inside an embedded app may not expose USB devices; open the same address in Chrome or Edge.

To publish this installer, host the **whole directory** on an HTTPS static host, preserving relative paths. It works under a subdirectory too. Serve `.js` as JavaScript and `.bin` as binary; do not rewrite missing firmware URLs to the HTML index. The firmware stays in this site's `firmware/` folder. Nothing needs to be installed on the controller before the first flash.

## Install

1. Back up saved configuration as JSON using the controller's Wi-Fi editor, if available.
2. Connect the controller over USB-C. Close serial monitors or IDEs using that port.
3. Click **Connect & install**, select the controller's USB serial device, and choose Install in the dialog. The installer detects the chip and accepts only ESP32-C6.
4. Leave **Erase device** unchecked to retain settings from this project's existing partition layout. Select it only for a deliberate factory reset, corrupt settings, or replacement of unrelated firmware. Erasing removes all mappings, calibration and settings.
5. Confirm installation. Keep the controller plugged in until the installer reports completion. It will try to restart automatically; press RESET if it stays in download mode.
6. In the controller's encoder menu choose Wi-Fi Setup. Join the displayed network and open `http://192.168.4.1` to configure MIDI. The firmware uses its own Wi-Fi editor, not Improv Wi-Fi provisioning. iPad Safari can edit settings after installation, but USB flashing requires a supported desktop browser.

If no serial device appears, try another data cable. To enter download mode, hold BOOT, tap RESET, release BOOT and reconnect. Re-select the port if it changes. Installation errors are shown in the installer dialog, which also provides Logs & Console. A failed connection does not mean installation completed. Only one program can own the serial port at a time.

## Choose the enclosure variant

In the Wi-Fi editor, open **Settings → Enclosure variant** and choose **Left · Screen on left** or **Right · Screen on right**, then **Save**. On the encoder use **EDIT CONFIG → ENCLOSURE → LEFT / RIGHT**, click to accept, hold back to setup and **SAVE & EXIT**.

Left combines mirrored switch/calibration list order with 180° screen rotation. Right combines the original order with 0°. MIDI actions, names, calibration and LED assignments remain attached to their physical switches. Existing 180° orientation settings migrate to Left; older saved configurations without an orientation setting retain Right. New configurations default to Left. The selector is saved across restarts.

## Images and saved settings

The boot image includes the bootloader at `0x0000` and partition table at `0x8000`, ending before `0x9000`. The application starts at `0x20000`. The saved-settings NVS partition `0x9000–0x18fff` and PHY data `0x19000–0x19fff` are excluded from both write images. This preserves compatible settings when full-device erase is not selected. Firmware may still reset unusable NVS during startup recovery. Back up important mappings first.

**The application-only download is not a first-install image.** Use the web installer for first installation, or follow the boot/application offsets in `manifest.json` with esptool. Both images use DIO, 40 MHz and 4 MB flash settings matching the compiled firmware.

The page checks manifest/image SHA-256 hashes, image lengths, ESP32-C6 headers and safe flash ranges before enabling installation. These hashes detect accidental corruption; they are not a firmware signature or proof of publisher identity. The verified image bytes are passed to ESP Web Tools using in-memory URLs. `SHA256.json` lists all distributed files for independent checking.

## Build from the source project

In the firmware repository, run:

```sh
python3 scripts/build.py
python3 scripts/serve_flasher.py
```

The build uses PlatformIO, then generates `distribution/web-flasher/` and `distribution/sigmidi-foot-controller-0.1-web-flasher.zip`. Set `PIO` and `PLATFORMIO_CORE_DIR` as described in `docs/bringup.md` if needed. To repackage a current build without recompiling, run `python3 scripts/package_web_flasher.py` with the same tool environment. Packaging rejects stale sources, incorrect hashes, another chip, a different partition table or mismatched flash settings. Building and packaging never connect to or flash a physical device.

Browser installer: **ESP Web Tools 10.4.0**, distributed locally under Apache-2.0; see `vendor/esp-web-tools/LICENSE` , `vendor/esp-web-tools/provenance.json` and `vendor/THIRD_PARTY_NOTICES.txt`. The source project's `scripts/vendor_web_flasher.py` verifies the pinned npm SHA-512 archive before refreshing these assets. Firmware builds do not download browser dependencies.

The installer uses `assets/enclosure-left.png`, copied without geometry or image alterations from `design/fusion/mirrored/main/assembled.png`. Its source hash is recorded beside the image. Refresh that asset after changing the primary Left enclosure render.
