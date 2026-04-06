#!/usr/bin/env python3
"""
Baseline Rollback Testing
=========================

Tests the ability to rollback to previous baseline versions
and verify system behavior after rollback.

Features:
- Create baseline snapshots
- Rollback to previous versions
- Verify rollback integrity
- Test rollback scenarios

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BaselineRollbackTester:
    """Test baseline rollback functionality."""

    def __init__(self, baseline_dir: Path, backup_root: Path):
        """
        Initialize tester.
        
        Args:
            baseline_dir: Current baseline directory
            backup_root: Root directory for backups
        """
        self.baseline_dir = baseline_dir
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
    def create_snapshot(self, label: Optional[str] = None) -> Tuple[bool, str, Path]:
        """
        Create a snapshot of the current baseline.
        
        Args:
            label: Optional label for the snapshot
            
        Returns:
            Tuple of (success, message, snapshot_path)
        """
        if not self.baseline_dir.exists():
            return False, "Baseline directory does not exist", None
        
        # Generate snapshot name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if label:
            snapshot_name = f"snapshot_{timestamp}_{label}"
        else:
            snapshot_name = f"snapshot_{timestamp}"
        
        snapshot_path = self.backup_root / snapshot_name
        
        try:
            # Copy baseline to snapshot
            shutil.copytree(self.baseline_dir, snapshot_path)
            
            # Create metadata
            metadata = {
                "timestamp": timestamp,
                "label": label,
                "source": str(self.baseline_dir),
                "snapshot": str(snapshot_path)
            }
            
            metadata_file = snapshot_path / "snapshot_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            return True, f"Created snapshot: {snapshot_name}", snapshot_path
            
        except Exception as e:
            return False, f"Failed to create snapshot: {e}", None
    
    def list_snapshots(self) -> List[Dict[str, any]]:
        """List all available snapshots."""
        snapshots = []
        
        for snapshot_dir in sorted(self.backup_root.glob("snapshot_*")):
            if not snapshot_dir.is_dir():
                continue
            
            metadata_file = snapshot_dir / "snapshot_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    metadata["path"] = str(snapshot_dir)
                    snapshots.append(metadata)
            else:
                # No metadata, create basic info
                snapshots.append({
                    "snapshot": snapshot_dir.name,
                    "path": str(snapshot_dir),
                    "timestamp": "unknown"
                })
        
        return snapshots
    
    def rollback(self, snapshot_name: str, verify: bool = True) -> Tuple[bool, str]:
        """
        Rollback to a previous snapshot.
        
        Args:
            snapshot_name: Name of snapshot to rollback to
            verify: Verify rollback integrity
            
        Returns:
            Tuple of (success, message)
        """
        snapshot_path = self.backup_root / snapshot_name
        
        if not snapshot_path.exists():
            return False, f"Snapshot {snapshot_name} does not exist"
        
        try:
            # Create backup of current baseline before rollback
            backup_success, backup_msg, backup_path = self.create_snapshot("pre_rollback")
            if not backup_success:
                return False, f"Failed to backup current baseline: {backup_msg}"
            
            # Remove current baseline
            if self.baseline_dir.exists():
                shutil.rmtree(self.baseline_dir)
            
            # Copy snapshot to baseline
            shutil.copytree(snapshot_path, self.baseline_dir)
            
            # Remove snapshot metadata from restored baseline
            metadata_file = self.baseline_dir / "snapshot_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Verify if requested
            if verify:
                verify_success, verify_msg = self.verify_rollback(snapshot_path)
                if not verify_success:
                    return False, f"Rollback verification failed: {verify_msg}"
            
            return True, f"Successfully rolled back to {snapshot_name}"
            
        except Exception as e:
            return False, f"Rollback failed: {e}"
    
    def verify_rollback(self, snapshot_path: Path) -> Tuple[bool, str]:
        """
        Verify that rollback was successful.
        
        Args:
            snapshot_path: Path to snapshot that was rolled back to
            
        Returns:
            Tuple of (success, message)
        """
        # Compare checksums
        snapshot_checksums = self._read_checksums(snapshot_path / "checksums.txt")
        baseline_checksums = self._read_checksums(self.baseline_dir / "checksums.txt")
        
        if snapshot_checksums != baseline_checksums:
            return False, "Checksums do not match after rollback"
        
        # Compare notebook counts
        snapshot_notebooks = len(list(snapshot_path.glob("*.ipynb")))
        baseline_notebooks = len(list(self.baseline_dir.glob("*.ipynb")))
        
        if snapshot_notebooks != baseline_notebooks:
            return False, f"Notebook count mismatch: {snapshot_notebooks} vs {baseline_notebooks}"
        
        # Verify required files
        required_files = ["checksums.txt", "notebook-report.txt", "deterministic-status.json"]
        for filename in required_files:
            if not (self.baseline_dir / filename).exists():
                return False, f"Missing required file after rollback: {filename}"
        
        return True, "Rollback verification passed"
    
    def _read_checksums(self, file_path: Path) -> Dict[str, str]:
        """Read checksums file into dictionary."""
        if not file_path.exists():
            return {}
        
        checksums = {}
        with open(file_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    checksums[parts[1]] = parts[0]
        return checksums
    
    def test_rollback_scenario(self) -> Tuple[bool, List[str]]:
        """
        Test a complete rollback scenario.
        
        Returns:
            Tuple of (success, test_results)
        """
        results = []
        
        # Step 1: Create initial snapshot
        results.append("Step 1: Creating initial snapshot...")
        success, msg, snapshot1 = self.create_snapshot("test_initial")
        results.append(f"  {msg}")
        if not success:
            return False, results
        
        # Step 2: Modify baseline (simulate corruption)
        results.append("Step 2: Simulating baseline modification...")
        test_file = self.baseline_dir / "test_modification.txt"
        test_file.write_text("This is a test modification")
        results.append("  Modified baseline")
        
        # Step 3: Create second snapshot
        results.append("Step 3: Creating second snapshot...")
        success, msg, snapshot2 = self.create_snapshot("test_modified")
        results.append(f"  {msg}")
        if not success:
            return False, results
        
        # Step 4: Rollback to initial
        results.append("Step 4: Rolling back to initial snapshot...")
        success, msg = self.rollback(snapshot1.name, verify=True)
        results.append(f"  {msg}")
        if not success:
            return False, results
        
        # Step 5: Verify test file is gone
        results.append("Step 5: Verifying rollback...")
        if test_file.exists():
            results.append("  ❌ Test file still exists after rollback")
            return False, results
        results.append("  ✅ Test file removed as expected")
        
        # Step 6: Cleanup test snapshots
        results.append("Step 6: Cleaning up test snapshots...")
        if snapshot1.exists():
            shutil.rmtree(snapshot1)
        if snapshot2.exists():
            shutil.rmtree(snapshot2)
        results.append("  Cleaned up test snapshots")
        
        results.append("\n✅ Rollback scenario test PASSED")
        return True, results
    
    def cleanup_old_snapshots(self, keep_count: int = 5) -> Tuple[int, List[str]]:
        """
        Cleanup old snapshots, keeping only the most recent ones.
        
        Args:
            keep_count: Number of snapshots to keep
            
        Returns:
            Tuple of (removed_count, removed_snapshots)
        """
        snapshots = self.list_snapshots()
        
        if len(snapshots) <= keep_count:
            return 0, []
        
        # Sort by timestamp (newest first)
        snapshots.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Remove old snapshots
        removed = []
        for snapshot in snapshots[keep_count:]:
            snapshot_path = Path(snapshot["path"])
            if snapshot_path.exists():
                shutil.rmtree(snapshot_path)
                removed.append(snapshot["snapshot"])
        
        return len(removed), removed


def main():
    parser = argparse.ArgumentParser(
        description="Test baseline rollback functionality"
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=Path("exports/determinism-baselines/CANONICAL_42"),
        help="Baseline directory"
    )
    parser.add_argument(
        "--backup-root",
        type=Path,
        default=Path("exports/baseline-backups"),
        help="Backup root directory"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Snapshot command
    snap_parser = subparsers.add_parser("snapshot", help="Create snapshot")
    snap_parser.add_argument("--label", help="Optional label for snapshot")
    
    # List command
    subparsers.add_parser("list", help="List snapshots")
    
    # Rollback command
    roll_parser = subparsers.add_parser("rollback", help="Rollback to snapshot")
    roll_parser.add_argument("snapshot", help="Snapshot name")
    roll_parser.add_argument("--no-verify", action="store_true", help="Skip verification")
    
    # Test command
    subparsers.add_parser("test", help="Run rollback scenario test")
    
    # Cleanup command
    clean_parser = subparsers.add_parser("cleanup", help="Cleanup old snapshots")
    clean_parser.add_argument("--keep", type=int, default=5, help="Number to keep")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    tester = BaselineRollbackTester(args.baseline_dir, args.backup_root)
    
    if args.command == "snapshot":
        success, msg, _ = tester.create_snapshot(args.label)
        print(msg)
        return 0 if success else 1
    
    elif args.command == "list":
        snapshots = tester.list_snapshots()
        print(json.dumps(snapshots, indent=2))
        return 0
    
    elif args.command == "rollback":
        success, msg = tester.rollback(args.snapshot, verify=not args.no_verify)
        print(msg)
        return 0 if success else 1
    
    elif args.command == "test":
        success, results = tester.test_rollback_scenario()
        for result in results:
            print(result)
        return 0 if success else 1
    
    elif args.command == "cleanup":
        count, removed = tester.cleanup_old_snapshots(args.keep)
        print(f"Removed {count} old snapshots")
        for snapshot in removed:
            print(f"  - {snapshot}")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
