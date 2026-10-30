# SIGMIDI v0.1 - Arduino Nano ESP32 direct base mounting

The Arduino Nano ESP32 ABX00083 mounts **component-side up** directly on four reinforced posts integral to the electronics base. The USB-C connector faces the rear protective pocket. There are no separate mounting inserts, glued mounting feet or bridge fasteners. This applies to Left and Right, Main and Modular assemblies.

![Nano directly mounted on the base, components facing up](installed.png)

## Printed parts and hardware

Print the electronics base from the selected enclosure family:

| Assembly | Electronics base |
|---|---|
| Left Main | `../mirrored/main/base-left.stl` / `.3mf` |
| Left Modular | `../mirrored/modular/electronics-base-left.stl` / `.3mf` |
| Right Main | `../print/base-right.stl` / `.3mf` |
| Right Modular | `../modular/electronics-base.stl` / `.3mf` |

Use **four M1.6 x 5 mm pan-head screws** through the Nano's approximately 1.61 mm PCB into the integral posts. Board mounting holes are 1.66 mm diameter on a 40.64 x 15.24 mm rectangle. Printed pilots are 1.55 mm diameter, 4.3 mm deep; nominal screw engagement is 3.39 mm. Check the actual printed pilots and screw heads; tighten gently without bending the PCB. No headers are included in the clearance model: solder the peripheral harness directly to the pads and leave service slack.

The posts have 6 mm shafts with 8 mm root envelopes and 45-degree root transitions. USB-side posts have a flat rear face to clear the unchanged pocket partition. The opposite posts have 45-degree arch channels over the existing floor slot, preserving all thirteen floor vents. The posts are one solid with the base, rather than cantilevered adapter arms. The base prints outside-floor down, posts up, with the supplied 0.6 mm PETG profile.

The PCB bottom is approximately Z -13.336 mm and the component face Z -11.730 mm in assembly-local coordinates; the outside floor is Z -24 mm. The USB connector retains its X/Z alignment and sits 1.5 mm farther inward, giving full 6 mm shafts on the USB-side posts. The pocket and cutout are unchanged; check the actual cable plug reaches and seats fully in the recess. Other controls, mounting supports, split joints, base perimeter and upper-shell geometry are unchanged. The 6 mm shafts provide 2.225 mm radial material around the pilot bore, with at least 2.06 mm blind material above the vent channel. Dimensions and checks are recorded in [mount-fit.json](mount-fit.json) and [assembly-clearance.json](assembly-clearance.json).

![Board and four mounting screws above the integral posts](exploded.png)

## Assembly

1. Clean the printed electronics base and pilot entrances. Remove loose strands and check the four mounting positions against the actual board. Leave the floor vents and chamfered post channels clear.
2. Identify the Nano pads in component-side view, USB-C up. Solder and insulate the direct harness while access is easy. Keep B1, GND and RST accessible for ROM flashing.
3. Place the Nano **components up**, USB-C toward the rear. All four PCB holes should align with the integral post pilots. The bare PCB underside rests on the posts; no component or wire should be trapped underneath.
4. Start all four M1.6x5 screws loosely, then seat them gently. Check the PCB stays flat and supported at every post. No glue is used for the board mounting.
5. Dry-fit the unchanged upper shell and the actual USB plug. Verify connector seating, cable access, component clearance and a usable service-removal path before closing. Do not force the base against a trapped connector.

Disconnect power before servicing. Release the four Nano screws and withdraw its USB-C connector clear of the protective pocket partition before lowering the populated base. Support the floor and use harness slack or labeled service connectors; never pull the socket or PCB against the pocket.

## CAD, prints and checks

- [Complete native Fusion model](../sigmidi-foot-controller-0.1.f3d): all four assemblies and modular libraries, fitted with components-up Nano references.
- [Direct mount detail F3D](nano-esp32-direct-mount.f3d) and [STEP](nano-esp32-direct-mount.step): a cropped mechanical reference including the fitted board and integral posts. Print the full base listed above, not this detail.
- [Mount fit](mount-fit.json), [installation](installation.json) and [assembly clearance](assembly-clearance.json): board pose, pilots, screw engagement, all four assembly checks and unchanged upper-shell verification.
- [Instance placement](instance-placement.json): each board follows its own assembly and aligns with its integral posts.
- [Print verification](print-verification.json): watertight full-base meshes and support-free 0.6 mm PETG slicing.
- `direct_mount.py`, `render_mounts.py`, `check_prints.py`, `package_current.py`: model update, exports/renders and print checks.

These are nominal CAD and slicing checks. Printed strength, screw retention, connector seating, vibration and thermal behavior require physical testing. The four posts are integral to the base; there are no extra Nano mounting pieces.

## Electrical and manufacturer references

Use the [Nano GPIO and VBUS-divider wiring](../../../docs/hardware.md), [power guide](../../../docs/power.md), [ROM flashing procedure](../../../docs/web-flasher.md) and [assembly guide](../../../docs/assembly-guide.md). Nano VIN takes the positive sleeve of the 9 V center-negative inlet; the Pololu 5 V output supplies only the optional LEDs. Do not tie its output to USB VBUS.

[Arduino Nano ESP32 documentation](https://docs.arduino.cc/hardware/nano-esp32/) - [Official datasheet](https://docs.arduino.cc/resources/datasheets/ABX00083-datasheet.pdf) - [Official STEP archive](https://docs.arduino.cc/resources/models/ABX00083-step.zip). Local copies are in `datasheets/`; holes follow the official drawing on page 17. Pin names and electrical assignments do not change with the board's mechanical orientation.
