"""
Utility functions and constants.
"""
import numpy  as     np
from   socket import socket

HOST: str = "127.0.0.1"
PORT: int = 65432
CHUNK_SIZE: int = 4096 # Standard page size
DEFAULT_POINTS: int = 1_000_000
DEFAULT_THREADS: int = 4
DEFAULT_DIMS: int = 2
DEFAULT_MARGINS: tuple[int, int] = -100_000, 100_000
SEED: int | None = None #9999879

type CArray = np.ndarray
type NPoint = CArray[np.float64]

def recv_exact(sock: socket, size: int) -> bytes | None:
    """Receives exactly `size` bytes from the socket connection."""
    buf: bytes = b''
    while len(buf) < size:
        pack: bytes | None = sock.recv(min(size - len(buf), CHUNK_SIZE))
        if not pack:
            return None
        buf += pack
    return buf

def generate_points(n: int, dims: int = DEFAULT_DIMS, min_val: int = DEFAULT_MARGINS[0], max_val: int = DEFAULT_MARGINS[1], seed: int | None = None) -> CArray[NPoint]:
    """Generates a list of N random points with specified dimensions."""
    print(f"[Generate] {n} random points with {dims} dimensions.")
    rng: np.random.Generator = np.random.default_rng(seed)
    pts: CArray[NPoint] = rng.uniform(min_val, max_val, (n, dims))
    return np.round(pts, 2)
