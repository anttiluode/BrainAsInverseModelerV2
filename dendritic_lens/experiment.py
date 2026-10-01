"""Frozen dendritic-lens experiments and machine-readable receipt export."""

from __future__ import annotations

import base64
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy

from .cable import impulse_operator, make_cable
from .inverse import svd_inverse
from .readout import QuadraticReadout, normalized_rmse
from .world import delay_features, exponential_features, lorenz


TOMO_NOISE_FRACTIONS = [0.0, 0.0001, 0.001, 0.01, 0.05]
TRAIN_SEEDS = [10, 11, 12, 13, 14, 15]
TEST_SEEDS = [100, 101, 102, 103]


def _plain(value):
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return value.item()
    return value


def _initial_for_seed(seed):
    rng = np.random.default_rng(seed)
    return np.array([
        rng.uniform(-15.0, 15.0),
        rng.uniform(-15.0, 15.0),
        rng.uniform(5.0, 35.0),
    ])


def _world(seed, burn, observe):
    return lorenz(_initial_for_seed(seed), burn + observe, 0.01)[burn:]


def _r2(truth, pred):
    denom = float(np.sum((truth - truth.mean()) ** 2))
    if denom <= 0:
        return 0.0
    return float(1.0 - np.sum((truth - pred) ** 2) / denom)


def _tomography(quick=False):
    diverse = make_cable(diverse=True)
    symmetric = make_cable(diverse=False)
    k_div = impulse_operator(diverse)
    k_sym = impulse_operator(symmetric)
    reference = k_div @ np.full(6, 0.5)
    reference_rms = float(np.sqrt(np.mean(reference ** 2)))
    seeds = [0] if quick else [0, 1, 2, 3, 4]
    scenes_per_seed = 12 if quick else 64
    fractions = [0.0, 0.001, 0.05] if quick else TOMO_NOISE_FRACTIONS

    architecture = {
        "diverse": {"operator": k_div, "summary": {}},
        "symmetric": {"operator": k_sym, "summary": {}},
    }

    for fraction in fractions:
        sigma = fraction * reference_rms
        per_arch = {name: [] for name in architecture}
        retained = {}
        singulars = {}
        for name, info in architecture.items():
            _, s, keep = svd_inverse(info["operator"], sigma)
            retained[name] = int(keep.sum())
            singulars[name] = s
        for seed in seeds:
            rng = np.random.default_rng(seed)
            amplitudes = rng.uniform(0.0, 1.0, size=(scenes_per_seed, 6))
            unit_noise = rng.normal(size=(scenes_per_seed, k_div.shape[0]))
            for name, info in architecture.items():
                k = info["operator"]
                observed = amplitudes @ k.T + sigma * unit_noise
                inverse, _, _ = svd_inverse(k, sigma)
                recovered = observed @ inverse.T
                reconstructed = recovered @ k.T
                per_arch[name].append({
                    "amplitude_rmse": float(np.sqrt(np.mean((recovered - amplitudes) ** 2))),
                    "measurement_residual": float(np.sqrt(np.mean((reconstructed - observed) ** 2)) / reference_rms),
                })
        for name, info in architecture.items():
            key = f"fraction_{fraction:g}"
            info["summary"][key] = {
                "sigma_mv": sigma,
                "amplitude_rmse": float(np.mean([x["amplitude_rmse"] for x in per_arch[name]])),
                "measurement_residual": float(np.mean([x["measurement_residual"] for x in per_arch[name]])),
                "retained_modes": retained[name],
                "singular_values": singulars[name],
            }

    fixed_sigma = 0.01
    fixed = {}
    rng = np.random.default_rng(12345)
    amplitudes = rng.uniform(0.0, 1.0, size=(scenes_per_seed, 6))
    unit_noise = rng.normal(size=(scenes_per_seed, k_div.shape[0]))
    for name, info in architecture.items():
        k = info["operator"]
        inv, s, keep = svd_inverse(k, fixed_sigma)
        observed = amplitudes @ k.T + fixed_sigma * unit_noise
        recovered = observed @ inv.T
        fixed[name] = {
            "amplitude_rmse": float(np.sqrt(np.mean((recovered - amplitudes) ** 2))),
            "retained_modes": int(keep.sum()),
            "singular_values": s,
        }

    snapshot_index = int(round(20.0 / 0.5)) - 1
    snapshot = {}
    rng = np.random.default_rng(777)
    amps = rng.uniform(0.0, 1.0, size=(scenes_per_seed, 6))
    for name, info in architecture.items():
        row = info["operator"][snapshot_index:snapshot_index + 1]
        inv, _, keep = svd_inverse(row, 0.0)
        obs = amps @ row.T
        rec = obs @ inv.T
        snapshot[name] = {
            "retained_modes": int(keep.sum()),
            "amplitude_rmse": float(np.sqrt(np.mean((rec - amps) ** 2))),
        }

    k_wrong_world = impulse_operator(make_cable(diverse=True, tau_scale=1.2))
    rng = np.random.default_rng(909)
    mismatch_amps = rng.uniform(0.0, 1.0, size=(scenes_per_seed, 6))
    mismatch_obs = mismatch_amps @ k_wrong_world.T
    mismatch_inv, _, _ = svd_inverse(k_div, 0.0)
    mismatch_rec = mismatch_obs @ mismatch_inv.T
    mismatch_fit = mismatch_rec @ k_div.T
    mismatch = {
        "amplitude_rmse": float(np.sqrt(np.mean((mismatch_rec - mismatch_amps) ** 2))),
        "measurement_residual_over_reference_rms": float(np.sqrt(np.mean((mismatch_fit - mismatch_obs) ** 2)) / reference_rms),
    }

    twin_a = k_sym[:, 0]
    twin_b = k_sym[:, 5]
    result = {
        "noise_reference_rms_mv": reference_rms,
        "noise_fractions": fractions,
        "fixed_noise_sigma_mv": fixed_sigma,
        "fixed_noise": fixed,
        "snapshot_20ms": snapshot,
        "model_mismatch_tau_scale": 1.2,
        "model_mismatch": mismatch,
        "symmetric_twin_trace_max_abs_diff_mv": float(np.max(np.abs(twin_a - twin_b))),
        "architectures": {},
    }
    for name, info in architecture.items():
        result["architectures"][name] = {
            "noise_reference_rms_mv": reference_rms,
            "scenes": info["summary"],
        }
    calibration = {}
    for name, k in [("diverse", k_div), ("symmetric", k_sym)]:
        u, s, vt = np.linalg.svd(k, full_matrices=False)
        calibration[name] = {"K": k, "U": u, "S": s, "Vt": vt}
    calibration["mismatch_true"] = {"K": k_wrong_world}
    return result, calibration, seeds


def _feature_bank(x_norm):
    current = 0.01 * x_norm[:, None] * np.ones((1, 6))
    diverse_cable = make_cable(diverse=True)
    symmetric_cable = make_cable(diverse=False)
    diverse = diverse_cable.encode(current, 1.0)
    symmetric = symmetric_cable.encode(current, 1.0)
    delays = delay_features(x_norm, size=19, stride=2)
    exp_bank = exponential_features(x_norm, dt_ms=1.0, size=19)
    soma = np.zeros_like(diverse)
    soma[:, 0] = diverse[:, 0]
    present = np.zeros_like(diverse)
    present[:, 0] = x_norm
    _, h = diverse_cable.transition(1.0)
    reset = current @ h.T
    return {
        "diverse_cable": diverse,
        "symmetric_cable": symmetric,
        "delay_19": delays,
        "exponential_19": exp_bank,
        "soma_only": soma,
        "current_only": present,
        "diverse_reset_each_sample": reset,
    }


def _same_present_example(states, x_mean, x_scale, yz_scale):
    x = (states[:, 0] - x_mean) / x_scale
    yz = states[:, 1:3]
    order = np.argsort(x)
    best = None
    left = 0
    for r in range(len(order)):
        while x[order[r]] - x[order[left]] > 0.02:
            left += 1
        for q in range(max(left, r - 80), r):
            i, j = order[q], order[r]
            sep = float(np.linalg.norm((yz[i] - yz[j]) / yz_scale))
            if sep > 1.0 and (best is None or sep > best[0]):
                best = (sep, int(i), int(j))
    if best is None:
        return {"found": False}
    sep, i, j = best
    return {
        "found": True,
        "indices": [i, j],
        "x_difference_training_std": float(abs(states[i, 0] - states[j, 0]) / x_scale),
        "hidden_yz_separation_training_std": sep,
        "state_a": states[i],
        "state_b": states[j],
    }


def _dynamics(quick=False):
    if quick:
        train_seeds, test_seeds = [10, 11], [100]
        burn, observe, discard = 300, 1200, 200
    else:
        train_seeds, test_seeds = TRAIN_SEEDS, TEST_SEEDS
        burn, observe, discard = 1000, 4000, 500
    stride = 4
    train_worlds = {seed: _world(seed, burn, observe) for seed in train_seeds}
    test_worlds = {seed: _world(seed, burn, observe) for seed in test_seeds}
    all_train_x = np.concatenate([s[:, 0] for s in train_worlds.values()])
    x_mean = float(all_train_x.mean())
    x_scale = float(all_train_x.std())
    sample_idx = np.arange(discard, observe, stride)
    train_targets_phys = np.concatenate([s[sample_idx, 1:3] for s in train_worlds.values()], axis=0)
    target_mean = train_targets_phys.mean(axis=0)
    target_scale = train_targets_phys.std(axis=0)
    target_norm = (train_targets_phys - target_mean) / target_scale
    noise_levels = [0.0, 0.02]
    results = {}
    demo = {}
    noise0_train_features = None
    noise0_test_features = None

    for noise_level in noise_levels:
        train_by_arm = {}
        for seed in train_seeds:
            state = train_worlds[seed]
            rng = np.random.default_rng(200000 + seed + int(noise_level * 10000))
            noisy_x = state[:, 0] + noise_level * x_scale * rng.normal(size=observe)
            x_norm = (noisy_x - x_mean) / x_scale
            bank = _feature_bank(x_norm)
            for arm, features in bank.items():
                train_by_arm.setdefault(arm, []).append(features[sample_idx])
        train_by_arm = {arm: np.concatenate(parts, axis=0) for arm, parts in train_by_arm.items()}
        models = {arm: QuadraticReadout(0.001).fit(features, target_norm) for arm, features in train_by_arm.items()}

        arm_metrics = {arm: [] for arm in models}
        first_demo = None
        test_features_cache = {}
        for seed in test_seeds:
            state = test_worlds[seed]
            rng = np.random.default_rng(200000 + seed + int(noise_level * 10000))
            noisy_x = state[:, 0] + noise_level * x_scale * rng.normal(size=observe)
            x_norm = (noisy_x - x_mean) / x_scale
            bank = _feature_bank(x_norm)
            for arm, model in models.items():
                feat = bank[arm][sample_idx]
                pred_norm = model.predict(feat)
                pred = pred_norm * target_scale + target_mean
                truth = state[sample_idx, 1:3]
                y_nrmse = normalized_rmse(truth[:, 0], pred[:, 0], target_scale[0])
                z_nrmse = normalized_rmse(truth[:, 1], pred[:, 1], target_scale[1])
                metric = {
                    "seed": seed,
                    "y_nrmse": y_nrmse,
                    "z_nrmse": z_nrmse,
                    "mean_nrmse": float((y_nrmse + z_nrmse) / 2.0),
                    "y_r2": _r2(truth[:, 0], pred[:, 0]),
                    "z_r2": _r2(truth[:, 1], pred[:, 1]),
                }
                arm_metrics[arm].append(metric)
                if seed == test_seeds[0] and noise_level == 0.0:
                    test_features_cache[arm] = feat
                    if arm == "diverse_cable":
                        take = np.linspace(0, len(sample_idx) - 1, min(250, len(sample_idx)), dtype=int)
                        first_demo = {
                            "time_index": sample_idx[take],
                            "x": state[sample_idx[take], 0],
                            "truth_y": truth[take, 0],
                            "truth_z": truth[take, 1],
                            "pred_y": pred[take, 0],
                            "pred_z": pred[take, 1],
                        }
        key = f"noise_{noise_level:g}"
        results[key] = {}
        for arm, rows in arm_metrics.items():
            results[key][arm] = {
                "mean_nrmse": float(np.mean([r["mean_nrmse"] for r in rows])),
                "mean_r2": float(np.mean([(r["y_r2"] + r["z_r2"]) / 2.0 for r in rows])),
                "per_trajectory": rows,
            }
        if noise_level == 0.0:
            demo = first_demo
            noise0_train_features = train_by_arm["diverse_cable"]
            noise0_test_features = test_features_cache["diverse_cable"]

    train_hidden_parts = []
    for seed in train_seeds:
        rng = np.random.default_rng(500000 + seed)
        train_hidden_parts.append(rng.normal(size=observe)[sample_idx])
    train_hidden = np.concatenate(train_hidden_parts)
    hidden_mean = float(train_hidden.mean())
    hidden_scale = float(train_hidden.std())
    hidden_model = QuadraticReadout(0.001).fit(noise0_train_features, ((train_hidden - hidden_mean) / hidden_scale)[:, None])
    hidden_metrics = []
    for seed in test_seeds:
        state = test_worlds[seed]
        x_norm = (state[:, 0] - x_mean) / x_scale
        feat = _feature_bank(x_norm)["diverse_cable"][sample_idx]
        rng = np.random.default_rng(500000 + seed)
        truth = rng.normal(size=observe)[sample_idx]
        pred = hidden_model.predict(feat)[:, 0] * hidden_scale + hidden_mean
        hidden_metrics.append({
            "seed": seed,
            "nrmse": normalized_rmse(truth, pred, hidden_scale),
            "r2": _r2(truth, pred),
        })
    independent = {
        "nrmse": float(np.mean([m["nrmse"] for m in hidden_metrics])),
        "r2": float(np.mean([m["r2"] for m in hidden_metrics])),
        "per_trajectory": hidden_metrics,
        "note": "Independent Gaussian label never enters the x observation or cable.",
    }
    same_present = _same_present_example(test_worlds[test_seeds[0]][discard:], x_mean, x_scale, target_scale)
    results["independent_hidden"] = independent
    results["same_present_example"] = same_present
    results["training_scales"] = {
        "x_mean": x_mean,
        "x_std": x_scale,
        "target_yz_mean": target_mean,
        "target_yz_std": target_scale,
    }
    return results, demo, train_seeds, test_seeds


def _source_hashes():
    package = Path(__file__).resolve().parent
    names = ["cable.py", "inverse.py", "world.py", "readout.py", "experiment.py"]
    return {name: hashlib.sha256((package / name).read_bytes()).hexdigest() for name in names}


def run_experiment(output_dir, site_dir, quick=False):
    output_dir = Path(output_dir)
    site_dir = Path(site_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    site_dir.mkdir(parents=True, exist_ok=True)
    tomography, calibration, tomography_seeds = _tomography(quick=quick)
    dynamics, demo, train_seeds, test_seeds = _dynamics(quick=quick)
    receipt = {
        "title": "Dendritic lens experiment receipt",
        "quick": bool(quick),
        "provenance": {
            "tomography_seeds": tomography_seeds,
            "dynamics_train_seeds": train_seeds,
            "dynamics_test_seeds": test_seeds,
            "observer_inputs": ["noisy_x"],
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "reproduce": "OPENBLAS_NUM_THREADS=1 python scripts/run_experiment.py",
            "source_sha256": _source_hashes(),
        },
        "tomography": tomography,
        "dynamics": dynamics,
    }
    plain_receipt = _plain(receipt)
    (output_dir / "receipt.json").write_text(json.dumps(plain_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def pack_f32(array):
        value = np.asarray(array, dtype="<f4")
        return {
            "shape": list(value.shape),
            "b64": base64.b64encode(value.tobytes()).decode("ascii"),
        }

    packed_calibration = {
        "diverse": {key: pack_f32(calibration["diverse"][key]) for key in ("U", "S", "Vt")},
        "symmetric": {key: pack_f32(calibration["symmetric"][key]) for key in ("U", "S", "Vt")},
        "mismatch_true": {"K": pack_f32(calibration["mismatch_true"]["K"])},
    }
    packed_demo = {key: pack_f32(value) for key, value in demo.items()}
    site_summary = {
        "noise_0": {
            name: {
                "mean_nrmse": dynamics["noise_0"][name]["mean_nrmse"],
                "mean_r2": dynamics["noise_0"][name]["mean_r2"],
            }
            for name in ("delay_19", "diverse_cable", "exponential_19", "current_only", "diverse_reset_each_sample")
        },
        "same_present_example": dynamics["same_present_example"],
        "independent_hidden": {
            "nrmse": dynamics["independent_hidden"]["nrmse"],
            "r2": dynamics["independent_hidden"]["r2"],
        },
    }
    site_tomography = {
        "noise_reference_rms_mv": tomography["noise_reference_rms_mv"],
        "architectures": {
            "diverse": {
                "scenes": {
                    "fraction_0": {
                        "amplitude_rmse": tomography["architectures"]["diverse"]["scenes"]["fraction_0"]["amplitude_rmse"]
                    }
                }
            }
        },
    }
    meta = {
        "tomography": site_tomography,
        "dynamics_summary": site_summary,
        "provenance": {
            "tomography_seeds": plain_receipt["provenance"]["tomography_seeds"],
            "dynamics_train_seeds": plain_receipt["provenance"]["dynamics_train_seeds"],
            "dynamics_test_seeds": plain_receipt["provenance"]["dynamics_test_seeds"],
            "observer_inputs": plain_receipt["provenance"]["observer_inputs"],
        },
    }
    decoder = (
        "(function(){\n"
        "const decodeF32=(p)=>{const raw=atob(p.b64),buf=new ArrayBuffer(raw.length),bytes=new Uint8Array(buf);"
        "for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);const view=new DataView(buf),flat=new Array(raw.length/4);"
        "for(let i=0;i<flat.length;i++)flat[i]=view.getFloat32(i*4,true);if(p.shape.length===1)return flat;"
        "if(p.shape.length===2){const [r,c]=p.shape,out=new Array(r);for(let i=0;i<r;i++)out[i]=flat.slice(i*c,(i+1)*c);return out;}"
        "throw new Error(\"unsupported packed shape\");};\n"
        "const deriveK=(c)=>{const m=c.U.length,q=c.S.length,n=c.Vt[0].length;c.K=Array.from({length:m},()=>Array(n).fill(0));"
        "for(let r=0;r<m;r++)for(let j=0;j<n;j++){let z=0;for(let k=0;k<q;k++)z+=c.U[r][k]*c.S[k]*c.Vt[k][j];c.K[r][j]=z;}return c;};\n"
        "const packed=window.__DL_PACKED;\nconst meta=__META__;\nconst calibration={};\n"
        "for(const [name,parts] of Object.entries(packed.calibration)){calibration[name]={};"
        "for(const [key,value] of Object.entries(parts))calibration[name][key]=decodeF32(value);if(calibration[name].S)deriveK(calibration[name]);}\n"
        "const example={};for(const [key,value] of Object.entries(packed.demo))example[key]=decodeF32(value);\n"
        "window.DENDRITIC_LENS_DATA={calibration,tomography:meta.tomography,dynamics:{summary:meta.dynamics_summary,example},provenance:meta.provenance};\n"
        "})();\n"
    )
    prefix = "window.__DL_PACKED=window.__DL_PACKED||{calibration:{},demo:{}};\n"
    shards = {
        "data-diverse.js": prefix + "window.__DL_PACKED.calibration.diverse=" + json.dumps(packed_calibration["diverse"], separators=(",", ":")) + ";\n",
        "data-symmetric.js": prefix + "window.__DL_PACKED.calibration.symmetric=" + json.dumps(packed_calibration["symmetric"], separators=(",", ":")) + ";\n",
        "data-mismatch.js": prefix + "window.__DL_PACKED.calibration.mismatch_true=" + json.dumps(packed_calibration["mismatch_true"], separators=(",", ":")) + ";\n",
        "data-demo.js": prefix + "window.__DL_PACKED.demo=" + json.dumps(packed_demo, separators=(",", ":")) + ";\n",
    }
    for name, content in shards.items():
        (site_dir / name).write_text(content, encoding="utf-8")
    script = decoder.replace("__META__", json.dumps(_plain(meta), separators=(",", ":")))
    (site_dir / "data.js").write_text(script, encoding="utf-8")
    return plain_receipt
