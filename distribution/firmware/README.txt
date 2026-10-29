SIGMIDI Foot Controller v0.1

Arduino Nano ESP32 / ESP32-S3. USB MIDI + BLE MIDI. Use the web flasher in ROM download mode.
Pedal interface: two controller resistors per input (5.1k ring reference, 10k GPIO bias to TIP).
TIP goes directly to ADC. Enabled resistor mode drives bias HIGH; pot/disabled mode is high impedance.
Use passive 0-10k pedals and recapture heel/toe after rewiring. No active pedal interface or 1.5x scaling.
Manual esptool write_flash offsets: bootloader.bin 0x0, partitions.bin 0x8000, firmware.bin 0x20000.
Download mode: jumper B1 to GND, tap RST, remove jumper, then select the new USB serial port.
Native MIDI replaces factory Arduino DFU firmware; double-reset DFU is not provided.
The versioned application alone requires an existing compatible bootloader and partition table.
Export controller settings before updating; avoid full erase to preserve compatible NVS settings.
