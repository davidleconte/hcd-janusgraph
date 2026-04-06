#!/usr/bin/env python3
"""
Multi-Seed Baseline Management
===============================

Manages baselines for multiple seeds (42, 123, 999) to ensure
deterministic behavior across different seed values.

Features:
- Generate baselines for all valid seeds
- Compare baselines across seeds
- Validate seed-specific determinism
- Promote seed baselines to canonical status

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MultiSeedBaselineManager:
    """Manage baselines for multiple seeds."""

    VALID_SEEDS = {42, 123, 999}
    CANONICAL_SEED = 42  # Primary seed for canonical baseline
    
    def __init__(self, baseline_root: Path):
        """
        Initialize manager.
        
        Args:
            baseline_root: Root directory for all baselines
        """
        self.baseline_root = baseline_root
        self.baseline_root.mkdir(parents=True, exist_ok=True)
        
    def get_baseline_dir(self, seed: int) -> Path:
        """Get baseline directory for a seed."""
        return self.baseline_root / f"SEED_{seed}"
    
    def get_canonical_dir(self) -> Path:
        """Get canonical baseline directory."""
        return self.baseline_root / f"CANONICAL_{self.CANONICAL_SEED}"
    
    def generate_baseline(self, seed: int, force: bool = False) -> Tuple[bool, str]:
        """
        Generate baseline for a specific seed.
        
        Args:
            seed: Seed value to generate baseline for
            force: Force regeneration even if baseline exists
            
        Returns:
            Tuple of (success, message)
        """
        if seed not in self.VALID_SEEDS:
            return False, f"Invalid seed {seed}. Must be one of {self.VALID_SEEDS}"
        
        baseline_dir = self.get_baseline_dir(seed)
        
        if baseline_dir.exists() and not force:
            return False, f"Baseline for seed {seed} already exists. Use --force to regenerate."
        
        # Create baseline directory
        baseline_dir.mkdir(parents=True, exist_ok=True)
        
        # Run deterministic pipeline with this seed
        try:
            cmd = [
                "bash",
                "scripts/testing/run_demo_pipeline_repeatable.sh",
                "--seed", str(seed),
                "--output-dir", str(baseline_dir)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode != 0:
                return False, f"Pipeline failed for seed {seed}: {result.stderr}"
            
            return True, f"Successfully generated baseline for seed {seed}"
            
        except subprocess.TimeoutExpired:
            return False, f"Pipeline timed out for seed {seed}"
        except Exception as e:
            return False, f"Error generating baseline for seed {seed}: {e}"
    
    def generate_all_baselines(self, force: bool = False) -> Dict[int, Tuple[bool, str]]:
        """
        Generate baselines for all valid seeds.
        
        Args:
            force: Force regeneration even if baselines exist
            
        Returns:
            Dictionary mapping seed to (success, message)
        """
        results = {}
        for seed in sorted(self.VALID_SEEDS):
            print(f"\nGenerating baseline for seed {seed}...")
            success, message = self.generate_baseline(seed, force)
            results[seed] = (success, message)
            print(f"  {message}")
        
        return results
    
    def compare_baselines(self, seed1: int, seed2: int) -> Dict[str, any]:
        """
        Compare baselines between two seeds.
        
        Args:
            seed1: First seed
            seed2: Second seed
            
        Returns:
            Comparison results dictionary
        """
        dir1 = self.get_baseline_dir(seed1)
        dir2 = self.get_baseline_dir(seed2)
        
        if not dir1.exists():
            return {"error": f"Baseline for seed {seed1} does not exist"}
        if not dir2.exists():
            return {"error": f"Baseline for seed {seed2} does not exist"}
        
        comparison = {
            "seed1": seed1,
            "seed2": seed2,
            "differences": [],
            "identical": True
        }
        
        # Compare checksums
        checksums1 = self._read_checksums(dir1 / "checksums.txt")
        checksums2 = self._read_checksums(dir2 / "checksums.txt")
        
        if checksums1 != checksums2:
            comparison["identical"] = False
            comparison["differences"].append("Checksums differ between seeds")
        
        # Compare notebook counts
        notebooks1 = len(list(dir1.glob("*.ipynb")))
        notebooks2 = len(list(dir2.glob("*.ipynb")))
        
        if notebooks1 != notebooks2:
            comparison["identical"] = False
            comparison["differences"].append(
                f"Notebook count differs: {notebooks1} vs {notebooks2}"
            )
        
        # Compare notebook reports
        report1 = self._read_notebook_report(dir1 / "notebook-report.txt")
        report2 = self._read_notebook_report(dir2 / "notebook-report.txt")
        
        if report1 != report2:
            comparison["identical"] = False
            comparison["differences"].append("Notebook reports differ")
        
        return comparison
    
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
    
    def _read_notebook_report(self, file_path: Path) -> Dict[str, str]:
        """Read notebook report into dictionary."""
        if not file_path.exists():
            return {}
        
        report = {}
        with open(file_path, "r") as f:
            for line in f:
                if ":" in line:
                    parts = line.strip().split(":", 1)
                    if len(parts) == 2:
                        report[parts[0].strip()] = parts[1].strip()
        return report
    
    def validate_seed_determinism(self, seed: int, runs: int = 2) -> Tuple[bool, str]:
        """
        Validate that a seed produces deterministic results across multiple runs.
        
        Args:
            seed: Seed to validate
            runs: Number of runs to compare
            
        Returns:
            Tuple of (is_deterministic, message)
        """
        if seed not in self.VALID_SEEDS:
            return False, f"Invalid seed {seed}"
        
        print(f"Validating determinism for seed {seed} across {runs} runs...")
        
        temp_dirs = []
        try:
            # Generate multiple baselines
            for i in range(runs):
                temp_dir = self.baseline_root / f"TEMP_SEED_{seed}_RUN_{i+1}"
                temp_dirs.append(temp_dir)
                
                print(f"  Run {i+1}/{runs}...")
                success, message = self.generate_baseline(seed, force=True)
                if not success:
                    return False, f"Failed to generate baseline: {message}"
                
                # Move to temp directory
                baseline_dir = self.get_baseline_dir(seed)
                if baseline_dir.exists():
                    import shutil
                    shutil.move(str(baseline_dir), str(temp_dir))
            
            # Compare all runs
            for i in range(1, runs):
                comparison = self.compare_baselines_dirs(temp_dirs[0], temp_dirs[i])
                if not comparison["identical"]:
                    return False, f"Runs differ: {comparison['differences']}"
            
            return True, f"Seed {seed} is deterministic across {runs} runs"
            
        finally:
            # Cleanup temp directories
            import shutil
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
    
    def compare_baselines_dirs(self, dir1: Path, dir2: Path) -> Dict[str, any]:
        """Compare two baseline directories."""
        comparison = {
            "dir1": str(dir1),
            "dir2": str(dir2),
            "differences": [],
            "identical": True
        }
        
        # Compare checksums
        checksums1 = self._read_checksums(dir1 / "checksums.txt")
        checksums2 = self._read_checksums(dir2 / "checksums.txt")
        
        if checksums1 != checksums2:
            comparison["identical"] = False
            comparison["differences"].append("Checksums differ")
        
        return comparison
    
    def promote_to_canonical(self, seed: int) -> Tuple[bool, str]:
        """
        Promote a seed baseline to canonical status.
        
        Args:
            seed: Seed to promote
            
        Returns:
            Tuple of (success, message)
        """
        if seed not in self.VALID_SEEDS:
            return False, f"Invalid seed {seed}"
        
        source_dir = self.get_baseline_dir(seed)
        if not source_dir.exists():
            return False, f"Baseline for seed {seed} does not exist"
        
        canonical_dir = self.get_canonical_dir()
        
        # Copy to canonical
        import shutil
        if canonical_dir.exists():
            shutil.rmtree(canonical_dir)
        
        shutil.copytree(source_dir, canonical_dir)
        
        return True, f"Promoted seed {seed} baseline to canonical status"
    
    def list_baselines(self) -> List[Dict[str, any]]:
        """List all available baselines."""
        baselines = []
        
        for seed in sorted(self.VALID_SEEDS):
            baseline_dir = self.get_baseline_dir(seed)
            if baseline_dir.exists():
                # Get basic info
                notebooks = len(list(baseline_dir.glob("*.ipynb")))
                has_checksums = (baseline_dir / "checksums.txt").exists()
                has_report = (baseline_dir / "notebook-report.txt").exists()
                
                baselines.append({
                    "seed": seed,
                    "path": str(baseline_dir),
                    "notebooks": notebooks,
                    "has_checksums": has_checksums,
                    "has_report": has_report,
                    "complete": has_checksums and has_report and notebooks >= 16
                })
        
        # Check canonical
        canonical_dir = self.get_canonical_dir()
        if canonical_dir.exists():
            notebooks = len(list(canonical_dir.glob("*.ipynb")))
            baselines.append({
                "seed": self.CANONICAL_SEED,
                "path": str(canonical_dir),
                "notebooks": notebooks,
                "canonical": True,
                "complete": True
            })
        
        return baselines


def main():
    parser = argparse.ArgumentParser(
        description="Manage multi-seed baselines"
    )
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=Path("exports/determinism-baselines"),
        help="Root directory for baselines"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate baseline(s)")
    gen_parser.add_argument("--seed", type=int, help="Specific seed to generate")
    gen_parser.add_argument("--all", action="store_true", help="Generate all seeds")
    gen_parser.add_argument("--force", action="store_true", help="Force regeneration")
    
    # Compare command
    cmp_parser = subparsers.add_parser("compare", help="Compare baselines")
    cmp_parser.add_argument("seed1", type=int, help="First seed")
    cmp_parser.add_argument("seed2", type=int, help="Second seed")
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate seed determinism")
    val_parser.add_argument("seed", type=int, help="Seed to validate")
    val_parser.add_argument("--runs", type=int, default=2, help="Number of runs")
    
    # Promote command
    prm_parser = subparsers.add_parser("promote", help="Promote to canonical")
    prm_parser.add_argument("seed", type=int, help="Seed to promote")
    
    # List command
    subparsers.add_parser("list", help="List all baselines")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = MultiSeedBaselineManager(args.baseline_root)
    
    if args.command == "generate":
        if args.all:
            results = manager.generate_all_baselines(args.force)
            all_success = all(success for success, _ in results.values())
            return 0 if all_success else 1
        elif args.seed:
            success, message = manager.generate_baseline(args.seed, args.force)
            print(message)
            return 0 if success else 1
        else:
            print("Error: Must specify --seed or --all")
            return 1
    
    elif args.command == "compare":
        comparison = manager.compare_baselines(args.seed1, args.seed2)
        print(json.dumps(comparison, indent=2))
        return 0 if comparison.get("identical", False) else 1
    
    elif args.command == "validate":
        success, message = manager.validate_seed_determinism(args.seed, args.runs)
        print(message)
        return 0 if success else 1
    
    elif args.command == "promote":
        success, message = manager.promote_to_canonical(args.seed)
        print(message)
        return 0 if success else 1
    
    elif args.command == "list":
        baselines = manager.list_baselines()
        print(json.dumps(baselines, indent=2))
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
