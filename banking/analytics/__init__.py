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
from .detect_ato import ATOAlert, ATODetector
from .detect_mule_chains import MuleChainAlert, MuleChainDetector
from .detect_procurement import ProcurementFraudAlert, ProcurementFraudDetector
from .governance import (
    PrecisionProxyResult,
    calculate_precision_proxy,
    export_kpi_summary,
    precision_proxy_to_dict,
)
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
    # ATO Detection
    "ATOAlert",
    "ATODetector",
    # Mule Chain Detection
    "MuleChainAlert",
    "MuleChainDetector",
    # Procurement Fraud Detection
    "ProcurementFraudAlert",
    "ProcurementFraudDetector",
    # Governance KPI Utilities
    "PrecisionProxyResult",
    "calculate_precision_proxy",
    "export_kpi_summary",
    "precision_proxy_to_dict",
    # Graph ML
    "EmbeddingMethod",
    "RiskPrediction",
    "NodeEmbedding",
    "GraphEmbeddingResult",
    "Node2Vec",
    "GraphMLEngine",
]
