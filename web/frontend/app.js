/* Forge3D frontend — talks to the FastAPI backend, renders GLB in Three.js */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const $ = (id) => document.getElementById(id);
const state = { tab: 'text', uploadId: null, jobs: [], currentJob: null, viewer: null };

/* ---------- tabs ---------- */
document.querySelectorAll('.tab').forEach((b) => {
  b.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((x) => x.classList.remove('active'));
    b.classList.add('active');
    state.tab = b.dataset.tab;
    for (const t of ['text', 'image', 'multi'])
      $('pane-' + t).classList.toggle('hidden', t !== state.tab);
  });
});

/* ---------- upload dropzone (phone-friendly: plain file input) ---------- */
const dz = $('dropzone'), fileInput = $('file');
dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', (e) => {
  e.preventDefault(); dz.classList.remove('over');
  if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; doUpload(); }
});
fileInput.addEventListener('change', doUpload);

async function doUpload() {
  const f = fileInput.files[0];
  if (!f) return;
  const prev = $('dz-preview');
  prev.src = URL.createObjectURL(f);
  prev.classList.remove('hidden');
  const fd = new FormData();
  fd.append('file', f);
  const r = await fetch('/api/upload', { method: 'POST', body: fd });
  const j = await r.json();
  state.uploadId = j.upload_id;
}

/* ---------- providers ---------- */
async function loadProviders() {
  const r = await fetch('/api/providers');
  const j = await r.json();
  const sel = $('provider');
  let okCount = 0;
  for (const p of j.providers) {
    const o = document.createElement('option');
    o.value = p.name;
    o.textContent = `${p.name} ${p.available ? '●' : '○'}`;
    if (!p.available) o.title = p.reason;
    sel.appendChild(o);
    if (p.available) okCount++;
  }
  $('provider-pill').textContent = `${okCount}/${j.providers.length} backends ready`;
}

/* ---------- three.js viewport ---------- */
function initViewer() {
  const el = $('viewport');
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(el.clientWidth, el.clientHeight);
  renderer.setClearColor(0xffffff, 1);
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, el.clientWidth / el.clientHeight, 0.1, 100);
  camera.position.set(2.2, 1.4, 2.6);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 0.9, 0);
  scene.add(new THREE.GridHelper(6, 24, 0x7C3AED, 0xDDD6FE));
  scene.add(new THREE.HemisphereLight(0xffffff, 0xDDD6FE, 1.1));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(3, 5, 4);
  scene.add(key);
  state.viewer = { renderer, scene, camera, controls, model: null };
  (function tick() {
    requestAnimationFrame(tick);
    controls.update();
    renderer.render(scene, camera);
  })();
  addEventListener('resize', () => {
    renderer.setSize(el.clientWidth, el.clientHeight);
    camera.aspect = el.clientWidth / el.clientHeight;
    camera.updateProjectionMatrix();
  });
}

function showModel(url) {
  const v = state.viewer;
  if (!v) return;
  if (v.model) { v.scene.remove(v.model); v.model = null; }
  new GLTFLoader().load(url, (gltf) => {
    const m = gltf.scene;
    const box = new THREE.Box3().setFromObject(m);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    m.position.sub(center).add(new THREE.Vector3(0, size.y / 2, 0));
    v.scene.add(m);
    v.model = m;
    $('empty-state').classList.add('hidden');
  }, undefined, (err) => console.error('model load failed', err));
}

/* ---------- generate flow ---------- */
$('generate').addEventListener('click', async () => {
  const prompt = ($('prompt').value || $('prompt2').value || '').trim();
  if (state.tab === 'text' && !prompt) { alert('Enter a prompt first.'); return; }
  if (state.tab === 'image' && !state.uploadId) { alert('Upload an image first.'); return; }
  const btn = $('generate');
  btn.disabled = true;
  const body = {
    prompt: prompt || null,
    upload_id: state.tab === 'image' ? state.uploadId : null,
    provider: $('provider').value,
    texture: $('texture').value,
    densify: $('densify').checked,
    rig: $('rig').checked,
  };
  const r = await fetch('/api/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  btn.disabled = false;
  if (!r.ok) { alert('generate failed: ' + (j.detail || r.status)); return; }
  addHistoryItem(j.job_id, body.prompt || 'image upload');
  pollJob(j.job_id);
});

function addHistoryItem(jobId, title) {
  const list = $('history');
  const empty = list.querySelector('.note');
  if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = 'hist-item';
  div.id = 'hist-' + jobId;
  div.innerHTML = `<div><div class="t">${escapeHtml(title.slice(0, 42))}</div><div class="s">queued</div></div>`;
  div.addEventListener('click', () => selectJob(jobId));
  list.prepend(div);
  state.jobs.unshift(jobId);
}

const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

async function pollJob(jobId) {
  $('jobbar').classList.remove('hidden');
  for (;;) {
    const r = await fetch('/api/job/' + jobId);
    const j = await r.json();
    $('job-title').textContent = `${j.prompt || 'model'} — ${j.status} (${j.provider || ''})`;
    $('progfill').style.width = (j.progress || 0) + '%';
    const el = document.querySelector('#hist-' + jobId + ' .s');
    if (el) { el.textContent = j.status + (j.error ? ': ' + j.error.slice(0, 80) : ''); el.className = 's ' + j.status; }
    if (j.status === 'done' || j.status === 'failed') {
      if (j.status === 'done') selectJob(jobId, j);
      else $('jobbar').classList.add('hidden');
      break;
    }
    await new Promise((res) => setTimeout(res, 2500));
  }
}

async function selectJob(jobId, cached) {
  const j = cached || await (await fetch('/api/job/' + jobId)).json();
  if (j.status !== 'done') return;
  state.currentJob = jobId;
  $('modelinfo').classList.remove('hidden');
  const pv = $('previews');
  pv.innerHTML = '';
  for (const u of (j.previews || [])) {
    const img = document.createElement('img');
    img.src = u;
    pv.appendChild(img);
  }
  const s = j.stats || {};
  const rows = [
    ['Faces', (s.faces || 0).toLocaleString()],
    ['Vertices', (s.vertices || 0).toLocaleString()],
    ['vs Tripo bar', s.face_ratio_vs_tripo ? (s.face_ratio_vs_tripo * 100).toFixed(1) + '%' : '—'],
    ['Texture maps', (s.texture_images || []).map((t) => t[0] + '×' + t[1]).join(', ') || '—'],
    ['Watertight', s.watertight ? 'yes' : 'no'],
    ['Bones (rig)', s.bones || 0],
    ['Height', s.height_m ? s.height_m.toFixed(2) + ' m' : '—'],
    ['Stages', (j.stages || []).join(' → ')],
  ];
  $('stats').innerHTML = rows.map((r) => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('');
  $('dl-glb').href = '/api/download/' + jobId + '?format=glb';
  $('dl-usd').href = '/api/download/' + jobId + '?format=usdz';
  $('dl-fbx').href = '/api/download/' + jobId + '?format=fbx';
  $('dl-note').textContent = 'GLB is native. USD is best-effort conversion. FBX needs a DCC converter — honest 501 on hosts without one.';
  showModel('/api/download/' + jobId + '?format=glb');
  const item = $('hist-' + jobId);
  if (item && j.previews && j.previews[0]) {
    const img = document.createElement('img');
    img.src = j.previews[0];
    item.prepend(img);
  }
}

/* ---------- boot ---------- */
try {
  initViewer();
} catch (e) {
  console.error('3D viewport failed (CDN?):', e);
  $('empty-state').querySelector('p').textContent = '3D viewport needs network access for the Three.js CDN. Generation still works via the API.';
}
loadProviders();
