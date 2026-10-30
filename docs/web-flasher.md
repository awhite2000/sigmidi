# SIGMIDI Foot Controller v0.1 — Web flasher

The complete installer is in `distribution/web-flasher/`, with a portable `distribution/sigmidi-foot-controller-0.1-web-flasher.zip`. It contains verified firmware, a manifest and pinned local ESP Web Tools assets. Source browser files are in `flasher/`.

## Run and install

```sh
python3 scripts/serve_flasher.py
```

Open **http://localhost:8766/** in desktop Chrome or Edge and connect the Nano ESP32 over USB-C. Choose **Connect & install**, select its serial port and confirm. Before flashing, jumper B1 to GND, tap RST, then remove the jumper and select the new USB serial port. The running firmware is a MIDI-only USB device, so repeat this ROM download procedure for every update. This installer replaces factory Arduino firmware and does not provide double-reset DFU; [Arduino restoration instructions](https://support.arduino.cc/hc/en-us/articles/9810414060188-Reset-the-Arduino-bootloader-on-the-Nano-ESP32) remain available. The server binds to `127.0.0.1`, verifies hashes at startup and serves only the installer directory. `--port 8767` selects another port; `--directory PATH` selects an extracted package.

An extracted ZIP can be served with `python3 -m http.server 8766 --bind 127.0.0.1` from its directory. USB access requires a supported desktop browser and HTTPS or localhost. iPad Safari is suitable for the controller's Wi-Fi editor after installation.

Export settings before updating. Leave **Erase device** unchecked to preserve compatible mappings/calibration; intentional erase clears the device. The boot region is written at `0x0` through the partition table, ending before NVS at `0x9000`; the app starts at `0x20000`. NVS `0x9000–0x18fff` and PHY `0x19000–0x19fff` are outside those images. Firmware recovery may clear unusable NVS.

## Build and package

```sh
python3 scripts/build.py
```

Set `PIO` and `PLATFORMIO_CORE_DIR` as described in [bring-up](bringup.md) if needed. The helper publishes release binaries, firmware ZIP and installer ZIP to `distribution/`; compiler/debug files go to disposable `build/`. Version 0.1 comes from `SIGMIDI_VERSION` in `src/branding.hpp`; configuration schema is 6.

To refresh installer HTML/CSS/JavaScript or its guide without recompiling firmware:

```sh
python3 scripts/package_web_flasher.py
```

The packager uses a current `build/` if present, otherwise `distribution/firmware/`. It verifies the compiled source fingerprint, image hashes, ESP32-S3 headers, partition layout and DIO / 40 MHz / 16 MB settings. Firmware or embedded-editor changes require a full build.

ESP Web Tools is pinned to **10.4.0**, with provenance in `flasher/vendor/esp-web-tools/provenance.json`. `scripts/vendor_web_flasher.py` verifies the pinned npm archive when generating browser dependencies. Normal installation requires no CDN.

## Validation and hosting

```sh
python3 tests/flasher_test.py
node tests/flasher_test.mjs
python3 scripts/verify_distribution.py
```

Tests cover corrupted/missing firmware, wrong chips, unsafe offsets, settings preservation and browser capability. The browser also checks hashes and safe image ranges before passing exact verified bytes to ESP Web Tools. Hashes detect accidental corruption, not publisher identity. Physical USB writing/restart require hardware validation.

Publish the entire `distribution/web-flasher/` directory to an HTTPS static host. Preserve paths and MIME types, avoid caching release/manifest files during updates, and return errors for missing assets. Relative URLs support subdirectories. A restrictive Permissions Policy must allow `serial=(self)`.

The app partition is 0x3E0000 bytes at 0x20000; the remaining flash is unused. Nano PSRAM is not required or enabled. The installer replaces the partition table: export saved settings before installation. Settings preservation applies to compatible SIGMIDI installations, not arbitrary Nano factory firmware.
