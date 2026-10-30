# SIGMIDI Foot Controller v0.1 — Enclosures

The [complete Fusion archive](sigmidi-foot-controller-0.1.f3d) contains native component hierarchies for Left and Right main/modular assemblies and part libraries. [Export metadata](sigmidi-foot-controller-0.1-model.json) records its hash and component inventory. **Left is preferred**; its [assembly guide](mirrored/README.md) lists the electronics-on-left files.

| Variant | Electronics | Extension direction | Ten-switch rows, left to right | Files |
|---|---|---|---|---|
| Left | Left | Right | A B C D E / 1 2 3 4 5 | `mirrored/main/`, `mirrored/modular/` |
| Right | Right | Left | E D C B A / 5 4 3 2 1 | Main CAD here; `print/`, `modular/` |

## Shell and base

Main body size is **350 × 92 × 54 mm**, excluding controls. Switches have 65 mm horizontal pitch, 32.5 mm stagger and 53 mm row spacing. The raised rear deck is 30 mm above the front deck, joined by an 80° transition. Side walls are at least 2 mm and roofs 3 mm. Visible upper side edges have 4 × 3 mm chamfers; other upper edge blends use 4 mm fillets.

The 2 mm base follows the enclosure outline and carries the shell walls on its perimeter. The vent zone has a 3 mm floor, with a 3 mm border around the slot pattern. Positioning ribs are 1.8 mm thick, 3 mm high, with 0.5 mm lead-ins and 0.20 mm shell clearance. Blind screw pilots have 2 mm roof caps. Main and eight-switch modular assemblies each use eight M2×6 countersunk base screws; a two-switch section uses two, and the electronics base four.

Upper parts meet at continuous hooked joints with 2 × 2 mm bevels, 0.20 mm inclined-face clearance and 0.25 mm exterior seams. Lower the outer shell vertically onto its electronics-side neighbor. Base segments meet at straight butt seams with 2 mm-high internal glue lands and 45° inward runouts. Assemble and glue upper and base chains separately.

## Controls and mounts

The Waveshare 24382 glass is flush with the lower deck. Four hollow towers have 2 mm walls and recessed head seats for **M2×5 countersunk screws**. Nominal factory-stud engagement is 1.39 mm; check the actual blind holes. The encoder body is 15 × 15 mm with a 15 mm-diameter, 5 mm-high knob. Arduino Nano ESP32 is mounted component-side down using the [two-insert mounting kit](nano-esp32/README.md), with USB-C facing the rear protective pocket. The existing shell and posts are retained.

Switch labels are Arial Bold, 8 mm high, recessed 0.8 mm, leaving 2.2 mm roof backing. Left labels sit to the left of each LED; Right labels sit to its right. Left electronics shells carry a 25 × 20.183 mm icon raised 0.6 mm between A and B, giving 54.6 mm local body height.

Each optional Pololu 2535 LED has a 5.4 mm bore, 6.4 × 0.8 mm flange recess and 0.8 mm exterior cover. Nominal dome exposure is 0.8 mm, maximum 1 mm. Seats have 45° support tapers and teardrop ceilings. Verify LED package dimensions against the purchased parts. See [LED wiring and assembly](leds.md).

## Power and cooling

The rear input is **9 V DC, center-negative, 5.5 × 2.1 mm**. The socket has an 8 mm thread, 8 mm threaded length, 4 mm flange/body, 6 mm terminals and 2 mm nut; its panel bore is 8.4 mm. The Pololu S13V10F5 #4083 supplies regulated 5 V to the optional LEDs. The same 9 V input feeds Nano VIN directly; all returns share GND. Converter 5 V and USB VBUS stay separate.

The converter rests on three bare-edge seats held by two PETG clips: 4.8 mm wide, 1.6 mm bending thickness, with 0.8 mm root gussets at 45°. It has 8.65 mm clearance below its lowest component. Spread the leaves about 0.6 mm for insertion/removal and keep wires clear of the springs.

The base has six 2.4 mm-wide slots around the converter and seven below the controller mounting area. The rear has three columns of four 2.4 mm-high slots, with a 7.6 mm solid upper rim. A full-height internal rib between two columns has a 2 mm crest, 45° side chamfers and nominal base contact. It merges with the USB-pocket chamfer. All twelve rear slots have **0.6 mm internal print membranes**; remove them before use. Finished rear open area is 380.16 mm². Provide at least 3 mm free space below the base vents. See [power and thermal assembly](power.md).

## Manufacturing files

- [Right main CAD](midi-foot-chassis.f3d) and [STEP](midi-foot-chassis.step).
- [Right main print package](print/mk3s-petg-06-print-package.zip) and [printing guide](print/README.md).
- [Right modular package](modular/chainable-enclosure-mk3s-petg-06.zip) and [parts guide](modular/README.md).
- [Left main/modular packages](mirrored/README.md).
- [Fit coupons and tolerances](printing-tolerances.md).

Use the supplied Prusa MK3S+ PETG profiles with a 0.6 mm nozzle and 0.3 mm layers. Print oriented STLs/3MFs directly. Bases print outside-floor down without supports; upper shells print on their outer ends with automatic snug supports at 40°. Print coupons before full parts. Keep the USB connector withdrawal path clear when removing a populated base.

Nominal BRep fit, mesh topology, wall samples and slicer checks accompany the files. They do not establish physical fit, adhesive/load strength, spring life or thermal performance.
