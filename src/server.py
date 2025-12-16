"""
Implements a multi-threaded server that listens for client connections, receives point data, and computes the convex hull using parallel processing.
"""
from socket    import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, timeout
from pickle    import dumps, loads
from struct    import pack, unpack
from zlib      import compress, decompress
from typing    import Any

from quickhull import benchmark
from utility   import HOST, PORT, CHUNK_SIZE, DEFAULT_THREADS
from pools     import ThreadPool

def check_gil_status() -> None:
    """Checks and prints whether the Global Interpreter Lock (GIL) is enabled."""
    import sys
    if hasattr(sys, "_is_gil_enabled"):
        gil: bool = sys._is_gil_enabled()
        st: str = "ENABLED" if gil else "DISABLED"
    else:
        gil: bool = True
        st: str = "ENABLED (Standard Build)"

    print(f"[Info] GIL Status: {st}")

def recv_exact(sock: socket, size: int) -> bytes:
    """Receives exactly `size` bytes from the socket connection."""
    buf: bytes = b''
    while len(buf) < size:
        pack: bytes = sock.recv(min(size - len(buf), CHUNK_SIZE))
        if not pack:
            return None
        buf += pack
    return buf

def handle_client(sock: socket, addr: tuple[str, int]) -> None:
    """Handles a single client connection, processing the request and sending the response."""
    print(f"[Server] Accepted connection from {addr[0]}:{addr[1]}.")
    try:
        data_len: bytes = recv_exact(sock, 4)
        if not data_len:
            return
        msg_len: int = unpack('>I', data_len)[0]
        
        comp_data: bytes = recv_exact(sock, msg_len)
        if not comp_data:
            return

        req: dict[str, Any]= loads(decompress(comp_data))
        
        points: list[object] = req.get('points', [])
        thr: int = req.get('threads', DEFAULT_THREADS)
        print(f"[Process] Processing {len(points)} points with {thr} threads / processes.")
        
        res: dict[str, Any]= benchmark(points, thr)
        print(f"[Done] Data processed. Returning response to {addr[0]}:{addr[1]}.")
        
        res_bytes: bytes = compress(dumps(res))
        sock.sendall(pack('>I', len(res_bytes)) + res_bytes)
    except Exception as e:
        print(f"[Error] Processing error: {e}")
    finally:
        print(f"[Server] Closing connection to {addr[0]}:{addr[1]}.")
        sock.close()

def run_server():
    """Starts the server to listen for incoming connections."""
    check_gil_status()
    pool: ThreadPool = ThreadPool(4)

    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen()
        print(f"[Server] Listening on {HOST}:{PORT}")
        sock.settimeout(1.0) 
        try:
            while True:
                try:
                    conn, addr = sock.accept()
                    conn.settimeout(None) 
                    
                    pool.submit(handle_client, conn, addr)
                except timeout:
                    continue
        except KeyboardInterrupt:
            print("[Stop] Server stopping...")
        finally:
            pool.shutdown()
            sock.close()

if __name__ == "__main__":
    run_server()