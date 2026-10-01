(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.DendriticLensCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function dot(a, b) {
    let s = 0;
    for (let i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }

  function factorizeMatrix(K) {
    if (!Array.isArray(K) || K.length === 0 || !Array.isArray(K[0]) || K[0].length === 0) {
      throw new Error('operator must be a nonempty matrix');
    }
    const m = K.length;
    const n = K[0].length;
    for (const row of K) {
      if (!Array.isArray(row) || row.length !== n || row.some(v => !Number.isFinite(v))) {
        throw new Error('operator must be a finite rectangular matrix');
      }
    }
    const A = Array.from({ length: n }, () => Array(n).fill(0));
    for (let i = 0; i < n; i++) {
      for (let j = i; j < n; j++) {
        let s = 0;
        for (let r = 0; r < m; r++) s += K[r][i] * K[r][j];
        A[i][j] = A[j][i] = s;
      }
    }
    const V = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => i === j ? 1 : 0));
    const maxIter = Math.max(32, 80 * n * n);
    for (let iter = 0; iter < maxIter; iter++) {
      let p = 0, q = 1, max = 0;
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const z = Math.abs(A[i][j]);
          if (z > max) { max = z; p = i; q = j; }
        }
      }
      if (max < 1e-15) break;
      const app = A[p][p], aqq = A[q][q], apq = A[p][q];
      const phi = 0.5 * Math.atan2(2 * apq, aqq - app);
      const c = Math.cos(phi), s = Math.sin(phi);
      for (let k = 0; k < n; k++) {
        if (k === p || k === q) continue;
        const akp = A[k][p], akq = A[k][q];
        A[k][p] = A[p][k] = c * akp - s * akq;
        A[k][q] = A[q][k] = s * akp + c * akq;
      }
      A[p][p] = c*c*app - 2*s*c*apq + s*s*aqq;
      A[q][q] = s*s*app + 2*s*c*apq + c*c*aqq;
      A[p][q] = A[q][p] = 0;
      for (let k = 0; k < n; k++) {
        const vkp = V[k][p], vkq = V[k][q];
        V[k][p] = c * vkp - s * vkq;
        V[k][q] = s * vkp + c * vkq;
      }
    }
    const modeCount = Math.min(m, n);
    const order = Array.from({ length: n }, (_, i) => i).sort((a, b) => A[b][b] - A[a][a]).slice(0, modeCount);
    const S = order.map(i => Math.sqrt(Math.max(0, A[i][i])));
    const Vt = order.map(i => Array.from({ length: n }, (_, j) => V[j][i]));
    const U = Array.from({ length: m }, () => Array(modeCount).fill(0));
    for (let mode = 0; mode < modeCount; mode++) {
      const sv = S[mode];
      if (sv <= 1e-14) continue;
      const v = Vt[mode];
      for (let r = 0; r < m; r++) U[r][mode] = dot(K[r], v) / sv;
    }
    return { K, U, S, Vt };
  }

  function reconstruct(operator, observation, sigma) {
    if (!Number.isFinite(sigma) || sigma < 0) throw new Error('sigma must be finite and nonnegative');
    const cal = operator && !Array.isArray(operator) && operator.K && operator.U && operator.S && operator.Vt
      ? operator : factorizeMatrix(operator);
    const K = cal.K;
    if (!Array.isArray(observation) || observation.length !== K.length || observation.some(v => !Number.isFinite(v))) {
      throw new Error('observation length must match operator rows and be finite');
    }
    const smax = cal.S.length ? cal.S[0] : 0;
    const threshold = Math.max(3 * sigma, smax * 1e-10);
    const mask = cal.S.map(s => s > threshold);
    const estimate = Array(K[0].length).fill(0);
    for (let mode = 0; mode < cal.S.length; mode++) {
      if (!mask[mode]) continue;
      let proj = 0;
      for (let r = 0; r < K.length; r++) proj += cal.U[r][mode] * observation[r];
      const gain = proj / cal.S[mode];
      for (let j = 0; j < estimate.length; j++) estimate[j] += cal.Vt[mode][j] * gain;
    }
    const predicted = K.map(row => dot(row, estimate));
    let residual = 0;
    for (let r = 0; r < predicted.length; r++) residual += (predicted[r] - observation[r]) ** 2;
    residual = Math.sqrt(residual / Math.max(1, predicted.length));
    return {
      estimate,
      singularValues: cal.S.slice(),
      mask,
      retainedModes: mask.filter(Boolean).length,
      predicted,
      residualRms: residual,
      threshold
    };
  }

  return { reconstruct, factorizeMatrix };
});
