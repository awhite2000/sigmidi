#!/usr/bin/env python3
"""Compare a KiCad XML netlist export with the electrical diagram's pin map."""

import argparse
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def verify_physical_order(source_path, pin_locations_path):
    """Check Konnect's queried coordinates, independently of requested placement."""
    source = json.loads(source_path.read_text())
    queried = json.loads(pin_locations_path.read_text())
    components = {c['reference']: c for c in queried['components']}
    board = {p['number']: p for p in components['U1']['pins']}
    assert set(board) == set(source['components']['U1']['pins'])
    headers = {}
    for header, count in [('P2', 18), ('P1', 14)]:
        pins = [board[f'{header}:{i}'] for i in range(1, count + 1)]
        assert len({round(p['x'], 6) for p in pins}) == 1, header
        pitch = pins[1]['y'] - pins[0]['y']
        assert pitch > 0, header
        assert all(math.isclose(pins[i]['y'] - pins[i - 1]['y'], pitch,
                                abs_tol=1e-6) for i in range(1, count)), header
        headers[header] = (pins, pitch)
    left, pitch = headers['P2']
    right, right_pitch = headers['P1']
    assert left[0]['x'] < right[0]['x']
    assert math.isclose(pitch, right_pitch, abs_tol=1e-6)
    assert math.isclose(right[0]['y'] - left[0]['y'], 4 * pitch, abs_tol=1e-6)
    for number, data in source['dfrobot_external_pins'].items():
        assert board[number]['name'].startswith(data['physical_label']), (number, data)

    lcd = {p['number']: p for p in components['U2']['pins']}
    expected_names = ['BL', 'RST', 'D/C', 'CS', 'SCL/CLK', 'SDA/DIN', 'GND', 'VCC']
    assert set(lcd) == {f'P2:{i}' for i in range(1, 9)}
    pins = [lcd[f'P2:{i}'] for i in range(1, 9)]
    assert [p['name'].replace(' ', '') for p in pins] == expected_names
    assert len({round(p['x'], 6) for p in pins}) == 1
    assert all(pins[i]['y'] > pins[i - 1]['y'] for i in range(1, 8))
    return {'dfrobot_physical_order': True, 'dfrobot_P1_offset_pitches': 4,
            'display_physical_order': True}


def verify(source_path, exported_path):
    source = json.loads(source_path.read_text())
    exported = ET.parse(exported_path).getroot()
    expected_components = source['components']
    components = {c.attrib['ref'] for c in exported.findall('./components/comp')
                  if not c.attrib['ref'].startswith('#')}
    assert components == set(expected_components), {
        'missing_components': sorted(set(expected_components) - components),
        'unexpected_components': sorted(components - set(expected_components)),
    }

    expected = {name: {tuple(terminal.split('.', 1)) for terminal in terminals}
                for name, terminals in source['nets'].items()}
    actual = {}
    seen = set()
    unused = {(ref, pin) for ref, component in expected_components.items()
              for pin, net in component['pins'].items() if net is None}
    for net in exported.findall('./nets/net'):
        pins = {(node.attrib['ref'], node.attrib['pin'])
                for node in net.findall('node') if node.attrib['ref'] in components}
        assert not seen.intersection(pins), ('Pins in multiple nets', seen.intersection(pins))
        seen.update(pins)
        if not pins:
            continue
        if pins <= unused and len(pins) == 1:
            continue  # KiCad may include an isolated NC pin as a one-node net.
        assert not pins.intersection(unused), ('Unexpected NC connection', net.attrib, pins)
        name = net.attrib['name'].removeprefix('/')
        assert name not in actual, ('Duplicate net name', name)
        actual[name] = pins

    assert set(actual) == set(expected), {
        'missing_nets': sorted(set(expected) - set(actual)),
        'unexpected_nets': sorted(set(actual) - set(expected)),
    }
    for name, pins in expected.items():
        assert actual[name] == pins, {
            'net': name,
            'missing_pins': sorted(pins - actual[name]),
            'unexpected_pins': sorted(actual[name] - pins),
        }
    return {
        'components': len(components),
        'nets': len(actual),
        'connected_terminals': sum(map(len, actual.values())),
        'unused_terminals': len(unused),
        'connectivity_matches_source': True,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', nargs='?', type=Path,
                        default=ROOT / 'design/kicad/sigmidi-foot-controller.net')
    parser.add_argument('--source', type=Path,
                        default=ROOT / 'design/electrical/netlist.json')
    parser.add_argument('--pins', type=Path,
                        default=ROOT / 'design/kicad/verification/pin-locations.json')
    args = parser.parse_args()
    result = verify(args.source, args.export)
    result.update(verify_physical_order(args.source, args.pins))
    print(json.dumps(result, indent=2))
