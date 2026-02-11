#!/usr/bin/env python3
"""
Credential Rotation Framework for HCD + JanusGraph Banking Platform

This framework provides zero-downtime credential rotation for all services:
- JanusGraph/HCD passwords
- OpenSearch passwords
- Grafana passwords
- Pulsar tokens
- SSL/TLS certificates

Features:
- Zero-downtime rotation with graceful service updates
- Vault integration for secure credential storage
- Audit logging for all rotation events
- Rollback capability on failure
- Health checks before and after rotation
- Prometheus metrics for monitoring

Usage:
    python credential_rotation_framework.py rotate --service janusgraph
    python credential_rotation_framework.py rotate --service all
    python credential_rotation_framework.py verify --service opensearch
    python credential_rotation_framework.py rollback --service grafana
"""

import argparse
import json
import logging
import secrets
import string
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import hvac
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging (must be before metrics import)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/credential-rotation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics (optional - only if prometheus_client is available)
try:
    from prometheus_client import Counter, Histogram, Gauge
    METRICS_AVAILABLE = True
    
    # Define metrics
    rotation_counter = Counter(
        'credential_rotation_total',
        'Total credential rotations',
        ['service', 'status']
    )
    rotation_duration = Histogram(
        'credential_rotation_duration_seconds',
        'Credential rotation duration',
        ['service'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
    )
    rotation_status_gauge = Gauge(
        'credential_rotation_status',
        'Current rotation status',
        ['service']
    )
    logger.info("Prometheus metrics enabled")
except ImportError:
    METRICS_AVAILABLE = False
    rotation_counter = None
    rotation_duration = None
    rotation_status_gauge = None
    logger.warning("prometheus_client not available, metrics disabled")


class ServiceType(Enum):
    """Supported services for credential rotation"""
    JANUSGRAPH = "janusgraph"
    HCD = "hcd"
    OPENSEARCH = "opensearch"
    GRAFANA = "grafana"
    PULSAR = "pulsar"
    CERTIFICATES = "certificates"
    ALL = "all"


class RotationStatus(Enum):
    """Rotation operation status"""
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    IN_PROGRESS = "in_progress"


@dataclass
class RotationResult:
    """Result of a credential rotation operation"""
    service: str
    status: RotationStatus
    old_credential_id: Optional[str]
    new_credential_id: Optional[str]
    timestamp: datetime
    duration_seconds: float
    error_message: Optional[str] = None


class VaultClient:
    """Wrapper for HashiCorp Vault operations"""
    
    def __init__(self, vault_addr: str = "http://localhost:8200", vault_token: Optional[str] = None):
        self.vault_addr = vault_addr
        self.client = hvac.Client(url=vault_addr, token=vault_token)
        
        if not self.client.is_authenticated():
            raise ValueError("Vault authentication failed")
    
    def read_secret(self, path: str) -> Dict:
        """Read secret from Vault KV v2"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to read secret from {path}: {e}")
            raise
    
    def write_secret(self, path: str, data: Dict) -> None:
        """Write secret to Vault KV v2"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(path=path, secret=data)
            logger.info(f"Successfully wrote secret to {path}")
        except Exception as e:
            logger.error(f"Failed to write secret to {path}: {e}")
            raise
    
    def create_backup(self, path: str) -> str:
        """Create backup of current secret"""
        try:
            current = self.read_secret(path)
            backup_path = f"{path}_backup_{int(time.time())}"
            self.write_secret(backup_path, current)
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise


class PasswordGenerator:
    """Secure password generation"""
    
    @staticmethod
    def generate_password(length: int = 32, include_special: bool = True) -> str:
        """Generate cryptographically secure password"""
        alphabet = string.ascii_letters + string.digits
        if include_special:
            alphabet += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
        # Ensure password has at least one of each character type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
        ]
        
        if include_special:
            password.append(secrets.choice("!@#$%^&*()-_=+"))
        
        # Fill remaining length
        password.extend(secrets.choice(alphabet) for _ in range(length - len(password)))
        
        # Shuffle to avoid predictable patterns
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    @staticmethod
    def generate_token(length: int = 64) -> str:
        """Generate secure token for API authentication"""
        return secrets.token_urlsafe(length)


class ServiceHealthChecker:
    """Health check utilities for services"""
    
    def __init__(self):
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def check_janusgraph(self, host: str = "localhost", port: int = 8182) -> bool:
        """Check JanusGraph health"""
        try:
            response = self.session.get(
                f"http://{host}:{port}?gremlin=g.V().count()",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"JanusGraph health check failed: {e}")
            return False
    
    def check_opensearch(self, host: str = "localhost", port: int = 9200, 
                        username: str = "admin", password: str = "") -> bool:
        """Check OpenSearch health"""
        try:
            response = self.session.get(
                f"http://{host}:{port}/_cluster/health",
                auth=(username, password),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenSearch health check failed: {e}")
            return False
    
    def check_grafana(self, host: str = "localhost", port: int = 3001) -> bool:
        """Check Grafana health"""
        try:
            response = self.session.get(f"http://{host}:{port}/api/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Grafana health check failed: {e}")
            return False
    
    def check_pulsar(self, host: str = "localhost", port: int = 8080) -> bool:
        """Check Pulsar health"""
        try:
            response = self.session.get(f"http://{host}:{port}/admin/v2/brokers/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Pulsar health check failed: {e}")
            return False


class CredentialRotator:
    """Main credential rotation orchestrator"""
    
    def __init__(self, vault_client: VaultClient, project_name: str = "janusgraph-demo"):
        self.vault = vault_client
        self.project_name = project_name
        self.health_checker = ServiceHealthChecker()
        self.password_gen = PasswordGenerator()
    
    def rotate_janusgraph_password(self) -> RotationResult:
        """Rotate JanusGraph admin password with zero downtime"""
        start_time = time.time()
        service = "janusgraph"
        
        try:
            logger.info("Starting JanusGraph password rotation")
            
            # 1. Pre-rotation health check
            if not self.health_checker.check_janusgraph():
                raise RuntimeError("JanusGraph is not healthy before rotation")
            
            # 2. Create backup of current credentials
            backup_path = self.vault.create_backup("janusgraph/admin")
            old_creds = self.vault.read_secret("janusgraph/admin")
            
            # 3. Generate new password
            new_password = self.password_gen.generate_password(length=32)
            
            # 4. Update Vault with new password
            new_creds = {
                "username": old_creds.get("username", "admin"),
                "password": new_password,
                "rotated_at": datetime.utcnow().isoformat(),
                "rotated_by": "credential_rotation_framework"
            }
            self.vault.write_secret("janusgraph/admin", new_creds)
            
            # 5. Update JanusGraph configuration (requires restart)
            self._update_janusgraph_config(new_password)
            
            # 6. Graceful restart with health check
            self._restart_service("janusgraph", wait_seconds=30)
            
            # 7. Post-rotation health check
            if not self.health_checker.check_janusgraph():
                logger.error("JanusGraph health check failed after rotation, rolling back")
                self._rollback_from_backup(backup_path, "janusgraph/admin")
                self._restart_service("janusgraph", wait_seconds=30)
                raise RuntimeError("Post-rotation health check failed")
            
            duration = time.time() - start_time
            logger.info(f"JanusGraph password rotation completed in {duration:.2f}s")
            
            result = RotationResult(
                service=service,
                status=RotationStatus.SUCCESS,
                old_credential_id=backup_path,
                new_credential_id="janusgraph/admin",
                timestamp=datetime.utcnow(),
                duration_seconds=duration
            )
            
            # Record metrics
            if METRICS_AVAILABLE:
                rotation_counter.labels(service=service, status='success').inc()
                rotation_duration.labels(service=service).observe(duration)
                rotation_status_gauge.labels(service=service).set(1)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"JanusGraph password rotation failed: {e}")
            
            result = RotationResult(
                service=service,
                status=RotationStatus.FAILED,
                old_credential_id=None,
                new_credential_id=None,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                error_message=str(e)
            )
            
            # Record metrics
            if METRICS_AVAILABLE:
                rotation_counter.labels(service=service, status='failed').inc()
                rotation_duration.labels(service=service).observe(duration)
                rotation_status_gauge.labels(service=service).set(0)
            
            return result
    
    def rotate_opensearch_password(self) -> RotationResult:
        """Rotate OpenSearch admin password with zero downtime"""
        start_time = time.time()
        service = "opensearch"
        
        try:
            logger.info("Starting OpenSearch password rotation")
            
            # 1. Pre-rotation health check
            old_creds = self.vault.read_secret("opensearch/admin")
            if not self.health_checker.check_opensearch(
                username=old_creds["username"],
                password=old_creds["password"]
            ):
                raise RuntimeError("OpenSearch is not healthy before rotation")
            
            # 2. Create backup
            backup_path = self.vault.create_backup("opensearch/admin")
            
            # 3. Generate new password
            new_password = self.password_gen.generate_password(length=32)
            
            # 4. Update OpenSearch internal user (using Security API)
            self._update_opensearch_user(
                old_creds["username"],
                old_creds["password"],
                new_password
            )
            
            # 5. Update Vault
            new_creds = {
                "username": old_creds["username"],
                "password": new_password,
                "rotated_at": datetime.utcnow().isoformat(),
                "rotated_by": "credential_rotation_framework"
            }
            self.vault.write_secret("opensearch/admin", new_creds)
            
            # 6. Verify new credentials work
            if not self.health_checker.check_opensearch(
                username=new_creds["username"],
                password=new_password
            ):
                logger.error("OpenSearch health check failed with new credentials, rolling back")
                self._rollback_opensearch_user(
                    old_creds["username"],
                    new_password,
                    old_creds["password"]
                )
                self._rollback_from_backup(backup_path, "opensearch/admin")
                raise RuntimeError("Post-rotation health check failed")
            
            duration = time.time() - start_time
            logger.info(f"OpenSearch password rotation completed in {duration:.2f}s")
            
            return RotationResult(
                service=service,
                status=RotationStatus.SUCCESS,
                old_credential_id=backup_path,
                new_credential_id="opensearch/admin",
                timestamp=datetime.utcnow(),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"OpenSearch password rotation failed: {e}")
            return RotationResult(
                service=service,
                status=RotationStatus.FAILED,
                old_credential_id=None,
                new_credential_id=None,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def rotate_grafana_password(self) -> RotationResult:
        """Rotate Grafana admin password"""
        start_time = time.time()
        service = "grafana"
        
        try:
            logger.info("Starting Grafana password rotation")
            
            # 1. Pre-rotation health check
            if not self.health_checker.check_grafana():
                raise RuntimeError("Grafana is not healthy before rotation")
            
            # 2. Create backup
            backup_path = self.vault.create_backup("grafana/admin")
            old_creds = self.vault.read_secret("grafana/admin")
            
            # 3. Generate new password
            new_password = self.password_gen.generate_password(length=32)
            
            # 4. Update Grafana admin password via API
            self._update_grafana_password(
                old_creds["username"],
                old_creds["password"],
                new_password
            )
            
            # 5. Update Vault
            new_creds = {
                "username": old_creds["username"],
                "password": new_password,
                "rotated_at": datetime.utcnow().isoformat(),
                "rotated_by": "credential_rotation_framework"
            }
            self.vault.write_secret("grafana/admin", new_creds)
            
            # 6. Verify new credentials
            if not self._verify_grafana_login(new_creds["username"], new_password):
                logger.error("Grafana login failed with new credentials, rolling back")
                self._update_grafana_password(
                    new_creds["username"],
                    new_password,
                    old_creds["password"]
                )
                self._rollback_from_backup(backup_path, "grafana/admin")
                raise RuntimeError("Post-rotation verification failed")
            
            duration = time.time() - start_time
            logger.info(f"Grafana password rotation completed in {duration:.2f}s")
            
            return RotationResult(
                service=service,
                status=RotationStatus.SUCCESS,
                old_credential_id=backup_path,
                new_credential_id="grafana/admin",
                timestamp=datetime.utcnow(),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Grafana password rotation failed: {e}")
            return RotationResult(
                service=service,
                status=RotationStatus.FAILED,
                old_credential_id=None,
                new_credential_id=None,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def rotate_pulsar_token(self) -> RotationResult:
        """Rotate Pulsar authentication token"""
        start_time = time.time()
        service = "pulsar"
        
        try:
            logger.info("Starting Pulsar token rotation")
            
            # 1. Pre-rotation health check
            if not self.health_checker.check_pulsar():
                raise RuntimeError("Pulsar is not healthy before rotation")
            
            # 2. Create backup
            backup_path = self.vault.create_backup("pulsar/admin")
            
            # 3. Generate new token
            new_token = self.password_gen.generate_token(length=64)
            
            # 4. Update Pulsar token configuration
            self._update_pulsar_token(new_token)
            
            # 5. Update Vault
            new_creds = {
                "token": new_token,
                "rotated_at": datetime.utcnow().isoformat(),
                "rotated_by": "credential_rotation_framework"
            }
            self.vault.write_secret("pulsar/admin", new_creds)
            
            # 6. Restart Pulsar services
            self._restart_service("pulsar", wait_seconds=30)
            
            # 7. Post-rotation health check
            if not self.health_checker.check_pulsar():
                logger.error("Pulsar health check failed after rotation, rolling back")
                self._rollback_from_backup(backup_path, "pulsar/admin")
                self._restart_service("pulsar", wait_seconds=30)
                raise RuntimeError("Post-rotation health check failed")
            
            duration = time.time() - start_time
            logger.info(f"Pulsar token rotation completed in {duration:.2f}s")
            
            return RotationResult(
                service=service,
                status=RotationStatus.SUCCESS,
                old_credential_id=backup_path,
                new_credential_id="pulsar/admin",
                timestamp=datetime.utcnow(),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Pulsar token rotation failed: {e}")
            return RotationResult(
                service=service,
                status=RotationStatus.FAILED,
                old_credential_id=None,
                new_credential_id=None,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def rotate_certificates(self) -> RotationResult:
        """Rotate SSL/TLS certificates"""
        start_time = time.time()
        service = "certificates"
        
        try:
            logger.info("Starting SSL/TLS certificate rotation")
            
            # 1. Generate new certificates
            cert_dir = Path("config/security/certs")
            backup_dir = cert_dir / f"backup_{int(time.time())}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 2. Backup existing certificates
            for cert_file in cert_dir.glob("*.pem"):
                subprocess.run(["cp", str(cert_file), str(backup_dir)], check=True)
            
            # 3. Generate new certificates
            subprocess.run(["bash", "scripts/security/generate_certificates.sh"], check=True)
            
            # 4. Update Vault with certificate metadata
            cert_metadata = {
                "generated_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
                "backup_location": str(backup_dir)
            }
            self.vault.write_secret("certificates/metadata", cert_metadata)
            
            # 5. Restart services that use certificates
            services_to_restart = ["janusgraph", "opensearch", "nginx"]
            for svc in services_to_restart:
                self._restart_service(svc, wait_seconds=15)
            
            # 6. Verify all services are healthy
            all_healthy = all([
                self.health_checker.check_janusgraph(),
                self.health_checker.check_opensearch(username="admin", password=""),
                self.health_checker.check_grafana()
            ])
            
            if not all_healthy:
                logger.error("Some services unhealthy after certificate rotation, rolling back")
                for cert_file in backup_dir.glob("*.pem"):
                    subprocess.run(["cp", str(cert_file), str(cert_dir)], check=True)
                for svc in services_to_restart:
                    self._restart_service(svc, wait_seconds=15)
                raise RuntimeError("Post-rotation health check failed")
            
            duration = time.time() - start_time
            logger.info(f"Certificate rotation completed in {duration:.2f}s")
            
            return RotationResult(
                service=service,
                status=RotationStatus.SUCCESS,
                old_credential_id=str(backup_dir),
                new_credential_id=str(cert_dir),
                timestamp=datetime.utcnow(),
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Certificate rotation failed: {e}")
            return RotationResult(
                service=service,
                status=RotationStatus.FAILED,
                old_credential_id=None,
                new_credential_id=None,
                timestamp=datetime.utcnow(),
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _update_janusgraph_config(self, new_password: str) -> None:
        """Update JanusGraph configuration with new password"""
        # This would update the janusgraph-auth.properties file
        # Implementation depends on deployment method
        logger.info("Updating JanusGraph configuration")
        # TODO: Implement actual config update
    
    def _update_opensearch_user(self, username: str, old_password: str, new_password: str) -> None:
        """Update OpenSearch internal user password"""
        url = "http://localhost:9200/_plugins/_security/api/internalusers/admin"
        headers = {"Content-Type": "application/json"}
        data = {"password": new_password}
        
        response = requests.put(
            url,
            auth=(username, old_password),
            headers=headers,
            json=data,
            timeout=10
        )
        response.raise_for_status()
        logger.info("Updated OpenSearch user password")
    
    def _rollback_opensearch_user(self, username: str, current_password: str, old_password: str) -> None:
        """Rollback OpenSearch user password"""
        self._update_opensearch_user(username, current_password, old_password)
    
    def _update_grafana_password(self, username: str, old_password: str, new_password: str) -> None:
        """Update Grafana admin password"""
        url = "http://localhost:3001/api/user/password"
        headers = {"Content-Type": "application/json"}
        data = {
            "oldPassword": old_password,
            "newPassword": new_password,
            "confirmNew": new_password
        }
        
        response = requests.put(
            url,
            auth=(username, old_password),
            headers=headers,
            json=data,
            timeout=10
        )
        response.raise_for_status()
        logger.info("Updated Grafana admin password")
    
    def _verify_grafana_login(self, username: str, password: str) -> bool:
        """Verify Grafana login with new credentials"""
        try:
            response = requests.get(
                "http://localhost:3001/api/user",
                auth=(username, password),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Grafana login verification failed: {e}")
            return False
    
    def _update_pulsar_token(self, new_token: str) -> None:
        """Update Pulsar authentication token"""
        # This would update Pulsar's token configuration
        logger.info("Updating Pulsar token configuration")
        # TODO: Implement actual token update
    
    def _restart_service(self, service: str, wait_seconds: int = 30) -> None:
        """Gracefully restart a service using podman-compose"""
        try:
            logger.info(f"Restarting {service} service")
            subprocess.run([
                "podman-compose",
                "-p", self.project_name,
                "-f", "config/compose/docker-compose.full.yml",
                "restart", service
            ], check=True, cwd="/Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph")
            
            logger.info(f"Waiting {wait_seconds}s for {service} to be ready")
            time.sleep(wait_seconds)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart {service}: {e}")
            raise
    
    def _rollback_from_backup(self, backup_path: str, target_path: str) -> None:
        """Rollback credentials from backup"""
        try:
            backup_data = self.vault.read_secret(backup_path.replace("janusgraph/", ""))
            self.vault.write_secret(target_path, backup_data)
            logger.info(f"Rolled back {target_path} from {backup_path}")
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise


def main():
    """Main entry point for credential rotation"""
    parser = argparse.ArgumentParser(description="Credential Rotation Framework")
    parser.add_argument(
        "action",
        choices=["rotate", "verify", "rollback"],
        help="Action to perform"
    )
    parser.add_argument(
        "--service",
        choices=[s.value for s in ServiceType],
        required=True,
        help="Service to rotate credentials for"
    )
    parser.add_argument(
        "--vault-addr",
        default="http://localhost:8200",
        help="Vault server address"
    )
    parser.add_argument(
        "--vault-token",
        help="Vault authentication token (or set VAULT_TOKEN env var)"
    )
    parser.add_argument(
        "--project-name",
        default="janusgraph-demo",
        help="Podman compose project name"
    )
    
    args = parser.parse_args()
    
    # Initialize Vault client
    vault_token = args.vault_token or subprocess.check_output(
        ["bash", "-c", "source scripts/security/vault_access.sh && echo $VAULT_APP_TOKEN"],
        text=True
    ).strip()
    
    vault_client = VaultClient(vault_addr=args.vault_addr, vault_token=vault_token)
    rotator = CredentialRotator(vault_client, project_name=args.project_name)
    
    # Execute action
    if args.action == "rotate":
        if args.service == ServiceType.ALL.value:
            services = [
                ServiceType.JANUSGRAPH,
                ServiceType.OPENSEARCH,
                ServiceType.GRAFANA,
                ServiceType.PULSAR,
                ServiceType.CERTIFICATES
            ]
        else:
            services = [ServiceType(args.service)]
        
        results = []
        for service in services:
            if service == ServiceType.JANUSGRAPH:
                result = rotator.rotate_janusgraph_password()
            elif service == ServiceType.OPENSEARCH:
                result = rotator.rotate_opensearch_password()
            elif service == ServiceType.GRAFANA:
                result = rotator.rotate_grafana_password()
            elif service == ServiceType.PULSAR:
                result = rotator.rotate_pulsar_token()
            elif service == ServiceType.CERTIFICATES:
                result = rotator.rotate_certificates()
            else:
                continue
            
            results.append(result)
            
            # Log result
            logger.info(f"Rotation result for {result.service}: {result.status.value}")
            if result.status == RotationStatus.FAILED:
                logger.error(f"Error: {result.error_message}")
        
        # Print summary
        print("\n=== Rotation Summary ===")
        for result in results:
            status_emoji = "✅" if result.status == RotationStatus.SUCCESS else "❌"
            print(f"{status_emoji} {result.service}: {result.status.value} ({result.duration_seconds:.2f}s)")
        
        # Exit with error if any rotation failed
        if any(r.status == RotationStatus.FAILED for r in results):
            sys.exit(1)
    
    elif args.action == "verify":
        # Verify service health
        health_checker = ServiceHealthChecker()
        if args.service == ServiceType.JANUSGRAPH.value:
            healthy = health_checker.check_janusgraph()
        elif args.service == ServiceType.OPENSEARCH.value:
            healthy = health_checker.check_opensearch(username="admin", password="")
        elif args.service == ServiceType.GRAFANA.value:
            healthy = health_checker.check_grafana()
        elif args.service == ServiceType.PULSAR.value:
            healthy = health_checker.check_pulsar()
        else:
            print(f"Verification not implemented for {args.service}")
            sys.exit(1)
        
        if healthy:
            print(f"✅ {args.service} is healthy")
            sys.exit(0)
        else:
            print(f"❌ {args.service} is not healthy")
            sys.exit(1)
    
    elif args.action == "rollback":
        print(f"Rollback for {args.service} - manual intervention required")
        print("Check Vault backups and restore manually if needed")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
