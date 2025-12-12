from time import time
from processpool import ProcessPool
from utility import Point
import sys
import math

sys.setrecursionlimit(20000)

def get_distance(p1: Point, p2: Point, p3: Point) -> float:
    return abs((p3[1] - p1[1]) * (p2[0] - p1[0]) - (p2[1] - p1[1]) * (p3[0] - p1[0]))

def find_side(p1: Point, p2: Point, p3: Point) -> int:
    val: float = (p3[1] - p1[1]) * (p2[0] - p1[0]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
    return int(val > 0) - int(val < 0)

def worker_find_max(points: list[Point], p1: Point, p2: Point, side: int):
    max_dist = -1.0
    ind = -1
    
    for i, p in enumerate(points):
        if find_side(p1, p2, p) == side:
            dist = get_distance(p1, p2, p)
            if dist > max_dist:
                max_dist = dist
                ind = i
                
    return (max_dist, points[ind] if ind != -1 else None)

def worker_partition(points: list[Point], p1: Point, p2: Point, p_max: Point, target_side_1: int, target_side_2: int):
    s1_points = []
    s2_points = []
    
    for p in points:
        if p == p_max: continue
        
        if find_side(p_max, p1, p) == target_side_1:
            s1_points.append(p)
        elif find_side(p_max, p2, p) == target_side_2:
            s2_points.append(p)
            
    return (s1_points, s2_points)

def quickhull_serial(points: list[Point], p1: Point, p2: Point, side: int) -> list[Point]:
    if not points:
        return []

    ind = -1
    max_dist = 0
    
    for i in range(len(points)):
        temp = get_distance(p1, p2, points[i])
        if find_side(p1, p2, points[i]) == side and temp > max_dist:
            ind = i
            max_dist = temp

    if ind == -1:
        return [p1, p2]

    p_max = points[ind]
    
    s1_points = []
    s2_points = []
    
    target_side_1 = -find_side(p_max, p1, p2)
    target_side_2 = -find_side(p_max, p2, p1)

    for p in points:
        if p == p_max: continue
        if find_side(p_max, p1, p) == target_side_1:
            s1_points.append(p)
        elif find_side(p_max, p2, p) == target_side_2:
            s2_points.append(p)

    res1 = quickhull_serial(s1_points, p1, p_max, target_side_1)
    res2 = quickhull_serial(s2_points, p_max, p2, target_side_2)
    
    return res1 + res2 + [p_max]

def run_serial(points: list[Point]) -> list[Point]:
    if len(points) < 3: return points

    min_x = min(points, key=lambda p: p[0])
    max_x = max(points, key=lambda p: p[0])

    hull: list[Point] = []
    hull += quickhull_serial(points, min_x, max_x, 1)
    hull += quickhull_serial(points, min_x, max_x, -1)

    return list(set(hull))

def run_parallel(points: list[Point], num_threads: int) -> list[Point]:
    if len(points) < 3: return points
    
    pool = ProcessPool(num_threads)
    
    min_x = min(points, key=lambda p: p[0])
    max_x = max(points, key=lambda p: p[0])

    hull_points = [min_x, max_x]
    
    task_queue = [
        (points, min_x, max_x, 1),
        (points, min_x, max_x, -1)
    ]
    
    serial_futures = []
    
    PARALLEL_THRESHOLD = 20000

    while task_queue:
        curr_points, p1, p2, side = task_queue.pop(0)
        
        if not curr_points:
            continue
            
        if len(curr_points) < PARALLEL_THRESHOLD:
            f = pool.submit(quickhull_serial, curr_points, p1, p2, side)
            serial_futures.append(f)
            continue
            
        chunk_size = math.ceil(len(curr_points) / num_threads)
        chunks = [curr_points[i:i + chunk_size] for i in range(0, len(curr_points), chunk_size)]
        
        max_futures = []
        for chunk in chunks:
            max_futures.append(pool.submit(worker_find_max, chunk, p1, p2, side))
            
        global_max_dist = -1.0
        p_max = None
        
        for f in max_futures:
            dist, pt = f.get_result()
            if pt is not None and dist > global_max_dist:
                global_max_dist = dist
                p_max = pt
        
        if p_max is None:
            continue
            
        hull_points.append(p_max)
        
        target_side_1 = -find_side(p_max, p1, p2)
        target_side_2 = -find_side(p_max, p2, p1)
        
        part_futures = []
        for chunk in chunks:
            part_futures.append(pool.submit(worker_partition, chunk, p1, p2, p_max, target_side_1, target_side_2))
            
        s1_total = []
        s2_total = []
        
        for f in part_futures:
            s1, s2 = f.get_result()
            s1_total.extend(s1)
            s2_total.extend(s2)
            
        if s1_total:
            task_queue.append((s1_total, p1, p_max, target_side_1))
        if s2_total:
            task_queue.append((s2_total, p_max, p2, target_side_2))
            
    for f in serial_futures:
        hull_points.extend(f.get_result())
        
    pool.shutdown()
    
    return list(set(hull_points))

def benchmark(points: list[Point], threads: int) -> dict[str, any]:
    start: float = time()
    ser_res: list[Point]= run_serial(points)
    serial_time: float = time() - start

    start: float = time()
    par_res: list[Point] = run_parallel(points, threads)
    par_time: float = time() - start
    
    return {
        "hull": par_res, 
        "serial_time": serial_time,
        "parallel_time": par_time,
        "speedup": serial_time / par_time if par_time > 0.0001 else 1.0 
    }