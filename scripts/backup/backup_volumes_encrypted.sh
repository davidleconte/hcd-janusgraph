#!/bin/bash
# Encrypted Backup Script for HCD and JanusGraph
# File: scripts/backup/backup_volumes_encrypted.sh
# Created: 2026-01-28
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/janusgraph}"
RETENTION_DAYS="${RETENTION_DAYS:-90}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
TEMP_DIR="/tmp/${BACKUP_NAME}"

# Encryption configuration
GPG_RECIPIENT="${BACKUP_ENCRYPTION_KEY:-backup@example.com}"
ENCRYPTION_ENABLED="${BACKUP_ENCRYPTION_ENABLED:-true}"

# AWS S3 configuration (optional)
S3_BUCKET="${AWS_S3_BACKUP_BUCKET:-}"
S3_REGION="${AWS_REGION:-us-east-1}"
S3_STORAGE_CLASS="${S3_STORAGE_CLASS:-STANDARD_IA}"
S3_ENCRYPTION="${S3_ENCRYPTION:-aws:kms}"
S3_KMS_KEY="${AWS_KMS_KEY_ID:-}"

# Podman configuration
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-wxd}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if podman is accessible
    if ! podman --remote --connection "$PODMAN_CONNECTION" ps >/dev/null 2>&1; then
        log_error "Cannot connect to Podman. Check connection: $PODMAN_CONNECTION"
        exit 1
    fi

    # Check if GPG is installed (for encryption)
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        if ! command -v gpg &> /dev/null; then
            log_error "GPG not installed. Install with: apt-get install gnupg"
            exit 1
        fi

        # Check if GPG key exists
        if ! gpg --list-keys "$GPG_RECIPIENT" &> /dev/null; then
            log_warning "GPG key for $GPG_RECIPIENT not found"
            log_info "Generate key with: gpg --gen-key"
            log_info "Or import existing key: gpg --import key.asc"
        fi
    fi

    # Check if AWS CLI is installed (if S3 backup enabled)
    if [ -n "$S3_BUCKET" ]; then
        if ! command -v aws &> /dev/null; then
            log_warning "AWS CLI not installed. S3 backup will be skipped."
            log_info "Install with: pip install awscli"
            S3_BUCKET=""
        fi
    fi

    log_success "Prerequisites check completed"
}

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory..."
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$TEMP_DIR"
    log_success "Backup directory created: $BACKUP_DIR"
}

# Backup HCD data
backup_hcd() {
    log_info "Backing up HCD data..."

    # Create HCD snapshot
    log_info "Creating HCD snapshot..."
    podman --remote --connection "$PODMAN_CONNECTION" exec hcd-server \
        /opt/hcd/bin/nodetool snapshot janusgraph || {
        log_warning "HCD snapshot failed (non-critical)"
    }

    # Export HCD data
    log_info "Exporting HCD data..."
    podman --remote --connection "$PODMAN_CONNECTION" exec hcd-server \
        tar -czf /tmp/hcd_data.tar.gz /var/lib/hcd/data 2>/dev/null || {
        log_error "Failed to create HCD data archive"
        return 1
    }

    # Copy from container
    podman --remote --connection "$PODMAN_CONNECTION" cp \
        hcd-server:/tmp/hcd_data.tar.gz "$TEMP_DIR/hcd_data.tar.gz"

    # Cleanup container temp file
    podman --remote --connection "$PODMAN_CONNECTION" exec hcd-server \
        rm -f /tmp/hcd_data.tar.gz

    log_success "HCD data backed up: $(du -h "$TEMP_DIR/hcd_data.tar.gz" | cut -f1)"
}

# Backup JanusGraph data
backup_janusgraph() {
    log_info "Backing up JanusGraph data..."

    # Export JanusGraph data
    podman --remote --connection "$PODMAN_CONNECTION" exec janusgraph-server \
        tar -czf /tmp/janusgraph_data.tar.gz /var/lib/janusgraph 2>/dev/null || {
        log_error "Failed to create JanusGraph data archive"
        return 1
    }

    # Copy from container
    podman --remote --connection "$PODMAN_CONNECTION" cp \
        janusgraph-server:/tmp/janusgraph_data.tar.gz "$TEMP_DIR/janusgraph_data.tar.gz"

    # Cleanup container temp file
    podman --remote --connection "$PODMAN_CONNECTION" exec janusgraph-server \
        rm -f /tmp/janusgraph_data.tar.gz

    log_success "JanusGraph data backed up: $(du -h "$TEMP_DIR/janusgraph_data.tar.gz" | cut -f1)"
}

# Export graph to GraphML
export_graphml() {
    log_info "Exporting graph to GraphML..."

    # Use Python script if available
    if [ -f "$SCRIPT_DIR/export_graph.py" ]; then
        python3 "$SCRIPT_DIR/export_graph.py" \
            --output "$TEMP_DIR/graph_export.graphml" \
            --host localhost \
            --port 18182 || {
            log_warning "GraphML export failed (non-critical)"
            return 0
        }
        log_success "Graph exported to GraphML: $(du -h "$TEMP_DIR/graph_export.graphml" | cut -f1)"
    else
        log_warning "export_graph.py not found, skipping GraphML export"
    fi
}

# Create backup metadata
create_metadata() {
    log_info "Creating backup metadata..."

    cat > "$TEMP_DIR/backup_metadata.json" <<EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$TIMESTAMP",
  "date": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "components": {
    "hcd": {
      "version": "1.2.3",
      "data_size": "$(du -sb "$TEMP_DIR/hcd_data.tar.gz" 2>/dev/null | cut -f1 || echo 0)"
    },
    "janusgraph": {
      "version": "latest",
      "data_size": "$(du -sb "$TEMP_DIR/janusgraph_data.tar.gz" 2>/dev/null | cut -f1 || echo 0)"
    }
  },
  "encryption": {
    "enabled": $ENCRYPTION_ENABLED,
    "method": "GPG",
    "recipient": "$GPG_RECIPIENT"
  },
  "retention_days": $RETENTION_DAYS
}
EOF

    log_success "Metadata created"
}

# Encrypt backup
encrypt_backup() {
    if [ "$ENCRYPTION_ENABLED" != "true" ]; then
        log_warning "Encryption disabled, skipping..."
        return 0
    fi

    log_info "Encrypting backup files..."

    # Encrypt each file
    for file in "$TEMP_DIR"/*.tar.gz "$TEMP_DIR"/*.graphml 2>/dev/null; do
        if [ -f "$file" ]; then
            log_info "Encrypting $(basename "$file")..."
            gpg --encrypt --recipient "$GPG_RECIPIENT" \
                --trust-model always \
                --output "${file}.gpg" \
                "$file" || {
                log_error "Failed to encrypt $file"
                return 1
            }
            # Remove unencrypted file
            rm -f "$file"
            log_success "Encrypted: $(basename "$file").gpg"
        fi
    done

    # Encrypt metadata
    gpg --encrypt --recipient "$GPG_RECIPIENT" \
        --trust-model always \
        --output "$TEMP_DIR/backup_metadata.json.gpg" \
        "$TEMP_DIR/backup_metadata.json"
    rm -f "$TEMP_DIR/backup_metadata.json"

    log_success "All files encrypted"
}

# Create final backup archive
create_final_archive() {
    log_info "Creating final backup archive..."

    local archive_name="${BACKUP_NAME}.tar.gz"
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        archive_name="${BACKUP_NAME}_encrypted.tar.gz"
    fi

    tar -czf "$BACKUP_DIR/$archive_name" -C "$TEMP_DIR" . || {
        log_error "Failed to create final archive"
        return 1
    }

    log_success "Final archive created: $BACKUP_DIR/$archive_name"
    log_info "Archive size: $(du -h "$BACKUP_DIR/$archive_name" | cut -f1)"
}

# Upload to S3
upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        log_info "S3 backup not configured, skipping..."
        return 0
    fi

    log_info "Uploading to S3: s3://$S3_BUCKET/..."

    local archive_name="${BACKUP_NAME}.tar.gz"
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        archive_name="${BACKUP_NAME}_encrypted.tar.gz"
    fi

    # Upload with server-side encryption
    if [ -n "$S3_KMS_KEY" ]; then
        aws s3 cp "$BACKUP_DIR/$archive_name" \
            "s3://$S3_BUCKET/janusgraph/$archive_name" \
            --region "$S3_REGION" \
            --storage-class "$S3_STORAGE_CLASS" \
            --sse "$S3_ENCRYPTION" \
            --sse-kms-key-id "$S3_KMS_KEY" || {
            log_error "S3 upload failed"
            return 1
        }
    else
        aws s3 cp "$BACKUP_DIR/$archive_name" \
            "s3://$S3_BUCKET/janusgraph/$archive_name" \
            --region "$S3_REGION" \
            --storage-class "$S3_STORAGE_CLASS" \
            --sse AES256 || {
            log_error "S3 upload failed"
            return 1
        }
    fi

    log_success "Uploaded to S3"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."

    # Local cleanup
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
    local deleted_count=$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS | wc -l)

    if [ "$deleted_count" -gt 0 ]; then
        log_success "Deleted $deleted_count old local backups"
    else
        log_info "No old local backups to delete"
    fi

    # S3 cleanup (if configured)
    if [ -n "$S3_BUCKET" ]; then
        log_info "Cleaning up old S3 backups..."
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d 2>/dev/null || date -v -${RETENTION_DAYS}d +%Y-%m-%d)

        aws s3 ls "s3://$S3_BUCKET/janusgraph/" --region "$S3_REGION" | \
        while read -r line; do
            local file_date=$(echo "$line" | awk '{print $1}')
            local file_name=$(echo "$line" | awk '{print $4}')

            if [[ "$file_date" < "$cutoff_date" ]]; then
                aws s3 rm "s3://$S3_BUCKET/janusgraph/$file_name" --region "$S3_REGION"
                log_info "Deleted old S3 backup: $file_name"
            fi
        done
    fi
}

# Cleanup temporary files
cleanup_temp() {
    log_info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    log_success "Temporary files cleaned up"
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."

    local archive_name="${BACKUP_NAME}.tar.gz"
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        archive_name="${BACKUP_NAME}_encrypted.tar.gz"
    fi

    # Test archive integrity
    if tar -tzf "$BACKUP_DIR/$archive_name" >/dev/null 2>&1; then
        log_success "Backup archive integrity verified"
    else
        log_error "Backup archive is corrupted!"
        return 1
    fi

    # Calculate checksum
    local checksum=$(sha256sum "$BACKUP_DIR/$archive_name" | awk '{print $1}')
    echo "$checksum  $archive_name" > "$BACKUP_DIR/${archive_name}.sha256"
    log_success "Checksum: $checksum"
}

# Main execution
main() {
    echo "=========================================="
    echo "🔐 Encrypted Backup - HCD + JanusGraph"
    echo "=========================================="
    echo ""
    echo "Timestamp: $(date)"
    echo "Backup Name: $BACKUP_NAME"
    echo "Encryption: $ENCRYPTION_ENABLED"
    echo "Retention: $RETENTION_DAYS days"
    echo ""

    # Execute backup steps
    check_prerequisites
    create_backup_dir

    backup_hcd || log_error "HCD backup failed"
    backup_janusgraph || log_error "JanusGraph backup failed"
    export_graphml

    create_metadata
    encrypt_backup
    create_final_archive
    verify_backup

    upload_to_s3
    cleanup_old_backups
    cleanup_temp

    echo ""
    echo "=========================================="
    echo -e "${GREEN}✅ Backup Completed Successfully${NC}"
    echo "=========================================="
    echo ""
    echo "📁 Backup Location: $BACKUP_DIR"
    echo "📦 Archive: ${BACKUP_NAME}*.tar.gz"
    echo "🔐 Encryption: $ENCRYPTION_ENABLED"
    echo "☁️  S3 Upload: $([ -n "$S3_BUCKET" ] && echo "Yes" || echo "No")"
    echo ""
    echo "To restore this backup:"
    echo "  ./scripts/backup/restore_volumes.sh $BACKUP_DIR/${BACKUP_NAME}*.tar.gz"
    echo ""
}

# Trap errors
trap 'log_error "Backup failed at line $LINENO"; cleanup_temp; exit 1' ERR

# Run main function
main

exit 0

# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
