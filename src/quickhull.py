"""
QuickHull algorithm implementation for Convex Hull construction.
"""
import numpy   as     np
from   time    import time
from   typing  import Any

from   pools   import ThreadPool, ProcessPool, Future
from   utility import CArray, NPoint

type Task = tuple[CArray[NPoint], NPoint, NPoint, int] # Points within, Start point, End point, Side
type Partition = tuple[NPoint, Task, Task] # Best point, Side 1, Side 2

def _partition(points: NPoint, p1: NPoint, p2: NPoint, side: int) -> Partition | None:
    """Partitions points for a single QuickHull step, returning the max point and sub-tasks."""
    v1x, v1y = p2[0] - p1[0], p2[1] - p1[1]
    
    cross: NPoint = (points[:, 1] - p1[1]) * v1x - v1y * (points[:, 0] - p1[0])
    
    if side == 1:
        mask: CArray[bool] = cross > 0
        if not np.any(mask): return None
        valid_points: NPoint = points[mask]
        p_max: NPoint = valid_points[np.argmax(cross[mask])]
    else:
        mask: CArray[bool] = cross < 0
        if not np.any(mask): return None
        valid_points: NPoint = points[mask]
        p_max: NPoint = valid_points[np.argmin(cross[mask])]

    dx1, dy1 = p_max[0] - p1[0], p_max[1] - p1[1]
    c1: NPoint = (valid_points[:, 1] - p1[1]) * dx1 - dy1 * (valid_points[:, 0] - p1[0])
    
    dx2, dy2 = p2[0] - p_max[0], p2[1] - p_max[1]
    c2: NPoint = (valid_points[:, 1] - p_max[1]) * dx2 - dy2 * (valid_points[:, 0] - p_max[0])
    
    if side == 1:
        s1: NPoint = valid_points[c1 > 0]
        s2: NPoint = valid_points[c2 > 0]
    else:
        s1: NPoint = valid_points[c1 < 0]
        s2: NPoint = valid_points[c2 < 0]
        
    return p_max, (s1, p1, p_max, side), (s2, p_max, p2, side)

def _quickhull_step(points: NPoint, p1: NPoint, p2: NPoint, side: int) -> list[NPoint]:
    """Recursively computes the convex hull for points on one side of the line p1-p2."""
    part: Partition | None = _partition(points, p1, p2, side)
    if part is None: return []
    
    p_max, t1, t2 = part

    return _quickhull_step(*t1) + [p_max] + _quickhull_step(*t2)

def run_serial(points: CArray[NPoint]) -> list[NPoint]:
    """Runs the QuickHull algorithm sequentially."""
    if len(points) < 3: return list(points)
    
    min_x: NPoint = points[np.argmin(points[:, 0])]
    max_x: NPoint = points[np.argmax(points[:, 0])]

    hull: list[NPoint] = [min_x, max_x] + _quickhull_step(points, min_x, max_x, 1) + _quickhull_step(points, min_x, max_x, -1)

    hull_np: NPoint = np.array(hull)
    return list(np.unique(hull_np, axis=0))

def run_parallel_thread(points: CArray[NPoint], num_threads: int) -> list[NPoint]:
    """Runs the QuickHull algorithm in parallel using a ThreadPool."""
    if len(points) < 3: return list(points)

    min_x: NPoint = points[np.argmin(points[:, 0])]
    max_x: NPoint = points[np.argmax(points[:, 0])]
    
    hull: list[NPoint] = [min_x, max_x]
    cur_tasks: list[Task] = [(points, min_x, max_x, 1), (points, min_x, max_x, -1)]
    
    tar: int = num_threads * 4
    pool: ThreadPool = ThreadPool(num_threads)

    while len(cur_tasks) < tar and cur_tasks:
        futures: list[Future] = [pool.submit(_partition, *args) for args in cur_tasks]
        next_tasks: list[Task] = []

        for f in futures:
            res: Partition | None = f.get_result()
            if not res: continue
            p_max, t1, t2 = res
            hull.append(p_max)
            if t1[0].size > 0: next_tasks.append(t1)
            if t2[0].size > 0: next_tasks.append(t2)
        cur_tasks = next_tasks

    futures: list[Future] = [pool.submit(_quickhull_step, *args) for args in cur_tasks]
    
    for f in futures:
        hull += f.get_result()
            
    pool.shutdown()
    hull_np: CArray[NPoint] = np.array(hull)
    return list(np.unique(hull_np, axis=0))

def run_parallel_process(points: CArray[NPoint], num_procs: int) -> list[NPoint]:
    """Runs the QuickHull algorithm in parallel using a ProcessPool."""
    if len(points) < 3: return list(points)

    min_x: NPoint = points[np.argmin(points[:, 0])]
    max_x: NPoint = points[np.argmax(points[:, 0])]
    
    hull: list[NPoint] = [min_x, max_x]
    cur_tasks: list[Task] = [(points, min_x, max_x, 1), (points, min_x, max_x, -1)]
    
    tar: int = num_procs * 4
    pool: ProcessPool = ProcessPool(num_procs)

    while len(cur_tasks) < tar and cur_tasks:
        futures: list[Future] = [pool.submit(_partition, *args) for args in cur_tasks]
        next_tasks: list[Task] = []

        for f in futures:
            res: Partition | None = f.get_result()
            if not res: continue
            p_max, t1, t2 = res
            hull.append(p_max)
            if t1[0].size > 0: next_tasks.append(t1)
            if t2[0].size > 0: next_tasks.append(t2)
        cur_tasks = next_tasks

    futures: list[Future] = [pool.submit(_quickhull_step, *args) for args in cur_tasks]
    
    for f in futures:
        hull += f.get_result()
            
    pool.shutdown()
    hull_np: CArray[NPoint] = np.array(hull)
    return list(np.unique(hull_np, axis=0))

def benchmark(points: CArray[NPoint], threads: int) -> dict[str, Any]:
    """Runs both serial and parallel implementations and returns timing results."""
    beg: float = time()
    res1: list[NPoint] = run_serial(points)
    st: float = time() - beg

    beg = time()
    res2: list[NPoint] = run_parallel_thread(points, threads)
    tt: float = time() - beg

    beg = time()
    res3: list[NPoint] = run_parallel_process(points, threads)
    pt: float = time() - beg
    
    if not np.array_equal(res1, res2) or not np.array_equal(res1, res3):
        raise RuntimeError("[Error] Results aren't equal")

    return {
        "hull": res1,
        "serial_time": st,
        "threaded_time": tt,
        "processes_time": pt,
        "speedup": ((st / tt if tt > 0 else 0), (st / pt if pt > 0 else 0))
    }