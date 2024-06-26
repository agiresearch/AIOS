# src/scheduler/

This contains the mechanism for scheduling multiple agents at the same time under the same LLM. Both FIFOScheduler and RRScheduler use threads internally and use queues to manage data being sent between the LLM and the agents.

Both schedulers rely on the underlying FIFO Queue mechanism for scheduling, which returns which agent is not blocking first. RRScheduler has a much shorter wait time of 0.05 seconds, which is why it is distributing CPU time more evenly, but at the cost of more iterations. The FIFOScheduler waits a second, which makes it more **likely** that whatever enters the queue first exits first, however this is not always the case.
