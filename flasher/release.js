// Validate both metadata and bytes before enabling the USB installer.
export const APP_OFFSET = 0x20000;
export const FLASH_BYTES = 0x1000000;
const EXPECTED = [{ path: 'firmware/boot-region.bin', offset: 0 },
                  { path: 'firmware/application.bin', offset: APP_OFFSET }];
const isHash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);

export async function sha256(bytes, cryptoImpl = globalThis.crypto) {
  const digest = await cryptoImpl.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
}

export function validateMetadata(release, manifest) {
  if (release.schema !== 1 || release.chip !== 'ESP32-S3' || release.flash_bytes !== FLASH_BYTES ||
      typeof release.version !== 'string' || !release.version || !isHash(release.source_sha256) ||
      !Array.isArray(release.files) || release.files.length !== 2) {
    throw new Error('This is not a supported SIGMIDI Foot Controller firmware release.');
  }
  if (manifest.name !== 'SIGMIDI Foot Controller' || manifest.version !== release.version ||
      manifest.new_install_prompt_erase !== true || !Array.isArray(manifest.builds) || manifest.builds.length !== 1 ||
      manifest.builds[0].chipFamily !== 'ESP32-S3' || manifest.builds[0].improv !== false ||
      !Array.isArray(manifest.builds[0].parts) || manifest.builds[0].parts.length !== 2) {
    throw new Error('The installer manifest does not match this firmware release.');
  }
  for (let i = 0; i < EXPECTED.length; i++) {
    const file = release.files[i], part = manifest.builds[0].parts[i], expected = EXPECTED[i];
    if (!file || !part || file.path !== expected.path || part.path !== expected.path ||
        file.offset !== expected.offset || part.offset !== expected.offset ||
        !Number.isSafeInteger(file.bytes) || file.bytes < 24 || !isHash(file.sha256)) {
      throw new Error('Invalid firmware image or flash address.');
    }
    const endSector = Math.ceil((file.offset + file.bytes) / 4096) * 4096;
    if ((i === 0 && endSector > 0x9000) || (i === 1 && endSector > APP_OFFSET + 0x3e0000)) {
      throw new Error('Firmware would overwrite saved settings or exceed the flash size.');
    }
  }
}

export async function loadRelease(fetcher = globalThis.fetch, cryptoImpl = globalThis.crypto) {
  async function get(path) {
    const response = await fetcher(new URL(path, globalThis.location?.href || 'http://localhost/'), { cache: 'no-store', signal: AbortSignal.timeout(30000) });
    if (!response.ok) throw new Error(`Could not load ${path} (HTTP ${response.status}).`);
    return response;
  }
  const release = await (await get('./release.json')).json();
  const rawManifest = await (await get('./manifest.json')).arrayBuffer();
  if (!isHash(release.manifest_sha256) || await sha256(rawManifest, cryptoImpl) !== release.manifest_sha256) {
    throw new Error('Manifest integrity check failed. Rebuild or re-download the flasher package.');
  }
  const manifest = JSON.parse(new TextDecoder().decode(rawManifest));
  validateMetadata(release, manifest);
  const images = await Promise.all(release.files.map(async file => {
    const bytes = await (await get('./' + file.path)).arrayBuffer();
    if (bytes.byteLength !== file.bytes || await sha256(bytes, cryptoImpl) !== file.sha256) {
      throw new Error(`Firmware integrity check failed: ${file.path}. Rebuild or re-download the package.`);
    }
    const data = new Uint8Array(bytes);
    if (data[0] !== 0xE9 || data[12] !== 9 || data[13] !== 0 || data[2] !== 2 || data[3] !== 0x40) {
      throw new Error('The image is not the expected ESP32-S3 / 16 MB firmware.');
    }
    return { file, bytes };
  }));
  return { release, manifest, images };
}

export function browserCapability(context) {
  if (!context.secure) return { ok: false, message: 'USB installation needs HTTPS or localhost. Open this page from the local flasher server or an HTTPS host.' };
  if (!context.serial) return { ok: false, message: 'This browser cannot access USB serial devices. Open this page in desktop Chrome or Edge. The iPad can be used for MIDI and Wi-Fi setup after installation.' };
  return { ok: true, message: 'Firmware verified. Connect your controller to begin.' };
}
