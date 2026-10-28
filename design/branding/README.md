# SIGMIDI Foot Controller v0.1 — Logotype

The supplied mark is retained in `logotype-original.png`. The SVG assets trace its main ink boundary without redrawing, rotating, skewing or changing proportions. The optional pale drop shadow is removed; the original purple, project green and pale variants share identical path geometry.

- `sigmidi-mark.svg`: project green for light backgrounds and the installer favicon.
- `sigmidi-mark-light.svg`: pale variant for the Wi-Fi editor and dark render-sheet headers.
- `sigmidi-mark-original.svg`: the supplied purple ink color.
- Matching transparent PNGs support native render-sheet composition. `src/logo.hpp` is the small alpha bitmap used by the production LCD renderer.

Regenerate with `scripts/prepare_logotype.py` using Python and Pillow. The script also updates the embedded editor SVG and flasher icon; rerun the firmware build after regenerating. Trace provenance and source checksums are in `logotype-provenance.json`. Native enclosure geometry is unchanged.
