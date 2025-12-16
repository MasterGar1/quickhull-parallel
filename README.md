# Parallel QuickHull Client-Server

This project implements the QuickHull algorithm to find the Convex Hull of a set of N-dimensional points. It utilizes a Client-Server architecture where the server performs calculations in parallel.

## Features
**Client-Server Architecture**: TCP communication using Sockets.
**Multi-threaded Server**: The server spawns a new thread for each connected client to handle requests concurrently.
**Parallelization**: The Algorithm uses custom `ThreadPool` and `ProcessPool` implementations to distribute recursive sorting branches across workers.
**Vectorization**: Heavy geometric calculations are vectorized using **NumPy** for high performance.
**Benchmarking**: Automatically compares Serial vs Parallel execution times.

## Prerequisites
- Python 3.13+, GIL free recommended.

## How to Run
0. **Create a virtual environment and install requirements**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux
    source venv/bin/activate 
    pip install -r requirements.txt
   ```

1.  **Start the Server**:
    ```bash
    py server.py
    ```
    The server will listen on `127.0.0.1:65432`.

    The server can be shut down using *Ctrl+C*.

2.  **Start the Client** (in a new terminal):
    ```bash
    py client.py
    ```

3.  **Interaction**:
    - Enter the number of points (recommend  1,000,000 to see parallel benefits).
    - Enter the number of worker threads.
    - Enter the amount of dimensions the points should have.
    - View the timing results in the console.

## Implementation Details

### Algorithm
The QuickHull algorithm is a divide-and-conquer algorithm. 
- **Vectorization**: The partition step (calculating distances and filtering points) is fully vectorized using NumPy, allowing millions of points to be processed efficiently in compiled C code.
- **Parallel Strategy**: The algorithm parallelizes the recursive expansion phase. Initial heavy partition tasks are distributed across a `ThreadPool` (or `ProcessPool`) to maximize core usage, especially effective in GIL-free Python environments.

### Networking
- **Threading**: The server utilizes the `threading` module to handle multiple clients simultaneously. Each incoming connection is assigned a dedicated thread, allowing the server to process multiple requests in parallel without blocking the main listening loop.