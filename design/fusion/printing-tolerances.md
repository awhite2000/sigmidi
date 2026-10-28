# SIGMIDI Foot Controller v0.1 — Printing tolerances

Use **Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers** and the supplied `mk3s-petg-06.ini` or 3MF settings. Nominal extrusion width is 0.67 mm.

| Interface | CAD clearance |
|---|---:|
| Upper hooked joint, normal to inclined mating faces | 0.20 mm |
| Base positioning rib to inner shell wall, per face | 0.20 mm |
| Glued outer split seams | 0.25 mm |
| Integral cap floor to removable base butt edge | 0.30 mm |

Positioning ribs are 1.8 mm thick, 3 mm high, with 0.5 mm lead-ins. Upper parts seat with a vertical downward motion. For Left, the right shell lowers onto the left; Right uses the opposite handedness. The end cap enters from its outer side while raised 2 mm, then seats downward by 2 mm. Keep its fixed-floor/removable-base seam free of glue.

Print the two fit coupons with the intended orientation, material and profile. Remove brims/supports and let them cool. The joint should seat fully with a snug hand fit; glue secures it. If binding is confined to the bed edge, check the first layer and 0.2 mm elephant-foot compensation. If binding extends through the joint, check extrusion calibration and measured dimensions. Keep global XY compensation at zero.

Nozzle size, flow, PETG shrinkage and orientation affect physical fit. CAD checks and slicer toolpaths are available; printed fit and adhesive strength require validation. [Section views](snug-fit-sections.png).
