import math
import time
from concurrent.futures import ProcessPoolExecutor

# --- Helper Functions ---
def get_distance(p1, p2, p3):
    return abs((p3[1] - p1[1]) * (p2[0] - p1[0]) -
               (p2[1] - p1[1]) * (p3[0] - p1[0]))

def find_side(p1, p2, p3):
    val = (p3[1] - p1[1]) * (p2[0] - p1[0]) - \
          (p2[1] - p1[1]) * (p3[0] - p1[0])
    if val > 0: return 1
    if val < 0: return -1
    return 0

def quickhull_step(points, p1, p2, side):
    ind = -1
    max_dist = 0
    
    for i in range(len(points)):
        temp = get_distance(p1, p2, points[i])
        if find_side(p1, p2, points[i]) == side and temp > max_dist:
            ind = i
            max_dist = temp

    if ind == -1:
        return [p1, p2]

    # Recurse
    s1 = quickhull_step(points, points[ind], p1, -find_side(points[ind], p1, p2))
    s2 = quickhull_step(points, points[ind], p2, -find_side(points[ind], p2, p1))
    
    return s1 + s2

def run_serial(points):
    if len(points) < 3: return points
    min_x_ind = points.index(min(points, key=lambda p: p[0]))
    max_x_ind = points.index(max(points, key=lambda p: p[0]))

    hull = quickhull_step(points, points[min_x_ind], points[max_x_ind], 1)
    hull += quickhull_step(points, points[min_x_ind], points[max_x_ind], -1)
    
    return hull

def run_parallel(points, num_workers=4):
    if len(points) < 3: return points
    min_x_ind = points.index(min(points, key=lambda p: p[0]))
    max_x_ind = points.index(max(points, key=lambda p: p[0]))

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        f1 = executor.submit(quickhull_step, points, points[min_x_ind], points[max_x_ind], 1)
        f2 = executor.submit(quickhull_step, points, points[min_x_ind], points[max_x_ind], -1)
        
        res1 = f1.result()
        res2 = f2.result()

    hull = res1 + res2
    return hull

def benchmark(points, workers):
    # Serial
    start = time.time()
    run_serial(points)
    serial_time = time.time() - start

    # Parallel
    start = time.time()
    par_res = run_parallel(points, workers)
    par_time = time.time() - start

    return {
        "hull": par_res, 
        "serial_time": serial_time,
        "parallel_time": par_time,
        "speedup": serial_time / par_time if par_time > 0.0001 else 1.0 
    }