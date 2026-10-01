# Findings — The Dendritic Lens

## The question

Varjoluotain's inverse-problem lesson is that a restricted measurement can still contain fingerprints of hidden causes, but fitting the measurement does not guarantee that the causes were identified correctly. V2 applies that lesson to a passive dendritic cable.

The cable is not treated as a metaphorical delay line. Its voltages follow the exact zero-order-hold solution of the passive RC system. The reconstruction question is then empirical: **which distinctions in the hidden world remain accessible in the resulting temporal state?**

## 1. A soma trace can be an inverse instrument

The diverse six-branch cable has six linearly independent soma impulse responses under the frozen pulse protocol. With zero noise, all six amplitudes are recovered to numerical precision (RMSE 2.87×10⁻¹⁵). The symmetric control has six identical responses and therefore only one observable mode; its minimum-norm amplitude RMSE is 0.2649 even though its soma waveform can be fitted essentially perfectly.

That distinction is central. The inverse is not succeeding because it has six outputs. It succeeds only when the **forward physics leaves six distinguishable fingerprints** in the accessible trace.

Noise removes weak directions in the declared truncated-SVD inverse. At 5% of the fixed reference waveform RMS, the diverse cable keeps five modes and amplitude RMSE rises to 0.1577. At a fixed 0.01 mV noise level it keeps only three modes and reaches 0.2530 RMSE. The symmetric cable never has more than one source mode to lose.

A one-sample soma snapshot at 20 ms also has rank one by construction. Its diverse-cable amplitude RMSE is 0.3271. Temporal access—not merely the soma voltage itself—is what makes the six-source inverse possible.

## 2. Good waveform fit does not prove correct causes

The strongest inverse-problem control generates the data with a cable whose branch membrane time constants are all 20% slower, then inverts with the nominal calibration.

The nominal model fits the observed waveform with a residual of only 0.000752 of the reference RMS, yet its hidden-input RMSE is 0.2168. The accessible voltage can therefore look almost explained while the inferred causes are substantially wrong.

This is the dendritic version of the ambiguity that motivated the project: **forward agreement is necessary, not sufficient, for hidden-world identification.**

## 3. Ongoing cable state retains hidden dynamical information

The second experiment supplies only noisy Lorenz `x` to the observer. Hidden `y,z` are withheld from the cable and used only to train/evaluate a fixed quadratic information-content decoder on separate trajectories.

On held-out trajectories with zero input noise:

- 19 raw delays: 0.0777 mean NRMSE, R² 0.9938.
- diverse cable state: 0.1774, R² 0.9665.
- 19 exponential traces: 0.2043, R² 0.9479.
- symmetric cable state: 0.2792, R² 0.9112.
- current `x` only: 0.6216, R² 0.5904.
- diverse cable reset before every sample: 0.6216, R² 0.5904.
- soma alone: 0.6777, R² 0.4938.

The reset control is especially informative. The same diverse cable, stripped of its accumulated history at every readout, falls back to the current-observation baseline. The gain is therefore carried by temporal state rather than by an instantaneous nonlinear remapping.

The cable nevertheless does **not** beat the simple delay baseline. The result supports the narrower claim that passive dendritic dynamics can furnish useful history coordinates, not that this particular morphology is an optimal reconstruction machine.

At 2% input noise the diverse cable changes from 0.1774 to 0.1790 NRMSE, while raw delays change from 0.0777 to 0.0984. That robustness difference is interesting but does not reverse the ordering.

## 4. Same present, different hidden world

The held-out data contain a pair of moments whose current `x` differs by only 0.0149 training standard deviations while hidden `y,z` differ by 3.96 standard deviations. This is the concrete situation the history coordinates must resolve: a present scalar observation that is nearly the same can belong to very different states and futures.

## 5. Information that never touches the sensor stays hidden

A Gaussian variable generated independently of the Lorenz system is attached only as an evaluation label. It never affects `x`, the cable, or any observer feature. Its held-out reconstruction remains at NRMSE 0.9945 and R² −0.0052.

That negative control matters because embedding language can otherwise be over-read. History can reconstruct hidden variables only insofar as they influence the observed dynamical process. A dendritic lens cannot infer a variable that leaves no causal trace in its input.

## What survives

The useful synthesis is now sharper than “dendrites do Takens.”

1. **Physical cable dynamics create a bank of history-dependent coordinates.**
2. **Diverse dynamics can make hidden causes observable in time even when a single snapshot cannot.**
3. **The same stored history can expose hidden dynamical state downstream.**
4. **Observability has hard limits:** symmetry, measurement noise, model mismatch, output bottlenecks, and causally disconnected variables.
5. **An inverse model must represent ambiguity, not merely reproduce observations.**

That is the operational sense in which the dendrite can act as a lens on its world.
