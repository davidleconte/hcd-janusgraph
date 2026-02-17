# Backup and Restore Guide

**File**: docs/BACKUP.md
**Created**: 2026-01-28T11:07:00.123
**Author**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

---

## Overview

This guide covers backup and restore procedures for the HCD + JanusGraph stack.

## Backup Strategy

### What Gets Backed Up

1. **HCD Data**: Cassandra data files
2. **JanusGraph Data**: Graph database files
3. **Graph Export**: GraphML format for portability

### Backup Frequency

**Recommended Schedule**:

- Daily: Full backup (automated via cron)
- Hourly: Incremental snapshots
- Before deployments: Manual backup

---

## Manual Backup

### Create Backup

bash scripts/backup/backup_volumes.sh

This creates:

- HCD snapshot
- JanusGraph data archive
- GraphML export

Backup location: /backups/janusgraph/

### Backup Contents

timestamp_YYYYMMDD_HHMMSS/

- hcd/: HCD data files
- janusgraph.tar.gz: JanusGraph data
- graph.graphml: Graph export

---

## Automated Backups

### Setup Cron Job

Edit crontab:

crontab -e

Add daily backup at 2 AM:

0 2 ** * /path/to/scripts/backup/backup_volumes.sh

### Backup Retention

Default: 30 days

Configure in .env:

RETENTION_DAYS=30

Old backups auto-deleted after retention period.

---

## S3 Integration (Optional)

### Setup AWS Credentials

export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_S3_BACKUP_BUCKET=my-janusgraph-backups

### Automatic Upload

Backups automatically upload to S3 if AWS_S3_BACKUP_BUCKET is set.

Storage class: STANDARD_IA (Infrequent Access) for cost savings.

---

## Restore Procedures

### Restore from Backup

bash scripts/backup/restore_volumes.sh /backups/janusgraph/hcd_20260128_103000

Steps:

1. Prompts for confirmation
2. Stops all services
3. Restores HCD data
4. Restores JanusGraph data
5. Starts services
6. Runs smoke tests

### Verify Restore

After restore completes:

bash scripts/testing/run_tests.sh

Check:

- All tests pass
- Expected data present
- Services healthy

---

## Disaster Recovery

### RTO/RPO

**Recovery Time Objective (RTO)**: 1 hour
**Recovery Point Objective (RPO)**: 24 hours (daily backups)

### Recovery Steps

1. **Identify Issue**: What data is lost/corrupted?
2. **Select Backup**: Choose restore point
3. **Restore Data**: Run restore script
4. **Verify**: Check data integrity
5. **Resume Operations**: Restart services

### Test Restores

Regularly test restore procedures:

bash scripts/backup/test_backup.sh

Best practice: Test restore monthly.

---

## Backup Validation

### Verify Backup Integrity

After backup:

# Check backup exists

ls -lh /backups/janusgraph/

# Verify archive integrity

tar -tzf /backups/janusgraph/janusgraph_*.tar.gz > /dev/null

# Check GraphML export

wc -l /backups/janusgraph/graph_*.graphml

---

## Point-in-Time Recovery

### HCD Snapshots

HCD supports incremental snapshots:

PODMAN_CONNECTION=podman-wxd podman --remote exec hcd-server-server nodetool snapshot

Snapshots stored in HCD data directory.

### Restore from Snapshot

PODMAN_CONNECTION=podman-wxd podman --remote exec hcd-server-server nodetool refresh janusgraph edgestore

---

## Best Practices

1. **Test Restores**: Regularly test backup restoration
2. **Multiple Locations**: Store backups on-site and off-site
3. **Encryption**: Encrypt sensitive backups
4. **Monitoring**: Alert on backup failures
5. **Documentation**: Keep runbooks updated
6. **Retention Policy**: Balance storage costs with recovery needs

---

## Troubleshooting

### Backup Fails

Check:

- Disk space available
- Podman containers running
- Permissions on backup directory

View logs:

tail -f ~/.adal/bash_logs/*.log

### Restore Fails

Common issues:

- Services not stopped properly
- Insufficient disk space
- Permission errors

Solution: Check logs and retry.

### S3 Upload Fails

Verify:

- AWS credentials configured
- S3 bucket exists
- Network connectivity

Test:

aws s3 ls s3://my-janusgraph-backups/

---

**Signature**: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
