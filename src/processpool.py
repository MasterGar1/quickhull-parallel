from threading import Thread
from multiprocessing import Process, Queue, JoinableQueue, Event, cpu_count
import traceback

def worker_function(task_queue: JoinableQueue, result_queue: Queue) -> None:
    while True:
        task = task_queue.get()
        if task is None:
            task_queue.task_done()
            break

        task_id, func, args, kwargs = task
        try:
            res = func(*args, **kwargs)
            result_queue.put((task_id, True, res))
        except Exception as e:
            tb = traceback.format_exc()
            result_queue.put((task_id, False, Exception(f"{str(e)}\n{tb}")))
        finally:
            task_queue.task_done()

class Future:
    def __init__(self):
        self._result = None
        self._exception = None
        self._event = Event()
    
    def set_result(self, result: any) -> None:
        self._result = result
        self._event.set()
    
    def set_exception(self, exception: Exception) -> None:
        self._exception = exception
        self._event.set()
    
    def get_result(self) -> any:
        self._event.wait()
        if self._exception:
            raise self._exception
        return self._result

class ProcessPool:
    def __init__(self, num_processes: int = None):
        if num_processes is None:
            num_processes = cpu_count()
        
        self.num_processes = num_processes
        self.tasks: JoinableQueue = JoinableQueue()
        self.results_queue: Queue = Queue()
        self.processes: list[Process] = []
        self._is_shut: bool = False

        for _ in range(num_processes):
            p = Process(target=worker_function, args=(self.tasks, self.results_queue), daemon=True)
            p.start()
            self.processes.append(p)
            
        self.futures = {} 
        
        self.result_handler = Thread(target=self._handle_results, daemon=True)
        self.result_handler.start()
        self.task_counter = 0

    def _handle_results(self):
        while True:
            if self._is_shut and not self.futures:
                break
                
            try:
                task_id, success, data = self.results_queue.get()
                
                future = self.futures.pop(task_id, None)
                if future:
                    if success:
                        future.set_result(data)
                    else:
                        future.set_exception(data)
            except Exception:
                break

    def submit(self, func, *args, **kwargs) -> Future:
        if self._is_shut:
            raise RuntimeError("ProcessPool is shut down")
        
        future = Future()
        task_id = self.task_counter
        self.task_counter += 1
        
        self.futures[task_id] = future
        self.tasks.put((task_id, func, args, kwargs))
        return future

    def shutdown(self) -> None:
        self._is_shut = True
        for _ in self.processes:
            self.tasks.put(None)
        
        for p in self.processes:
            p.join()