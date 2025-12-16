"""
ThreadPool and ProcessPool classes that manage pools of workers and a Future class for handling asynchronous results.
"""
from multiprocessing import Process, cpu_count, Queue as MPQueue
from threading       import Thread, Event
from queue           import Queue
from typing          import Any

class Future:
    """Represents a future result of an asynchronous computation."""
    def __init__(self):
        """Initializes the Future object."""
        self._result: Any = None
        self._exception: Exception = None
        self._event: Event = Event()
    
    def set_result(self, res: Any) -> None:
        """Sets the result of the computation and signals completion."""
        self._result = res
        self._event.set()
    
    def set_exception(self, exc: Exception) -> None:
        """Sets an exception if the computation failed."""
        self._exception = exc
        self._event.set()
    
    def get_result(self) -> Any:
        """Waits for the computation to complete and returns the result or raises an exception."""
        self._event.wait()
        if self._exception:
            raise self._exception
        return self._result

class ThreadPool:
    """Represents a thread pool for executing asynchronous tasks."""
    def __init__(self, num_threads: int):
        """Initializes the ThreadPool with a specified number of worker threads."""
        self.num_threads: int = num_threads
        self.tasks: Queue = Queue()
        self.res_queue: Queue = Queue()
        self.threads: list[Thread] = []
        self.futures: dict[int, Future] = {}
        self.res_hand: Thread = Thread(target=self._handle_results, daemon=True)
        self.task_count: int = 0
        self._is_shut: bool = False

        self.res_hand.start()

        for _ in range(num_threads):
            t = Thread(target=_thread_worker, args=(self.tasks, self.res_queue), daemon=True)
            t.start()
            self.threads.append(t)

    def _handle_results(self) -> None:
        """Background thread that moves results from the internal queue to Future objects."""
        while True:
            if self._is_shut and not self.futures:
                break
            tid, suc, data = self.res_queue.get()
            
            future: Future = self.futures.pop(tid, None)
            if future:
                if suc:
                    future.set_result(data)
                else:
                    future.set_exception(data)

    def submit(self, func, *args, **kwargs) -> Future:
        """Submits a function to be executed by the thread pool."""
        if self._is_shut: raise RuntimeError("[Error] ThreadPool is shut down")
        
        future: Future = Future()
        tid: int = self.task_count
        self.task_count += 1
        
        self.futures[tid] = future
        self.tasks.put((tid, func, args, kwargs))
        return future

    def shutdown(self) -> None:
        """Shuts down the thread pool and waits for all threads to finish."""
        self._is_shut = True

        for _ in self.threads: self.tasks.put(None)
        for t in self.threads: t.join()

class ProcessPool:
    """Represents a process pool for executing asynchronous tasks."""
    def __init__(self, num_processes: int = None):
        """Initializes the ProcessPool with a specified number of worker processes."""
        if num_processes is None:
            try:
                num_processes = cpu_count()
            except NotImplementedError:
                num_processes = 4

        self.num_processes: int = num_processes
        self.tasks: MPQueue = MPQueue()
        self.res_queue: MPQueue = MPQueue()
        self.processes: list[Process] = []
        self.futures: dict[int, Future] = {}
        self.res_hand: Thread = Thread(target=self._handle_results, daemon=True)
        self.task_count: int = 0
        self._is_shut: bool = False

        self.res_hand.start()

        for _ in range(num_processes):
            p = Process(target=_process_worker, args=(self.tasks, self.res_queue), daemon=True)
            p.start()
            self.processes.append(p)

    def _handle_results(self) -> None:
        """Background thread that moves results from the internal queue to Future objects."""
        while True:
            if self._is_shut and not self.futures:
                break
            
            try:
                tid, suc, data = self.res_queue.get()
            except Exception:
                break
            
            future: Future = self.futures.pop(tid, None)
            if future:
                if suc:
                    future.set_result(data)
                else:
                    future.set_exception(data)

    def submit(self, func, *args, **kwargs) -> Future:
        """Submits a function to be executed by the process pool."""
        if self._is_shut: raise RuntimeError("[Error] ProcessPool is shut down")
        
        future: Future = Future()
        tid: int = self.task_count
        self.task_count += 1
        
        self.futures[tid] = future
        self.tasks.put((tid, func, args, kwargs))
        return future

    def shutdown(self) -> None:
        """Shuts down the process pool and waits for all processes to finish."""
        self._is_shut = True

        for _ in self.processes: self.tasks.put(None)
        for p in self.processes: p.join()

def _thread_worker(task_queue: Queue, res_queue: Queue) -> None:
    """Worker function that retrieves tasks from the queue and executes them."""
    while True:
        task: tuple[int, callable, list, dict] = task_queue.get()
        if task is None:
            task_queue.task_done()
            break

        tid, func, args, kwargs = task
        try:
            res: Any = func(*args, **kwargs)
            res_queue.put((tid, True, res))
        except Exception as e:
            res_queue.put((tid, False, Exception(str(e))))
        finally:
            task_queue.task_done()

def _process_worker(task_queue: MPQueue, res_queue: MPQueue) -> None:
    """Worker function that retrieves tasks from the queue and executes them."""
    while True:
        task = task_queue.get()
        if task is None:
            break

        tid, func, args, kwargs = task
        try:
            res: Any = func(*args, **kwargs)
            res_queue.put((tid, True, res))
        except Exception as e:
            res_queue.put((tid, False, e))