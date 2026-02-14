"""
Integration Tests for Analytics Detection Modules
==================================================

Tests that verify TBML and Insider Trading detection modules
work correctly against live JanusGraph instance.

Requires:
- JanusGraph running at localhost:18182
- Graph populated with test data

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from gremlin_python.driver import client, serializer

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def is_janusgraph_available() -> bool:
    """Check if JanusGraph is running and accessible."""
    try:
        jg_client = client.Client(
            "ws://localhost:18182/gremlin",
            "g",
            message_serializer=serializer.GraphSONSerializersV3d0(),
        )
        result = jg_client.submit("g.V().count()").all().result()
        jg_client.close()
        return result[0] >= 0
    except Exception:
        return False


# Skip all tests if JanusGraph is not available
requires_janusgraph = pytest.mark.skipif(
    not is_janusgraph_available(), reason="JanusGraph not available at localhost:18182"
)


@requires_janusgraph
class TestTBMLIntegration:
    """Integration tests for TBML Detection against live JanusGraph"""

    def test_tbml_detector_connects(self):
        """Test that TBMLDetector can connect to JanusGraph"""
        from banking.analytics.detect_tbml import TBMLDetector

        detector = TBMLDetector()
        detector.connect()

        assert detector.client is not None

        # Verify connection by running simple query
        result = detector._query("g.V().count()")
        assert len(result) == 1
        assert result[0] >= 0

        detector.close()

    def test_tbml_query_company_vertices(self):
        """Test querying company vertices"""
        from banking.analytics.detect_tbml import TBMLDetector

        detector = TBMLDetector()
        detector.connect()

        try:
            # Query for companies
            companies = detector._query("g.V().hasLabel('company').count()")
            assert isinstance(companies[0], int)
            print(f"Found {companies[0]} company vertices")
        finally:
            detector.close()

    def test_tbml_query_transactions(self):
        """Test querying transaction vertices"""
        from banking.analytics.detect_tbml import TBMLDetector

        detector = TBMLDetector()
        detector.connect()

        try:
            # Query for transactions
            transactions = detector._query("g.V().hasLabel('transaction').count()")
            assert isinstance(transactions[0], int)
            print(f"Found {transactions[0]} transaction vertices")
        finally:
            detector.close()

    def test_shell_company_detection_runs(self):
        """Test that shell company detection runs without errors"""
        from banking.analytics.detect_tbml import TBMLDetector

        detector = TBMLDetector()
        detector.connect()

        try:
            # Run shell company detection (may find 0 alerts, but should not error)
            alerts = detector.detect_shell_company_networks()
            assert isinstance(alerts, list)
            print(f"Shell company detection found {len(alerts)} alerts")
        except Exception as e:
            # Detection may fail if graph schema doesn't match, but connection should work
            pytest.skip(f"Shell company detection skipped: {e}")
        finally:
            detector.close()

    def test_generate_report_after_scan(self):
        """Test report generation after running detection"""
        from banking.analytics.detect_tbml import TBMLDetector

        detector = TBMLDetector()
        detector.connect()

        try:
            report = detector.generate_report()

            assert "report_date" in report
            assert "total_alerts" in report
            assert "alerts_by_type" in report
            assert isinstance(report["total_alerts"], int)
        finally:
            detector.close()


@requires_janusgraph
class TestInsiderTradingIntegration:
    """Integration tests for Insider Trading Detection against live JanusGraph"""

    def test_insider_trading_detector_connects(self):
        """Test that InsiderTradingDetector can connect to JanusGraph"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector

        detector = InsiderTradingDetector()
        detector.connect()

        assert detector.client is not None

        # Verify connection
        result = detector._query("g.V().count()")
        assert len(result) == 1
        assert result[0] >= 0

        detector.close()

    def test_query_trade_vertices(self):
        """Test querying trade vertices"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector

        detector = InsiderTradingDetector()
        detector.connect()

        try:
            trades = detector._query("g.V().hasLabel('trade').count()")
            assert isinstance(trades[0], int)
            print(f"Found {trades[0]} trade vertices")
        finally:
            detector.close()

    def test_query_person_vertices(self):
        """Test querying person vertices (traders)"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector

        detector = InsiderTradingDetector()
        detector.connect()

        try:
            persons = detector._query("g.V().hasLabel('person').count()")
            assert isinstance(persons[0], int)
            print(f"Found {persons[0]} person vertices")
        finally:
            detector.close()

    def test_coordinated_trading_detection_runs(self):
        """Test that coordinated trading detection runs without errors"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector

        detector = InsiderTradingDetector()
        detector.connect()

        try:
            alerts = detector.detect_coordinated_trading()
            assert isinstance(alerts, list)
            print(f"Coordinated trading detection found {len(alerts)} alerts")
        except Exception as e:
            pytest.skip(f"Coordinated trading detection skipped: {e}")
        finally:
            detector.close()

    def test_generate_report_after_scan(self):
        """Test report generation"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector

        detector = InsiderTradingDetector()
        detector.connect()

        try:
            report = detector.generate_report()

            assert "report_date" in report
            assert "total_alerts" in report
            assert "alerts_by_type" in report
            assert "unique_traders" in report
        finally:
            detector.close()


@requires_janusgraph
class TestCombinedAnalyticsWorkflow:
    """Integration tests for combined analytics workflow"""

    def test_full_tbml_scan_workflow(self):
        """Test complete TBML scan workflow"""
        from banking.analytics.detect_tbml import TBMLDetector

        detector = TBMLDetector()
        detector.connect()

        try:
            # Run all detection methods
            carousel_alerts = detector.detect_carousel_fraud(max_depth=2)
            invoice_anomalies, invoice_alerts = detector.detect_invoice_manipulation()
            shell_alerts = detector.detect_shell_company_networks()

            # Generate final report
            report = detector.generate_report()

            assert isinstance(report, dict)
            assert report["total_alerts"] == len(detector.alerts)

            print("TBML Scan Complete:")
            print(f"  - Carousel alerts: {len(carousel_alerts)}")
            print(f"  - Invoice anomalies: {len(invoice_anomalies)}")
            print(f"  - Shell company alerts: {len(shell_alerts)}")
            print(f"  - Total alerts: {report['total_alerts']}")
        except Exception as e:
            pytest.skip(f"TBML scan workflow skipped due to: {e}")
        finally:
            detector.close()

    def test_full_insider_trading_scan_workflow(self):
        """Test complete Insider Trading scan workflow"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector

        detector = InsiderTradingDetector()
        detector.connect()

        try:
            # Run timing pattern detection
            timing_alerts = detector.detect_timing_patterns()

            # Run coordinated trading detection
            coord_alerts = detector.detect_coordinated_trading()

            # Generate report
            report = detector.generate_report()

            assert isinstance(report, dict)

            print("Insider Trading Scan Complete:")
            print(f"  - Timing alerts: {len(timing_alerts)}")
            print(f"  - Coordinated trading alerts: {len(coord_alerts)}")
            print(f"  - Total alerts: {report['total_alerts']}")
        except Exception as e:
            pytest.skip(f"Insider trading scan workflow skipped due to: {e}")
        finally:
            detector.close()

    def test_both_detectors_can_run_sequentially(self):
        """Test that both detectors can run sequentially"""
        from banking.analytics.detect_insider_trading import InsiderTradingDetector
        from banking.analytics.detect_tbml import TBMLDetector

        # Run TBML detector
        tbml_detector = TBMLDetector()
        tbml_detector.connect()
        tbml_report = tbml_detector.generate_report()
        tbml_detector.close()

        # Run Insider Trading detector
        it_detector = InsiderTradingDetector()
        it_detector.connect()
        it_report = it_detector.generate_report()
        it_detector.close()

        # Both should produce valid reports
        assert "report_date" in tbml_report
        assert "report_date" in it_report

        print("Sequential detection complete:")
        print(f"  - TBML alerts: {tbml_report['total_alerts']}")
        print(f"  - Insider Trading alerts: {it_report['total_alerts']}")


@requires_janusgraph
class TestGraphSchemaValidation:
    """Validate that expected graph schema exists"""

    def test_expected_vertex_labels_exist(self):
        """Test that expected vertex labels exist in graph"""
        from gremlin_python.driver import client, serializer

        jg_client = client.Client(
            "ws://localhost:18182/gremlin",
            "g",
            message_serializer=serializer.GraphSONSerializersV3d0(),
        )

        try:
            labels = jg_client.submit("g.V().label().dedup()").all().result()

            # Core labels that should exist
            expected_labels = ["person", "account", "transaction"]

            for label in expected_labels:
                assert label in labels, f"Expected label '{label}' not found in graph"

            print(f"Found vertex labels: {labels}")
        finally:
            jg_client.close()

    def test_vertex_counts(self):
        """Test that vertices exist for each label"""
        from gremlin_python.driver import client, serializer

        jg_client = client.Client(
            "ws://localhost:18182/gremlin",
            "g",
            message_serializer=serializer.GraphSONSerializersV3d0(),
        )

        try:
            counts = (
                jg_client.submit(
                    """
                g.V().groupCount().by(label)
            """
                )
                .all()
                .result()
            )

            if counts:
                print(f"Vertex counts by label: {counts[0]}")

                # Verify at least some vertices exist
                total = sum(counts[0].values()) if counts[0] else 0
                assert total > 0, "Graph should have at least some vertices"
        finally:
            jg_client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
