from threading import Event, Thread
from typing import Optional, Any, Dict
from datetime import datetime
from cerebrum.utils.communication import Query

class Syscall(Thread):
    """
    Base class for system calls in the AIOS framework.
    
    This class extends Thread to handle asynchronous system calls and provides
    functionality for tracking call status, timing, and response handling.
    
    Example:
        ```python
        class LLMSyscall(Syscall):
            def __init__(self, agent_name: str, query: LLMQuery):
                super().__init__(agent_name, query)
                
        syscall = LLMSyscall("agent_1", LLMQuery(...))
        syscall.start()
        syscall.join()
        response = syscall.get_response()
        ```
    """
    
    def __init__(self, agent_name: str, query: Query):
        """
        Initialize a system call.
        
        Args:
            agent_name: Name of the agent making the call
            query: Query object containing call parameters
            
        Example:
            ```python
            syscall = Syscall("agent_1", Query(operation="read"))
            ```
        """
        super().__init__()
        self.agent_name = agent_name
        self.query = query
        self.event = Event()
        
        # Call identification and status
        self.pid: Optional[int] = None  # Process ID
        self.aid: Optional[str] = None  # Agent ID
        self.status: Optional[str] = None  # Current status of the call
        
        # Response and timing information
        self.response: Optional[Any] = None  # Call response
        self.time_limit: Optional[float] = None  # Time limit for execution
        
        # Timing metrics
        self.created_time: Optional[float] = None  # When call was created
        self.start_time: Optional[float] = None  # When call started execution
        self.end_time: Optional[float] = None  # When call finished execution
        
        # Routing information
        self.source: Optional[str] = None  # Source of the call
        self.target: Optional[str] = None  # Target of the call
        self.priority: Optional[int] = None  # Call priority

    def set_created_time(self, time: float) -> None:
        """
        Set the creation time of the system call.
        
        Example:
            ```python
            syscall.set_created_time(time.time())
            ```
        """
        self.created_time = time

    def get_created_time(self) -> Optional[float]:
        """
        Get the creation time of the system call.
        
        Returns:
            Creation timestamp or None if not set
            
        Example:
            ```python
            created_at = syscall.get_created_time()
            # Returns: 1234567890.123
            ```
        """
        return self.created_time

    def set_start_time(self, time: float) -> None:
        """
        Set the start time of the system call execution.
        
        Example:
            ```python
            syscall.set_start_time(time.time())
            ```
        """
        self.start_time = time

    def get_start_time(self) -> Optional[float]:
        """
        Get the start time of the system call execution.
        
        Returns:
            Start timestamp or None if not started
            
        Example:
            ```python
            start_time = syscall.get_start_time()
            # Returns: 1234567890.234
            ```
        """
        return self.start_time

    def set_end_time(self, time: float) -> None:
        """
        Set the end time of the system call execution.
        
        Example:
            ```python
            syscall.set_end_time(time.time())
            ```
        """
        self.end_time = time

    def get_end_time(self) -> Optional[float]:
        """
        Get the end time of the system call execution.
        
        Returns:
            End timestamp or None if not finished
            
        Example:
            ```python
            end_time = syscall.get_end_time()
            # Returns: 1234567890.345
            ```
        """
        return self.end_time

    def set_priority(self, priority: int) -> None:
        """
        Set the priority level of the system call.
        
        Example:
            ```python
            syscall.set_priority(1)  # High priority
            ```
        """
        self.priority = priority

    def get_priority(self) -> Optional[int]:
        """
        Get the priority level of the system call.
        
        Returns:
            Priority level or None if not set
            
        Example:
            ```python
            priority = syscall.get_priority()
            # Returns: 1
            ```
        """
        return self.priority

    def set_status(self, status: str) -> None:
        """
        Set the current status of the system call.
        
        Example:
            ```python
            syscall.set_status("running")
            ```
        """
        self.status = status

    def get_status(self) -> Optional[str]:
        """
        Get the current status of the system call.
        
        Returns:
            Current status or None if not set
            
        Example:
            ```python
            status = syscall.get_status()
            # Returns: "running"
            ```
        """
        return self.status

    def set_aid(self, aid: str) -> None:
        """
        Set the agent ID for the system call.
        
        Example:
            ```python
            syscall.set_aid("agent_1")
            ```
        """
        self.aid = aid

    def get_aid(self) -> Optional[str]:
        """
        Get the agent ID of the system call.
        
        Returns:
            Agent ID or None if not set
            
        Example:
            ```python
            aid = syscall.get_aid()
            # Returns: "agent_1"
            ```
        """
        return self.aid

    def set_pid(self, pid: int) -> None:
        """
        Set the process ID for the system call.
        
        Example:
            ```python
            syscall.set_pid(12345)
            ```
        """
        self.pid = pid

    def get_pid(self) -> Optional[int]:
        """
        Get the process ID of the system call.
        
        Returns:
            Process ID or None if not set
            
        Example:
            ```python
            pid = syscall.get_pid()
            # Returns: 12345
            ```
        """
        return self.pid

    def get_response(self) -> Optional[Any]:
        """
        Get the response from the system call.
        
        Returns:
            Response data or None if not completed
            
        Example:
            ```python
            response = syscall.get_response()
            # Returns: {"status": "success", "data": "Hello, World!"}
            ```
        """
        return self.response

    def set_response(self, response: Any) -> None:
        """
        Set the response for the system call.
        
        Example:
            ```python
            syscall.set_response({"status": "success", "data": "Hello, World!"})
            ```
        """
        self.response = response

    def get_time_limit(self) -> Optional[float]:
        """
        Get the time limit for the system call execution.
        
        Returns:
            Time limit in seconds or None if not set
            
        Example:
            ```python
            time_limit = syscall.get_time_limit()
            # Returns: 30.0
            ```
        """
        return self.time_limit

    def set_time_limit(self, time_limit: float) -> None:
        """
        Set the time limit for the system call execution.
        
        Example:
            ```python
            syscall.set_time_limit(30.0)  # 30 seconds timeout
            ```
        """
        self.time_limit = time_limit

    def run(self) -> None:
        """
        Execute the system call.
        
        This method is called when the thread starts. It sets the process ID
        and waits for the event to be set.
        
        Example:
            ```python
            syscall.start()  # Calls run() internally
            syscall.event.set()  # Triggers execution
            ```
        """
        # self.set_pid(self.native_id)
        self.event.wait()

    def get_source(self) -> Optional[str]:
        """
        Get the source of the system call.
        
        Returns:
            Source identifier or None if not set
            
        Example:
            ```python
            source = syscall.get_source()
            # Returns: "agent_1"
            ```
        """
        return self.source

    def get_target(self) -> Optional[str]:
        """
        Get the target of the system call.
        
        Returns:
            Target identifier or None if not set
            
        Example:
            ```python
            target = syscall.get_target()
            # Returns: "storage"
            ```
        """
        return self.target

    def set_source(self, source: str) -> None:
        """
        Set the source of the system call.
        
        Example:
            ```python
            syscall.set_source("agent_1")
            ```
        """
        self.source = source

    def set_target(self, target: str) -> None:
        """
        Set the target of the system call.
        
        Example:
            ```python
            syscall.set_target("storage")
            ```
        """
        self.target = target

