# aios/

This folder contains the internal implementation of AIOS.

```
command_executor.py
command_parser.py
```

are helper utilities that transfer the command to the agent of the requested command.

## Base Implementations
The structure of this code contains a number of base implementations which are subclassed and extended for each use case. For example, the BaseLLMKernel class provides an abstract implementation of the kernel for others to implement.

For more information, enter the subdirectories.
