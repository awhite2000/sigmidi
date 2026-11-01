# SIGMIDI Foot Controller v0.1 — Design

- [Illustrated assembly guide](../output/pdf/sigmidi-foot-controller-0.1-assembly-guide.pdf): print selection, mechanical fitting, wiring and first power-up. [Editable source](../docs/assembly-guide.md).
- [Complete native Fusion model](fusion/sigmidi-foot-controller-0.1.f3d): all Left/Right main and modular assemblies and part libraries.
- [Left enclosure](fusion/mirrored/README.md): preferred electronics-on-left assemblies and manufacturing packages.
- [Right enclosure](fusion/README.md): electronics-on-right assemblies.
- [Front panel](front-panel.md): dimensions, labels and display placement.
- [Right main printing](fusion/print/README.md) and [Right modular assembly](fusion/modular/README.md).
- [Printing tolerances](../docs/printing-tolerances.md), [ladder wiring](../docs/resistor-ladders.md) and [preview gallery](../previews/README.md).
- [Brand assets](branding/README.md).
- [KiCad electrical schematic](kicad/README.md): editable external-board wiring, physical connector pin order and connectivity exports.

CAD uses manufacturer PCB models for the Waveshare 24382 display, Arduino Nano ESP32 and Pololu S13V10F5, and the ACJS-MHDC drawing for the dual TRS socket. Datasheets are in `fusion/datasheets/`: the [Waveshare 24382 model](fusion/datasheets/waveshare-24382.stp), [drawing](fusion/datasheets/waveshare-24382-drawing.pdf), [schematic](fusion/datasheets/waveshare-24382-schematic.pdf) and its vendor ST7789V2 driver ([LCD_1in69.c](fusion/datasheets/LCD_1in69.c), [LCD_1in69.h](fusion/datasheets/LCD_1in69.h)), the [Pololu 4083 model](fusion/datasheets/pololu-4083.step) and [drawing](fusion/datasheets/pololu-4083-dimensions.pdf), and the [ACJS-MHDC drawing](fusion/datasheets/double-trs-ACJS-MHDC.pdf). Printed parts use the supplied PETG 0.6 mm nozzle profiles. Physical fit, loading and thermal operation require assembly tests.
