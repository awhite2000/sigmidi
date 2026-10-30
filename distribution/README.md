# SIGMIDI Foot Controller v0.1 distribution

- [Portable web flasher ZIP](sigmidi-foot-controller-0.1-web-flasher.zip): complete offline installer with boot and application images.
- [Firmware ZIP](sigmidi-foot-controller-0.1-firmware.zip): bootloader, partition table, application, source/build metadata and checksums.
- [Versioned application](sigmidi-foot-controller-0.1.bin): for an existing compatible installation, at offset `0x20000`.
- [Complete Fusion model](../design/fusion/sigmidi-foot-controller-0.1.f3d): native hierarchy for both Left/Right main and modular enclosures, with the 25 mm embossed icon.
- [CAD/print packages](../design/fusion/mirrored/README.md) and [Right alternatives](../design/fusion/README.md).

These bundles target **Arduino Nano ESP32 / ESP32-S3, 16 MB flash**, with USB MIDI and BLE MIDI fan-out. Enter ROM download mode before installation: jumper B1 to GND, tap RST, remove jumper, and select the new serial port. They replace factory Arduino firmware and do not include double-reset DFU. Use the [Nano pin map and mandatory USB VBUS divider](../docs/hardware.md).

From the project root, run `python3 scripts/serve_flasher.py` and open http://localhost:8766/ in desktop Chrome or Edge. The server uses `distribution/web-flasher/`. No rebuild is required. For static hosting, publish that directory as a unit over HTTPS.

Build intermediates are disposable. `scripts/build.py` publishes firmware and web-flasher bundles here. `scripts/package_web_flasher.py` can reuse these release firmware files if `build/` has been removed; stale firmware sources still fail validation.

These bundles use the [passive pedal wiring](../docs/hardware.md#two-selectable-pedal-inputs): two resistors per input (5.1 kΩ ring reference and 10 kΩ GPIO bias), TIP directly to ADC, and HIGH/high-impedance bias selection. Use unpowered 0–10 kΩ pedals and recapture endpoint calibration after rewiring.

Run `python3 scripts/verify_distribution.py` to check release hashes, ZIP contents, firmware compatibility and the full native Fusion archive. `verification/` contains build/test records. Physical flashing and print testing remain unverified.

PC messages support STATIC, INCR (`PC+`) and DECR (`PC-`), with an independent persistent counter per message. No values are sent at startup. The first invocation after reboot sends the stored value unchanged; later invocations step and wrap within 0–127. Changed counters are checkpointed to flash every five minutes. Configuration and JSON backups use schema 6. See [firmware behavior](../docs/firmware.md).

Per-switch Toggle mode alternates the Press and Release lists on successive presses, with white/off LED feedback and no physical-release action. It defaults to disabled; runtime toggle state starts OFF after reboot, setup or all-MIDI offline/online transitions.
