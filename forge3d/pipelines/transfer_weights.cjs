#!/usr/bin/env node
/* ── FORGE3D PORT ─────────────────────────────────────────────────────────────
 * Source: mhvnsnt/Bannon repo, tools/model_diag/transfer_weights.cjs
 * Commit: 95300506b4b2a8be7ee7af54d2e93a2016dd9c4a (bannon-repair clone, 2026-10-06)
 * License: Bannon LICENSE.md — Copyright (c) 2026 mhvnsnt, All Rights Reserved.
 *          Ported intra-owner (mhvnsnt) at owner direction; same copyright holder.
 *          See docs/PROVENANCE.md and LICENSES.md.
 * Verbatim port — original header and logic below unchanged.
 * ─────────────────────────────────────────────────────────────────────────── */
/* BANNON skin-weight TRANSFER — give a badly-weighted mesh a PROVEN rig without a re-rig service.
 *
 *   node tools/model_diag/transfer_weights.cjs <source.glb> <target.glb> [out.glb]
 *
 * Why this exists: the Heavyweight body (BANNON_muscular_skinned.glb) carries 16-joint skin.cjs
 * weights that skinqa measures at p95 0.3131 — catastrophic smearing, the deformation the owner
 * reported. The documented fix is a UniRig re-rig, but the hosted space kept returning DEGENERATE
 * rigs (9 joints, no limbs) under queue load. Meanwhile BANNON_rigged.glb is the SAME CHARACTER with a
 * good 28-joint UniRig skeleton that scores 0.0682. So: copy that rig onto the fat mesh.
 *
 * How: both meshes are the same character at the same height, so after centre-aligning them in bind
 * space, every target vertex sits near source vertices that belong to the same body part. For each
 * target vertex we take the K nearest source vertices and blend their joint influences by inverse
 * distance, then renormalise. Nearest-neighbour search uses a uniform spatial hash (brute force would
 * be 16k x 146k = 2.4 billion distance tests).
 *
 * Output carries: TARGET geometry + TARGET texture/material, SOURCE skeleton nodes + joints +
 * inverseBindMatrices, and the transferred JOINTS_0/WEIGHTS_0. Non-destructive; gate with skinqa and
 * only promote if p95 beats the original.
 */
const fs = require('fs');

const SRC = process.argv[2], TGT = process.argv[3];
if (!SRC || !TGT) { console.error('usage: node transfer_weights.cjs <source.glb> <target.glb> [out.glb]'); process.exit(1); }
const OUT = process.argv[4] || TGT.replace(/\.glb$/i, '') + '_xfer.glb';
const K = 6;                       // neighbours blended per target vertex

// ── COMPRESSED INPUT IS UNREADABLE BY THE PARSER BELOW, AND IT DOES NOT SAY SO ────────────────
// This file has its own minimal GLB reader, which is why it is fast and dependency-light. It knows
// nothing about EXT_meshopt_compression — and EVERY rig in assets/models is meshopt-compressed now.
// Fed one, it reads compressed bytes as float32 and produces numbers like src height 6.74e+38, then
// prints "wrote ... 58 joints ... texture preserved" and exits 0. A TOTAL SUCCESS MESSAGE ON PURE
// GARBAGE. Decompress to a temp file first, and refuse rather than guess if that is not possible.
function decompressIfNeeded(p) {
  let declared = false;
  try {
    const b = fs.readFileSync(p);
    let off = 12;
    while (off < b.length) {
      const l = b.readUInt32LE(off), t = b.readUInt32LE(off + 4);
      if (t === 0x4E4F534A) {
        const j = JSON.parse(b.slice(off + 8, off + 8 + l).toString('utf8'));
        declared = (j.extensionsUsed || []).indexOf('EXT_meshopt_compression') >= 0;
      }
      off += 8 + l;
    }
  } catch (e) { return p; }
  if (!declared) return p;
  const out = require('os').tmpdir() + '/xfer_' + require('path').basename(p);
  const r = require('child_process').spawnSync(process.execPath, ['-e', `
    const {NodeIO}=require('@gltf-transform/core'),{ALL_EXTENSIONS}=require('@gltf-transform/extensions');
    const {MeshoptEncoder,MeshoptDecoder}=require('meshoptimizer');
    const {normalizeBuffer}=require(${JSON.stringify(__dirname + '/fix_extensions_used.cjs')});
    const fs=require('fs');
    (async()=>{ await MeshoptEncoder.ready; await MeshoptDecoder.ready;
      const io=new NodeIO().registerExtensions(ALL_EXTENSIONS)
        .registerDependencies({'meshopt.encoder':MeshoptEncoder,'meshopt.decoder':MeshoptDecoder});
      const d=await io.readBinary(normalizeBuffer(fs.readFileSync(${JSON.stringify(p)})));
      // strip the extension so the plain reader downstream sees raw accessors
      for (const e of d.getRoot().listExtensionsUsed()) if (/meshopt/i.test(e.extensionName)) e.dispose();
      fs.writeFileSync(${JSON.stringify(out)}, Buffer.from(await io.writeBinary(d)));
    })();`, ], { cwd: process.cwd(), encoding: 'utf8' });
  if (r.status !== 0 || !fs.existsSync(out)) {
    console.error('REFUSED: ' + p + ' is EXT_meshopt_compression and could not be decompressed.\n' +
                  'This tool\'s GLB reader cannot decode it and would silently produce garbage.');
    process.exit(4);
  }
  console.error('  (decompressed ' + require('path').basename(p) + ' for reading)');
  return out;
}

function readGLB(path) {
  const b = fs.readFileSync(path);
  let off = 12, json = null, binOff = 0, binLen = 0;
  while (off < b.length) {
    const clen = b.readUInt32LE(off), ctype = b.readUInt32LE(off + 4);
    if (ctype === 0x4E4F534A) json = JSON.parse(b.slice(off + 8, off + 8 + clen).toString('utf8'));
    else if (ctype === 0x004E4942) { binOff = off + 8; binLen = clen; }
    off += 8 + clen;
  }
  return { json, bin: b.slice(binOff, binOff + binLen) };
}
const CSIZE = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 };
const NCOMP = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
function accessor(g, i) {
  const a = g.json.accessors[i], bv = g.json.bufferViews[a.bufferView];
  const base = (bv.byteOffset || 0) + (a.byteOffset || 0);
  const nc = NCOMP[a.type], cs = CSIZE[a.componentType];
  const stride = bv.byteStride || nc * cs;
  const rd = { 5120: o => g.bin.readInt8(o), 5121: o => g.bin.readUInt8(o), 5122: o => g.bin.readInt16LE(o),
               5123: o => g.bin.readUInt16LE(o), 5125: o => g.bin.readUInt32LE(o), 5126: o => g.bin.readFloatLE(o) }[a.componentType];
  const out = [];
  for (let v = 0; v < a.count; v++) { const e = []; for (let c = 0; c < nc; c++) e.push(rd(base + v * stride + c * cs)); out.push(e); }
  return { data: out, comp: a.componentType, type: a.type, count: a.count };
}

const S = readGLB(decompressIfNeeded(SRC)), T = readGLB(decompressIfNeeded(TGT));
if (!S.json.skins || !S.json.skins.length) { console.error('source has no skin — nothing to transfer'); process.exit(2); }
if (!T.json.meshes || T.json.meshes.length !== 1 || T.json.meshes[0].primitives.length !== 1) {
  console.error('target must be a single mesh / single primitive (run strip_satellites first)'); process.exit(2);
}

// ── gather ALL source skinned vertices (the source may be split across many primitives)
const srcPos = [], srcJoints = [], srcWeights = [];
for (const mesh of S.json.meshes) {
  for (const prim of mesh.primitives) {
    if (prim.attributes.JOINTS_0 == null || prim.attributes.WEIGHTS_0 == null) continue;
    const P = accessor(S, prim.attributes.POSITION);
    const J = accessor(S, prim.attributes.JOINTS_0);
    const W = accessor(S, prim.attributes.WEIGHTS_0);
    for (let v = 0; v < P.count; v++) { srcPos.push(P.data[v]); srcJoints.push(J.data[v]); srcWeights.push(W.data[v]); }
  }
}
if (!srcPos.length) { console.error('source has no skinned vertices'); process.exit(2); }

const tprim = T.json.meshes[0].primitives[0];
const TP = accessor(T, tprim.attributes.POSITION);
const tgtPos = TP.data;

// ── centre-align in bind space: same character, but the fat mesh sits offset. Match bbox centres in
// X/Z and match the FEET (min Y) so the vertical mapping stays anatomically honest.
function bbox(list) {
  const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
  for (const p of list) for (let k = 0; k < 3; k++) { if (p[k] < mn[k]) mn[k] = p[k]; if (p[k] > mx[k]) mx[k] = p[k]; }
  return { mn, mx };
}
const sb = bbox(srcPos), tb = bbox(tgtPos);
const shift = [
  ((sb.mn[0] + sb.mx[0]) / 2) - ((tb.mn[0] + tb.mx[0]) / 2),
  sb.mn[1] - tb.mn[1],
  ((sb.mn[2] + sb.mx[2]) / 2) - ((tb.mn[2] + tb.mx[2]) / 2)
];
// scale height to match so limbs line up even if the bodies differ slightly in stature
const sH = sb.mx[1] - sb.mn[1], tH = tb.mx[1] - tb.mn[1];
const yScale = (tH > 1e-6) ? (sH / tH) : 1;
console.log('align: shift [' + shift.map(v => v.toFixed(3)) + '], yScale ' + yScale.toFixed(4) +
  '  (src H ' + sH.toFixed(3) + ', tgt H ' + tH.toFixed(3) + ')');

function mapped(p) {   // target vertex -> source bind space
  return [ (p[0] + shift[0]), sb.mn[1] + (p[1] - tb.mn[1]) * yScale, (p[2] + shift[2]) ];
}

// ── uniform spatial hash over source verts
const CELL = Math.max(0.02, sH / 60);
const grid = new Map();
const key = (x, y, z) => x + ',' + y + ',' + z;
function cellOf(p) { return [Math.floor(p[0] / CELL), Math.floor(p[1] / CELL), Math.floor(p[2] / CELL)]; }
for (let i = 0; i < srcPos.length; i++) {
  const c = cellOf(srcPos[i]), k = key(c[0], c[1], c[2]);
  let arr = grid.get(k); if (!arr) { arr = []; grid.set(k, arr); }
  arr.push(i);
}
console.log('spatial hash: ' + grid.size + ' cells over ' + srcPos.length + ' source verts (cell ' + CELL.toFixed(3) + 'm)');

function nearest(p, k) {
  const c = cellOf(p);
  let found = [], ring = 0;
  // grow the search ring until we have enough candidates (cheap: bodies are dense)
  while (found.length < k && ring <= 6) {
    found = [];
    for (let dx = -ring; dx <= ring; dx++) for (let dy = -ring; dy <= ring; dy++) for (let dz = -ring; dz <= ring; dz++) {
      const arr = grid.get(key(c[0] + dx, c[1] + dy, c[2] + dz));
      if (arr) for (const idx of arr) found.push(idx);
    }
    ring++;
  }
  const scored = found.map(i => {
    const q = srcPos[i];
    const dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2];
    return { i, d2: dx * dx + dy * dy + dz * dz };
  }).sort((a, b) => a.d2 - b.d2);
  return scored.slice(0, k);
}

// ── transfer
const outJ = [], outW = [];
let worst = 0, sumD = 0;
for (let v = 0; v < tgtPos.length; v++) {
  const p = mapped(tgtPos[v]);
  const nn = nearest(p, K);
  const acc = new Map();                     // joint -> accumulated weight
  if (!nn.length) { outJ.push([0, 0, 0, 0]); outW.push([1, 0, 0, 0]); continue; }
  const d0 = Math.sqrt(nn[0].d2); if (d0 > worst) worst = d0; sumD += d0;
  for (const n of nn) {
    const w = 1 / (Math.sqrt(n.d2) + 1e-4);  // inverse-distance blend
    const J = srcJoints[n.i], W = srcWeights[n.i];
    for (let c = 0; c < 4; c++) {
      const jw = W[c]; if (!jw) continue;
      const j = J[c];
      acc.set(j, (acc.get(j) || 0) + jw * w);
    }
  }
  // keep the 4 strongest influences (glTF allows 4 per vertex), renormalise to 1
  const top = [...acc.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4);
  const tot = top.reduce((s, e) => s + e[1], 0) || 1;
  const js = [0, 0, 0, 0], ws = [0, 0, 0, 0];
  top.forEach((e, i) => { js[i] = e[0]; ws[i] = e[1] / tot; });
  outJ.push(js); outW.push(ws);
}
console.log('transferred ' + tgtPos.length + ' vertices  (mean nearest-source distance ' +
  (sumD / tgtPos.length).toFixed(4) + 'm, worst ' + worst.toFixed(4) + 'm)');

// ── write: target geometry + target texture + SOURCE skeleton/skin
const parts = [], views = [], accs = [];
function align4() { const o = parts.reduce((a, x) => a + x.length, 0); const p = (4 - o % 4) % 4; if (p) parts.push(Buffer.alloc(p)); }
function push(rows, comp, type, target, minmax) {
  align4();
  const nc = NCOMP[type], cs = CSIZE[comp];
  const buf = Buffer.alloc(rows.length * nc * cs);
  const wr = { 5121: (o, v) => buf.writeUInt8(v, o), 5123: (o, v) => buf.writeUInt16LE(v, o),
               5125: (o, v) => buf.writeUInt32LE(v, o), 5126: (o, v) => buf.writeFloatLE(v, o) }[comp];
  let o = 0; for (const r of rows) for (let c = 0; c < nc; c++) { wr(o, r[c]); o += cs; }
  const boff = parts.reduce((a, x) => a + x.length, 0); parts.push(buf);
  views.push({ buffer: 0, byteOffset: boff, byteLength: buf.length, ...(target ? { target } : {}) });
  const acc = { bufferView: views.length - 1, componentType: comp, count: rows.length, type };
  if (minmax) {
    const mn = [], mx = [];
    for (let c = 0; c < nc; c++) { mn[c] = Infinity; mx[c] = -Infinity; }
    for (const r of rows) for (let c = 0; c < nc; c++) { if (r[c] < mn[c]) mn[c] = r[c]; if (r[c] > mx[c]) mx[c] = r[c]; }
    acc.min = mn; acc.max = mx;
  }
  accs.push(acc); return accs.length - 1;
}
function copyRaw(g, byteOffset, byteLength, target) {
  align4();
  const buf = Buffer.from(g.bin.slice(byteOffset, byteOffset + byteLength));
  const boff = parts.reduce((a, x) => a + x.length, 0); parts.push(buf);
  views.push({ buffer: 0, byteOffset: boff, byteLength, ...(target ? { target } : {}) });
  return views.length - 1;
}

const attrs = {};
attrs.POSITION = push(tgtPos, 5126, 'VEC3', 34962, true);
if (tprim.attributes.NORMAL != null)     attrs.NORMAL     = push(accessor(T, tprim.attributes.NORMAL).data, 5126, 'VEC3', 34962, false);
if (tprim.attributes.TEXCOORD_0 != null) attrs.TEXCOORD_0 = push(accessor(T, tprim.attributes.TEXCOORD_0).data, 5126, 'VEC2', 34962, false);
attrs.JOINTS_0  = push(outJ, 5123, 'VEC4', 34962, false);     // ushort joints
attrs.WEIGHTS_0 = push(outW, 5126, 'VEC4', 34962, false);
const tIdx = accessor(T, tprim.indices);
const idxAcc = push(tIdx.data.map(e => [e[0]]), 5125, 'SCALAR', 34963, false);

// source inverse-bind matrices, copied verbatim
const sSkin = S.json.skins[0];
const ibmA = S.json.accessors[sSkin.inverseBindMatrices];
const ibmBV = S.json.bufferViews[ibmA.bufferView];
const ibmView = copyRaw(S, (ibmBV.byteOffset || 0) + (ibmA.byteOffset || 0), ibmA.count * 64, 0);
const ibmAcc = accs.push({ bufferView: ibmView, componentType: 5126, count: ibmA.count, type: 'MAT4' }) - 1;

// target texture image, copied verbatim
let images, textures, samplers;
if (T.json.images && T.json.images.length) {
  images = T.json.images.map(img => {
    if (img.bufferView != null) {
      const bv = T.json.bufferViews[img.bufferView];
      return { mimeType: img.mimeType, bufferView: copyRaw(T, bv.byteOffset || 0, bv.byteLength) };
    }
    return Object.assign({}, img);
  });
  textures = T.json.textures ? JSON.parse(JSON.stringify(T.json.textures)) : undefined;
  samplers = T.json.samplers ? JSON.parse(JSON.stringify(T.json.samplers)) : undefined;
}

// SOURCE node graph (the skeleton) + one new mesh node bound to the copied skin.
const nodes = JSON.parse(JSON.stringify(S.json.nodes));
// drop any mesh bindings the source nodes had — we only want its bones
nodes.forEach(n => { delete n.mesh; delete n.skin; });
const meshNodeIndex = nodes.length;
nodes.push({ mesh: 0, skin: 0, name: 'BANNON_XFER_MESH' });

// scene roots: keep the source's roots (bones) and add our mesh node
let roots = (S.json.scenes && S.json.scenes[S.json.scene || 0] && S.json.scenes[S.json.scene || 0].nodes) || [];
roots = roots.slice(); roots.push(meshNodeIndex);

const g = {
  asset: { version: '2.0', generator: 'bannon transfer_weights (source rig -> target mesh, K=' + K + ')' },
  scene: 0, scenes: [{ nodes: roots }],
  nodes,
  meshes: [{ name: (T.json.meshes[0].name || 'mesh') + '_xfer', primitives: [{ attributes: attrs, indices: idxAcc, material: 0 }] }],
  materials: T.json.materials ? JSON.parse(JSON.stringify(T.json.materials)) : [{ pbrMetallicRoughness: { baseColorFactor: [0.83, 0.62, 0.5, 1] } }],
  skins: [{ joints: sSkin.joints.slice(), inverseBindMatrices: ibmAcc, ...(sSkin.skeleton != null ? { skeleton: sSkin.skeleton } : {}) }],
  bufferViews: views, accessors: accs
};
if (images) g.images = images;
if (textures) g.textures = textures;
if (samplers) g.samplers = samplers;

let blob = Buffer.concat(parts); const bp = (4 - blob.length % 4) % 4; if (bp) blob = Buffer.concat([blob, Buffer.alloc(bp)]);
g.buffers = [{ byteLength: blob.length }];
let js = Buffer.from(JSON.stringify(g)); const jp = (4 - js.length % 4) % 4; if (jp) js = Buffer.concat([js, Buffer.alloc(jp, 0x20)]);
const head = Buffer.alloc(12); head.write('glTF', 0); head.writeUInt32LE(2, 4); head.writeUInt32LE(12 + 8 + js.length + 8 + blob.length, 8);
const jh = Buffer.alloc(8); jh.writeUInt32LE(js.length, 0); jh.writeUInt32LE(0x4E4F534A, 4);
const bh = Buffer.alloc(8); bh.writeUInt32LE(blob.length, 0); bh.writeUInt32LE(0x004E4942, 4);
fs.writeFileSync(OUT, Buffer.concat([head, jh, js, bh, blob]));

console.log('wrote ' + OUT + '  ' + (fs.statSync(OUT).size / 1024 | 0) + ' KB, ' + tgtPos.length + ' verts, ' +
  sSkin.joints.length + ' joints (from source), texture ' + (images ? 'preserved' : 'none'));
console.log('NEXT: gate it -> node tools/model_diag/skinqa.cjs ' + OUT.split('/').pop() + '   (promote only if p95 beats the original)');
