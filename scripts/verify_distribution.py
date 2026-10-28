#!/usr/bin/env python3
"""Verify preserved releases and the complete latest native Fusion model."""
from pathlib import Path
import hashlib,json,zipfile
from package_web_flasher import read_build

root=Path(__file__).resolve().parents[1];dist=root/'distribution'
def sha(data):return hashlib.sha256(data).hexdigest()
def check_zip(path,folder):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None,path
  for name in z.namelist():
   assert z.read(name)==(folder/name).read_bytes(),name
  return len(z.namelist())
info,images=read_build(root)
assert sha((dist/f"sigmidi-foot-controller-{info['version']}.bin").read_bytes())==info['sha256']['firmware.bin']
firmware_count=check_zip(dist/f"sigmidi-foot-controller-{info['version']}-firmware.zip",dist/'firmware')
flasher_count=check_zip(dist/f"sigmidi-foot-controller-{info['version']}-web-flasher.zip",dist/'web-flasher')
for directory in [dist,dist/'firmware',dist/'web-flasher']:
 for name,digest in json.loads((directory/'SHA256.json').read_text()).items():
  path=(directory/name).resolve();assert path.is_relative_to(directory.resolve())
  assert sha(path.read_bytes())==digest,name
model=json.loads((root/'design/fusion/sigmidi-foot-controller-0.1-model.json').read_text())
archive=root/'design/fusion'/model['path'];assert sha(archive.read_bytes())==model['sha256']
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
assert model['embossed_icon']['main_and_modular_updated']
assert all(any(token in n for n in model['top_level_components']) for token in ['ALT Chainable','ALT Mirrored MAIN','ALT Mirrored MODULAR'])
print(json.dumps({'version':info['version'],'firmware_ZIP_files':firmware_count,'flasher_ZIP_files':flasher_count,'release_hashes_verified':True,'source_fingerprint_current':True,'latest_complete_Fusion_archive_verified':True,'native_document':model['native_document']},indent=2))
