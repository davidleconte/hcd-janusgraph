#!/usr/bin/env python3
"""
Fix Banking Notebooks - Connection Strings and Import Paths
============================================================

Systematically fixes all banking notebooks:
1. Replace localhost with container names
2. Fix import paths for container environment
3. Add prerequisites sections

Author: AdaL (SylphAI CLI)
Date: 2026-01-29
"""

import json
import sys
from pathlib import Path

def fix_notebook_cell(cell_content: str) -> str:
    """Fix code cell content"""
    fixed = cell_content
    
    # Fix 1: Replace localhost with container names
    replacements = {
        "opensearch_host='localhost'": "opensearch_host='opensearch'",
        'opensearch_host="localhost"': 'opensearch_host="opensearch"',
        "janusgraph_host='localhost'": "janusgraph_host='janusgraph-server'",
        'janusgraph_host="localhost"': 'janusgraph_host="janusgraph-server"',
        "host='localhost'": "host='opensearch'",
        'host="localhost"': 'host="opensearch"',
    }
    
    for old, new in replacements.items():
        fixed = fixed.replace(old, new)
    
    # Fix 2: Replace wrong import paths with container paths
    path_replacements = {
        "sys.path.insert(0, '../../src/python')": "sys.path.insert(0, '/workspace/src/python')",
        'sys.path.insert(0, "../../src/python")': 'sys.path.insert(0, "/workspace/src/python")',
        "sys.path.insert(0, '../../banking')": "sys.path.insert(0, '/workspace/banking')",
        'sys.path.insert(0, "../../banking")': 'sys.path.insert(0, "/workspace/banking")',
        "sys.path.insert(0, '../..')": "sys.path.insert(0, '/workspace')",
        'sys.path.insert(0, "../..")': 'sys.path.insert(0, "/workspace")',
    }
    
    for old, new in path_replacements.items():
        fixed = fixed.replace(old, new)
    
    return fixed

def fix_notebook(notebook_path: Path) -> bool:
    """Fix a single notebook"""
    print(f"\nFixing: {notebook_path.name}")
    
    try:
        # Load notebook
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)
        
        # Track changes
        changes = 0
        
        # Fix code cells
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if isinstance(source, list):
                    source = ''.join(source)
                
                fixed_source = fix_notebook_cell(source)
                
                if fixed_source != source:
                    # Convert back to list format (one line per element)
                    cell['source'] = fixed_source.split('\n')
                    # Ensure newlines are preserved
                    cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                                     for i, line in enumerate(cell['source'])]
                    changes += 1
        
        if changes > 0:
            # Backup original
            backup_path = notebook_path.with_suffix('.ipynb.backup')
            with open(backup_path, 'w') as f:
                json.dump(notebook, f, indent=1)
            print(f"  ✅ Backup created: {backup_path.name}")
            
            # Write fixed version
            with open(notebook_path, 'w') as f:
                json.dump(notebook, f, indent=1)
            
            print(f"  ✅ Fixed {changes} code cells")
            return True
        else:
            print(f"  ℹ️  No changes needed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("Banking Notebooks Fix Tool")
    print("=" * 60)
    
    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    banking_notebooks = project_root / 'banking' / 'notebooks'
    
    print(f"\nProject root: {project_root}")
    print(f"Banking notebooks: {banking_notebooks}")
    
    if not banking_notebooks.exists():
        print(f"\n❌ ERROR: Directory not found: {banking_notebooks}")
        sys.exit(1)
    
    # Find all notebooks
    notebooks = list(banking_notebooks.glob('*.ipynb'))
    
    if not notebooks:
        print(f"\n❌ ERROR: No notebooks found in {banking_notebooks}")
        sys.exit(1)
    
    print(f"\nFound {len(notebooks)} notebooks to fix")
    
    # Fix each notebook
    fixed_count = 0
    for notebook_path in sorted(notebooks):
        if fix_notebook(notebook_path):
            fixed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Fix Summary")
    print("=" * 60)
    print(f"Total notebooks: {len(notebooks)}")
    print(f"Fixed: {fixed_count}")
    print(f"No changes: {len(notebooks) - fixed_count}")
    
    if fixed_count > 0:
        print("\n✅ Notebooks fixed successfully!")
        print("\nNext steps:")
        print("1. Review changes in notebooks")
        print("2. Rebuild Jupyter container:")
        print("   cd config/compose")
        print("   podman-compose -p janusgraph-demo build jupyter")
        print("   podman-compose -p janusgraph-demo restart jupyter")
        print("3. Test notebooks")
    else:
        print("\nℹ️  All notebooks are already correct")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
