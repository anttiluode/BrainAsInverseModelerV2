import json
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

from dendritic_lens.experiment import run_experiment
from dendritic_lens.site_export import compact_site


class ExperimentTests(unittest.TestCase):
    def test_seeded_quick_receipt_preserves_blind_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); out=root/'results'; site=root/'site'
            receipt=run_experiment(out,site,quick=True)
            compact_site(site)
            self.assertEqual(receipt['provenance']['tomography_seeds'],[0])
            self.assertEqual(receipt['provenance']['observer_inputs'],['noisy_x'])
            self.assertEqual(receipt['tomography']['noise_reference_rms_mv'],receipt['tomography']['architectures']['diverse']['noise_reference_rms_mv'])
            self.assertEqual(receipt['tomography']['noise_reference_rms_mv'],receipt['tomography']['architectures']['symmetric']['noise_reference_rms_mv'])
            self.assertLessEqual(receipt['tomography']['symmetric_twin_trace_max_abs_diff_mv'],1e-12)
            self.assertIn('independent_hidden',receipt['dynamics'])
            self.assertTrue(np.isfinite(receipt['dynamics']['independent_hidden']['nrmse']))
            disk=json.loads((out/'receipt.json').read_text())
            self.assertEqual(disk['provenance'],receipt['provenance'])
            bundle_names=['data-diverse.js','data-symmetric.js','data-mismatch.js','data-demo.js','data.js']
            self.assertTrue(all((site/name).exists() for name in bundle_names))
            bundle=[(site/name).read_text() for name in bundle_names]
            data=''.join(bundle)
            self.assertIn('DENDRITIC_LENS_DATA',data)
            self.assertIn('mismatch_true',data)
            self.assertLess(sum(len(part.encode('utf-8')) for part in bundle),20_000)
            self.assertTrue(all(len(part.encode('utf-8'))<20_000 for part in bundle))
            self.assertNotIn('observer_y',data)
            self.assertNotIn('observer_z',data)


    def test_cli_runner_imports_package_from_repo_root(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            proc=subprocess.run([
                sys.executable, 'scripts/run_experiment.py', '--quick',
                '--output-dir', str(tmp/'results'), '--site-dir', str(tmp/'site')
            ], cwd=root, capture_output=True, text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertIn('wrote',proc.stdout)
            self.assertTrue((tmp/'results'/'receipt.json').exists())
            self.assertTrue((tmp/'site'/'data.js').exists())
            bundle_names=['data-diverse.js','data-symmetric.js','data-mismatch.js','data-demo.js','data.js']
            self.assertLess(sum((tmp/'site'/name).stat().st_size for name in bundle_names),20_000)

    def test_quick_run_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra=run_experiment(Path(a)/'results',Path(a)/'site',quick=True)
            rb=run_experiment(Path(b)/'results',Path(b)/'site',quick=True)
            self.assertEqual(ra['tomography']['architectures']['diverse']['scenes'],rb['tomography']['architectures']['diverse']['scenes'])
            self.assertEqual(ra['dynamics']['noise_0']['diverse_cable']['mean_nrmse'],rb['dynamics']['noise_0']['diverse_cable']['mean_nrmse'])

if __name__=='__main__':
    unittest.main()
