"""
QuickHull algorithm implementation for Convex Hull construction.
"""
from time    import time
from typing  import Any

from pools   import ThreadPool, ProcessPool, Future
from utility import Point

type Task = tuple[list[Point], Point, Point, int] # Points within, Start point, End line, Side 
type Partition = tuple[Point, Task, Task] # Best point, Side 1, Side 2

def quickhull_step(points: list[Point], p1: Point, p2: Point, side: int) -> list[Point]:
    """Recursively computes the convex hull for points on one side of the line p1-p2."""
    res: Partition | None = partition(points, p1, p2, side)
    if res is None:
        return []
    
    p_max, task1, task2 = res
    return quickhull_step(*task1) + [p_max] + quickhull_step(*task2)

def partition(points: list[Point], p1: Point, p2: Point, side: int) -> Partition | None:
    """Partitions points for a single QuickHull step, returning the max point and sub-tasks."""
    x1, y1 = p1.coords
    x2, y2 = p2.coords
    dx, dy = x2 - x1, y2 - y1

    max_dist: float = 0.0
    p_max: Point = None

    for p in points:
        px, py = p.coords
        cross: float = (py - y1) * dx - dy * (px - x1)
        
        if side == 1:
            if cross > max_dist:
                max_dist = cross
                p_max = p
        else:
            if cross < -max_dist:
                max_dist = -cross
                p_max = p
    
    if not p_max: return None
    
    s1: list[Point] = []
    s2: list[Point] = []
    
    mx, my = p_max.coords
    dx1, dy1 = mx - x1, my - y1
    dx2, dy2 = x2 - mx, y2 - my
    
    for p in points:
        if p is p_max: continue
        px, py = p.coords
        
        cp1 = (py - y1) * dx1 - dy1 * (px - x1)
        if (side == 1 and cp1 > 0) or (side == -1 and cp1 < 0):
            s1.append(p)
            continue
            
        cp2 = (py - my) * dx2 - dy2 * (px - mx)
        if (side == 1 and cp2 > 0) or (side == -1 and cp2 < 0):
            s2.append(p)
    
    return (p_max, (s1, p1, p_max, side), (s2, p_max, p2, side))

def run_serial(points: list[Point]) -> list[Point]:
    """Runs the QuickHull algorithm sequentially."""
    if len(points) < 3: return points

    min_x: Point = min(points, key=lambda p: p[0])
    max_x: Point = max(points, key=lambda p: p[0])

    hull: list[Point] = [min_x, max_x]
    hull += quickhull_step(points, min_x, max_x, 1)
    hull += quickhull_step(points, min_x, max_x, -1)

    return list(set(hull))

def run_parallel_thread(points: list[Point], num_threads: int) -> list[Point]:
    """Runs the QuickHull algorithm in parallel using a ThreadPool."""
    if len(points) < 3: return points
    
    min_x: Point = min(points, key=lambda p: p[0])
    max_x: Point = max(points, key=lambda p: p[0])

    hull: list[Point] = [min_x, max_x]
    
    cur_tasks: list[Task]= [(points, min_x, max_x, 1), (points, min_x, max_x, -1)]
    
    tar: int = num_threads * 4

    while len(cur_tasks) < tar and cur_tasks:
        next_tasks: list[Task] = []

        for args in cur_tasks:
            res: Partition | None = partition(*args)
            if not res: continue
            p_max, t1, t2 = res
            hull.append(p_max)
            if t1[0]: next_tasks.append(t1)
            if t2[0]: next_tasks.append(t2)
        cur_tasks = next_tasks

    pool: ThreadPool = ThreadPool(num_threads)

    futures: list[Future] = [pool.submit(quickhull_step, *args) for args in cur_tasks]
    
    for f in futures:
        hull += f.get_result()
            
    pool.shutdown()
    return list(set(hull))

def run_parallel_process(points: list[Point], num_procs: int) -> list[Point]:
    """Runs the QuickHull algorithm in parallel using a ProcessPool."""
    if len(points) < 3: return points
    
    min_x: Point = min(points, key=lambda p: p[0])
    max_x: Point = max(points, key=lambda p: p[0])

    hull: list[Point] = [min_x, max_x]
    
    cur_tasks: list[Task]= [(points, min_x, max_x, 1), (points, min_x, max_x, -1)]
    
    tar: int = num_procs * 4

    while len(cur_tasks) < tar and cur_tasks:
        next_tasks: list[Task] = []

        for args in cur_tasks:
            res: Partition | None = partition(*args)
            if not res: continue
            p_max, t1, t2 = res
            hull.append(p_max)
            if t1[0]: next_tasks.append(t1)
            if t2[0]: next_tasks.append(t2)
        cur_tasks = next_tasks

    pool: ProcessPool = ProcessPool(num_procs)

    futures: list[Future] = [pool.submit(quickhull_step, *args) for args in cur_tasks]
    
    for f in futures:
        hull += f.get_result()
            
    pool.shutdown()
    return list(set(hull))

def benchmark(points: list[Point], threads: int) -> dict[str, Any]:
    """Runs both serial and parallel implementations and returns timing results."""
    beg: float = time()
    res1: list[Point] = run_serial(points)
    st: float = time() - beg

    beg = time()
    res2: list[Point] = run_parallel_thread(points, threads)
    tt: float = time() - beg

    beg = time()
    res3: list[Point] = run_parallel_process(points, threads)
    pt: float = time() - beg
    
    if frozenset(res1) != frozenset(res2) or frozenset(res1) != frozenset(res3):
        raise RuntimeError("[Error] Results aren't equal")

    return {
        "hull": res1,
        "serial_time": st,
        "threaded_time": tt,
        "processes_time": pt,
        "speedup": ((st / tt if tt > 0 else 0), (st / pt if pt > 0 else 0))
    }