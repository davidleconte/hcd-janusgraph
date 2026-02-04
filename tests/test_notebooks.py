"""
Notebook Validation Tests
==========================
Tests to validate notebook structure, metadata, and imports.

Author: IBM Bob
Date: 2026-02-04
"""

import json
import pytest
from pathlib import Path
import sys

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
NOTEBOOKS_DIR = PROJECT_ROOT / "banking" / "notebooks"


class TestNotebookStructure:
    """Test notebook JSON structure and metadata."""

    @pytest.fixture
    def all_notebooks(self):
        """Get all notebook files."""
        return list(NOTEBOOKS_DIR.glob("*.ipynb"))

    def test_notebooks_exist(self, all_notebooks):
        """Verify notebooks directory has expected notebooks."""
        assert len(all_notebooks) >= 9, f"Expected at least 9 notebooks, found {len(all_notebooks)}"
    
    @pytest.mark.parametrize("notebook_name", [
        "01_Sanctions_Screening_Demo.ipynb",
        "02_AML_Structuring_Detection_Demo.ipynb",
        "03_Fraud_Detection_Demo.ipynb",
        "04_Customer_360_View_Demo.ipynb",
        "05_Advanced_Analytics_OLAP.ipynb",
        "06_TBML_Detection_Demo.ipynb",
        "07_Insider_Trading_Detection_Demo.ipynb",
        "08_UBO_Discovery_Demo.ipynb",
        "09_API_Integration_Demo.ipynb",
    ])
    def test_notebook_exists(self, notebook_name):
        """Test that each expected notebook exists."""
        nb_path = NOTEBOOKS_DIR / notebook_name
        assert nb_path.exists(), f"Notebook {notebook_name} not found"

    @pytest.mark.parametrize("notebook_name", [
        "01_Sanctions_Screening_Demo.ipynb",
        "02_AML_Structuring_Detection_Demo.ipynb",
        "03_Fraud_Detection_Demo.ipynb",
        "04_Customer_360_View_Demo.ipynb",
        "05_Advanced_Analytics_OLAP.ipynb",
        "06_TBML_Detection_Demo.ipynb",
        "07_Insider_Trading_Detection_Demo.ipynb",
        "08_UBO_Discovery_Demo.ipynb",
        "09_API_Integration_Demo.ipynb",
    ])
    def test_valid_json(self, notebook_name):
        """Test that notebook is valid JSON."""
        nb_path = NOTEBOOKS_DIR / notebook_name
        if not nb_path.exists():
            pytest.skip(f"Notebook {notebook_name} not found")
        
        with open(nb_path, 'r') as f:
            try:
                nb = json.load(f)
                assert 'cells' in nb, "Missing 'cells' key"
                assert 'metadata' in nb, "Missing 'metadata' key"
                assert 'nbformat' in nb, "Missing 'nbformat' key"
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {notebook_name}: {e}")

    @pytest.mark.parametrize("notebook_name", [
        "01_Sanctions_Screening_Demo.ipynb",
        "02_AML_Structuring_Detection_Demo.ipynb",
        "03_Fraud_Detection_Demo.ipynb",
        "04_Customer_360_View_Demo.ipynb",
        "05_Advanced_Analytics_OLAP.ipynb",
        "06_TBML_Detection_Demo.ipynb",
        "07_Insider_Trading_Detection_Demo.ipynb",
        "08_UBO_Discovery_Demo.ipynb",
        "09_API_Integration_Demo.ipynb",
    ])
    def test_correct_kernel(self, notebook_name):
        """Test that notebook has correct kernel specification."""
        nb_path = NOTEBOOKS_DIR / notebook_name
        if not nb_path.exists():
            pytest.skip(f"Notebook {notebook_name} not found")
        
        with open(nb_path, 'r') as f:
            nb = json.load(f)
        
        assert 'kernelspec' in nb.get('metadata', {}), "Missing kernelspec in metadata"
        kernelspec = nb['metadata']['kernelspec']
        assert kernelspec.get('name') == 'janusgraph-analysis', \
            f"Expected kernel 'janusgraph-analysis', got '{kernelspec.get('name')}'"
        assert kernelspec.get('language') == 'python', "Expected language 'python'"


class TestNotebookContent:
    """Test notebook content quality."""

    @pytest.mark.parametrize("notebook_name", [
        "06_TBML_Detection_Demo.ipynb",
        "07_Insider_Trading_Detection_Demo.ipynb",
        "08_UBO_Discovery_Demo.ipynb",
        "09_API_Integration_Demo.ipynb",
    ])
    def test_uses_notebook_config(self, notebook_name):
        """Test that newer notebooks use notebook_config for initialization."""
        nb_path = NOTEBOOKS_DIR / notebook_name
        if not nb_path.exists():
            pytest.skip(f"Notebook {notebook_name} not found")
        
        with open(nb_path, 'r') as f:
            content = f.read()
        
        assert 'notebook_config' in content or 'init_notebook' in content, \
            f"Notebook {notebook_name} should use notebook_config for initialization"

    @pytest.mark.parametrize("notebook_name", [
        "01_Sanctions_Screening_Demo.ipynb",
        "02_AML_Structuring_Detection_Demo.ipynb",
        "03_Fraud_Detection_Demo.ipynb",
        "04_Customer_360_View_Demo.ipynb",
        "05_Advanced_Analytics_OLAP.ipynb",
        "06_TBML_Detection_Demo.ipynb",
        "07_Insider_Trading_Detection_Demo.ipynb",
        "08_UBO_Discovery_Demo.ipynb",
        "09_API_Integration_Demo.ipynb",
    ])
    def test_has_markdown_header(self, notebook_name):
        """Test that notebook starts with a markdown cell (title)."""
        nb_path = NOTEBOOKS_DIR / notebook_name
        if not nb_path.exists():
            pytest.skip(f"Notebook {notebook_name} not found")
        
        with open(nb_path, 'r') as f:
            nb = json.load(f)
        
        cells = nb.get('cells', [])
        assert len(cells) > 0, "Notebook has no cells"
        assert cells[0].get('cell_type') == 'markdown', \
            "First cell should be markdown (title/header)"


class TestNotebookConfig:
    """Test notebook_config.py module."""

    def test_notebook_config_exists(self):
        """Test that notebook_config.py exists."""
        config_path = NOTEBOOKS_DIR / "notebook_config.py"
        assert config_path.exists(), "notebook_config.py not found"

    def test_notebook_config_imports(self):
        """Test that notebook_config.py can be imported."""
        sys.path.insert(0, str(NOTEBOOKS_DIR))
        try:
            import notebook_config
            assert hasattr(notebook_config, 'init_notebook')
            assert hasattr(notebook_config, 'JANUSGRAPH_CONFIG')
            assert hasattr(notebook_config, 'OPENSEARCH_CONFIG')
            assert hasattr(notebook_config, 'get_data_path')
        finally:
            sys.path.remove(str(NOTEBOOKS_DIR))

    def test_janusgraph_config_defaults(self):
        """Test JanusGraph configuration defaults."""
        sys.path.insert(0, str(NOTEBOOKS_DIR))
        try:
            import notebook_config
            config = notebook_config.JANUSGRAPH_CONFIG
            assert 'url' in config
            assert '18182' in config['url'], "JanusGraph port should be 18182"
        finally:
            sys.path.remove(str(NOTEBOOKS_DIR))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
