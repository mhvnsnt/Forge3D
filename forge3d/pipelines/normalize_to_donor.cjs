#!/usr/bin/env node
/* ── FORGE3D PORT ─────────────────────────────────────────────────────────────
 * Source: mhvnsnt/Bannon repo, out/tools/normalize_to_donor.cjs (build-output dir, untracked)
 * Commit: 95f68f4bd2af8241e9d63fc2e1c6979db99279f3 (bannon-repair clone, 2026-10-06)
 * License: Bannon LICENSE.md — Copyright (c) 2026 mhvnsnt, All Rights Reserved.
 *          Ported intra-owner (mhvnsnt) at owner direction; same copyright holder.
 *          See docs/PROVENANCE.md and LICENSES.md.
 * Verbatim port — original header and logic below unchanged.
 * ─────────────────────────────────────────────────────────────────────────── */
/* normalize_to_donor.cjs — bake a target mesh into the donor's bind space.
 * Applies the SAME mapping transfer_weights uses for correspondence (uniform scale
 * to donor height + translate to donor bbox centre) PERMANENTLY to POSITION, so the
 * transfer's verbatim skeleton+IBMs fit the mesh. Normals corrected for the scale.
 * Skips (copies) targets already within [1.5, 2.2]m height.
 * Usage: node normalize_to_donor.cjs <donor.glb> <target.glb> <out.glb>
 */
'use strict';
const fs = require('fs');
const [DONOR, TGT, OUT] = process.argv.slice(2);
if (!DONOR || !TGT || !OUT) { console.error('usage: node normalize_to_donor.cjs <donor.glb> <target.glb> <out.glb>'); process.exit(1); }
(async () => {
  const { NodeIO } = require('@gltf-transform/core');
  const { ALL_EXTENSIONS } = require('@gltf-transform/extensions');
  const { MeshoptDecoder } = require('meshoptimizer');
  await MeshoptDecoder.ready;
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
  const bboxOf = async (f) => {
    const doc = await io.readBinary(fs.readFileSync(f));
    const mn = [1e9,1e9,1e9], mx = [-1e9,-1e9,-1e9];
    for (const m of doc.getRoot().listMeshes()) for (const p of m.listPrimitives()) {
      const a = p.getAttribute('POSITION'); if (!a) continue;
      const arr = a.getArray();
      for (let i = 0; i < arr.length; i += 3) for (let k = 0; k < 3; k++) {
        if (arr[i+k] < mn[k]) mn[k] = arr[i+k]; if (arr[i+k] > mx[k]) mx[k] = arr[i+k];
      }
    }
    return { mn, mx };
  };
  const sb = await bboxOf(DONOR), tb = await bboxOf(TGT);
  const sH = sb.mx[1]-sb.mn[1], tH = tb.mx[1]-tb.mn[1];
  console.log(`donor H=${sH.toFixed(3)} centre=(${sb.mn.map((v,k)=>((v+sb.mx[k])/2).toFixed(2)).join(',')})`);
  console.log(`target H=${tH.toFixed(3)} centre=(${tb.mn.map((v,k)=>((v+tb.mx[k])/2).toFixed(2)).join(',')})`);
  const doc = await io.readBinary(fs.readFileSync(TGT));
  const root = doc.getRoot();
  // Always align: the transfer's verbatim skeleton+IBMs are only valid in donor space.
  // If the target is already there, k=1 and t=0 (harmless no-op).
  {
    const k = sH / tH; // uniform scale preserves proportions
    const tc = tb.mn.map((v,i)=>(v+tb.mx[i])/2), sc = sb.mn.map((v,i)=>(v+sb.mx[i])/2);
    const t = sc.map((v,i)=>v - tc[i]*k);
    const isId = Math.abs(k-1)<1e-6 && t.every(v=>Math.abs(v)<1e-6);
    console.log(`uniform scale k=${k.toFixed(4)}, translate=(${t.map(v=>v.toFixed(3)).join(',')})${isId?' — identity, no-op':''}`);
    for (const m of root.listMeshes()) for (const p of m.listPrimitives()) {
      const pa = p.getAttribute('POSITION');
      if (pa) { const a = pa.getArray();
        for (let i=0;i<a.length;i+=3){ a[i]=a[i]*k+t[0]; a[i+1]=a[i+1]*k+t[1]; a[i+2]=a[i+2]*k+t[2]; }
        pa.setArray(a); }
      const na = p.getAttribute('NORMAL');
      if (na) { const a = na.getArray(); // uniform scale: direction preserved, renormalize
        for (let i=0;i<a.length;i+=3){ const l=Math.hypot(a[i],a[i+1],a[i+2])||1; a[i]/=l; a[i+1]/=l; a[i+2]/=l; }
        na.setArray(a); }
      for (const tg of p.listTargets()) for (const nm of ['POSITION']) {
        const ta = tg.getAttribute(nm); if (!ta) continue;
        const a = ta.getArray(); for (let i=0;i<a.length;i++) a[i]*=k; ta.setArray(a);
      }
    }
  }
  const buf = await (async () => {
    // drop meshopt so the minimal writer path is used (uncompressed intermediate)
    for (const e of root.listExtensionsUsed()) if (/meshopt/i.test(e.extensionName)) e.dispose();
    return io.writeBinary(doc);
  })();
  fs.writeFileSync(OUT, Buffer.from(buf));
  console.log('wrote', OUT);
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
