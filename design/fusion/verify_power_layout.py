"""Confirm cooling changes preserve all controls and unaffected print parts."""
from pathlib import Path
import json,zipfile,math,hashlib
P=Path(__file__).resolve().parent
current=json.loads((P/'current-layout.json').read_text())
display5=current['revision']=='display_m2x5'
snug=current['revision']=='snug_06_tolerances'
ribs=current['revision']=='refined_positioning_ribs'
full_audit=current['revision']=='enclosure_wall_reinforcement'
upper=current['revision']=='upper_corner_walls'
wide=current['revision']=='wide_pololu_clips'
corner=current['revision']=='base_corner_repair'
labels=current['revision']=='recessed_switch_labels'
extra=current['revision']=='extra_right_base_screws'
membranes=current['revision']=='rear_vent_membranes'
straight=current['revision']=='straight_rear_rib'
full_height=current['revision'] in ['full_height_rear_rib','straight_rear_rib','rear_vent_membranes']
reinforced=current['revision']=='reinforced_floor_grilles'
ribbed=current['revision']=='rear_column_rib'
raised=current['revision']=='raised_rear_grilles'
expanded=current['revision']=='expanded_cooling_grilles'
baseline='archive/pre-display-m2x5.zip' if display5 else 'archive/pre-snug-06-tolerances.zip' if snug else 'archive/pre-positioning-rib-refinement.zip' if ribs else 'archive/pre-enclosure-wall-reinforcement.zip' if full_audit else 'archive/pre-upper-corner-walls.zip' if upper else 'archive/pre-wide-pololu-clips.zip' if wide else 'archive/pre-base-corner-repair.zip' if corner else 'archive/pre-recessed-switch-labels.zip' if labels else 'archive/pre-extra-right-base-screws.zip' if extra else 'archive/pre-rear-vent-membranes.zip' if membranes else 'archive/pre-straight-rear-rib.zip' if straight else 'archive/pre-full-height-rear-rib.zip' if full_height else 'archive/pre-base-vent-reinforcement.zip' if reinforced else 'archive/pre-column-rib.zip' if ribbed else 'archive/pre-raised-rear-vents.zip' if (raised or ribbed) else ('archive/pre-expanded-vents.zip' if expanded else 'archive/pre-ventilated-clip.zip')
with zipfile.ZipFile(P/baseline) as z:
    previous=json.loads(z.read('design/fusion/current-layout.json'))
    def component_key(r):return 'PCB screws' if r['component'].startswith('PCB screws') else 'Base fasteners' if r['component'].startswith('Base fasteners') else r['component']
    prior={component_key(r):r for r in previous['main']}
    if extra or labels or corner or wide or upper or full_audit or ribs or snug or display5:assert set(prior)=={component_key(r) for r in current['main']}
    changed=[r['component'] for r in current['main'] if component_key(r) in prior and r!=prior[component_key(r)]]
    expected=('02 ','PCB screws') if display5 else ('01 ','02 ') if snug else ('02 ',) if ribs else ('01 ','02 ') if full_audit else ('01 ',) if upper else ('02 ',) if (corner or wide) else ('01 ',) if labels else ('01 ','02 ','Base fasteners') if extra else ('01 ',) if full_height else ('02 ',) if reinforced else ('01 ',) if (raised or ribbed) else (('01 ','02 ') if expanded else ('01 ','02 ','Pololu ','REF AUX DC'))
    assert all(n.startswith(expected) for n in changed),changed
    old=next(r for r in previous['main'] if r['component'].startswith('Pololu '))['bodies'][0]
    new=next(r for r in current['main'] if r['component'].startswith('Pololu '))['bodies'][0]
    for key in ['min_world_mm','max_world_mm']:
        assert all(abs(a-b)<1e-6 for a,b in zip(old[key][:2],new[key][:2]))
        assert abs(new[key][2]-old[key][2]-(0 if (raised or ribbed or expanded or reinforced or full_height or extra or labels or corner or wide or upper or full_audit or ribs or snug or display5) else 6))<1e-6
    assert abs(new['volume_mm3']-old['volume_mm3'])<1e-6
    unchanged=['print/shell-left.stl','print/base-left.stl','modular/pair-shell.stl','modular/pair-shell-at-cap.stl','modular/pair-base.stl','modular/left-cap.stl']
    if corner or wide:unchanged=['print/shell-left.stl','print/shell-right.stl','print/base-left.stl','modular/pair-base.stl','modular/pair-shell.stl','modular/pair-shell-at-cap.stl','modular/left-cap.stl','modular/pair-shell-D.stl','modular/pair-shell-at-cap-C.stl','modular/pair-shell-at-cap-E.stl','print/fit-coupon-left.stl','print/fit-coupon-right.stl']
    if upper:unchanged=['print/base-left.stl','print/base-right.stl','modular/pair-base.stl','modular/pair-shell.stl','modular/pair-shell-at-cap.stl','modular/pair-shell-D.stl','modular/pair-shell-at-cap-C.stl','modular/pair-shell-at-cap-E.stl','print/fit-coupon-left.stl','print/fit-coupon-right.stl']
    if full_audit:unchanged=['print/base-right.stl','modular/pair-base.stl','print/fit-coupon-left.stl','print/fit-coupon-right.stl']
    if ribs:unchanged=['print/shell-left.stl','print/shell-right.stl','modular/pair-shell.stl','modular/pair-shell-at-cap.stl','modular/left-cap.stl','modular/pair-shell-D.stl','modular/pair-shell-at-cap-C.stl','modular/pair-shell-at-cap-E.stl','print/fit-coupon-left.stl','print/fit-coupon-right.stl']
    if snug:unchanged=['print/shell-left.stl','modular/left-cap.stl']
    if display5:unchanged=['print/shell-left.stl','print/shell-right.stl','print/base-left.stl','modular/pair-base.stl','modular/pair-shell.stl','modular/pair-shell-at-cap.stl','modular/left-cap.stl','modular/pair-shell-D.stl','modular/pair-shell-at-cap-C.stl','modular/pair-shell-at-cap-E.stl','print/fit-coupon-left.stl','print/fit-coupon-right.stl']
    if labels:unchanged=['print/base-left.stl','print/base-right.stl','modular/pair-base.stl','modular/left-cap.stl','print/fit-coupon-left.stl','print/fit-coupon-right.stl']
    if reinforced:unchanged+=['print/shell-right.stl','modular/electronics-shell.stl']
    if raised or ribbed or full_height:unchanged+=['print/base-right.stl','modular/electronics-base.stl']
    if extra:
        before=next(r for r in previous['main'] if r['component'].startswith('Base fasteners'))
        after=next(r for r in current['main'] if r['component'].startswith('Base fasteners'))
        assert len(before['bodies'])==6 and len(after['bodies'])==8
        assert before['bodies']==after['bodies'][:6]
        for b,(x,y) in zip(after['bodies'][-2:],[(201,6),(201,86)]):
            assert abs((b['min_world_mm'][0]+b['max_world_mm'][0])/2-x)<1e-5
            assert abs((b['min_world_mm'][1]+b['max_world_mm'][1])/2+y)<1e-5
    if display5:
        oldhw=prior['PCB screws'];newhw=next(r for r in current['main'] if r['component'].startswith('PCB screws'))
        oldlcd=[b for b in oldhw['bodies'] if b['name'].startswith('LCD24382')]
        newlcd=[b for b in newhw['bodies'] if b['name'].startswith('LCD24382')]
        assert len(oldlcd)==len(newlcd)==4
        assert [b for b in oldhw['bodies'] if not b['name'].startswith('LCD24382')]==[b for b in newhw['bodies'] if not b['name'].startswith('LCD24382')]
        for a,b in zip(oldlcd,newlcd):
            for k in ['min_world_mm','max_world_mm']:
                assert all(abs(u-v)<1e-6 for u,v in zip(a[k][:2],b[k][:2]))
            assert abs(b['min_world_mm'][2]-a['min_world_mm'][2]-1)<1e-6
            assert abs(b['max_world_mm'][2]-a['max_world_mm'][2])<1e-6
            assert abs(b['max_world_mm'][2]-b['min_world_mm'][2]-5)<1e-6
    for n in unchanged:
        assert hashlib.sha256((P/n).read_bytes()).digest()==hashlib.sha256(z.read('design/fusion/'+n)).digest(),n
assert current['main_outline_mm']==[350,92,54]
report={'revision':current['revision'],'snapshot':baseline,'expected_changed_components':changed,'all_other_existing_component_geometry_and_transforms_identical':True,'converter_raise_mm_from_snapshot':0 if (raised or ribbed or expanded or reinforced or full_height or extra or labels or corner or wide or upper or full_audit or ribs or snug or display5) else 6,'converter_total_raise_mm':6,'converter_XY_and_exact_shape_unchanged':True,'outer_case_dimensions_unchanged':True,'unchanged_print_meshes':unchanged}
(P/'power-layout-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
