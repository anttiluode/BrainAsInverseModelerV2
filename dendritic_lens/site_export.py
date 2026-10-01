"""Compact the full browser export without changing scientific receipt data."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import numpy as np


def _read_assignment(path, marker):
    text = Path(path).read_text(encoding="utf-8")
    start = text.index(marker) + len(marker)
    end = text.index(";", start)
    return json.loads(text[start:end])


def _decode_f32(packed):
    raw = base64.b64decode(packed["b64"])
    return np.frombuffer(raw, dtype="<f4").reshape(packed["shape"])


def _pack_f32(array):
    value = np.asarray(array, dtype="<f4")
    return {
        "shape": list(value.shape),
        "b64": base64.b64encode(value.tobytes()).decode("ascii"),
    }


def _derive_k(parts):
    if "K" in parts:
        return _decode_f32(parts["K"])
    u = _decode_f32(parts["U"])
    s = _decode_f32(parts["S"])
    vt = _decode_f32(parts["Vt"])
    return (u * s[None, :]) @ vt


def _read_meta(path):
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(r"const meta=(.*?);\nconst calibration=", text, re.S)
    if not match:
        raise ValueError("Could not locate generated site metadata.")
    return json.loads(match.group(1))


def compact_site(site_dir):
    """Replace the full generated browser bundle with a compact 2 ms view."""
    site_dir = Path(site_dir)
    diverse = _read_assignment(site_dir / "data-diverse.js", "window.__DL_PACKED.calibration.diverse=")
    symmetric = _read_assignment(site_dir / "data-symmetric.js", "window.__DL_PACKED.calibration.symmetric=")
    mismatch = _read_assignment(site_dir / "data-mismatch.js", "window.__DL_PACKED.calibration.mismatch_true=")
    demo = _read_assignment(site_dir / "data-demo.js", "window.__DL_PACKED.demo=")
    meta = _read_meta(site_dir / "data.js")

    demo_rows = slice(3, None, 4)  # 2, 4, ..., 200 ms from 0.5 ms source samples.
    diverse_k = _derive_k(diverse)[demo_rows]
    symmetric_k = _derive_k(symmetric)[demo_rows]
    symmetric_trace = symmetric_k.mean(axis=1, keepdims=True)
    symmetric_k = np.repeat(symmetric_trace, symmetric_k.shape[1], axis=1)
    packed_calibration = {
        "diverse": {"K": _pack_f32(diverse_k)},
        "symmetric": {"K": _pack_f32(symmetric_k)},
        "mismatch_true": {"K": _pack_f32(_derive_k(mismatch)[demo_rows])},
    }
    decoded_demo = {key: _decode_f32(value) for key, value in demo.items()}
    demo_length = len(next(iter(decoded_demo.values()))) if decoded_demo else 0
    take = np.linspace(0, demo_length - 1, min(125, demo_length), dtype=int) if demo_length else np.array([], dtype=int)
    packed_demo = {key: _pack_f32(value[take]) for key, value in decoded_demo.items()}
    meta["tomography"]["demo_sample_dt_ms"] = 2.0

    prefix = "window.__DL_PACKED=window.__DL_PACKED||{calibration:{},demo:{}};\n"
    shards = {
        "data-diverse.js": prefix + "window.__DL_PACKED.calibration.diverse=" + json.dumps(packed_calibration["diverse"], separators=(",", ":")) + ";\n",
        "data-symmetric.js": prefix + "window.__DL_PACKED.calibration.symmetric=" + json.dumps(packed_calibration["symmetric"], separators=(",", ":")) + ";\n",
        "data-mismatch.js": prefix + "window.__DL_PACKED.calibration.mismatch_true=" + json.dumps(packed_calibration["mismatch_true"], separators=(",", ":")) + ";\n",
        "data-demo.js": prefix + "window.__DL_PACKED.demo=" + json.dumps(packed_demo, separators=(",", ":")) + ";\n",
    }
    for name, content in shards.items():
        (site_dir / name).write_text(content, encoding="utf-8")

    decoder = (
        "(function(){\n"
        "const decodeF32=(p)=>{const raw=atob(p.b64),buf=new ArrayBuffer(raw.length),bytes=new Uint8Array(buf);"
        "for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);const view=new DataView(buf),flat=new Array(raw.length/4);"
        "for(let i=0;i<flat.length;i++)flat[i]=view.getFloat32(i*4,true);if(p.shape.length===1)return flat;"
        "if(p.shape.length===2){const [r,c]=p.shape,out=new Array(r);for(let i=0;i<r;i++)out[i]=flat.slice(i*c,(i+1)*c);return out;}"
        "throw new Error(\"unsupported packed shape\");};\n"
        "const packed=window.__DL_PACKED;\nconst meta=__META__;\nconst calibration={};\n"
        "for(const [name,parts] of Object.entries(packed.calibration)){calibration[name]={};"
        "for(const [key,value] of Object.entries(parts))calibration[name][key]=decodeF32(value);}\n"
        "const example={};for(const [key,value] of Object.entries(packed.demo))example[key]=decodeF32(value);\n"
        "window.DENDRITIC_LENS_DATA={calibration,tomography:meta.tomography,dynamics:{summary:meta.dynamics_summary,example},provenance:meta.provenance};\n"
        "})();\n"
    )
    (site_dir / "data.js").write_text(
        decoder.replace("__META__", json.dumps(meta, separators=(",", ":"))),
        encoding="utf-8",
    )
