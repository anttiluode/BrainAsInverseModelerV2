(() => {
  'use strict';
  const DATA = window.DENDRITIC_LENS_DATA;
  const { reconstruct } = window.DendriticLensCore;
  const $ = id => document.getElementById(id);
  const amps = [0.12, 0.74, 0.31, 0.93, 0.27, 0.58];
  const sliderRoot = $('sliders');

  function fmt(v, digits=3) {
    if (!Number.isFinite(v)) return '—';
    if (Math.abs(v) < 1e-3 && v !== 0) return v.toExponential(2);
    return v.toFixed(digits);
  }
  function rmse(a,b){ return Math.sqrt(a.reduce((s,v,i)=>s+(v-b[i])**2,0)/a.length); }
  function matvec(K,x){ return K.map(row=>row.reduce((s,v,j)=>s+v*x[j],0)); }
  function gaussianNoise(n) {
    let seed=0x2f6e2b1;
    const out=[];
    const uniform=()=>{seed=(1664525*seed+1013904223)>>>0; return (seed+1)/4294967297;};
    while(out.length<n){const u1=uniform(),u2=uniform();const r=Math.sqrt(-2*Math.log(u1));out.push(r*Math.cos(2*Math.PI*u2));if(out.length<n)out.push(r*Math.sin(2*Math.PI*u2));}
    return out;
  }
  const noiseTemplate=gaussianNoise(DATA.calibration.diverse.K.length);

  amps.forEach((value,i)=>{
    const row=document.createElement('div'); row.className='slider-row';
    row.innerHTML=`<div class="slider-head"><span>branch ${i+1}</span><strong id="amp-v-${i}">${value.toFixed(2)}</strong></div><input id="amp-${i}" type="range" min="0" max="1" step="0.01" value="${value}" aria-label="Branch ${i+1} hidden amplitude">`;
    sliderRoot.appendChild(row);
    row.querySelector('input').addEventListener('input',e=>{amps[i]=+e.target.value;$(`amp-v-${i}`).textContent=amps[i].toFixed(2);render();});
  });

  function setAmps(values){values.forEach((v,i)=>{amps[i]=v;$(`amp-${i}`).value=v;$(`amp-v-${i}`).textContent=v.toFixed(2);});}
  function sigmaValue(){const v=$('noise-level').value; return v==='fixed'?0.01:+v*DATA.tomography.noise_reference_rms_mv;}

  function drawLines(canvas, series) {
    const dpr=window.devicePixelRatio||1, w=Math.max(300,canvas.clientWidth), h=+canvas.getAttribute('height')||220;
    canvas.width=w*dpr; canvas.height=h*dpr; const c=canvas.getContext('2d'); c.scale(dpr,dpr);
    c.clearRect(0,0,w,h); const all=series.flatMap(s=>s.values).filter(Number.isFinite); let lo=Math.min(...all),hi=Math.max(...all); if(!(hi>lo)){lo-=1;hi+=1;} const pad=(hi-lo)*.08;lo-=pad;hi+=pad;
    c.strokeStyle='#243744'; c.lineWidth=1; for(let q=0;q<=4;q++){const y=18+(h-36)*q/4;c.beginPath();c.moveTo(0,y);c.lineTo(w,y);c.stroke();}
    const colors=['#63e6e2','#ffc96b','#ff8fa3','#9ee493'];
    series.forEach((s,k)=>{const vals=s.values;c.strokeStyle=colors[k%colors.length];c.lineWidth=k===0?2:1.5;c.beginPath();vals.forEach((v,i)=>{const x=vals.length===1?w/2:i*(w-1)/(vals.length-1);const y=18+(hi-v)*(h-36)/(hi-lo);if(i===0)c.moveTo(x,y);else c.lineTo(x,y);});c.stroke();});
  }

  function renderBars(truth, estimate) {
    $('input-bars').innerHTML=truth.map((v,i)=>`<div class="input-row"><span>B${i+1}</span><div class="paired-bar"><div class="truth" style="width:${Math.max(0,Math.min(100,v*100))}%"></div><div class="estimate" style="width:${Math.max(0,Math.min(100,estimate[i]*100))}%"></div></div><span class="bar-value">${fmt(estimate[i],2)}</span></div>`).join('');
  }
  function renderSpectrum(s,mask){const max=s[0]||1;$('singular-bars').innerHTML=s.map((v,i)=>`<div class="singular-row"><span>${i+1}</span><div class="singular-track"><div class="singular-fill ${mask[i]?'':'off'}" style="width:${Math.max(1,100*v/max)}%"></div></div><span class="bar-value">${fmt(v,3)}</span></div>`).join('');}

  function render(){
    const arch=$('architecture').value; const nominal=DATA.calibration[arch]; const mismatch=$('mismatch').checked && arch==='diverse';
    const forwardK=mismatch?DATA.calibration.mismatch_true.K:nominal.K; const sigma=sigmaValue();
    let observed=matvec(forwardK,amps).map((v,i)=>v+sigma*noiseTemplate[i]);
    let inverseOperator=nominal, reconstruction, displayObserved=observed, displayPredicted;
    if($('readout-mode').value==='snapshot'){
      const idx=39; reconstruction=reconstruct([nominal.K[idx]],[observed[idx]],sigma); displayObserved=[observed[idx]]; displayPredicted=reconstruction.predicted; $('trace-label').textContent='single 20 ms sample';
    } else { reconstruction=reconstruct(inverseOperator,observed,sigma); displayPredicted=reconstruction.predicted; $('trace-label').textContent='observed vs inverse-projected trace'; }
    $('retained').textContent=`${reconstruction.retainedModes} / 6`; $('input-error').textContent=fmt(rmse(amps,reconstruction.estimate),4); $('measurement-error').textContent=fmt(reconstruction.residualRms/DATA.tomography.noise_reference_rms_mv,4); $('sigma').textContent=`${fmt(sigma,5)} mV`;
    renderBars(amps,reconstruction.estimate); renderSpectrum(reconstruction.singularValues,reconstruction.mask); drawLines($('trace-canvas'),[{values:displayObserved},{values:displayPredicted}]);
    let text;
    if($('readout-mode').value==='snapshot') text='One instantaneous soma value exposes at most one source direction. The inverse can fit that scalar while most hidden amplitudes remain unresolved.';
    else if(arch==='symmetric') text='All six branches have the same impulse response. The soma sees their sum, not their identities; minimum-norm inversion therefore distributes evidence across indistinguishable branches.';
    else if(mismatch) text='The trace was generated by a 20% slower cable but inverted with the nominal one. A small voltage residual can coexist with a much larger hidden-input error: fitting the wall is not the same as recovering the scene.';
    else if(sigma>0) text='Noise first removes the weakest singular directions. The control uses the same absolute voltage noise for both architectures, so the comparison is not rescued by rescaling each cable.';
    else text='With diverse temporal fingerprints and the known pulse timing, the full soma trace spans all six source directions in this illustrative circuit.';
    $('interpretation').textContent=text;
  }

  function renderDynamics(){
    const s=DATA.dynamics.summary.noise_0; const arms=[['delay_19','19 raw delays'],['diverse_cable','diverse cable'],['exponential_19','19 exponential traces'],['current_only','current x only']];
    $('comparison').innerHTML=arms.map(([k,label],i)=>`<div class="${i===0?'best':''}"><span>${label}</span><strong>${s[k].mean_nrmse.toFixed(3)}</strong><span>mean hidden y/z NRMSE · R² ${s[k].mean_r2.toFixed(3)}</span></div>`).join('');
    const ex=DATA.dynamics.example; drawLines($('y-canvas'),[{values:ex.truth_y},{values:ex.pred_y}]); drawLines($('z-canvas'),[{values:ex.truth_z},{values:ex.pred_z}]);
    $('reset-copy').textContent=`Ongoing diverse-cable state: ${s.diverse_cable.mean_nrmse.toFixed(3)} NRMSE. Reset the same cable before every readout: ${s.diverse_reset_each_sample.mean_nrmse.toFixed(3)}, essentially the current-only ${s.current_only.mean_nrmse.toFixed(3)}. The useful part is the retained history.`;
    const sp=DATA.dynamics.summary.same_present_example; $('same-present-copy').textContent=sp.found?`Two held-out moments differ in observed x by only ${sp.x_difference_training_std.toFixed(3)} training σ, yet their hidden y/z states are ${sp.hidden_yz_separation_training_std.toFixed(2)} σ apart. Present value alone does not identify the world.`:'No qualifying pair was found in this run.';
    const h=DATA.dynamics.summary.independent_hidden; $('hidden-copy').textContent=`An independent Gaussian variable that never affects x stays unrecoverable: NRMSE ${h.nrmse.toFixed(3)}, R² ${h.r2.toFixed(3)}. Temporal reconstruction cannot reveal variables that leave no trace in the observation.`;
    $('hero-diverse').textContent=DATA.tomography.architectures.diverse.scenes.fraction_0.amplitude_rmse.toExponential(1); $('hero-state').textContent=s.diverse_cable.mean_nrmse.toFixed(3); $('hero-delay').textContent=s.delay_19.mean_nrmse.toFixed(3);
  }

  document.querySelectorAll('#architecture,#readout-mode,#noise-level,#mismatch').forEach(el=>el.addEventListener('change',render));
  document.querySelectorAll('[data-preset]').forEach(btn=>btn.addEventListener('click',()=>{
    document.querySelectorAll('[data-preset]').forEach(b=>b.classList.remove('active'));btn.classList.add('active');
    const p=btn.dataset.preset;
    if(p==='readable'){ $('architecture').value='diverse';$('readout-mode').value='trace';$('noise-level').value='0';$('mismatch').checked=false;setAmps([.12,.74,.31,.93,.27,.58]); }
    if(p==='twins'){ $('architecture').value='symmetric';$('readout-mode').value='trace';$('noise-level').value='0';$('mismatch').checked=false;setAmps([1,0,0,0,0,0]); }
    if(p==='noise'){ $('architecture').value='diverse';$('readout-mode').value='trace';$('noise-level').value='0.01';$('mismatch').checked=false;setAmps([.12,.74,.31,.93,.27,.58]); }
    if(p==='mismatch'){ $('architecture').value='diverse';$('readout-mode').value='trace';$('noise-level').value='0';$('mismatch').checked=true;setAmps([.12,.74,.31,.93,.27,.58]); }
    render();
  }));
  window.addEventListener('resize',()=>{render();renderDynamics();});
  renderDynamics(); render();
})();
