"""
Utility functions and constants.
"""
import numpy as np

HOST: str = "127.0.0.1"
PORT: int = 65432
CHUNK_SIZE: int = 40_960
DEFAULT_POINTS: int = 1_000_000
DEFAULT_THREADS: int = 4
DEFAULT_DIMS: int = 2
DEFAULT_MARGINS: tuple[int, int] = -100_000, 100_000

type CArray = np.ndarray
type NPoint = CArray[np.float64]

def generate_points(n: int, dims: int = DEFAULT_DIMS, min_val: int = DEFAULT_MARGINS[0], max_val: int = DEFAULT_MARGINS[1]) -> CArray[NPoint]:
    """Generates a list of N random points with specified dimensions."""
    print(f"[Generate] {n} random points with {dims} dimensions.")
    rng: np.random.Generator = np.random.default_rng()
    pts: CArray[NPoint] = rng.uniform(min_val, max_val, (n, dims))
    return np.round(pts, 2)
