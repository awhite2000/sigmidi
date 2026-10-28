SIGMIDI Foot Controller v0.1

ESP32-C6 / DFRobot DFR1075. For first installation, use the web flasher.
Manual esptool write_flash offsets: bootloader.bin 0x0, partitions.bin 0x8000, firmware.bin 0x20000.
The versioned application alone requires an existing compatible bootloader and partition table.
Export controller settings before updating; avoid full erase to preserve compatible NVS settings.
