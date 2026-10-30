SIGMIDI Foot Controller v0.1

Arduino Nano ESP32 / ESP32-S3. USB MIDI + BLE MIDI. Use the web flasher in ROM download mode.
Pedal interface: two controller resistors per input (5.1k ring reference, 10k GPIO bias to TIP).
TIP goes directly to ADC. Enabled resistor mode drives bias HIGH; pot/disabled mode is high impedance.
Use passive 0-10k pedals and capture heel/toe after wiring; calibration stores raw ADC millivolts.
Manual esptool write_flash offsets: bootloader.bin 0x0, partitions.bin 0x8000, firmware.bin 0x20000.
Download mode: jumper B1 to GND, tap RST, remove jumper, then select the new USB serial port.
The running application exposes native USB MIDI. Installation and updates use ROM download mode.
The versioned application alone requires an existing compatible bootloader and partition table.
Export controller settings before updating; avoid full erase to preserve compatible NVS settings.
