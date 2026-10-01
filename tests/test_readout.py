import unittest
import numpy as np
from dendritic_lens.readout import QuadraticReadout, normalized_rmse

class ReadoutTests(unittest.TestCase):
    def test_quadratic_readout_generalizes_exact_quadratic(self):
        rng=np.random.default_rng(2); x=rng.normal(size=(240,3)); y=(1.2+2*x[:,0]-0.5*x[:,1]+0.75*x[:,0]*x[:,2]+0.2*x[:,1]**2)[:,None]
        model=QuadraticReadout(ridge_factor=1e-10).fit(x[:180],y[:180]); pred=model.predict(x[180:]); self.assertLess(np.sqrt(np.mean((pred-y[180:])**2)),1e-6)
    def test_feature_normalization_is_frozen_after_fit(self):
        train=np.array([[0.,1.],[2.,3.],[4.,5.]]); target=np.array([[0.],[1.],[2.]])
        model=QuadraticReadout().fit(train,target); mean=model.feature_mean_.copy(); scale=model.feature_scale_.copy(); model.predict(np.array([[1e9,-1e9]])); np.testing.assert_array_equal(model.feature_mean_,mean); np.testing.assert_array_equal(model.feature_scale_,scale)
    def test_constant_features_remain_finite(self):
        x=np.ones((20,4)); y=np.arange(20.0)[:,None]; model=QuadraticReadout().fit(x,y); pred=model.predict(x); self.assertTrue(np.isfinite(pred).all()); self.assertTrue(np.isfinite(model.coef_).all())
    def test_normalized_rmse(self):
        self.assertAlmostEqual(normalized_rmse(np.array([0.,2.]),np.array([0.,0.]),2.0),np.sqrt(2)/2)
        with self.assertRaises(ValueError): normalized_rmse([1],[1],0.0)
