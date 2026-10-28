import { loadRelease, browserCapability } from './release.js';

const status = document.querySelector('#status');
const installer = document.querySelector('#installer');
const connect = document.querySelector('#connect');
const retry = document.querySelector('#retry');
let checking = false;
let verifiedURLs = [];

async function prepare() {
  if (checking) return;
  checking = true;
  for (const url of verifiedURLs) URL.revokeObjectURL(url);
  verifiedURLs = [];
  installer.hidden = true;
  connect.disabled = true;
  retry.hidden = true;
  document.querySelector('#verified').hidden = true;
  document.querySelector('#firmware-download').hidden = true;
  status.dataset.kind = 'checking';
  status.textContent = 'Checking the firmware package and your browser…';
  try {
    const capability = browserCapability({ secure: window.isSecureContext, serial: 'serial' in navigator });
    if (!window.isSecureContext) {
      document.querySelector('#version').textContent = 'Secure connection required';
      status.dataset.kind = 'unsupported';
      status.textContent = capability.message;
      return;
    }
    const { release, manifest, images } = await loadRelease();
    document.querySelector('#version').textContent = release.version;
    document.querySelector('#verified').hidden = false;
    document.querySelector('#firmware-download').hidden = false;
    document.querySelector('#firmware-download').download = `sigmidi-foot-controller-${release.version}.bin`;
    if (!capability.ok) {
      status.dataset.kind = 'unsupported';
      status.textContent = capability.message;
      return;
    }
    await import('./vendor/esp-web-tools/install-button.js');
    await customElements.whenDefined('esp-web-install-button');
    // Install exactly the bytes that passed validation, even if the hosted release changes later.
    const parts = images.map(({ file, bytes }) => {
      const url = URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' }));
      verifiedURLs.push(url);
      return { offset: file.offset, path: url };
    });
    const frozen = { ...manifest, builds: [{ ...manifest.builds[0], parts }] };
    const url = URL.createObjectURL(new Blob([JSON.stringify(frozen)], { type: 'application/json' }));
    verifiedURLs.push(url);
    installer.manifest = url;
    connect.disabled = false;
    installer.hidden = false;
    status.dataset.kind = 'ready';
    status.textContent = capability.message;
  } catch (error) {
    document.querySelector('#version').textContent = 'Firmware unavailable';
    status.dataset.kind = 'error';
    status.textContent = error.message || 'Could not load the installer. Check the package and reload this page.';
    retry.hidden = false;
  } finally {
    checking = false;
  }
}
retry.addEventListener('click', prepare);
prepare();
