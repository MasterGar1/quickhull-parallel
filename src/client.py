import json
from socket import socket, SOCK_STREAM, AF_INET
from time import time
from utility import *

HOST = '127.0.0.1'
PORT = 65432

def run_client() -> None:
    try:
        with socket(AF_INET, SOCK_STREAM) as sock:
            print(f"[Client] Connecting to server at {HOST}:{PORT}...")
            sock.connect((HOST, PORT))
            num_points_str: str = input("[Input] Enter number of points (default 100000): ")
            num_points = int(num_points_str) if num_points_str else 100000
            
            num_threads_str: str = input("[Input] Enter processes for server (default 4): ")
            num_threads = int(num_threads_str) if num_threads_str else 4
            
            num_dims_str: str = input("[Input] Enter dimensions (default 2): ")
            num_dims = int(num_dims_str) if num_dims_str else 2

            points: list[Point] = generate_points(num_points, num_dims)
            
            payload: dict[str, any] = {"points": points, "threads": num_threads}
            print("[Client] Sending data.")
            start_time: float = time()
            sock.sendall(json.dumps(payload, cls=JsonEncodePoint).encode('utf-8'))
            fragments: list[bytes] = []
            while True:
                chunk: bytes = sock.recv(1024 * 128)
                if not chunk: break
                fragments.append(chunk)
            response_data: bytes = b''.join(fragments)
            total_roundtrip: float = time() - start_time
            print(f"[Done] Data received. Total time: {total_roundtrip:.2f}s")
        
        result: dict[str, any] = json.loads(response_data.decode('utf-8'), object_hook=decode_point)
        hull_raw = result['hull']

        print("\n" + "="*35)
        print("   RESULTS   ")
        print("="*35)
        print(f"Input Size: {num_points} points")
        print(f"Hull Points Found (Raw): {len(hull_raw)}")
        print("-" * 35)
        print(f"Server Serial Time:   {result['serial_time']:.4f} s")
        print(f"Server Parallel Time: {result['parallel_time']:.4f} s ({num_threads} threads)")
        print(f"Speedup:              {result['speedup']:.2f}x")
        print("="*35)

    except ConnectionRefusedError:
        print(f"\n[ERROR] Could not connect to {HOST}:{PORT}. Is the server running?")
    except json.JSONDecodeError:
        print("\n[ERROR] Failed to decode JSON response. Response might be incomplete.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == '__main__':
    run_client()