import unittest

import numpy as np

from dendritic_lens.cable import Cable, impulse_operator, make_cable


class CableTests(unittest.TestCase):
    def test_single_compartment_matches_analytic_rc_response(self):
        cable = Cable(np.array([2.0]), np.array([[0.5]]), [0])
        history = cable.encode(np.full((4, 1), 3.0), dt_ms=2.0)
        expected = 6.0 * (1.0 - np.exp(-0.5 * np.arange(1, 5)))
        np.testing.assert_allclose(history[:, 0], expected, atol=1e-12)

    def test_axial_current_conserves_total_charge(self):
        cable = Cable(np.array([2.0, 1.0]), np.array([[0.4, -0.4], [-0.4, 0.4]]), [0])
        f, _ = cable.transition(3.0)
        v = np.array([2.0, -1.0])
        self.assertAlmostEqual(cable.capacitance @ (f @ v), 3.0, places=12)

    def test_passive_cable_cannot_create_energy(self):
        cable = make_cable()
        f, _ = cable.transition(1.0)
        v = np.random.default_rng(1).normal(size=19)
        energy = lambda z: float(np.sum(cable.capacitance * z * z))
        for _ in range(30):
            after = f @ v
            self.assertLess(energy(after), energy(v))
            v = after

    def test_future_input_does_not_change_earlier_voltage(self):
        cable = make_cable()
        currents = np.zeros((40, 6))
        changed = currents.copy()
        changed[25:, 2] = 1.0
        before = cable.encode(currents, 0.5)
        after = cable.encode(changed, 0.5)
        np.testing.assert_array_equal(before[:25], after[:25])
        self.assertGreater(np.linalg.norm(after[25:]), 0)

    def test_symmetric_branches_create_indistinguishable_inputs(self):
        k = impulse_operator(make_cable(diverse=False))
        np.testing.assert_allclose(k[:, 0], k[:, 5], atol=1e-14)
        np.testing.assert_allclose(k @ [1, 0, 0, 0, 0, 0], k @ [0, 1, 0, 0, 0, 0], atol=1e-14)

    def test_impulse_operator_matches_actual_superposition(self):
        cable = make_cable()
        k = impulse_operator(cable)
        amplitudes = np.array([0.1, 0.7, 0.2, 0.9, 0.5, 0.3])
        currents = np.zeros((400, 6))
        currents[:2] = 0.01 * amplitudes
        observed = cable.encode(currents, 0.5)[:, 0]
        np.testing.assert_allclose(k @ amplitudes, observed, atol=1e-13)

    def test_invalid_circuit_and_time_are_rejected(self):
        with self.assertRaises(ValueError):
            Cable(np.array([0.0]), np.array([[0.5]]), [0])
        with self.assertRaises(ValueError):
            Cable(np.array([1.0]), np.array([[-0.5]]), [0])
        with self.assertRaises(ValueError):
            make_cable().transition(0.0)
        with self.assertRaises(ValueError):
            make_cable().encode(np.zeros((2, 5)), 1.0)
        with self.assertRaises(ValueError):
            impulse_operator(make_cable(), dt_ms=0.3)


if __name__ == "__main__":
    unittest.main()
