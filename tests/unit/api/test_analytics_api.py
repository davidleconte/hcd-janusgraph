"""
Unit Tests for FastAPI Analytics API
=====================================

Tests for the Graph Analytics API endpoints including health checks,
UBO discovery, AML structuring detection, and fraud ring detection.

Author: IBM Bob
Date: 2026-02-04
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Import the module under test
import sys
from pathlib import Path
src_path = str(Path(__file__).parent.parent.parent.parent / 'src' / 'python')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Mock gremlin_python before importing main
with patch.dict('sys.modules', {
    'gremlin_python': MagicMock(),
    'gremlin_python.driver': MagicMock(),
    'gremlin_python.driver.driver_remote_connection': MagicMock(),
    'gremlin_python.driver.serializer': MagicMock(),
    'gremlin_python.process': MagicMock(),
    'gremlin_python.process.anonymous_traversal': MagicMock(),
    'gremlin_python.process.graph_traversal': MagicMock(),
    'gremlin_python.process.traversal': MagicMock(),
}):
    from src.python.api.main import app, _flatten_value_map, get_graph_connection


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_graph_connection():
    """Mock JanusGraph connection"""
    mock_g = MagicMock()
    return mock_g


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    def test_health_endpoint_exists(self, client):
        """Test health endpoint returns response"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.limit.return_value.count.return_value.next.return_value = 1
            mock_conn.return_value = mock_g
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "timestamp" in data
            assert "services" in data
    
    def test_health_returns_healthy_when_connected(self, client):
        """Test health returns healthy when JanusGraph is connected"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.limit.return_value.count.return_value.next.return_value = 1
            mock_conn.return_value = mock_g
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["janusgraph"] is True
    
    def test_health_returns_degraded_when_disconnected(self, client):
        """Test health returns degraded when JanusGraph is not connected"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_conn.side_effect = Exception("Connection failed")
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["services"]["janusgraph"] is False


class TestStatsEndpoint:
    """Tests for /stats endpoint"""
    
    def test_stats_endpoint_exists(self, client):
        """Test stats endpoint returns response"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.count.return_value.next.return_value = 100
            mock_g.E.return_value.count.return_value.next.return_value = 200
            mock_g.V.return_value.hasLabel.return_value.count.return_value.next.return_value = 50
            mock_conn.return_value = mock_g
            
            response = client.get("/stats")
            
            assert response.status_code == 200
    
    def test_stats_returns_graph_statistics(self, client):
        """Test stats returns all expected fields"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.count.return_value.next.return_value = 1000
            mock_g.E.return_value.count.return_value.next.return_value = 2000
            mock_g.V.return_value.hasLabel.return_value.count.return_value.next.return_value = 100
            mock_conn.return_value = mock_g
            
            response = client.get("/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "vertex_count" in data
            assert "edge_count" in data
            assert "person_count" in data
            assert "company_count" in data
            assert "account_count" in data
            assert "transaction_count" in data
            assert "last_updated" in data


class TestUBODiscoverEndpoint:
    """Tests for POST /api/v1/ubo/discover endpoint"""
    
    def test_ubo_discover_endpoint_exists(self, client):
        """Test UBO discover endpoint accepts POST"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.has.return_value.valueMap.return_value.toList.return_value = [
                {'company_id': ['COMP-001'], 'legal_name': ['Test Corp']}
            ]
            mock_g.V.return_value.has.return_value.inE.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.post("/api/v1/ubo/discover", json={
                "company_id": "COMP-001"
            })
            
            assert response.status_code in [200, 404, 500]
    
    def test_ubo_discover_returns_404_for_missing_company(self, client):
        """Test UBO discover returns 404 for non-existent company"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.has.return_value.valueMap.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.post("/api/v1/ubo/discover", json={
                "company_id": "NON-EXISTENT"
            })
            
            assert response.status_code == 404
    
    def test_ubo_discover_validates_request_body(self, client):
        """Test UBO discover validates required fields"""
        response = client.post("/api/v1/ubo/discover", json={})
        
        assert response.status_code == 422  # Validation error
    
    def test_ubo_discover_with_custom_threshold(self, client):
        """Test UBO discover accepts custom ownership threshold"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.has.return_value.valueMap.return_value.toList.return_value = [
                {'company_id': ['COMP-001'], 'legal_name': ['Test Corp']}
            ]
            mock_g.V.return_value.has.return_value.inE.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.post("/api/v1/ubo/discover", json={
                "company_id": "COMP-001",
                "ownership_threshold": 10.0,
                "include_indirect": True,
                "max_depth": 5
            })
            
            assert response.status_code in [200, 404, 500]


class TestUBONetworkEndpoint:
    """Tests for GET /api/v1/ubo/network/{company_id} endpoint"""
    
    def test_network_endpoint_exists(self, client):
        """Test network endpoint returns response"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.has.return_value.hasNext.return_value = True
            mock_g.V.return_value.has.return_value.valueMap.return_value.next.return_value = {
                'company_id': ['COMP-001'], 
                'legal_name': ['Test Corp']
            }
            mock_g.V.return_value.has.return_value.inE.return_value.outV.return_value.valueMap.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.get("/api/v1/ubo/network/COMP-001")
            
            assert response.status_code in [200, 404, 500]
    
    def test_network_returns_404_for_missing_company(self, client):
        """Test network returns 404 for non-existent company"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.has.return_value.hasNext.return_value = False
            mock_conn.return_value = mock_g
            
            response = client.get("/api/v1/ubo/network/NON-EXISTENT")
            
            assert response.status_code == 404
    
    def test_network_accepts_depth_parameter(self, client):
        """Test network endpoint accepts depth query parameter"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.has.return_value.hasNext.return_value = True
            mock_g.V.return_value.has.return_value.valueMap.return_value.next.return_value = {
                'company_id': ['COMP-001'], 
                'legal_name': ['Test Corp']
            }
            mock_g.V.return_value.has.return_value.inE.return_value.outV.return_value.valueMap.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.get("/api/v1/ubo/network/COMP-001?depth=5")
            
            assert response.status_code in [200, 404, 500]


class TestAMLStructuringEndpoint:
    """Tests for POST /api/v1/aml/structuring endpoint"""
    
    def test_structuring_endpoint_exists(self, client):
        """Test structuring endpoint accepts POST"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.hasLabel.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.post("/api/v1/aml/structuring", json={})
            
            assert response.status_code == 200
    
    def test_structuring_with_custom_parameters(self, client):
        """Test structuring detection with custom parameters"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.hasLabel.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.post("/api/v1/aml/structuring", json={
                "time_window_days": 30,
                "threshold_amount": 5000.0,
                "min_transaction_count": 5
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert "total_alerts" in data
            assert "analysis_period" in data
            assert "query_time_ms" in data


class TestFraudRingsEndpoint:
    """Tests for GET /api/v1/fraud/rings endpoint"""
    
    def test_fraud_rings_endpoint_exists(self, client):
        """Test fraud rings endpoint returns response"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.hasLabel.return_value.where.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.get("/api/v1/fraud/rings")
            
            assert response.status_code == 200
    
    def test_fraud_rings_with_min_members(self, client):
        """Test fraud rings with min_members parameter"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.hasLabel.return_value.where.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []
            mock_conn.return_value = mock_g
            
            response = client.get("/api/v1/fraud/rings?min_members=5")
            
            assert response.status_code == 200
    
    def test_fraud_rings_returns_structure(self, client):
        """Test fraud rings returns expected structure"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.hasLabel.return_value.where.return_value.project.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = [
                {'address_id': 'ADDR-001', 'city': 'New York', 'persons': ['P1', 'P2', 'P3']}
            ]
            mock_conn.return_value = mock_g
            
            response = client.get("/api/v1/fraud/rings")
            
            assert response.status_code == 200
            data = response.json()
            assert "rings" in data
            assert "total_detected" in data


class TestFlattenValueMap:
    """Tests for _flatten_value_map helper function"""
    
    def test_flatten_single_value_lists(self):
        """Test flattening single-value lists"""
        value_map = {
            'name': ['John'],
            'age': [30]
        }
        
        result = _flatten_value_map(value_map)
        
        assert result['name'] == 'John'
        assert result['age'] == 30
    
    def test_flatten_keeps_multi_value_lists(self):
        """Test multi-value lists are preserved"""
        value_map = {
            'tags': ['a', 'b', 'c']
        }
        
        result = _flatten_value_map(value_map)
        
        assert result['tags'] == ['a', 'b', 'c']


class TestAPIDocumentation:
    """Tests for API documentation endpoints"""
    
    def test_openapi_json_available(self, client):
        """Test OpenAPI schema is available"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data
    
    def test_docs_endpoint_available(self, client):
        """Test Swagger UI docs endpoint is available"""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_redoc_endpoint_available(self, client):
        """Test ReDoc endpoint is available"""
        response = client.get("/redoc")
        
        assert response.status_code == 200


class TestAPIMetadata:
    """Tests for API metadata"""
    
    def test_api_title(self, client):
        """Test API title is correct"""
        response = client.get("/openapi.json")
        data = response.json()
        
        assert data["info"]["title"] == "Graph Analytics API"
    
    def test_api_version(self, client):
        """Test API version is set"""
        response = client.get("/openapi.json")
        data = response.json()
        
        assert "version" in data["info"]
        assert data["info"]["version"] == "1.0.0"


class TestRequestValidation:
    """Tests for request validation"""
    
    def test_ubo_discover_rejects_invalid_threshold(self, client):
        """Test UBO discover rejects invalid ownership threshold"""
        response = client.post("/api/v1/ubo/discover", json={
            "company_id": "COMP-001",
            "ownership_threshold": 150.0  # Invalid - over 100
        })
        
        assert response.status_code == 422
    
    def test_ubo_discover_rejects_invalid_max_depth(self, client):
        """Test UBO discover rejects invalid max depth"""
        response = client.post("/api/v1/ubo/discover", json={
            "company_id": "COMP-001",
            "max_depth": 0  # Invalid - must be >= 1
        })
        
        assert response.status_code == 422
    
    def test_structuring_rejects_invalid_time_window(self, client):
        """Test structuring detection rejects invalid time window"""
        response = client.post("/api/v1/aml/structuring", json={
            "time_window_days": 0  # Invalid - must be >= 1
        })
        
        assert response.status_code == 422


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_internal_error_returns_500(self, client):
        """Test internal errors return 500 status"""
        with patch('src.python.api.main.get_graph_connection') as mock_conn:
            mock_conn.side_effect = Exception("Database error")
            
            response = client.get("/stats")
            
            assert response.status_code == 500
    
    def test_error_response_includes_detail(self, client):
        """Test error responses include detail message"""
        response = client.post("/api/v1/ubo/discover", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
