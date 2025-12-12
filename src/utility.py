from random import randint
from json import JSONEncoder

class Point:
    def __init__(self, *args: list[float]):
        self.coords: tuple = tuple(args)

    def __len__(self) -> int:
        return len(self.coords)

    def __getitem__(self, index: int) -> float:
        return self.coords[index]

    def __repr__(self) -> str:
        return f"<{', '.join(map(str, self.coords))}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.coords == other.coords

    def __hash__(self) -> int:
        return hash(self.coords)

class JsonEncodePoint(JSONEncoder):
    def default(self, obj: any) -> any:
        if isinstance(obj, Point):
            return {'point' : obj.coords}
        return super().default(obj)

def decode_point(obj: any) -> Point:
    if "point" in obj:
        return Point(*obj['point'])
    return obj

def generate_points(n: int, dims: int = 2, min_val: int = 0, max_val: int = 5000) -> list[Point]:
    print(f"[Generate] Generating {n} random points in range [{min_val}, {max_val}] with {dims} dimensions.")
    return [Point(*[randint(min_val, max_val) for _ in range(dims)]) for _ in range(n)]