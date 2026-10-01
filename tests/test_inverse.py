import unittest

import numpy as np

from dendritic_lens.inverse import svd_inverse


class InverseTests(unittest.TestCase):
    def test_noiseless_full_rank_recovers_hidden_inputs(self):
        k = np.array([[2.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
        inverse, singular, mask = svd_inverse(k, 0.0)
        np.testing.assert_allclose(inverse @ [0.6, 0.8, 0.0], [0.3, 0.8])
        np.testing.assert_allclose(singular, [2.0, 1.0])
        self.assertEqual(mask.tolist(), [True, True])

    def test_noise_discards_weak_measurement_mode(self):
        k = np.array([[2.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
        inverse, _, mask = svd_inverse(k, 0.4)
        np.testing.assert_allclose(inverse @ [0.6, 0.8, 0.0], [0.3, 0.0])
        self.assertEqual(mask.tolist(), [True, False])

    def test_rank_one_returns_minimum_norm_without_inventing_information(self):
        k = np.array([[1.0, 1.0], [2.0, 2.0]])
        inverse, _, mask = svd_inverse(k, 0.0)
        np.testing.assert_allclose(inverse @ [1.0, 2.0], [0.5, 0.5], atol=1e-12)
        self.assertEqual(int(mask.sum()), 1)

    def test_zero_operator_and_large_noise_are_finite(self):
        for k, sigma in [(np.zeros((4, 2)), 0.0), (np.eye(2), 100.0)]:
            inverse, _, mask = svd_inverse(k, sigma)
            np.testing.assert_array_equal(inverse, np.zeros_like(inverse))
            self.assertFalse(mask.any())

    def test_invalid_noise_or_observation_operator_is_rejected(self):
        for sigma in [-0.1, float("nan")]:
            with self.assertRaises(ValueError):
                svd_inverse(np.eye(2), sigma)
        with self.assertRaises(ValueError):
            svd_inverse(np.array([[float("inf")]]), 0.1)


if __name__ == "__main__":
    unittest.main()
