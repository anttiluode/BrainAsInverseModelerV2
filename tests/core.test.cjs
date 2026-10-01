const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { reconstruct } = require('../site/core.js');

function closeVec(actual, expected, tol=1e-9) {
  assert.equal(actual.length, expected.length);
  actual.forEach((v,i)=>assert.ok(Math.abs(v-expected[i]) <= tol, `${i}: ${v} vs ${expected[i]}`));
}

test('hand-derived diagonal inverse obeys the three-sigma truncation', () => {
  const K=[[2,0],[0,1],[0,0]];
  closeVec(reconstruct(K,[0.6,0.8,0],0.4).estimate,[0.3,0.0],1e-10);
});

test('rank-one twins return the minimum-norm estimate', () => {
  const K=[[1,1],[2,2]];
  const out=reconstruct(K,[1,2],0);
  closeVec(out.estimate,[0.5,0.5],1e-8);
  assert.equal(out.retainedModes,1);
});

test('zero operator and huge noise stay finite and invent no modes', () => {
  for (const [K,y,sigma] of [
    [[[0,0],[0,0]],[1,-1],0],
    [[[1,0],[0,1]],[1,-1],100]
  ]) {
    const out=reconstruct(K,y,sigma);
    closeVec(out.estimate,[0,0],1e-12);
    assert.equal(out.retainedModes,0);
    assert.ok(out.estimate.every(Number.isFinite));
  }
});


test('one soma snapshot has at most one observable source mode', () => {
  const K=[[1,2,3,4,5,6]];
  const y=[7.0];
  const out=reconstruct(K,y,0);
  assert.equal(out.retainedModes,1);
  const norm2=91;
  closeVec(out.estimate,[1,2,3,4,5,6].map(v=>7*v/norm2),1e-10);
});

test('browser reconstruction agrees with exported Python calibration', () => {
  const sandbox={window:{},atob:globalThis.atob};
  for (const name of ['data-diverse.js','data-symmetric.js','data-mismatch.js','data-demo.js','data.js']) {
    const raw=fs.readFileSync(path.join(__dirname,'../site',name),'utf8');
    vm.runInNewContext(raw,sandbox);
  }
  const data=sandbox.window.DENDRITIC_LENS_DATA;
  const cal=data.calibration.diverse;
  const truth=[0.12,0.74,0.31,0.93,0.27,0.58];
  const y=cal.K.map(row=>row.reduce((s,v,j)=>s+v*truth[j],0));
  const out=reconstruct(cal,y,0);
  // site/data.js deliberately stores calibration matrices as Float32.
  closeVec(out.estimate,truth,2e-6);
  assert.equal(out.retainedModes,6);
});
