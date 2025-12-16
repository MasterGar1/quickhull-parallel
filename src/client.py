"""
Implements a client that generates random points, sends them to the server for processing, and displays the benchmark results.
"""
from socket  import socket, SOCK_STREAM, AF_INET
from pickle  import dumps, loads
from struct  import pack, unpack
from zlib    import compress, decompress
from time    import time
from typing  import Any

from utility import generate_points, Point, HOST, PORT, CHUNK_SIZE, DEFAULT_POINTS, DEFAULT_THREADS, DEFAULT_DIMS

def run_client() -> None:
    """Connects to the server, sends input data, and displays the results."""
    try:
        with socket(AF_INET, SOCK_STREAM) as sock:
            print(f"[Client] Connecting to server at {HOST}:{PORT}...")
            sock.connect((HOST, PORT))
            
            inpt: str = input(f"[Input] Enter number of points (default {DEFAULT_POINTS}): ")
            pts: int = int(inpt) if inpt else DEFAULT_POINTS
            
            inpt = input(f"[Input] Enter number of threads / processes (default {DEFAULT_THREADS}): ")
            thr: int = int(inpt) if inpt else DEFAULT_THREADS
            
            inpt = input(f"[Input] Enter dimensions (default {DEFAULT_DIMS}): ")
            dims: int = int(inpt) if inpt else DEFAULT_DIMS

            points: list[Point] = generate_points(pts, dims)
            
            payload: dict[str, Any]= {"points": points, "threads": thr}
            print("[Client] Compressing and sending data...")
            st: float = time()
            
            data: bytes = compress(dumps(payload))
            sock.sendall(pack('>I', len(data)) + data)
            
            data_len: bytes = sock.recv(4)
            if not data_len:
                print("[Error] No response length received.")
                return
            resp_len: int = unpack('>I', data_len)[0]
            
            fragments: list[bytes] = []
            rec_bytes: int = 0
            while rec_bytes < resp_len:
                chunk: bytes = sock.recv(min(resp_len - rec_bytes, CHUNK_SIZE))
                if not chunk: break
                fragments.append(chunk)
                rec_bytes += len(chunk)
            
            resp: bytes = b''.join(fragments)
            
            tt: float = time() - st
            print(f"[Done] Data received. Total time: {tt:.2f}s")
        
        result: dict[str, Any] = loads(decompress(resp))
        hull: list[Point] = result['hull']

        print("\n[RESULTS]")
        print(f"Input Size:                    {pts} points")
        print(f"Serial Time:                   {result['serial_time']:.4f} s")
        print(f"Parallel Time (Multithreaded): {result['threaded_time']:.4f} s ({thr} threads)")
        print(f"Parallel Time (Multiprocess):  {result['processes_time']:.4f} s ({thr} processes)")
        print(f"Speedup:                       {result['speedup'][0]:.2f}x : {result['speedup'][1]:.2f}x")
        print(f"Hull Points Amount:            {len(hull)}")
        print(f"Hull Points:{"   ".join([ f"{"\n" if i % 4 == 0 else ""}{p}" for i, p in enumerate(hull) ])}")
    except ConnectionRefusedError:
        print(f"\n[Error] Could not connect to {HOST}:{PORT}. Is the server running?")
    except Exception as e:
        print(f"\n[Error] An unexpected error occurred: {e}")

if __name__ == '__main__':
    run_client()