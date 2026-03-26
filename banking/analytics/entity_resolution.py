"""
Entity Resolution for Banking Compliance and Fraud Detection
=============================================================

Provides multi-level entity resolution capabilities for:
1. Standard: Customer deduplication during onboarding
2. High-Complexity: UBO/Sanctions multi-hop resolution
3. Ultra-High: Synthetic identity fraud ring detection

Key Concepts:
- Entity Resolution: Identifying when multiple records refer to the same real-world entity
- Graph-Based Resolution: Using relationships to improve matching accuracy
- Multi-Hop Resolution: Traversing ownership chains to find ultimate beneficial owners
- Confidence Scoring: Weighted combination of match signals

Business Value:
- Reduce duplicate customer records (operational efficiency)
- Ensure accurate KYC/AML screening (compliance)
- Detect sophisticated fraud schemes (risk mitigation)
- Support regulatory reporting (UBO registers, SAR filings)

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-03-23
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import re

from src.python.client.janusgraph_client import JanusGraphClient


class ResolutionComplexity(Enum):
    """Complexity levels for entity resolution."""
    STANDARD = "standard"           # Single-domain, direct matching
    HIGH = "high"                   # Multi-domain, multi-hop
    ULTRA_HIGH = "ultra_high"       # Multi-dimensional, network-based


class MatchType(Enum):
    """Types of matches in entity resolution."""
    EXACT = "exact"                 # Identical values
    FUZZY = "fuzzy"                 # Similar but not identical
    PHONETIC = "phonetic"           # Sounds similar (Soundex, Metaphone)
    DERIVATIVE = "derivative"       # Derived from (e.g., nickname)
    TRANSPOSITION = "transposition" # Character swap
    TEMPORAL = "temporal"           # Time-based relationship
    NETWORK = "network"             # Graph-based relationship


@dataclass
class MatchSignal:
    """A single signal contributing to entity match confidence."""
    attribute: str
    value_a: Any
    value_b: Any
    match_type: MatchType
    score: float
    weight: float
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attribute": self.attribute,
            "value_a": str(self.value_a),
            "value_b": str(self.value_b),
            "match_type": self.match_type.value,
            "score": self.score,
            "weight": self.weight,
            "weighted_score": self.score * self.weight,
            "explanation": self.explanation
        }


@dataclass
class EntityMatch:
    """Result of comparing two entities."""
    entity_a_id: str
    entity_b_id: str
    confidence: float
    match_signals: List[MatchSignal]
    resolution_action: str  # "merge", "link", "review", "separate"
    complexity: ResolutionComplexity
    hops: int = 0
    network_signals: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_a_id": self.entity_a_id,
            "entity_b_id": self.entity_b_id,
            "confidence": self.confidence,
            "resolution_action": self.resolution_action,
            "complexity": self.complexity.value,
            "hops": self.hops,
            "signals": [s.to_dict() for s in self.match_signals],
            "network_signals": self.network_signals
        }


@dataclass
class EntityCluster:
    """A cluster of resolved entities representing one real-world entity."""
    cluster_id: str
    canonical_entity_id: str
    member_ids: Set[str]
    confidence: float
    entity_type: str
    aliases: List[str]
    risk_indicators: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "canonical_entity_id": self.canonical_entity_id,
            "member_count": len(self.member_ids),
            "member_ids": list(self.member_ids),
            "confidence": self.confidence,
            "entity_type": self.entity_type,
            "aliases": self.aliases,
            "risk_indicators": self.risk_indicators
        }


class NameMatcher:
    """
    Advanced name matching for entity resolution.
    
    Handles:
    - Exact matches
    - Fuzzy matches (Levenshtein distance)
    - Phonetic matches (Soundex, Metaphone)
    - Cultural variants (John/Ivan/Johann)
    - Nicknames (Robert/Bob, William/Bill)
    - Transliteration (Schmidt/Шмидт)
    """
    
    # Common nickname mappings
    NICKNAMES = {
        "robert": ["bob", "rob", "bobby", "robbie"],
        "william": ["bill", "will", "billy", "willy"],
        "richard": ["dick", "rick", "rich", "ricky"],
        "michael": ["mike", "mikey", "mick"],
        "elizabeth": ["liz", "beth", "betty", "eliza", "lizzy"],
        "margaret": ["maggie", "meg", "peggy", "marge"],
        "jennifer": ["jen", "jenny", "jenn"],
        "katherine": ["kate", "kathy", "katie", "kay"],
        "patricia": ["pat", "patty", "tricia"],
        "david": ["dave", "davey"],
        "james": ["jim", "jimmy", "jamie"],
        "john": ["jack", "johnny"],
        "thomas": ["tom", "tommy"],
        "charles": ["charlie", "chuck", "chas"],
        "christopher": ["chris", "topher"],
        "daniel": ["dan", "danny"],
        "matthew": ["matt", "matty"],
        "anthony": ["tony", "ant"],
        "joseph": ["joe", "joey"],
        "andrew": ["andy", "drew"],
        "jonathan": ["jon", "johnny"],
        "hans": ["hannes", "johann", "john"],
        "ivan": ["john", "ioann", "jan"],
        "juan": ["john", "ivan"],
        "jean": ["john", "ivan"],
    }
    
    # Cultural name equivalents
    CULTURAL_EQUIVALENTS = {
        ("john", "ivan"): 0.85,
        ("john", "hans"): 0.85,
        ("john", "jean"): 0.80,
        ("john", "juan"): 0.80,
        ("smith", "schmidt"): 0.85,
        ("smith", "smirnov"): 0.70,
        ("smith", "smythe"): 0.90,
    }
    
    @classmethod
    def compare_names(cls, name_a: str, name_b: str) -> Tuple[float, MatchType, str]:
        """
        Compare two names and return match score.
        
        Returns:
            Tuple of (score, match_type, explanation)
        """
        name_a_lower = name_a.lower().strip()
        name_b_lower = name_b.lower().strip()
        
        # Exact match
        if name_a_lower == name_b_lower:
            return (1.0, MatchType.EXACT, f"Exact match: '{name_a}' = '{name_b}'")
        
        # Check nicknames
        for canonical, nicks in cls.NICKNAMES.items():
            all_variants = [canonical] + nicks
            if name_a_lower in all_variants and name_b_lower in all_variants:
                return (0.90, MatchType.DERIVATIVE, 
                        f"Nickname variants: '{name_a}' and '{name_b}' are both forms of '{canonical}'")
        
        # Check cultural equivalents
        key = tuple(sorted([name_a_lower, name_b_lower]))
        if key in cls.CULTURAL_EQUIVALENTS:
            score = cls.CULTURAL_EQUIVALENTS[key]
            return (score, MatchType.PHONETIC, 
                    f"Cultural equivalents: '{name_a}' ≈ '{name_b}' (cross-cultural variant)")
        
        # Fuzzy match (Levenshtein)
        distance = cls._levenshtein_distance(name_a_lower, name_b_lower)
        max_len = max(len(name_a_lower), len(name_b_lower))
        similarity = 1.0 - (distance / max_len) if max_len > 0 else 0.0
        
        if similarity >= 0.85:
            return (similarity, MatchType.FUZZY, 
                    f"Fuzzy match: '{name_a}' ≈ '{name_b}' (similarity: {similarity:.2f})")
        
        # Phonetic match (simplified Soundex)
        soundex_a = cls._soundex(name_a_lower)
        soundex_b = cls._soundex(name_b_lower)
        if soundex_a == soundex_b and soundex_a != "0000":
            return (0.70, MatchType.PHONETIC, 
                    f"Phonetic match: '{name_a}' sounds like '{name_b}' (Soundex: {soundex_a})")
        
        # No match
        return (0.0, MatchType.EXACT, f"No match: '{name_a}' ≠ '{name_b}'")
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return NameMatcher._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def _soundex(name: str) -> str:
        """Generate Soundex code for a name."""
        if not name:
            return "0000"
        
        # Soundex encoding
        mapping = {
            'b': '1', 'f': '1', 'p': '1', 'v': '1',
            'c': '2', 'g': '2', 'j': '2', 'k': '2', 'q': '2', 's': '2', 'x': '2', 'z': '2',
            'd': '3', 't': '3',
            'l': '4',
            'm': '5', 'n': '5',
            'r': '6'
        }
        
        name = name.lower()
        code = name[0].upper()
        prev = mapping.get(name[0], '0')
        
        for char in name[1:]:
            curr = mapping.get(char, '0')
            if curr != '0' and curr != prev:
                code += curr
            prev = curr
            if len(code) == 4:
                break
        
        return (code + '000')[:4]


class EntityResolver:
    """
    Multi-level entity resolution engine for banking compliance.
    
    Supports three complexity levels:
    1. Standard: Direct attribute matching for deduplication
    2. High: Multi-hop resolution through ownership chains
    3. Ultra-High: Network-based resolution with behavioral signals
    """
    
    # Attribute weights for different resolution contexts
    ATTRIBUTE_WEIGHTS = {
        "standard": {
            "ssn": 0.30,
            "tax_id": 0.30,
            "passport": 0.25,
            "dob": 0.20,
            "name": 0.15,
            "phone": 0.15,
            "email": 0.10,
            "address": 0.10,
        },
        "high_complexity": {
            "name": 0.20,
            "dob": 0.15,
            "passport": 0.20,
            "nationality": 0.10,
            "company_name": 0.15,
            "jurisdiction": 0.05,
            "director_overlap": 0.10,
            "address": 0.05,
        },
        "ultra_high": {
            "ssn": 0.15,
            "name": 0.10,
            "dob": 0.10,
            "address": 0.10,
            "phone": 0.08,
            "device_fingerprint": 0.12,
            "ip_address": 0.10,
            "behavioral_pattern": 0.15,
            "network_position": 0.10,
        }
    }
    
    def __init__(self, client: JanusGraphClient):
        """
        Initialize entity resolver.
        
        Args:
            client: JanusGraph client connection
        """
        self.client = client
    
    def resolve(
        self,
        entity_a_id: str,
        entity_b_id: str,
        complexity: ResolutionComplexity = ResolutionComplexity.STANDARD
    ) -> EntityMatch:
        """
        Resolve whether two entities are the same real-world entity.
        
        Args:
            entity_a_id: First entity ID
            entity_b_id: Second entity ID
            complexity: Resolution complexity level
            
        Returns:
            EntityMatch with confidence and signals
        """
        # Fetch entity data
        entity_a = self._fetch_entity(entity_a_id)
        entity_b = self._fetch_entity(entity_b_id)
        
        if not entity_a or not entity_b:
            return EntityMatch(
                entity_a_id=entity_a_id,
                entity_b_id=entity_b_id,
                confidence=0.0,
                match_signals=[],
                resolution_action="review",
                complexity=complexity
            )
        
        signals = []
        
        if complexity == ResolutionComplexity.STANDARD:
            signals = self._standard_resolution(entity_a, entity_b)
        elif complexity == ResolutionComplexity.HIGH:
            signals = self._high_complexity_resolution(entity_a, entity_b)
        else:
            signals = self._ultra_high_resolution(entity_a, entity_b)
        
        # Calculate confidence
        total_weight = sum(s.weight for s in signals)
        weighted_score = sum(s.score * s.weight for s in signals)
        confidence = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Determine action
        action = self._determine_action(confidence, complexity)
        
        return EntityMatch(
            entity_a_id=entity_a_id,
            entity_b_id=entity_b_id,
            confidence=confidence,
            match_signals=signals,
            resolution_action=action,
            complexity=complexity
        )
    
    def find_duplicates(
        self,
        entity_type: str = "Person",
        threshold: float = 0.85
    ) -> List[EntityMatch]:
        """
        Find potential duplicate entities in the graph.
        
        Args:
            entity_type: Type of entity to check
            threshold: Minimum confidence for duplicate
            
        Returns:
            List of potential duplicate matches
        """
        # Get all entities of type
        query = f"g.V().hasLabel('{entity_type}').valueMap().with('~tinkerpop.valueMap.tokens', '~all')"
        entities = self.client.execute(query)
        
        duplicates = []
        checked = set()
        
        for i, entity_a in enumerate(entities):
            for entity_b in entities[i+1:]:
                pair_key = tuple(sorted([entity_a.get("id"), entity_b.get("id")]))
                if pair_key in checked:
                    continue
                checked.add(pair_key)
                
                match = self.resolve(
                    entity_a.get("id"),
                    entity_b.get("id"),
                    ResolutionComplexity.STANDARD
                )
                
                if match.confidence >= threshold:
                    duplicates.append(match)
        
        return duplicates
    
    def resolve_ubo_chain(
        self,
        company_id: str,
        max_hops: int = 5,
        ownership_threshold: float = 0.25
    ) -> List[EntityCluster]:
        """
        Resolve ultimate beneficial owners through ownership chains.
        
        This is HIGH COMPLEXITY resolution - traverses multiple
        corporate layers to find natural persons with significant control.
        
        Args:
            company_id: Starting company ID
            max_hops: Maximum ownership chain length
            ownership_threshold: Minimum ownership percentage
            
        Returns:
            List of entity clusters representing UBOs
        """
        ubo_clusters = []
        visited = set()
        
        def traverse_ownership(entity_id: str, path: List[str], ownership_pct: float):
            if entity_id in visited or len(path) > max_hops:
                return
            
            visited.add(entity_id)
            
            # Get entity type
            type_query = f"g.V('{entity_id}').label()"
            entity_type = self.client.execute(type_query)
            entity_type = entity_type[0] if entity_type else "Unknown"
            
            if entity_type == "Person":
                # Found a natural person - potential UBO
                if ownership_pct >= ownership_threshold:
                    entity_data = self._fetch_entity(entity_id)
                    cluster = EntityCluster(
                        cluster_id=f"ubo-{entity_id}",
                        canonical_entity_id=entity_id,
                        member_ids={entity_id},
                        confidence=0.90,
                        entity_type="UBO",
                        aliases=[entity_data.get("name", "Unknown")],
                        risk_indicators=self._assess_ubo_risk(entity_id, path)
                    )
                    ubo_clusters.append(cluster)
            elif entity_type == "Company":
                # Continue traversing ownership
                shares_query = f"""
                    g.V('{entity_id}').inE('owns_share').as('e').
                        outV().as('owner').
                        select('e', 'owner').
                        by('percentage').
                        by('id')
                """
                ownerships = self.client.execute(shares_query)
                
                for own in ownerships:
                    if isinstance(own, dict):
                        owner_id = own.get("owner")
                        pct = own.get("e", 0)
                        if isinstance(pct, (int, float)):
                            traverse_ownership(
                                owner_id,
                                path + [entity_id],
                                ownership_pct * (pct / 100)
                            )
        
        traverse_ownership(company_id, [], 1.0)
        return ubo_clusters
    
    def detect_synthetic_identities(
        self,
        min_cluster_size: int = 3
    ) -> List[EntityCluster]:
        """
        Detect synthetic identity fraud rings using network analysis.
        
        This is ULTRA-HIGH COMPLEXITY resolution - combines:
        - Identity attribute matching
        - Behavioral pattern analysis
        - Network community detection
        - Device/fingerprint correlation
        
        Args:
            min_cluster_size: Minimum identities in a fraud ring
            
        Returns:
            List of entity clusters representing potential fraud rings
        """
        fraud_rings = []
        
        # Find clusters by shared addresses
        address_query = """
            g.V().hasLabel('Person').as('p').
                out('has_address').as('a').
                group().
                by('a').
                by('p')
        """
        address_groups = self.client.execute(address_query)
        
        for address, persons in address_groups.items():
            if len(persons) >= min_cluster_size:
                # Check for synthetic identity indicators
                signals = self._analyze_synthetic_indicators(persons)
                
                if signals["score"] >= 0.70:
                    cluster = EntityCluster(
                        cluster_id=f"synthetic-{hashlib.md5(address.encode()).hexdigest()[:8]}",
                        canonical_entity_id=persons[0],
                        member_ids=set(persons),
                        confidence=signals["score"],
                        entity_type="SyntheticIdentityRing",
                        aliases=[],
                        risk_indicators=signals["indicators"]
                    )
                    fraud_rings.append(cluster)
        
        return fraud_rings
    
    def _fetch_entity(self, entity_id: str) -> Dict[str, Any]:
        """Fetch entity data from graph.
        
        Args:
            entity_id: The business ID (personId, companyId, accountId) of the entity
            
        Returns:
            Dict with entity properties including '_internal_id' for graph operations
        """
        from gremlin_python.process.traversal import T
        
        # Query by property ID (personId, companyId, accountId) rather than internal JanusGraph ID
        # JanusGraph uses internal numeric IDs, so we must use has() to find by business ID
        # Try common ID properties in order
        for prop in ('personId', 'companyId', 'accountId', 'id'):
            query = f"g.V().has('{prop}', '{entity_id}').elementMap()"
            try:
                result = self.client.execute(query)
                if result:
                    entity = result[0] if isinstance(result, list) else result
                    # Extract internal ID from elementMap (key is T.id, not 'id')
                    internal_id = None
                    for key, value in entity.items():
                        if key == T.id:
                            internal_id = str(value)
                            break
                    # Store internal ID for graph operations
                    if internal_id:
                        entity['_internal_id'] = internal_id
                    return entity
            except Exception:
                continue
        return {}
    
    def _standard_resolution(
        self,
        entity_a: Dict[str, Any],
        entity_b: Dict[str, Any]
    ) -> List[MatchSignal]:
        """Standard resolution: direct attribute comparison."""
        signals = []
        weights = self.ATTRIBUTE_WEIGHTS["standard"]
        
        # Compare SSN/Tax ID (highest weight)
        for attr in ["ssn", "taxId", "passportNumber"]:
            val_a = entity_a.get(attr)
            val_b = entity_b.get(attr)
            if val_a and val_b:
                score = 1.0 if val_a == val_b else 0.0
                signals.append(MatchSignal(
                    attribute=attr,
                    value_a=val_a,
                    value_b=val_b,
                    match_type=MatchType.EXACT if score == 1.0 else MatchType.EXACT,
                    score=score,
                    weight=weights.get("ssn", 0.25),
                    explanation=f"{'Match' if score == 1.0 else 'No match'} on {attr}"
                ))
        
        # Compare DOB
        dob_a = entity_a.get("dateOfBirth") or entity_a.get("dob")
        dob_b = entity_b.get("dateOfBirth") or entity_b.get("dob")
        if dob_a and dob_b:
            score = 1.0 if dob_a == dob_b else 0.0
            signals.append(MatchSignal(
                attribute="dob",
                value_a=dob_a,
                value_b=dob_b,
                match_type=MatchType.EXACT,
                score=score,
                weight=weights.get("dob", 0.20),
                explanation=f"DOB {'match' if score == 1.0 else 'mismatch'}"
            ))
        
        # Compare names (fuzzy)
        name_a = entity_a.get("name") or entity_a.get("fullName")
        name_b = entity_b.get("name") or entity_b.get("fullName")
        if name_a and name_b:
            score, match_type, explanation = NameMatcher.compare_names(name_a, name_b)
            signals.append(MatchSignal(
                attribute="name",
                value_a=name_a,
                value_b=name_b,
                match_type=match_type,
                score=score,
                weight=weights.get("name", 0.15),
                explanation=explanation
            ))
        
        return signals
    
    def _high_complexity_resolution(
        self,
        entity_a: Dict[str, Any],
        entity_b: Dict[str, Any]
    ) -> List[MatchSignal]:
        """High complexity: multi-hop, cross-jurisdictional resolution."""
        signals = self._standard_resolution(entity_a, entity_b)
        
        # Add relationship-based signals
        # Use _internal_id (JanusGraph internal) or business ID for queries
        entity_a_id = entity_a.get("_internal_id") or entity_a.get("personId") or entity_a.get("companyId")
        entity_b_id = entity_b.get("_internal_id") or entity_b.get("personId") or entity_b.get("companyId")
        
        # Check for shared directors
        shared_directors = self._find_shared_directors(
            entity_a_id, entity_b_id
        )
        if shared_directors:
            signals.append(MatchSignal(
                attribute="shared_directors",
                value_a=entity_a_id,
                value_b=entity_b_id,
                match_type=MatchType.NETWORK,
                score=0.80,
                weight=0.15,
                explanation=f"Shared {len(shared_directors)} directors"
            ))
        
        # Check for shared addresses
        shared_addresses = self._find_shared_addresses(
            entity_a_id, entity_b_id
        )
        if shared_addresses:
            signals.append(MatchSignal(
                attribute="shared_addresses",
                value_a=entity_a_id,
                value_b=entity_b_id,
                match_type=MatchType.NETWORK,
                score=0.70,
                weight=0.10,
                explanation=f"Shared {len(shared_addresses)} addresses"
            ))
        
        return signals
    
    def _ultra_high_resolution(
        self,
        entity_a: Dict[str, Any],
        entity_b: Dict[str, Any]
    ) -> List[MatchSignal]:
        """Ultra-high complexity: network-based with behavioral signals."""
        signals = self._high_complexity_resolution(entity_a, entity_b)
        
        # Add device/fingerprint signals
        device_match = self._check_device_correlation(
            entity_a.get("id"), entity_b.get("id")
        )
        if device_match:
            signals.append(MatchSignal(
                attribute="device_fingerprint",
                value_a=entity_a.get("id"),
                value_b=entity_b.get("id"),
                match_type=MatchType.NETWORK,
                score=device_match["score"],
                weight=0.12,
                explanation=f"Shared device signals: {device_match['signals']}"
            ))
        
        # Add behavioral pattern signals
        behavioral_match = self._check_behavioral_patterns(
            entity_a.get("id"), entity_b.get("id")
        )
        if behavioral_match:
            signals.append(MatchSignal(
                attribute="behavioral_pattern",
                value_a=entity_a.get("id"),
                value_b=entity_b.get("id"),
                match_type=MatchType.TEMPORAL,
                score=behavioral_match["score"],
                weight=0.15,
                explanation=f"Similar behavioral patterns: {behavioral_match['patterns']}"
            ))
        
        return signals
    
    def _determine_action(
        self,
        confidence: float,
        complexity: ResolutionComplexity
    ) -> str:
        """Determine resolution action based on confidence."""
        if complexity == ResolutionComplexity.STANDARD:
            if confidence >= 0.90:
                return "merge"
            elif confidence >= 0.70:
                return "link"
            elif confidence >= 0.50:
                return "review"
            else:
                return "separate"
        elif complexity == ResolutionComplexity.HIGH:
            if confidence >= 0.85:
                return "merge"
            elif confidence >= 0.65:
                return "link"
            elif confidence >= 0.45:
                return "review"
            else:
                return "separate"
        else:  # Ultra-high
            if confidence >= 0.80:
                return "merge"
            elif confidence >= 0.60:
                return "link"
            elif confidence >= 0.40:
                return "review"
            else:
                return "separate"
    
    def _find_shared_directors(self, entity_a_id: str, entity_b_id: str) -> List[str]:
        """Find shared directors between two companies using property-based lookup."""
        # Use property-based lookup to handle string IDs
        # Try companyId first (companies), then fallback to internal ID
        query = f"""
            g.V().has('companyId', '{entity_a_id}').in('director_of').as('d').
            where(out('director_of').has('companyId', '{entity_b_id}')).
            select('d').id()
        """
        try:
            result = self.client.execute(query)
            if result:
                return result
        except Exception:
            pass
        return []
    
    def _find_shared_addresses(self, entity_a_id: str, entity_b_id: str) -> List[str]:
        """Find shared addresses between two entities using property-based lookup."""
        # Use property-based lookup to handle string IDs
        query = f"""
            g.V().has('personId', '{entity_a_id}').out('has_address').as('addr').
            where(__.in('has_address').has('personId', '{entity_b_id}')).
            select('addr').id()
        """
        try:
            result = self.client.execute(query)
            if result:
                return result
        except Exception:
            pass
        return []
    
    def _check_device_correlation(self, entity_a_id: str, entity_b_id: str) -> Optional[Dict]:
        """Check device/fingerprint correlation."""
        # Simplified - would check device fingerprints in production
        return None
    
    def _check_behavioral_patterns(self, entity_a_id: str, entity_b_id: str) -> Optional[Dict]:
        """Check behavioral pattern similarity."""
        # Simplified - would analyze transaction patterns in production
        return None
    
    def _assess_ubo_risk(self, person_id: str, path: List[str]) -> List[str]:
        """Assess risk indicators for a UBO."""
        indicators = []
        
        if len(path) > 3:
            indicators.append("Deep ownership chain (>3 layers)")
        
        # Check for sanctions
        sanctions_query = f"g.V('{person_id}').has('sanctioned', true)"
        if self.client.execute(sanctions_query):
            indicators.append("Sanctioned individual")
        
        # Check for PEP status
        pep_query = f"g.V('{person_id}').has('pep', true)"
        if self.client.execute(pep_query):
            indicators.append("Politically Exposed Person (PEP)")
        
        return indicators
    
    def _analyze_synthetic_indicators(self, persons: List[str]) -> Dict[str, Any]:
        """Analyze synthetic identity fraud indicators."""
        indicators = []
        score = 0.0
        
        # Check for sequential SSNs
        # Check for same DOB patterns
        # Check for address apartment number pattern
        # Check for phone number pattern
        
        if len(persons) >= 5:
            indicators.append("Large cluster at single address")
            score += 0.30
        
        return {"score": min(score, 1.0), "indicators": indicators}


def create_entity_resolution_report(
    client: JanusGraphClient,
    resolution_type: str = "standard"
) -> Dict[str, Any]:
    """
    Create comprehensive entity resolution report.
    
    Args:
        client: JanusGraph client
        resolution_type: "standard", "high", or "ultra_high"
        
    Returns:
        Resolution report with statistics and findings
    """
    resolver = EntityResolver(client)
    complexity = {
        "standard": ResolutionComplexity.STANDARD,
        "high": ResolutionComplexity.HIGH,
        "ultra_high": ResolutionComplexity.ULTRA_HIGH
    }.get(resolution_type, ResolutionComplexity.STANDARD)
    
    duplicates = resolver.find_duplicates(threshold=0.70)
    
    return {
        "resolution_type": resolution_type,
        "complexity": complexity.value,
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "potential_duplicates": len(duplicates),
            "high_confidence_matches": len([d for d in duplicates if d.confidence >= 0.90]),
            "review_required": len([d for d in duplicates if 0.50 <= d.confidence < 0.90])
        },
        "findings": [d.to_dict() for d in duplicates[:10]]  # Top 10
    }
