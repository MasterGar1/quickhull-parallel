import socket
import selectors
import types
import json
from quickhull import benchmark

HOST = '127.0.0.1'
PORT = 65432

sel = selectors.DefaultSelector()

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)

    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", response_created=False)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    # --- READ ---
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(4096 * 4)
            if recv_data:
                data.inb += recv_data
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
        except ConnectionResetError:
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        # Process Data if we haven't already created a response
        if data.inb and not data.response_created:
            try:
                req = json.loads(data.inb.decode('utf-8'))
                print(f"Processing request for {len(req['points'])} points from {data.addr}")
                
                result = benchmark(req['points'], req.get('threads', 4))
                
                response = json.dumps(result).encode('utf-8')
                data.outb += response
                data.inb = b""
                
                data.response_created = True 
                
            except json.JSONDecodeError:
                pass 

        # Send Data if output buffer has content
        if data.outb:
            try:
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]
            except ConnectionError:
                sel.unregister(sock)
                sock.close()
                return

        # CLOSE CONNECTION: If response was created AND output buffer is empty
        if data.response_created and len(data.outb) == 0:
            print(f"Response sent. Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

if __name__ == "__main__":
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print(f"Listening on {(HOST, PORT)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()