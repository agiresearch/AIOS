import pytest
from aios.scheduler.ledger import AgentLedger

def test_agent_registration_and_waiting_accounting():
    ledger = AgentLedger()
    ledger.register_agent("agent_1", priority="LOW", arrival_time=0.0)
    
    assert ledger.get_wait_ticks("agent_1") == 0
    
    # Simulate queue waiting ticks update
    ledger.update_waiting_ticks(["agent_1"])
    ledger.update_waiting_ticks(["agent_1"])
    
    assert ledger.get_wait_ticks("agent_1") == 2

def test_service_accounting():
    ledger = AgentLedger()
    ledger.register_agent("agent_A")
    ledger.record_service("agent_A", service_count=5)
    
    report = ledger.generate_report()
    assert report["agents"]["agent_A"]["service_count"] == 5

def test_jains_fairness_index():
    ledger = AgentLedger()
    ledger.register_agent("agent_1")
    ledger.register_agent("agent_2")
    
    # Perfectly equal allocation should give fairness index = 1.0
    ledger.record_service("agent_1", 10)
    ledger.record_service("agent_2", 10)
    assert pytest.approx(ledger.calculate_jains_fairness_index(), 0.01) == 1.0
    
    # Unequal allocation
    ledger2 = AgentLedger()
    ledger2.register_agent("agent_1")
    ledger2.register_agent("agent_2")
    ledger2.record_service("agent_1", 20)
    ledger2.record_service("agent_2", 10)
    
    # J = (30)^2 / (2 * (400 + 100)) = 900 / 1000 = 0.9
    assert pytest.approx(ledger2.calculate_jains_fairness_index(), 0.01) == 0.9