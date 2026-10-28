# SIGMIDI Foot Controller v0.1 distribution

- [Portable web flasher ZIP](sigmidi-foot-controller-0.1-web-flasher.zip): complete offline installer with boot and application images.
- [Firmware ZIP](sigmidi-foot-controller-0.1-firmware.zip): bootloader, partition table, application, source/build metadata and checksums.
- [Versioned application](sigmidi-foot-controller-0.1.bin): for an existing compatible installation, at offset `0x20000`.
- [Complete Fusion model](../design/fusion/sigmidi-foot-controller-0.1.f3d): native hierarchy for both Left/Right main and modular enclosures, with the 25 mm embossed icon.
- [CAD/print packages](../design/fusion/mirrored/README.md) and [Right alternatives](../design/fusion/README.md).

From the project root, run `python3 scripts/serve_flasher.py` and open http://localhost:8766/ in desktop Chrome or Edge. The server uses `distribution/web-flasher/`. No rebuild is required. For static hosting, publish that directory as a unit over HTTPS.

Build intermediates are disposable. `scripts/build.py` publishes firmware and web-flasher bundles here. `scripts/package_web_flasher.py` can reuse these release firmware files if `build/` has been removed; stale firmware sources still fail validation.

Run `python3 scripts/verify_distribution.py` to check release hashes, ZIP contents, firmware compatibility and the full native Fusion archive. `verification/` contains build/test records. Physical flashing and print testing remain unverified.
