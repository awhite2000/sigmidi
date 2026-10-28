# SIGMIDI Foot Controller v0.1 — Browser firmware installation

The USB installer is in `flasher/`. A successful firmware build generates a complete, locally hosted site in `distribution/web-flasher/` and a portable `distribution/sigmidi-foot-controller-0.1-web-flasher.zip` containing the firmware, manifest and pinned ESP Web Tools assets.

## Start the installer

```sh
# Use the preserved bundle directly; rebuilding is optional.
python3 scripts/serve_flasher.py
```

Open **http://localhost:8766/** in desktop Chrome or Edge and connect the DFR1075 using a USB-C data cable. Click **Connect & install**, choose the controller's USB serial port and confirm installation. Hold BOOT and tap RESET if automatic download mode fails. The default server binds only to `127.0.0.1`; it serves only the generated installer directory and checks its file hashes at startup.

Set the build tools if they are not on PATH:

```sh
PIO=/Users/ab/.platformio/penv/bin/pio \
PLATFORMIO_CORE_DIR=/tmp/midi-foot-toolchain \
python3 scripts/build.py
```

For another local port, use `python3 scripts/serve_flasher.py --port 8767`. An extracted ZIP can also be served with `python3 -m http.server 8766 --bind 127.0.0.1` from its directory. There is no CDN dependency; the complete package works without internet. USB access still requires a supported desktop browser and HTTPS or localhost. iPad Safari remains suitable for the controller's Wi-Fi editor after installation.

## Updating and saved settings

Export a JSON configuration backup from the controller's Wi-Fi editor before an update. Leave **Erase device** unchecked to preserve mappings, calibration and settings in a compatible SIGMIDI Foot Controller installation. Choose erase only when intentionally resetting the controller or replacing firmware with an incompatible partition layout. The installer requires confirmation before writing; opening the page does not flash a device.

The bootloader and partition table are merged by esptool into a boot image at `0x0`, ending at `0x8c00` (its erase sectors end at `0x9000`). The application is written at `0x20000`. Neither image overlaps NVS at `0x9000–0x18fff` or PHY data at `0x19000–0x19fff`. Full-device erase explicitly removes these regions. The firmware can also erase unusable NVS during its existing startup recovery, so preserving the region does not replace a backup.

The downloadable application `.bin` alone is for an existing compatible bootloader/partition layout at `0x20000`; it is not a complete first-install image. Use the browser installer for first installation.

## Build and release checks

Preserved release binaries and `build-info.json` are in `distribution/firmware/`; a fresh build also records binary SHA-256 hashes, a fingerprint of all compiled firmware/editor inputs and build time in `build/build-info.json`. The packager rejects stale sources, corrupted images, another chip, unsupported partition tables and flash settings other than this firmware's DIO / 40 MHz / 4 MB. The browser independently checks the manifest hash, both image hashes and lengths, ESP32-C6 headers and erase-sector boundaries before enabling installation. It gives ESP Web Tools in-memory URLs for the exact verified bytes. SHA-256 here detects accidental corruption, not publisher identity.

Packaging uses a current `build/` when present, otherwise the preserved `distribution/firmware/` binaries. It publishes releases to `distribution/`. To refresh the site after editing only its HTML/CSS/JavaScript, without rebuilding unchanged firmware:

```sh
python3 scripts/package_web_flasher.py
```

Use the same `PIO` / `PLATFORMIO_CORE_DIR` environment as the build if esptool is not on PATH. After changing firmware or the embedded Wi-Fi editor, run the full build instead. The project and firmware version is **0.1**, read from `SIGMIDI_VERSION` in `src/branding.hpp` by the firmware, CMake, build scripts and renderers. The ESP-IDF application descriptor also reports 0.1. A separate source fingerprint and `build_id` identify the exact compiled revision. Configuration schema version 4 is unchanged.

The browser assets are pinned to **ESP Web Tools 10.4.0**. Their verified package provenance and file hashes are in `flasher/vendor/esp-web-tools/provenance.json`. Refresh only through `python3 scripts/vendor_web_flasher.py`; it checks the pinned npm SHA-512 archive before extracting the browser distribution. No browser dependency download occurs during firmware builds or local use.

## Verification

```sh
python3 tests/flasher_test.py
node tests/flasher_test.mjs
```

The JavaScript test uses the actual generated firmware package, including corruption/missing-file, wrong-chip, unsafe-offset, settings-preservation and browser-capability cases. Build the package first. These tests are also included in `scripts/test.sh` when the corresponding runtime/artifacts are available. Page rendering and readiness were checked in a browser; physical USB writing and board restart still need a connected controller.

## Static hosting

Publish the contents of `distribution/web-flasher/` to an HTTPS static host. Relative URLs support a subdirectory. Preserve the `firmware/` and `vendor/` trees and MIME types. Avoid caching the manifest/release files during updates and do not return `index.html` for missing assets. Deploy the directory as a unit. The same-origin default is simplest; a restrictive host Permissions Policy must allow `serial=(self)`.

References: [ESP Web Tools documentation](https://esphome.github.io/esp-web-tools/) and [source](https://github.com/esphome/esp-web-tools), [esptool merge-bin documentation](https://docs.espressif.com/projects/esptool/en/latest/esp32c6/esptool/basic-commands.html#merge-binaries-for-flashing-merge-bin).
