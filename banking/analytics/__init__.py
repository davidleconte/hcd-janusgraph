"""
Banking Analytics Module
========================

AML and Fraud detection analytics for JanusGraph.
"""

from .aml_structuring_detector import AMLStructuringDetector
from .community_detection import (
    CommunityDetector,
    CommunityRiskLevel,
    CommunityMember,
    FraudCommunity,
    CommunityDetectionResult,
    create_community_detection_report,
)
from .detect_mule_chains import MuleChainAlert, MuleChainDetector
from .graph_ml import (
    EmbeddingMethod,
    RiskPrediction,
    NodeEmbedding,
    GraphEmbeddingResult,
    Node2Vec,
    GraphMLEngine,
)

__all__ = [
    # AML
    "AMLStructuringDetector",
    # Community Detection
    "CommunityDetector",
    "CommunityRiskLevel",
    "CommunityMember",
    "FraudCommunity",
    "CommunityDetectionResult",
    "create_community_detection_report",
    # Mule Chain Detection
    "MuleChainAlert",
    "MuleChainDetector",
    # Graph ML
    "EmbeddingMethod",
    "RiskPrediction",
    "NodeEmbedding",
    "GraphEmbeddingResult",
    "Node2Vec",
    "GraphMLEngine",
]
