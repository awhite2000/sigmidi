# SIGMIDI Foot Controller v0.1 — USB firmware installer

Use desktop **Chrome or Edge**, a USB-C data cable and the **DFRobot DFR1075 FireBeetle 2 ESP32-C6, 4 MB flash**. This installer includes firmware and ESP Web Tools locally and works without internet. Web Serial requires HTTPS or localhost. iPad Safari can use the controller's Wi-Fi editor after installation; it cannot run this USB installer.

## Open the installer

From the complete project, run `python3 scripts/serve_flasher.py` and open **http://localhost:8766/**. For an extracted installer ZIP, run this command inside its directory:

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

For static hosting, publish the whole directory over HTTPS, including `firmware/` and `vendor/`. Serve `.js` as JavaScript and `.bin` as binary. Relative paths support subdirectory hosting; missing assets must return an error, not the HTML index.

## Install

1. Export a configuration backup from an operational controller.
2. Connect USB-C and close applications using its serial port.
3. Choose **Connect & install**, select the controller and confirm.
4. Leave **Erase device** unchecked to keep compatible settings. Select erase for an intentional reset; it removes mappings, calibration and settings.
5. Wait for completion and restart. Hold BOOT and tap RESET if automatic download mode fails.

The page validates firmware hashes and compatibility before enabling installation. Opening the page does not write to a device.

## Configure

The BLE name is **SIGMIDI Foot Controller v0.1**. On the controller, open **Wi-Fi Setup**, join the displayed network, open **http://192.168.4.1/** and use the displayed password. Configure the ladder count, calibrate inputs and assign MIDI actions.

Choose **Left · Screen on left** for 180° display rotation and A–E / 1–5 list order from left to right. **Right · Screen on right** uses 0° and reverses each row. Left is the default. MIDI actions, names, calibration and LED assignments belong to physical taps. Save the selected variant.

## Flash layout and integrity

The boot-region image contains the bootloader at `0x0` and partition table at `0x8000`, ending below `0x9000`. The application starts at `0x20000`. NVS at `0x9000–0x18fff` and PHY data at `0x19000–0x19fff` are outside the write images. Unchecked erase preserves these regions; firmware startup recovery can reset unusable NVS.

The installer checks manifest/image SHA-256 hashes, lengths, ESP32-C6 headers and safe flash ranges, then passes those verified bytes to ESP Web Tools. `SHA256.json` lists distributed-file hashes. They detect corruption and do not authenticate a publisher. The downloadable application alone needs a compatible bootloader/partition layout.

ESP Web Tools **10.4.0** is distributed locally under Apache-2.0. See `vendor/esp-web-tools/LICENSE`, `vendor/esp-web-tools/provenance.json` and `vendor/THIRD_PARTY_NOTICES.txt`. Physical USB writing and restart require testing with a controller.
