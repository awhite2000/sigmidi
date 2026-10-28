SIGMIDI Foot Controller v0.1

ESP32-C6 / DFRobot DFR1075. For first installation, use the web flasher.
Pedal interface: two controller resistors per input (5.1k ring reference, 10k GPIO bias to TIP).
TIP goes directly to ADC. Enabled resistor mode drives bias HIGH; pot/disabled mode is high impedance.
Use passive 0-10k pedals and recapture heel/toe after rewiring. No active pedal interface or 1.5x scaling.
Manual esptool write_flash offsets: bootloader.bin 0x0, partitions.bin 0x8000, firmware.bin 0x20000.
The versioned application alone requires an existing compatible bootloader and partition table.
Export controller settings before updating; avoid full erase to preserve compatible NVS settings.
