import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { loadRelease, validateMetadata, browserCapability, sha256 } from '../flasher/release.js';

const site = new URL('../distribution/web-flasher/', import.meta.url);
const manifestBytes = await readFile(new URL('manifest.json', site));
const manifest = JSON.parse(manifestBytes);
const release = JSON.parse(await readFile(new URL('release.json', site)));
const good = new Map([['release.json', Buffer.from(JSON.stringify(release))], ['manifest.json', manifestBytes]]);
for (const file of release.files) good.set(file.path, await readFile(new URL(file.path, site)));
let checks = 0;
const fetcher = files => async url => {
  const name = new URL(url).pathname.slice(1);
  return files.has(name) ? new Response(files.get(name)) : new Response('missing', { status: 404 });
};
const loaded = await loadRelease(fetcher(good), webcrypto);
assert.equal(loaded.release.version, release.version);
assert.equal(loaded.images.length, 2);
assert.equal(loaded.images[1].bytes.byteLength, release.files[1].bytes); checks++;
for (const change of [
  r => { r.chip = 'ESP32'; },
  r => { r.files[0].bytes = 0x9001; }, // rounded erase sector would hit NVS
  r => { r.files[1].bytes = 0x3E0001; },
  r => { r.files[1].offset = 0x10000; },
  r => { r.files[0].path = 'https://untrusted.example/boot.bin'; },
]) {
  const altered = structuredClone(release); change(altered);
  assert.throws(() => validateMetadata(altered, manifest)); checks++;
}
for (const change of [
  m => { m.builds[0].chipFamily = 'ESP32'; },
  m => { m.new_install_prompt_erase = false; },
  m => { m.builds[0].parts[1].offset = 0x10000; },
  m => { m.builds[0].improv = true; },
]) {
  const altered = structuredClone(manifest); change(altered);
  assert.throws(() => validateMetadata(release, altered)); checks++;
}
// Relative manifest/image URLs work when hosted beneath a project subdirectory.
{
  globalThis.location = { href: 'http://localhost/projects/midi/install/' };
  const nestedFetch = async (url, options) => {
    const requested = new URL(url);
    assert.ok(requested.pathname.startsWith('/projects/midi/install/'));
    return fetcher(good)(new URL(requested.pathname.replace('/projects/midi/install/', '/'), requested), options);
  };
  await loadRelease(nestedFetch, webcrypto);
  delete globalThis.location;
  checks++;
}
// Fail closed on missing, truncated or corrupt images; no installer API is invoked here.
for (const kind of ['missing', 'truncated', 'corrupt']) {
  const files = new Map(good), key = release.files[1].path;
  if (kind === 'missing') files.delete(key);
  if (kind === 'truncated') files.set(key, files.get(key).subarray(0, 200));
  if (kind === 'corrupt') { const data = Buffer.from(files.get(key)); data[100] ^= 0xFF; files.set(key, data); }
  await assert.rejects(loadRelease(fetcher(files), webcrypto)); checks++;
}
{
  const files = new Map(good); files.set('manifest.json', Buffer.from('{"bad":true}'));
  await assert.rejects(loadRelease(fetcher(files), webcrypto), /Manifest integrity/); checks++;
}
// Even self-consistent hashes cannot relabel another chip, including the old C6 release.
for (const chip of [5, 13]) {
  const files = new Map(good), altered = structuredClone(release), key = release.files[1].path;
  const data = Buffer.from(files.get(key)); data[12] = chip;
  files.set(key, data); altered.files[1].sha256 = await sha256(data, webcrypto);
  files.set('release.json', Buffer.from(JSON.stringify(altered)));
  await assert.rejects(loadRelease(fetcher(files), webcrypto), /ESP32-S3/); checks++;
}
assert.equal(browserCapability({ secure: true, serial: true }).ok, true); checks++;
assert.equal(browserCapability({ secure: true, serial: false }).ok, false); checks++;
assert.equal(browserCapability({ secure: false, serial: true }).ok, false); checks++;
console.log(`Web flasher: ${checks} integrity, flash-layout and compatibility checks passed.`);
