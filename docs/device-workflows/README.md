# On-device editing screen paths

These figures use the production menu code and display renderer with a Left enclosure and switch A example.

- [Performance to a Program value](switch-message-workflow.png): nine numbered screens, with the encoder action beneath each screen.
- [Other menus](other-menus-workflow.png): routes to pedal inputs, ladder centers, LED settings and a controller parameter.
- [Save and return to Performance](save-workflow.png).

The individual 280 x 240 PNGs and `manifest.json` retain each screen's selected row, breadcrumb, edit state and source hashes. Regenerate with `python3 scripts/build_device_workflows.py`, using Pillow, a C++17 compiler and the ESP-IDF cJSON sources. The capture harness asserts each navigation target before exporting its frame. This is a host-rendered guide, not a hardware capture.
