"""
Mock Producer for Testing
=========================

Simple mock producer for testing without requiring Pulsar.

Author: AI Assistant
Date: 2026-04-10
"""

from typing import List

from banking.streaming.events import EntityEvent


class MockProducer:
    """Mock producer that stores events in memory instead of sending to Pulsar."""
    
    def __init__(self):
        """Initialize mock producer."""
        self.events: List[EntityEvent] = []
        self.send_count = 0
    
    def send(self, event: EntityEvent) -> None:
        """Store event in memory."""
        self.events.append(event)
        self.send_count += 1
    
    def close(self) -> None:
        """No-op close."""
        pass
    
    def get_events(self) -> List[EntityEvent]:
        """Get all stored events."""
        return self.events
    
    def clear(self) -> None:
        """Clear all stored events."""
        self.events.clear()
        self.send_count = 0

# Made with Bob
