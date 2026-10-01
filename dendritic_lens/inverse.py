"""Truncated linear inverse; unresolved components remain minimum-norm estimates."""

import numpy as np


def svd_inverse(operator, sigma=0.0):
    operator = np.asarray(operator, dtype=float)
    if operator.ndim != 2 or 0 in operator.shape or not np.all(np.isfinite(operator)):
        raise ValueError("The observation operator must be a finite nonempty matrix.")
    if not np.isfinite(sigma) or sigma < 0:
        raise ValueError("Noise standard deviation must be finite and nonnegative.")
    u, singular, vt = np.linalg.svd(operator, full_matrices=False)
    threshold = max(3.0 * sigma, singular[0] * 1e-10)
    keep = singular > threshold
    reciprocal = np.zeros_like(singular)
    reciprocal[keep] = 1.0 / singular[keep]
    inverse = (vt.T * reciprocal) @ u.T
    return inverse, singular, keep
