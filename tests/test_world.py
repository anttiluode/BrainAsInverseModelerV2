import unittest
import numpy as np
from dendritic_lens.world import lorenz, delay_features, exponential_features

class WorldTests(unittest.TestCase):
    def test_lorenz_one_rk4_step_matches_reference(self):
        got=lorenz(np.array([1.0,1.0,1.0]),steps=1,dt=0.01)
        np.testing.assert_allclose(got[0],[1.01256719,1.25991780,0.98489097],rtol=1e-7,atol=1e-8)
    def test_delay_features_are_causal_and_use_declared_stride(self):
        x=np.arange(8.0); f=delay_features(x,size=3,stride=2)
        np.testing.assert_array_equal(f[6],[6.0,4.0,2.0])
        changed=x.copy(); changed[7]=999.0
        np.testing.assert_array_equal(f[:7],delay_features(changed,size=3,stride=2)[:7])
    def test_exponential_features_are_causal(self):
        x=np.zeros(12); x[8:]=1.0
        before=exponential_features(x,dt_ms=1.0,size=5)
        changed=x.copy(); changed[10:]=4.0
        after=exponential_features(changed,dt_ms=1.0,size=5)
        np.testing.assert_array_equal(before[:10],after[:10])
        self.assertTrue(np.all(np.diff(before[8:,0])>0))
    def test_invalid_world_inputs_rejected(self):
        with self.assertRaises(ValueError): lorenz([1,2],3)
        with self.assertRaises(ValueError): delay_features([1,2,3],0,1)
        with self.assertRaises(ValueError): exponential_features([1,2,3],0.0,3)
