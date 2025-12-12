import json
from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, timeout
from quickhull import benchmark
from utility import *

HOST: str = '127.0.0.1'
PORT: int = 65432

def handle_client(conn: socket, addr: tuple[str, int]) -> None:
    print(f"[Server] Accepted connection from {''.join([addr[0], ':', str(addr[1])])}")
    
    buffer: bytes = b""
    try:
        while True:
            data: bytes = conn.recv(1024 * 128)
            if not data:
                break
            buffer += data
            
            try:
                req: dict[str, any] = json.loads(buffer.decode('utf-8'), object_hook=decode_point)
                print(f"[Process] Processing request for {len(req['points'])} points with {req.get('threads', 4)} processes.")
                
                result: dict[str, any]= benchmark(req.get('points', []), req.get('threads', 4))
                
                print(f"[Done] Serial: {result['serial_time']:.3f}s, Parallel: {result['parallel_time']:.3f}s")
                
                conn.sendall(json.dumps(result, cls=JsonEncodePoint).encode('utf-8'))
                break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[Error] Processing failed: {e}")
                break
                
    except ConnectionResetError:
        pass
    except Exception as e:
        print(f"[Error] Connection error: {e}")
    finally:
        print(f"[Server] Closing connection to {''.join([addr[0], ':', str(addr[1])])}")
        conn.close()

def run_server():
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen()
        print(f"[Server] Listening on {''.join([HOST, ':', str(PORT)])}")
        sock.settimeout(1.0)

        try:
            while True:
                try:
                    conn, addr = sock.accept()
                except timeout:
                    continue
                conn.settimeout(None)
                handle_client(conn, addr)
        except KeyboardInterrupt:
            print("[Stop] Server stopping...")
        finally:
            sock.close()

if __name__ == "__main__":
    run_server()