# Parallel QuickHull Client-Server

This project implements the QuickHull algorithm to find the Convex Hull of a set of N-dimensional points. It utilizes a Client-Server architecture where the server performs calculations in parallel.

## Features
**Client-Server Architecture**: TCP communication using Sockets.
**Multi-threaded Server**: The server spawns a new thread for each connected client to handle requests concurrently.
**Parallelization**: The Algorithm uses a custom `ThreadPool` to distribute recursive sorting branches across worker threads.
**Benchmarking**: Automatically compares Serial vs Parallel execution times.

## Prerequisites
- Python 3.13+, GIL free recommended.
- There are no external libraries included in this project.

## How to Run

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
    - Enter the number of points (recommend > 1,000,000 to see parallel benefits).
    - Enter the number of worker threads.
    - Enter the amount of dimensions the points should have.
    - View the timing results in the console.

## Implementation Details

### Algorithm
The QuickHull algorithm is a divide-and-conquer algorithm. 
- **Parallel Strategy**: After finding the min/max X points, the dataset is split into "Upper" and "Lower" sets. These two recursive calls are heavy and independent, so they are offloaded to separate threads using a custom `ThreadPool`.

### Networking
- **Threading**: The server utilizes the `threading` module to handle multiple clients simultaneously. Each incoming connection is assigned a dedicated thread, allowing the server to process multiple requests in parallel without blocking the main listening loop.