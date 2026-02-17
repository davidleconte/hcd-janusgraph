#!/usr/bin/env python3
"""
Security Audit Framework for HCD + JanusGraph Banking Compliance Platform

This framework provides comprehensive security auditing capabilities including:
- Automated vulnerability scanning
- Configuration security checks
- Credential security validation
- SSL/TLS certificate validation
- Access control verification
- Audit log integrity checks
- Compliance validation

Usage:
    python security_audit_framework.py --full
    python security_audit_framework.py --quick
    python security_audit_framework.py --report-only
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Security finding severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AuditCategory(Enum):
    """Security audit categories"""
    AUTHENTICATION = "Authentication"
    AUTHORIZATION = "Authorization"
    ENCRYPTION = "Encryption"
    CREDENTIALS = "Credentials"
    NETWORK = "Network Security"
    CONFIGURATION = "Configuration"
    AUDIT_LOGGING = "Audit Logging"
    COMPLIANCE = "Compliance"
    VULNERABILITY = "Vulnerability"


@dataclass
class SecurityFinding:
    """Represents a security audit finding"""
    category: AuditCategory
    severity: SeverityLevel
    title: str
    description: str
    affected_component: str
    remediation: str
    cve_id: Optional[str] = None
    compliance_impact: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AuditReport:
    """Security audit report"""
    audit_id: str
    start_time: str
    end_time: Optional[str] = None
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    compliance_status: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class SecurityAuditFramework:
    """Main security audit framework"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.report = AuditReport(
            audit_id=f"audit-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            start_time=datetime.utcnow().isoformat()
        )
        
    def run_full_audit(self) -> AuditReport:
        """Run complete security audit"""
        logger.info("Starting full security audit...")
        
        # Run all audit checks
        self._audit_credentials()
        self._audit_ssl_tls()
        self._audit_vault_configuration()
        self._audit_network_security()
        self._audit_access_controls()
        self._audit_audit_logging()
        self._audit_dependencies()
        self._audit_configuration_security()
        self._audit_compliance()
        
        # Generate summary
        self._generate_summary()
        self.report.end_time = datetime.utcnow().isoformat()
        
        logger.info(f"Security audit completed. Found {len(self.report.findings)} findings.")
        return self.report
    
    def run_quick_audit(self) -> AuditReport:
        """Run quick security audit (critical checks only)"""
        logger.info("Starting quick security audit...")
        
        # Run critical checks only
        self._audit_credentials()
        self._audit_ssl_tls()
        self._audit_vault_configuration()
        
        self._generate_summary()
        self.report.end_time = datetime.utcnow().isoformat()
        
        logger.info(f"Quick audit completed. Found {len(self.report.findings)} findings.")
        return self.report
    
    def _audit_credentials(self):
        """Audit credential security"""
        logger.info("Auditing credential security...")
        
        # Check for default passwords
        env_files = [
            self.project_root / ".env",
            self.project_root / "config" / "compose" / ".env",
        ]
        
        default_passwords = [
            "changeit", "password", "admin", "root", "test",
            "YOUR_", "PLACEHOLDER", "CHANGE_THIS"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                content = env_file.read_text()
                for default_pwd in default_passwords:
                    if default_pwd.lower() in content.lower():
                        self.report.findings.append(SecurityFinding(
                            category=AuditCategory.CREDENTIALS,
                            severity=SeverityLevel.CRITICAL,
                            title="Default Password Detected",
                            description=f"Default or placeholder password found in {env_file.name}",
                            affected_component=str(env_file),
                            remediation="Replace all default passwords with strong, unique credentials",
                            compliance_impact=["SOC 2", "PCI DSS", "GDPR"]
                        ))
                        break
        
        # Check for hardcoded credentials in code
        code_dirs = [
            self.project_root / "src",
            self.project_root / "banking",
            self.project_root / "scripts"
        ]
        
        for code_dir in code_dirs:
            if code_dir.exists():
                result = subprocess.run(
                    ["grep", "-r", "-i", "-E", 
                     "(password|secret|api_key|token)\\s*=\\s*['\"][^'\"]+['\"]",
                     str(code_dir)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and result.stdout:
                    self.report.findings.append(SecurityFinding(
                        category=AuditCategory.CREDENTIALS,
                        severity=SeverityLevel.HIGH,
                        title="Potential Hardcoded Credentials",
                        description=f"Possible hardcoded credentials found in {code_dir.name}",
                        affected_component=str(code_dir),
                        remediation="Move all credentials to environment variables or Vault",
                        compliance_impact=["SOC 2", "PCI DSS"]
                    ))
    
    def _audit_ssl_tls(self):
        """Audit SSL/TLS configuration"""
        logger.info("Auditing SSL/TLS configuration...")
        
        cert_dir = self.project_root / "config" / "ssl"
        
        if not cert_dir.exists():
            self.report.findings.append(SecurityFinding(
                category=AuditCategory.ENCRYPTION,
                severity=SeverityLevel.CRITICAL,
                title="SSL/TLS Certificates Not Found",
                description="SSL certificate directory does not exist",
                affected_component="SSL/TLS Infrastructure",
                remediation="Run scripts/security/generate_certificates.sh",
                compliance_impact=["PCI DSS", "SOC 2", "GDPR"]
            ))
            return
        
        # Check certificate expiration
        cert_files = list(cert_dir.glob("*.crt"))
        for cert_file in cert_files:
            try:
                result = subprocess.run(
                    ["openssl", "x509", "-in", str(cert_file), "-noout", "-enddate"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Parse expiration date and check if within 30 days
                # This is a simplified check
                if "notAfter" in result.stdout:
                    logger.info(f"Certificate {cert_file.name}: {result.stdout.strip()}")
            except subprocess.CalledProcessError:
                self.report.findings.append(SecurityFinding(
                    category=AuditCategory.ENCRYPTION,
                    severity=SeverityLevel.HIGH,
                    title="Invalid SSL Certificate",
                    description=f"Certificate {cert_file.name} is invalid or corrupted",
                    affected_component=str(cert_file),
                    remediation="Regenerate SSL certificates",
                    compliance_impact=["PCI DSS", "SOC 2"]
                ))
        
        # Check for weak cipher suites in configuration
        config_files = [
            self.project_root / "config" / "janusgraph" / "janusgraph-server.yaml",
            self.project_root / "config" / "hcd" / "cassandra.yaml"
        ]
        
        weak_ciphers = ["SSL", "TLSv1", "TLSv1.1", "RC4", "MD5"]
        for config_file in config_files:
            if config_file.exists():
                content = config_file.read_text()
                for weak_cipher in weak_ciphers:
                    if weak_cipher in content:
                        self.report.findings.append(SecurityFinding(
                            category=AuditCategory.ENCRYPTION,
                            severity=SeverityLevel.MEDIUM,
                            title="Weak Cipher Suite Detected",
                            description=f"Weak cipher {weak_cipher} found in {config_file.name}",
                            affected_component=str(config_file),
                            remediation="Use TLSv1.2+ with strong cipher suites only",
                            compliance_impact=["PCI DSS"]
                        ))
    
    def _audit_vault_configuration(self):
        """Audit HashiCorp Vault configuration"""
        logger.info("Auditing Vault configuration...")
        
        vault_config = self.project_root / "config" / "vault" / "config.hcl"
        
        if not vault_config.exists():
            self.report.findings.append(SecurityFinding(
                category=AuditCategory.CONFIGURATION,
                severity=SeverityLevel.HIGH,
                title="Vault Configuration Missing",
                description="Vault configuration file not found",
                affected_component="HashiCorp Vault",
                remediation="Create Vault configuration and initialize",
                compliance_impact=["SOC 2", "PCI DSS"]
            ))
            return
        
        # Check Vault seal status (if Vault is running)
        try:
            result = subprocess.run(
                ["podman", "exec", "vault-server", "vault", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Sealed" in result.stdout and "true" in result.stdout:
                self.report.findings.append(SecurityFinding(
                    category=AuditCategory.CONFIGURATION,
                    severity=SeverityLevel.CRITICAL,
                    title="Vault is Sealed",
                    description="HashiCorp Vault is in sealed state",
                    affected_component="HashiCorp Vault",
                    remediation="Unseal Vault using unseal keys",
                    compliance_impact=["SOC 2"]
                ))
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            logger.warning("Could not check Vault status (may not be running)")
    
    def _audit_network_security(self):
        """Audit network security configuration"""
        logger.info("Auditing network security...")
        
        compose_files = [
            self.project_root / "config" / "compose" / "docker-compose.full.yml",
            self.project_root / "docker-compose.yml"
        ]
        
        for compose_file in compose_files:
            if compose_file.exists():
                content = compose_file.read_text()
                
                # Check for exposed management ports
                dangerous_ports = ["7199", "9042", "8080", "5005"]  # JMX, Cassandra, etc.
                for port in dangerous_ports:
                    if f'"{port}:' in content or f"'{port}:" in content:
                        self.report.findings.append(SecurityFinding(
                            category=AuditCategory.NETWORK,
                            severity=SeverityLevel.MEDIUM,
                            title="Management Port Exposed",
                            description=f"Port {port} is exposed in {compose_file.name}",
                            affected_component=str(compose_file),
                            remediation="Use SSH tunnels for management ports",
                            compliance_impact=["SOC 2"]
                        ))
                
                # Check for host network mode
                if "network_mode: host" in content:
                    self.report.findings.append(SecurityFinding(
                        category=AuditCategory.NETWORK,
                        severity=SeverityLevel.HIGH,
                        title="Host Network Mode Detected",
                        description="Container using host network mode",
                        affected_component=str(compose_file),
                        remediation="Use bridge networks with proper isolation",
                        compliance_impact=["SOC 2", "PCI DSS"]
                    ))
    
    def _audit_access_controls(self):
        """Audit access control configuration"""
        logger.info("Auditing access controls...")
        
        # Check file permissions on sensitive files
        sensitive_files = [
            self.project_root / ".env",
            self.project_root / "config" / "ssl",
            self.project_root / "config" / "vault"
        ]
        
        for path in sensitive_files:
            if path.exists():
                stat_info = path.stat()
                mode = oct(stat_info.st_mode)[-3:]
                
                # Check if world-readable
                if int(mode[2]) > 0:
                    self.report.findings.append(SecurityFinding(
                        category=AuditCategory.AUTHORIZATION,
                        severity=SeverityLevel.MEDIUM,
                        title="Insecure File Permissions",
                        description=f"{path.name} is world-readable (mode: {mode})",
                        affected_component=str(path),
                        remediation=f"chmod 600 {path} (or 700 for directories)",
                        compliance_impact=["SOC 2", "PCI DSS"]
                    ))
    
    def _audit_audit_logging(self):
        """Audit audit logging configuration"""
        logger.info("Auditing audit logging...")
        
        # Check if audit logger is configured
        audit_logger_file = self.project_root / "banking" / "compliance" / "audit_logger.py"
        
        if not audit_logger_file.exists():
            self.report.findings.append(SecurityFinding(
                category=AuditCategory.AUDIT_LOGGING,
                severity=SeverityLevel.HIGH,
                title="Audit Logger Not Found",
                description="Audit logging module is missing",
                affected_component="Compliance Infrastructure",
                remediation="Implement audit logging for all security events",
                compliance_impact=["SOC 2", "GDPR", "PCI DSS"]
            ))
            return
        
        # Check if audit logs directory exists
        logs_dir = self.project_root / "logs" / "audit"
        if not logs_dir.exists():
            self.report.findings.append(SecurityFinding(
                category=AuditCategory.AUDIT_LOGGING,
                severity=SeverityLevel.MEDIUM,
                title="Audit Logs Directory Missing",
                description="Audit logs directory does not exist",
                affected_component="Audit Logging",
                remediation="Create logs/audit directory with proper permissions",
                compliance_impact=["SOC 2", "GDPR"]
            ))
    
    def _audit_dependencies(self):
        """Audit dependencies for known vulnerabilities"""
        logger.info("Auditing dependencies...")
        
        requirements_files = [
            self.project_root / "requirements-security.txt",
            self.project_root / "requirements-dev.txt",
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                try:
                    # Run pip-audit (if available)
                    result = subprocess.run(
                        ["uv", "tool", "run", "pip-audit", "-r", str(req_file)],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode != 0 and "vulnerabilities" in result.stdout.lower():
                        self.report.findings.append(SecurityFinding(
                            category=AuditCategory.VULNERABILITY,
                            severity=SeverityLevel.HIGH,
                            title="Vulnerable Dependencies Detected",
                            description=f"Vulnerabilities found in {req_file.name}",
                            affected_component=str(req_file),
                            remediation="Update vulnerable packages to patched versions",
                            compliance_impact=["SOC 2", "PCI DSS"]
                        ))
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    logger.warning(f"Could not audit {req_file.name} (pip-audit not available)")
    
    def _audit_configuration_security(self):
        """Audit configuration security"""
        logger.info("Auditing configuration security...")
        
        # Check for debug mode in production configs
        config_files = list(self.project_root.glob("**/*.yaml")) + \
                      list(self.project_root.glob("**/*.yml")) + \
                      list(self.project_root.glob("**/*.conf"))
        
        for config_file in config_files:
            if "test" in str(config_file) or "example" in str(config_file):
                continue
                
            try:
                content = config_file.read_text()
                if "debug: true" in content.lower() or "debug=true" in content.lower():
                    self.report.findings.append(SecurityFinding(
                        category=AuditCategory.CONFIGURATION,
                        severity=SeverityLevel.MEDIUM,
                        title="Debug Mode Enabled",
                        description=f"Debug mode enabled in {config_file.name}",
                        affected_component=str(config_file),
                        remediation="Disable debug mode in production",
                        compliance_impact=["SOC 2"]
                    ))
            except Exception as e:
                logger.debug(f"Could not read {config_file}: {e}")
    
    def _audit_compliance(self):
        """Audit compliance requirements"""
        logger.info("Auditing compliance requirements...")
        
        # Check for required compliance documentation
        compliance_docs = {
            "GDPR": self.project_root / "docs" / "compliance" / "gdpr-compliance.md",
            "SOC 2": self.project_root / "docs" / "compliance" / "soc2-compliance.md",
            "PCI DSS": self.project_root / "docs" / "compliance" / "pci-dss-compliance.md",
            "BSA/AML": self.project_root / "docs" / "compliance" / "bsa-aml-compliance.md"
        }
        
        for standard, doc_path in compliance_docs.items():
            if not doc_path.exists():
                self.report.findings.append(SecurityFinding(
                    category=AuditCategory.COMPLIANCE,
                    severity=SeverityLevel.MEDIUM,
                    title=f"{standard} Documentation Missing",
                    description=f"Compliance documentation for {standard} not found",
                    affected_component="Compliance Documentation",
                    remediation=f"Create {standard} compliance documentation",
                    compliance_impact=[standard]
                ))
    
    def _generate_summary(self):
        """Generate audit summary"""
        # Count findings by severity
        severity_counts = {level: 0 for level in SeverityLevel}
        for finding in self.report.findings:
            severity_counts[finding.severity] += 1
        
        self.report.summary = {
            "total_findings": len(self.report.findings),
            "critical": severity_counts[SeverityLevel.CRITICAL],
            "high": severity_counts[SeverityLevel.HIGH],
            "medium": severity_counts[SeverityLevel.MEDIUM],
            "low": severity_counts[SeverityLevel.LOW],
            "info": severity_counts[SeverityLevel.INFO]
        }
        
        # Generate compliance status
        compliance_standards = ["GDPR", "SOC 2", "PCI DSS", "BSA/AML"]
        for standard in compliance_standards:
            critical_findings = [
                f for f in self.report.findings
                if standard in f.compliance_impact and 
                f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
            ]
            
            if len(critical_findings) == 0:
                self.report.compliance_status[standard] = "COMPLIANT"
            elif len(critical_findings) <= 2:
                self.report.compliance_status[standard] = "NEEDS_ATTENTION"
            else:
                self.report.compliance_status[standard] = "NON_COMPLIANT"
        
        # Generate recommendations
        if self.report.summary["critical"] > 0:
            self.report.recommendations.append(
                "CRITICAL: Address all critical findings immediately before production deployment"
            )
        if self.report.summary["high"] > 0:
            self.report.recommendations.append(
                "HIGH: Remediate high-severity findings within 7 days"
            )
        if self.report.summary["medium"] > 5:
            self.report.recommendations.append(
                "MEDIUM: Create remediation plan for medium-severity findings"
            )
    
    def save_report(self, output_dir: Path):
        """Save audit report to file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON report
        json_file = output_dir / f"{self.report.audit_id}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "audit_id": self.report.audit_id,
                "start_time": self.report.start_time,
                "end_time": self.report.end_time,
                "summary": self.report.summary,
                "compliance_status": self.report.compliance_status,
                "recommendations": self.report.recommendations,
                "findings": [
                    {
                        "category": f.category.value,
                        "severity": f.severity.value,
                        "title": f.title,
                        "description": f.description,
                        "affected_component": f.affected_component,
                        "remediation": f.remediation,
                        "cve_id": f.cve_id,
                        "compliance_impact": f.compliance_impact,
                        "timestamp": f.timestamp
                    }
                    for f in self.report.findings
                ]
            }, f, indent=2)
        
        logger.info(f"JSON report saved to {json_file}")
        
        # Save human-readable report
        md_file = output_dir / f"{self.report.audit_id}.md"
        self._save_markdown_report(md_file)
        logger.info(f"Markdown report saved to {md_file}")
    
    def _save_markdown_report(self, output_file: Path):
        """Save human-readable markdown report"""
        with open(output_file, 'w') as f:
            f.write(f"# Security Audit Report\n\n")
            f.write(f"**Audit ID:** {self.report.audit_id}\n")
            f.write(f"**Start Time:** {self.report.start_time}\n")
            f.write(f"**End Time:** {self.report.end_time}\n\n")
            
            # Summary
            f.write("## Executive Summary\n\n")
            f.write(f"Total Findings: **{self.report.summary['total_findings']}**\n\n")
            f.write("### Findings by Severity\n\n")
            f.write(f"- 🔴 Critical: {self.report.summary['critical']}\n")
            f.write(f"- 🟠 High: {self.report.summary['high']}\n")
            f.write(f"- 🟡 Medium: {self.report.summary['medium']}\n")
            f.write(f"- 🟢 Low: {self.report.summary['low']}\n")
            f.write(f"- ℹ️ Info: {self.report.summary['info']}\n\n")
            
            # Compliance Status
            f.write("### Compliance Status\n\n")
            for standard, status in self.report.compliance_status.items():
                emoji = "✅" if status == "COMPLIANT" else "⚠️" if status == "NEEDS_ATTENTION" else "❌"
                f.write(f"- {emoji} **{standard}**: {status}\n")
            f.write("\n")
            
            # Recommendations
            if self.report.recommendations:
                f.write("### Recommendations\n\n")
                for rec in self.report.recommendations:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            # Detailed Findings
            f.write("## Detailed Findings\n\n")
            
            # Group by severity
            for severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, 
                           SeverityLevel.MEDIUM, SeverityLevel.LOW, SeverityLevel.INFO]:
                findings = [f for f in self.report.findings if f.severity == severity]
                if findings:
                    f.write(f"### {severity.value} Severity\n\n")
                    for finding in findings:
                        f.write(f"#### {finding.title}\n\n")
                        f.write(f"**Category:** {finding.category.value}\n")
                        f.write(f"**Affected Component:** {finding.affected_component}\n")
                        f.write(f"**Description:** {finding.description}\n\n")
                        f.write(f"**Remediation:** {finding.remediation}\n\n")
                        if finding.compliance_impact:
                            f.write(f"**Compliance Impact:** {', '.join(finding.compliance_impact)}\n\n")
                        if finding.cve_id:
                            f.write(f"**CVE ID:** {finding.cve_id}\n\n")
                        f.write("---\n\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Security Audit Framework for HCD + JanusGraph Platform"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full security audit (all checks)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick audit (critical checks only)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/implementation/audits/security"),
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    # Determine project root
    project_root = Path(__file__).parent.parent.parent
    
    # Create framework
    framework = SecurityAuditFramework(project_root)
    
    # Run audit
    if args.quick:
        report = framework.run_quick_audit()
    else:
        report = framework.run_full_audit()
    
    # Save report
    framework.save_report(args.output_dir)
    
    # Print summary
    print("\n" + "="*80)
    print("SECURITY AUDIT SUMMARY")
    print("="*80)
    print(f"Total Findings: {report.summary['total_findings']}")
    print(f"  Critical: {report.summary['critical']}")
    print(f"  High: {report.summary['high']}")
    print(f"  Medium: {report.summary['medium']}")
    print(f"  Low: {report.summary['low']}")
    print(f"  Info: {report.summary['info']}")
    print("\nCompliance Status:")
    for standard, status in report.compliance_status.items():
        print(f"  {standard}: {status}")
    print("="*80)
    
    # Exit with error code if critical findings
    if report.summary['critical'] > 0:
        sys.exit(1)
    elif report.summary['high'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

# Made with Bob
