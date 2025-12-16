"""
Utility functions and constants.
"""
from random import uniform

HOST: str = "127.0.0.1"
PORT: int = 65432
CHUNK_SIZE: int = 40_960
DEFAULT_POINTS: int = 1_000_000
DEFAULT_THREADS: int = 4
DEFAULT_DIMS: int = 2
DEFAULT_MARGINS: tuple[int, int] = 0, 10_000

class Point:
    """Represents a point in N-dimensional space."""
    __slots__ = ('coords',) # reduces memory by not making Python creata a dynamic dictionary for every object
    def __init__(self, *args: list[float]):
        """Initializes a Point with N coordinates."""
        self.coords: tuple = tuple(args)

    def __len__(self) -> int:
        """Returns the number of dimensions."""
        return len(self.coords)

    def __getitem__(self, index: int) -> float:
        """Returns the coordinate at the specified index."""
        return self.coords[index]

    def __repr__(self) -> str:
        """Returns a string representation of the Point."""
        return f"<{", ".join([ str(c).rjust(5, " ") for c in self.coords])}>"

    def __eq__(self, other: object) -> bool:
        """Checks if two Points are equal."""
        if not isinstance(other, Point):
            return False
        return self.coords == other.coords

    def __hash__(self) -> int:
        """Returns the hash of the Point."""
        return hash(self.coords)

def get_distance(p1: Point, p2: Point, p3: Point) -> float:
    """Calculates a pseudo-distance (cross product) of p3 from the line p1-p2."""
    return abs((p3[1] - p1[1]) * (p2[0] - p1[0]) - (p2[1] - p1[1]) * (p3[0] - p1[0]))

def find_side(p1: Point, p2: Point, p3: Point) -> int:
    """Determines which side of the line p1-p2 the point p3 lies on."""
    val: float = (p3[1] - p1[1]) * (p2[0] - p1[0]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
    return int(val > 0) - int(val < 0)

def generate_points(n: int, dims: int = DEFAULT_DIMS, min_val: int = DEFAULT_MARGINS[0], max_val: int = DEFAULT_MARGINS[1]) -> list[Point]:
    """Generates a list of N random points with specified dimensions."""
    print(f"[Generate] {n} random points with {dims} dimensions.")
    return [Point(*[round(uniform(min_val, max_val), 2) for _ in range(dims)]) for _ in range(n)]
