import socket
import json
import random
import time
import math

HOST = '127.0.0.1'
PORT = 65432

def generate_points(n, min_val=0, max_val=5000):
    """Generates N random 2D points."""
    print(f"Generating {n} random points in range [{min_val}, {max_val}]...")
    return [[random.randint(min_val, max_val), random.randint(min_val, max_val)] for _ in range(n)]

def order_points_angularly(points):
    """
    Sorts points based on the angle they make with the center of the shape.
    This ensures they are connected consecutively to form a proper convex polygon.
    """
    if len(points) < 3:
        return points

    # Find Center (average x, average y)
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)

    # 3. Sort and remove exact duplicates produced by the base case of QuickHull
    # We use tuple conversion to make points hashable for set inclusion test
    unique_points = list(set(map(tuple, points)))
    sorted_points = sorted(unique_points, key=lambda pt: math.atan2(pt[1] - cy, pt[0] - cx))
    
    return sorted_points

def save_as_svg(hull_points_raw, filename="result_hull_outline.svg"):
    """
    Scales hull points and draws only the outline to a 512x512 SVG file.
    """
    if not hull_points_raw or len(hull_points_raw) < 3:
        print("Not enough hull points to draw a polygon.")
        return

    hull_points = order_points_angularly(hull_points_raw)

    CANVAS_SIZE = 512
    PADDING = 20
    DRAW_SIZE = CANVAS_SIZE - (PADDING * 2)

    min_x = min(p[0] for p in hull_points)
    max_x = max(p[0] for p in hull_points)
    min_y = min(p[1] for p in hull_points)
    max_y = max(p[1] for p in hull_points)

    data_width = max_x - min_x
    data_height = max_y - min_y
    
    # Prevent division by zero for degenerated hulls (points all in a line)
    if data_width == 0: data_width = 1
    if data_height == 0: data_height = 1

    # Calculate scale to fit the largest dimension into DRAW_SIZE
    scale = min(DRAW_SIZE / data_width, DRAW_SIZE / data_height)

    # Calculate offsets to center the shape
    offset_x = PADDING + (DRAW_SIZE - (data_width * scale)) / 2
    offset_y = PADDING + (DRAW_SIZE - (data_height * scale)) / 2

    # Coordinate Transformation Function
    def to_svg_coord(pt):
        sx = offset_x + (pt[0] - min_x) * scale
        sy = offset_y + (max_y - pt[1]) * scale
        return sx, sy

    print(f"Generating outline SVG: {filename} (Scale factor: {scale:.4f})")

    svg_content = [
        f'<svg width="{CANVAS_SIZE}" height="{CANVAS_SIZE}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="100%" height="100%" fill="white"/>' 
    ]

    poly_points_str = []
    for pt in hull_points:
        sx, sy = to_svg_coord(pt)
        poly_points_str.append(f"{sx:.2f},{sy:.2f}")
    
    points_joined = " ".join(poly_points_str)
    svg_content.append(f'<polygon points="{points_joined}" fill="none" stroke="red" stroke-width="2"/>')

    svg_content.append('</svg>')

    with open(filename, 'w') as f:
        f.write("\n".join(svg_content))
    print(f"SVG saved successfully.")


def run_client():
    num_points_str = input("Enter number of points (default 20000): ")
    num_points = int(num_points_str) if num_points_str else 20000
    
    num_threads_str = input("Enter processes for server (default 4): ")
    num_threads = int(num_threads_str) if num_threads_str else 4

    points = generate_points(num_points)
    
    payload = {"points": points, "threads": num_threads}

    print(f"\nConnecting to server at {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            print("Sending data and waiting for calculation...")
            start_time = time.time()
            sock.sendall(json.dumps(payload).encode('utf-8'))
            
            fragments = []
            while True:
                chunk = sock.recv(65536)
                if not chunk: break
                fragments.append(chunk)
            
            response_data = b''.join(fragments)
            total_roundtrip = time.time() - start_time
            print(f"Done. Total round-trip time: {total_roundtrip:.2f}s")
        
        result = json.loads(response_data.decode('utf-8'))
        hull_raw = result['hull']

        print("\n" + "="*35)
        print("   RESULTS   ")
        print("="*35)
        print(f"Input Size: {num_points} points")
        print(f"Hull Points Found (Raw): {len(hull_raw)}")
        print("-" * 35)
        print(f"Server Serial Time:   {result['serial_time']:.4f} s")
        print(f"Server Parallel Time: {result['parallel_time']:.4f} s ({num_threads} workers)")
        print(f"Speedup:              {result['speedup']:.2f}x")
        print("="*35)
        
        save_as_svg(hull_raw, "quickhull_outline.svg")

    except ConnectionRefusedError:
        print(f"\nERROR: Could not connect to {HOST}:{PORT}. Is the server running?")
    except json.JSONDecodeError:
        print("\nERROR: Failed to decode JSON response. Response might be incomplete.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == '__main__':
    run_client()