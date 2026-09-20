import math
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("AIOS.Scheduler.Ledger")

@dataclass
class AgentRecord:
    agent_id: str
    priority: str = "NORMAL"  # HIGH, NORMAL, LOW
    weight: float = 1.0       # Used for Fair-Share / Stride scheduling
    arrival_time: float = 0.0
    wait_ticks: int = 0
    service_count: int = 0
    total_service_time: float = 0.0

class AgentLedger:
    """
    Tracks per-agent scheduling state, accounting metrics, 
    and quantitative fairness evaluations for AIOS scheduling policies.
    """
    def __init__(self):
        self.agents: Dict[str, AgentRecord] = {}

    def register_agent(self, agent_id: str, priority: str = "NORMAL", weight: float = 1.0, arrival_time: float = 0.0) -> AgentRecord:
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentRecord(
                agent_id=agent_id,
                priority=priority,
                weight=weight,
                arrival_time=arrival_time
            )
            logger.info(f"Registered agent {agent_id} with priority {priority} and weight {weight}.")
        return self.agents[agent_id]

    def update_waiting_ticks(self, queued_agent_ids: List[str]) -> None:
        """Increment wait_ticks for all requests currently waiting in the scheduler queue."""
        for agent_id in queued_agent_ids:
            if agent_id in self.agents:
                self.agents[agent_id].wait_ticks += 1

    def record_service(self, agent_id: str, service_count: int = 1) -> None:
        """Record when an agent is selected and receives scheduling service."""
        if agent_id in self.agents:
            self.agents[agent_id].service_count += service_count
            logger.debug(f"Agent {agent_id} service count updated to {self.agents[agent_id].service_count}.")
            
    def get_wait_ticks(self, agent_id: str) -> int:
        return self.agents[agent_id].wait_ticks if agent_id in self.agents else 0

    def calculate_jains_fairness_index(self) -> float:
        """
        Computes Jain's fairness index across all registered agents 
        based on their service counts (allocations).
        Formula: J = (sum(x_i))^2 / (n * sum(x_i^2))
        """
        allocations = [record.service_count for record in self.agents.values()]
        n = len(allocations)
        if n == 0:
            return 1.0
        
        sum_x = sum(allocations)
        sum_x_sq = sum(x ** 2 for x in allocations)
        
        if sum_x_sq == 0:
            return 1.0
            
        fairness_index = (sum_x ** 2) / (n * sum_x_sq)
        return float(fairness_index)

    def generate_report(self) -> Dict:
        """Provides structured observability reporting for per-agent statistics."""
        report = {
            "agents": {
                aid: {
                    "priority": rec.priority,
                    "weight": rec.weight,
                    "wait_ticks": rec.wait_ticks,
                    "service_count": rec.service_count
                }
                for aid, rec in self.agents.items()
            },
            "jains_fairness_index": self.calculate_jains_fairness_index()
        }
        return report