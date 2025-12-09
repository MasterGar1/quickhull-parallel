# Parallel QuickHull Client-Server

This project implements the QuickHull algorithm to find the Convex Hull of a set of 2D points. It utilizes a Client-Server architecture where the server performs calculations in parallel.

## Features
1.  **Client-Server Architecture**: TCP communication using Sockets.
2.  **Selector Pattern**: The server uses Python's `selectors` module for non-blocking I/O multiplexing.
3.  **Parallelization**: The Algorithm uses `ProcessPoolExecutor` to distribute recursive sorting branches across CPU cores.
4.  **Benchmarking**: Automatically compares Serial vs Parallel execution times.

## Prerequisites
- Python 3.8+

## How to Run

1.  **Start the Server**:
    ```bash
    python server.py
    ```
    The server will listen on `127.0.0.1:65432`.

2.  **Start the Client** (in a new terminal):
    ```bash
    python client.py
    ```

3.  **Interaction**:
    - Enter the number of points (recommend > 50,000 to see parallel benefits).
    - Enter the number of worker processes.
    - View the timing results in the console.

## Implementation Details

### Algorithm
The QuickHull algorithm is a divide-and-conquer algorithm. 
- **Parallel Strategy**: After finding the min/max X points, the dataset is split into "Upper" and "Lower" sets. These two recursive calls are heavy and independent, so they are offloaded to separate processes using `concurrent.futures`.

### Networking
- **Selectors**: instead of creating a thread per client (which consumes memory), we use `selectors.DefaultSelector`. This allows the main thread to monitor multiple sockets (clients) and only act when they are ready to Read or Write.