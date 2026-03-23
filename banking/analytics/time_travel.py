"""
Time-Travel Queries for Historical Graph Analysis
==================================================

Enables querying the graph state at any historical point in time,
critical for audits, investigations, and regulatory compliance.

Features:
- Snapshot queries: "What did the graph look like on date X?"
- Evolution tracking: "How did this network evolve over time?"
- Audit reconstruction: "When was this suspicious pattern created?"
- Temporal comparison: "What changed between date A and date B?"

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-03-23
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.python.client.janusgraph_client import JanusGraphClient


class TimeGranularity(Enum):
    """Time granularity for queries."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class GraphSnapshot:
    """Represents graph state at a specific point in time."""
    timestamp: datetime
    vertex_count: int
    edge_count: int
    vertices: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    properties_frozen: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "vertex_count": self.vertex_count,
            "edge_count": self.edge_count,
            "vertices": self.vertices,
            "edges": self.edges,
            "properties_frozen": self.properties_frozen
        }


@dataclass
class TemporalChange:
    """Represents a change between two time points."""
    change_type: str  # "created", "deleted", "modified"
    element_type: str  # "vertex", "edge"
    element_id: str
    timestamp: datetime
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "change_type": self.change_type,
            "element_type": self.element_type,
            "element_id": self.element_id,
            "timestamp": self.timestamp.isoformat(),
            "before": self.before,
            "after": self.after
        }


class TimeTravelQuery:
    """
    Time-travel query engine for historical graph analysis.
    
    JanusGraph supports temporal queries through:
    1. Property TTL (time-to-live) for automatic expiration
    2. Explicit timestamp properties on vertices/edges
    3. Event sourcing pattern (append-only log of changes)
    
    This implementation uses the timestamp property approach
    for maximum compatibility and audit trail requirements.
    """
    
    def __init__(
        self,
        client: JanusGraphClient,
        timestamp_property: str = "createdAt",
        valid_from_property: str = "validFrom",
        valid_to_property: str = "validTo"
    ):
        """
        Initialize time-travel query engine.
        
        Args:
            client: JanusGraph client connection
            timestamp_property: Property name for creation timestamp
            valid_from_property: Property name for validity start
            valid_to_property: Property name for validity end
        """
        self.client = client
        self.timestamp_property = timestamp_property
        self.valid_from_property = valid_from_property
        self.valid_to_property = valid_to_property
    
    def get_snapshot(self, timestamp: datetime) -> GraphSnapshot:
        """
        Get graph state at a specific point in time.
        
        Returns all vertices and edges that were valid at the given timestamp.
        
        Args:
            timestamp: Point in time to query
            
        Returns:
            GraphSnapshot with vertices and edges valid at that time
        """
        ts_str = timestamp.isoformat()
        
        # Query vertices valid at timestamp
        vertex_query = f"""
            g.V().has('{self.valid_from_property}', lte('{ts_str}')).
                has('{self.valid_to_property}', gte('{ts_str}')).
                valueMap().with('~tinkerpop.valueMap.tokens', '~all')
        """
        
        # Query edges valid at timestamp
        edge_query = f"""
            g.E().has('{self.valid_from_property}', lte('{ts_str}')).
                has('{self.valid_to_property}', gte('{ts_str}')).
                valueMap().with('~tinkerpop.valueMap.tokens', '~all')
        """
        
        vertices = self.client.execute(vertex_query)
        edges = self.client.execute(edge_query)
        
        return GraphSnapshot(
            timestamp=timestamp,
            vertex_count=len(vertices) if vertices else 0,
            edge_count=len(edges) if edges else 0,
            vertices=vertices or [],
            edges=edges or []
        )
    
    def get_vertex_history(self, vertex_id: str) -> List[TemporalChange]:
        """
        Get the complete history of a vertex.
        
        Args:
            vertex_id: ID of the vertex to query
            
        Returns:
            List of temporal changes for the vertex
        """
        query = f"""
            g.V('{vertex_id}').valueMap().with('~tinkerpop.valueMap.tokens', '~all')
        """
        
        result = self.client.execute(query)
        if not result:
            return []
        
        # Extract history from properties
        changes = []
        vertex_data = result[0] if isinstance(result, list) else result
        
        if self.valid_from_property in vertex_data:
            created = vertex_data.get(self.valid_from_property)
            changes.append(TemporalChange(
                change_type="created",
                element_type="vertex",
                element_id=vertex_id,
                timestamp=self._parse_timestamp(created),
                after=vertex_data
            ))
        
        if self.valid_to_property in vertex_data:
            modified = vertex_data.get(self.valid_to_property)
            changes.append(TemporalChange(
                change_type="modified",
                element_type="vertex",
                element_id=vertex_id,
                timestamp=self._parse_timestamp(modified),
                before=vertex_data
            ))
        
        return changes
    
    def compare_snapshots(
        self,
        timestamp1: datetime,
        timestamp2: datetime
    ) -> Dict[str, Any]:
        """
        Compare graph states between two points in time.
        
        Args:
            timestamp1: First timestamp (earlier)
            timestamp2: Second timestamp (later)
            
        Returns:
            Dict with added, removed, and modified elements
        """
        snapshot1 = self.get_snapshot(timestamp1)
        snapshot2 = self.get_snapshot(timestamp2)
        
        # Extract vertex IDs
        ids1 = {v.get("id") or v.get("vertexId") or v.get("personId") 
                for v in snapshot1.vertices if v}
        ids2 = {v.get("id") or v.get("vertexId") or v.get("personId") 
                for v in snapshot2.vertices if v}
        
        added = ids2 - ids1
        removed = ids1 - ids2
        common = ids1 & ids2
        
        return {
            "timestamp_from": timestamp1.isoformat(),
            "timestamp_to": timestamp2.isoformat(),
            "vertices_added": len(added),
            "vertices_removed": len(removed),
            "vertices_unchanged": len(common),
            "vertex_count_change": snapshot2.vertex_count - snapshot1.vertex_count,
            "edge_count_change": snapshot2.edge_count - snapshot1.edge_count,
            "snapshot_from": snapshot1.to_dict(),
            "snapshot_to": snapshot2.to_dict()
        }
    
    def get_timeline(
        self,
        start: datetime,
        end: datetime,
        granularity: TimeGranularity = TimeGranularity.DAY
    ) -> List[Dict[str, Any]]:
        """
        Get graph evolution timeline over a period.
        
        Args:
            start: Start timestamp
            end: End timestamp
            granularity: Time granularity for snapshots
            
        Returns:
            List of timeline points with graph statistics
        """
        timeline = []
        current = start
        
        delta = self._get_timedelta(granularity)
        
        while current <= end:
            snapshot = self.get_snapshot(current)
            timeline.append({
                "timestamp": current.isoformat(),
                "vertex_count": snapshot.vertex_count,
                "edge_count": snapshot.edge_count
            })
            current += delta
        
        return timeline
    
    def find_pattern_emergence(
        self,
        pattern_query: str,
        start: datetime,
        end: datetime,
        granularity: TimeGranularity = TimeGranularity.DAY
    ) -> List[Dict[str, Any]]:
        """
        Find when a specific pattern first emerged in the graph.
        
        Args:
            pattern_query: Gremlin query defining the pattern
            start: Start timestamp for search
            end: End timestamp for search
            granularity: Search granularity
            
        Returns:
            List of timestamps where pattern appeared
        """
        emergence_points = []
        current = start
        delta = self._get_timedelta(granularity)
        prev_count = 0
        
        while current <= end:
            ts_str = current.isoformat()
            
            # Modify query to include time filter
            time_filtered_query = f"""
                {pattern_query}.
                has('{self.valid_from_property}', lte('{ts_str}')).
                has('{self.valid_to_property}', gte('{ts_str}'))
            """
            
            try:
                result = self.client.execute(time_filtered_query)
                count = len(result) if result else 0
                
                if count > prev_count:
                    emergence_points.append({
                        "timestamp": current.isoformat(),
                        "pattern_count": count,
                        "new_patterns": count - prev_count
                    })
                
                prev_count = count
            except Exception:
                pass
            
            current += delta
        
        return emergence_points
    
    def reconstruct_audit_trail(
        self,
        element_id: str,
        element_type: str = "vertex"
    ) -> Dict[str, Any]:
        """
        Reconstruct complete audit trail for an element.
        
        Args:
            element_id: ID of element to audit
            element_type: "vertex" or "edge"
            
        Returns:
            Complete audit trail with all changes
        """
        if element_type == "vertex":
            history = self.get_vertex_history(element_id)
        else:
            # Edge history query
            query = f"""
                g.E('{element_id}').valueMap().with('~tinkerpop.valueMap.tokens', '~all')
            """
            result = self.client.execute(query)
            history = []
            if result:
                edge_data = result[0] if isinstance(result, list) else result
                history.append(TemporalChange(
                    change_type="created",
                    element_type="edge",
                    element_id=element_id,
                    timestamp=self._parse_timestamp(
                        edge_data.get(self.valid_from_property)
                    ),
                    after=edge_data
                ))
        
        return {
            "element_id": element_id,
            "element_type": element_type,
            "changes": [c.to_dict() for c in history],
            "total_changes": len(history)
        }
    
    def _parse_timestamp(self, ts: Any) -> datetime:
        """Parse timestamp from various formats."""
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now()
        return datetime.now()
    
    def _get_timedelta(self, granularity: TimeGranularity) -> timedelta:
        """Get timedelta for granularity."""
        deltas = {
            TimeGranularity.SECOND: timedelta(seconds=1),
            TimeGranularity.MINUTE: timedelta(minutes=1),
            TimeGranularity.HOUR: timedelta(hours=1),
            TimeGranularity.DAY: timedelta(days=1),
            TimeGranularity.WEEK: timedelta(weeks=1),
            TimeGranularity.MONTH: timedelta(days=30)
        }
        return deltas[granularity]


def create_time_travel_report(
    client: JanusGraphClient,
    investigation_date: datetime,
    investigation_period_days: int = 30
) -> Dict[str, Any]:
    """
    Create a comprehensive time-travel investigation report.
    
    Args:
        client: JanusGraph client
        investigation_date: Target date for investigation
        investigation_period_days: Number of days to analyze before target
        
    Returns:
        Comprehensive report with timeline, changes, and patterns
    """
    engine = TimeTravelQuery(client)
    
    start_date = investigation_date - timedelta(days=investigation_period_days)
    
    # Get snapshots
    current_snapshot = engine.get_snapshot(investigation_date)
    start_snapshot = engine.get_snapshot(start_date)
    
    # Compare changes
    changes = engine.compare_snapshots(start_date, investigation_date)
    
    # Get timeline
    timeline = engine.get_timeline(
        start_date,
        investigation_date,
        TimeGranularity.DAY
    )
    
    return {
        "investigation_date": investigation_date.isoformat(),
        "period_start": start_date.isoformat(),
        "period_days": investigation_period_days,
        "current_state": current_snapshot.to_dict(),
        "start_state": start_snapshot.to_dict(),
        "changes": changes,
        "timeline": timeline,
        "summary": {
            "vertices_at_start": start_snapshot.vertex_count,
            "vertices_at_end": current_snapshot.vertex_count,
            "net_change": current_snapshot.vertex_count - start_snapshot.vertex_count,
            "edges_at_start": start_snapshot.edge_count,
            "edges_at_end": current_snapshot.edge_count
        }
    }
