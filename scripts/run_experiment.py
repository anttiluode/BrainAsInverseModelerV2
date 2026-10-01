import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dendritic_lens.experiment import run_experiment
from dendritic_lens.site_export import compact_site


def main():
    parser = argparse.ArgumentParser(description="Run the frozen dendritic-lens experiment.")
    parser.add_argument("--quick", action="store_true", help="Run the deterministic reduced integration-check schedule.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results", help="Receipt output directory.")
    parser.add_argument("--site-dir", type=Path, default=ROOT / "site", help="Generated site-data directory.")
    args = parser.parse_args()
    receipt = run_experiment(args.output_dir, args.site_dir, quick=args.quick)
    compact_site(args.site_dir)
    print(f"wrote {args.output_dir / 'receipt.json'} and {args.site_dir / 'data.js'}")
    print("diverse tomography zero-noise RMSE:", receipt["tomography"]["architectures"]["diverse"]["scenes"]["fraction_0"]["amplitude_rmse"])
    print("symmetric tomography zero-noise RMSE:", receipt["tomography"]["architectures"]["symmetric"]["scenes"]["fraction_0"]["amplitude_rmse"])
    print("diverse hidden-state NRMSE:", receipt["dynamics"]["noise_0"]["diverse_cable"]["mean_nrmse"])
    print("delay hidden-state NRMSE:", receipt["dynamics"]["noise_0"]["delay_19"]["mean_nrmse"])


if __name__ == "__main__":
    main()
