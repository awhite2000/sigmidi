# SIGMIDI Foot Controller v0.1 — Brand assets

The SIGMIDI mark uses the supplied outline at fixed proportions. All SVG palettes share the same path geometry.

| Asset | Use |
|---|---|
| `sigmidi-mark.svg` | Green mark for light backgrounds and installer favicon |
| `sigmidi-mark-light.svg` | Pale mark for dark backgrounds |
| `sigmidi-mark-original.svg` | Purple mark |
| Matching transparent PNGs | Render-sheet composition |
| `logotype-original.png` | Supplied image |
| `sigmidi-mark-cad-25mm.json` | Proportional 25 mm CAD outline |

The LCD uses the alpha bitmap in `src/logo.hpp`; the Wi-Fi editor and web flasher use SVG. Left enclosure shells carry a 25 mm-wide, 0.6 mm-raised mark between A and B.

Run `scripts/prepare_logotype.py` with Python/Pillow to generate interface assets, then rebuild firmware if embedded assets change. Trace checksums are in `logotype-provenance.json`.
