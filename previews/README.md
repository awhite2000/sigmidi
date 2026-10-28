# SIGMIDI Foot Controller v0.1 — Previews

## Enclosure renderings

**Left is preferred**, with electronics on the left and extensions to the right. [Left main](sigmidi-left-main.png) · [Left modular](sigmidi-left-modular.png) · [Right main](sigmidi-right-main.png) · [Right modular](sigmidi-right-modular.png).

![SIGMIDI Left main enclosure](sigmidi-left-main.png)

### Left

[Main top](../design/fusion/mirrored/main/top.png) · [Assembly](../design/fusion/mirrored/main/assembled.png) · [Rear](../design/fusion/mirrored/main/rear.png) · [Exploded](../design/fusion/mirrored/main/exploded.png) · [Display underside](../design/fusion/mirrored/main/display-underside.png) · [Base mounts](../design/fusion/mirrored/main/base-mounts.png) · [25 mm embossed icon](../design/fusion/mirrored/main/embossed-icon.png).

[Modular top](../design/fusion/mirrored/modular/top.png) · [Modular assembly](../design/fusion/mirrored/modular/assembled.png) · [Modular exploded](../design/fusion/mirrored/modular/exploded.png) · [Assembly guide](../design/fusion/mirrored/README.md).

### Right

[Top](../design/fusion/panel-top.png) · [Rear](../design/fusion/rear.png) · [Internal layout](../design/fusion/internal.png) · [Base supports](../design/fusion/base-supports.png) · [Labels](../design/fusion/switch-labels.png) · [Modular assembly](../design/fusion/modular/modular-assembled.png) · [Print orientations/supports](../design/fusion/print/printing-orientations-supports.png).

[Converter clips](../design/fusion/clip-mount.png) · [Base vents](../design/fusion/ventilation-base.png) · [Rear vents](../design/fusion/ventilation-rear.png) · [Vent membrane section](../design/fusion/rear-vent-membrane-section.png) · [Joint clearance sections](../design/fusion/snug-fit-sections.png).

Renders come from native Fusion geometry; manifests record image hashes. Presentation sheets are generated with `scripts/brand_enclosure_previews.py`.

## Firmware LCD

![LCD menus](display-preview.png)

The production renderer and `tests/display_preview.cpp` menu harness generate the 280×240 native screens `01.png`–`18.png` and contact sheets. Run `python3 scripts/preview_display.py` with Pillow, a C++17 compiler and ESP-IDF cJSON sources.

[Performance overview](display-overview.png) · [PC/CC forms](menu-editor-preview.png) · [LED settings](led-menu-preview.png) · [Enclosure selector](enclosure-menu-preview.png).

[Left/Right switch and calibration menus](enclosure-menus-both-variants.png) · [Scrolled continuation](enclosure-menus-scrolled.png). Left is the left column; Right is the right column. Captures use ten-switch defaults and are upright for the matching enclosure.

## Wi-Fi editor

![Wi-Fi editor](wifi-editor.png)

[PC editor](wifi-pc-editor.png) · [CC editor](wifi-cc-editor.png) · [Settings](wifi-settings.png) · [Calibration](wifi-calibration.png).

[Both switch lists](wifi-switches-both-variants.png) · [Both calibration lists](wifi-calibration-both-variants.png). Left reads A–E / 1–5; Right reverses each row. Calibration fields display whole millivolts. Actions, calibration and LED assignments remain attached to physical taps.

Full pages: [Left switches](wifi-left-switches.png), [Right switches](wifi-right-switches.png), [Left calibration](wifi-left-calibration.png), [Right calibration](wifi-right-calibration.png). Screenshots use the production editor with simulated default configuration and example actions, without a hardware connection. `scripts/preview_wifi.py` serves the demo; `scripts/compose_wifi_variant_previews.py` assembles comparisons.

## Installer and branding

[Web flasher](web-flasher.png) shows the installer with verified firmware, a Left enclosure render and Supported hardware details. [Run instructions](../docs/web-flasher.md).

[Brand assets](../design/branding/README.md) share the supplied SIGMIDI outline across LCD, Wi-Fi editor, installer and presentation sheets. [Render metadata](sigmidi-enclosure-renders.json).
