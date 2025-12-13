"""
QuickHull algorithm implementation for Convex Hull construction.
"""
from time       import time
from typing     import Any

from threadpool import ThreadPool, Future
from utility    import Point, find_side, get_distance

def quickhull_step(points: list[Point], p1: Point, p2: Point, side: int) -> list[Point]:
    """Recursively computes the convex hull for points on one side of the line p1-p2."""
    if not points:
        return []

    cand: list[Point] = [p for p in points if find_side(p1, p2, p) == side]

    if not cand:
        return [p1, p2]

    p_max: Point = max(cand, key=lambda p: get_distance(p1, p2, p))
    # Target sides
    ts1: int = -find_side(p_max, p1, p2)
    ts2: int = -find_side(p_max, p2, p1)

    s1: list[Point] = [p for p in cand if p != p_max and find_side(p_max, p1, p) == ts1]
    s2: list[Point] = [p for p in cand if p != p_max and find_side(p_max, p2, p) == ts2]

    res1: list[Point] = quickhull_step(s1, p1, p_max, ts1)
    res2: list[Point] = quickhull_step(s2, p_max, p2, ts2)
    
    return res1 + res2 + [p_max]

def partition(points: list[Point], p1: Point, p2: Point, side: int) -> tuple[Point, tuple[list[Point], Point, Point, int], tuple[list[Point], Point, Point, int]] | None:
    """Partitions points for a single QuickHull step, returning the max point and sub-tasks."""
    cand: list[Point] = [p for p in points if find_side(p1, p2, p) == side]
    if not cand:
        return None
    
    p_max: Point = max(cand, key=lambda p: get_distance(p1, p2, p))
    
    ts1: int = -find_side(p_max, p1, p2)
    ts2: int = -find_side(p_max, p2, p1)
    
    s1: list[Point] = [p for p in cand if p != p_max and find_side(p_max, p1, p) == ts1]
    s2: list[Point] = [p for p in cand if p != p_max and find_side(p_max, p2, p) == ts2]
    
    return (p_max, (s1, p1, p_max, ts1), (s2, p_max, p2, ts2))

def run_serial(points: list[Point]) -> list[Point]:
    """Runs the QuickHull algorithm sequentially."""
    if len(points) < 3: return points

    min_x: Point = min(points, key=lambda p: p[0])
    max_x: Point = max(points, key=lambda p: p[0])

    hull: list[Point] = []
    hull += quickhull_step(points, min_x, max_x, 1)
    hull += quickhull_step(points, min_x, max_x, -1)

    return list(set(hull))

def run_parallel(points: list[Point], num_threads: int) -> list[Point]:
    """Runs the QuickHull algorithm in parallel using a ThreadPool."""
    if len(points) < 3: return points

    pool: ThreadPool = ThreadPool(num_threads)
    
    min_x: Point = min(points, key=lambda p: p[0])
    max_x: Point = max(points, key=lambda p: p[0])

    hull: list[Point] = [min_x, max_x]
    
    cur_tasks: list[tuple[list[Point], Point, Point, int]]= [
        (points, min_x, max_x, 1),
        (points, min_x, max_x, -1)
    ]
    
    tar: int = num_threads * 4

    while len(cur_tasks) < tar and cur_tasks:
        futures: list[Future] = [pool.submit(partition, *args) for args in cur_tasks]
        next_tasks: list[tuple[list[Point], Point, Point, int]] = []

        for f in futures:
            res: Any = f.get_result()
            if res:
                p_max, t1, t2 = res
                hull.append(p_max)
                if t1[0]: next_tasks.append(t1)
                if t2[0]: next_tasks.append(t2)
        cur_tasks = next_tasks

    futures: list[Future] = [pool.submit(quickhull_step, *args) for args in cur_tasks]
    
    for f in futures:
        hull += f.get_result()
            
    pool.shutdown()
    return list(set(hull))

def benchmark(points: list[Point], threads: int) -> dict[str, Any]:
    """Runs both serial and parallel implementations and returns timing results."""
    beg: float = time()
    run_serial(points)
    st: float = time() - beg

    beg = time()
    res: list[Point] = run_parallel(points, threads)
    pt: float = time() - beg
    
    return {
        "hull": res,
        "serial_time": st,
        "parallel_time": pt,
        "speedup": st / pt if pt > 0.0001 else 1.0
    }