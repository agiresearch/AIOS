# aios/context

This folder contains the SimpleContextManager class and the base implementation.
This allows for snapshotting of context data for the LLMs.

The context stores the tensors which contains the weights and biases, the epoch number, and optimizations. This is used for offloading models to the disk which may be downloaded from HuggingFace or related sources.
