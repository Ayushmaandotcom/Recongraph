from typing import Iterable, Sequence

from recongraph.learning.protocols import LearningAgent, LearnedInsight
from recongraph.graph.review import ReviewPacket, ReviewOutcome

class LearningManager:
    """
    Manages a portfolio of LearningAgents.
    Orchestrates the distribution of human review outcomes to all active learners.
    """
    
    def __init__(self, agents: Sequence[LearningAgent]):
        self.agents = agents
        
    def observe(self, packet: ReviewPacket, outcome: ReviewOutcome) -> None:
        """Broadcasts a single review outcome to all learning agents."""
        for agent in self.agents:
            agent.observe(packet, outcome)
            
    def observe_batch(self, packets: Sequence[ReviewPacket], outcomes: Sequence[ReviewOutcome]) -> None:
        """Broadcasts a batch of review outcomes to all learning agents."""
        if len(packets) != len(outcomes):
            raise ValueError("Packets and outcomes must be the same length.")
            
        for packet, outcome in zip(packets, outcomes):
            self.observe(packet, outcome)
            
    def extract_insights(self) -> Iterable[LearnedInsight]:
        """Harvests all newly generated insights from all agents."""
        all_insights = []
        for agent in self.agents:
            insights = list(agent.get_insights())
            all_insights.extend(insights)
        return all_insights
