# Terraform Bare Metal Deep Audit

**Date:** 2026-02-19  
**Auditor:** Bob (AI Assistant)  
**Scope:** Terraform bare metal modules and environments  
**Status:** Critical Issues Found

---

## Executive Summary

Deep audit of Terraform bare metal infrastructure revealed **7 critical issues** and **12 warnings** that must be addressed before deployment.

**Severity Breakdown:**
- 🔴 Critical: 7 issues (deployment blockers)
- 🟡 Warning: 12 issues (best practice violations)
- 🟢 Info: 5 observations

**Overall Assessment:** ❌ **NOT READY FOR DEPLOYMENT**

---

## Critical Issues (🔴)

### 1. Missing Resource Dependencies

**File:** `terraform/modules/networking/baremetal.tf`  
**Lines:** 47, 83, 119

**Issue:** References to `null_resource.baremetal_*_os_install` that don't exist in cluster module.

```hcl
# Line 47
depends_on = [null_resource.baremetal_control_plane_os_install]  # ❌ DOES NOT EXIST

# Line 83
depends_on = [null_resource.baremetal_worker_os_install]  # ❌ DOES NOT EXIST

# Line 119
depends_on = [null_resource.baremetal_hcd_os_install]  # ❌ DOES NOT EXIST
```

**Impact:** Terraform will fail with "resource not found" error.

**Fix Required:**
```hcl
# Remove non-existent dependencies or create OS install resources
depends_on = [
  null_resource.baremetal_control_plane,  # Use existing resource
  null_resource.baremetal_worker,
  null_resource.baremetal_hcd
]
```

### 2. Missing Resource Reference

**File:** `terraform/modules/storage/baremetal.tf`  
**Line:** 283

**Issue:** References `null_resource.baremetal_kubernetes_init` from cluster module but not imported.

```hcl
depends_on = [
  null_resource.baremetal_ceph_pools,
  null_resource.baremetal_kubernetes_init  # ❌ NOT IN SCOPE
]
```

**Impact:** Terraform will fail to resolve dependency.

**Fix Required:** Either:
1. Pass as variable from cluster module
2. Use data source to reference
3. Remove dependency if not critical

### 3. Hardcoded Disk Device

**File:** `terraform/modules/storage/baremetal.tf`  
**Lines:** 173-174

**Issue:** Assumes `/dev/sdb` exists on all HCD nodes.

```hcl
parted -s /dev/sdb mklabel gpt
parted -s /dev/sdb mkpart primary xfs 0% 100%
```

**Impact:** Will fail if disk is named differently (sdc, nvme0n1, etc.).

**Fix Required:** Make disk device configurable:
```hcl
variable "baremetal_hcd_data_disk" {
  description = "Data disk device for Ceph OSDs"
  type        = string
  default     = "/dev/sdb"
}
```

### 4. Missing Error Handling

**File:** `terraform/modules/openshift-cluster/baremetal.tf`  
**Lines:** 167-175

**Issue:** No error handling for failed join commands.

```bash
JOIN_CMD=$(ssh ... 'kubeadm token create --print-join-command')
ssh ... "sudo $JOIN_CMD"  # ❌ No error checking
```

**Impact:** Silent failures if join command fails.

**Fix Required:**
```bash
JOIN_CMD=$(ssh ... 'kubeadm token create --print-join-command') || exit 1
ssh ... "sudo $JOIN_CMD" || exit 1
```

### 5. Insecure SSH Configuration

**File:** All modules  
**Multiple locations**

**Issue:** Uses `-o StrictHostKeyChecking=no` which is insecure.

```bash
ssh -o StrictHostKeyChecking=no ...  # ❌ SECURITY RISK
```

**Impact:** Vulnerable to man-in-the-middle attacks.

**Fix Required:**
```bash
# Pre-populate known_hosts or use proper SSH key verification
ssh -o StrictHostKeyChecking=accept-new ...  # Better alternative
```

### 6. No Idempotency

**File:** `terraform/modules/storage/baremetal.tf`  
**Lines:** 173-196

**Issue:** OSD creation not idempotent - will fail on re-run.

```bash
parted -s /dev/sdb mklabel gpt  # ❌ Fails if already partitioned
```

**Impact:** Cannot re-run Terraform apply.

**Fix Required:**
```bash
# Check if already partitioned
if ! parted /dev/sdb print | grep -q "Partition Table: gpt"; then
  parted -s /dev/sdb mklabel gpt
fi
```

### 7. Missing Validation

**File:** All environment configurations  
**Issue:** No validation of required variables.

**Impact:** Deployment will fail with cryptic errors.

**Fix Required:**
```hcl
variable "baremetal_control_plane_hosts" {
  description = "Control plane host configurations"
  type = list(object({
    id           = string
    ipmi_address = string
    ip_address   = string
    hostname     = string
    mac_address  = string
  }))
  
  validation {
    condition     = length(var.baremetal_control_plane_hosts) >= 1
    error_message = "At least one control plane host is required."
  }
  
  validation {
    condition     = length(var.baremetal_control_plane_hosts) % 2 == 1
    error_message = "Control plane hosts must be odd number (1, 3, 5, etc.) for etcd quorum."
  }
}
```

---

## Warnings (🟡)

### 1. Hardcoded Sleep Timers

**Files:** Multiple  
**Issue:** Fixed sleep timers don't account for varying hardware speeds.

```bash
sleep 60   # ❌ May be too short or too long
sleep 300  # ❌ Arbitrary wait time
```

**Recommendation:** Use polling with timeout:
```bash
# Wait for SSH to be available
timeout 300 bash -c 'until ssh -o ConnectTimeout=1 $HOST true; do sleep 5; done'
```

### 2. No Backup/Rollback Strategy

**Issue:** No mechanism to rollback failed deployments.

**Recommendation:** Implement:
- Pre-deployment snapshots
- Rollback procedures
- State backup

### 3. Missing Monitoring Integration

**Issue:** No health checks or monitoring setup.

**Recommendation:** Add:
- Node exporter installation
- Prometheus integration
- Alert configuration

### 4. No Resource Limits

**Issue:** No CPU/memory limits on provisioner commands.

**Recommendation:** Add resource constraints to prevent resource exhaustion.

### 5. Hardcoded Versions

**Files:** Multiple  
**Issue:** Hardcoded software versions.

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml  # ❌ No version pinning
```

**Recommendation:** Pin versions:
```bash
CALICO_VERSION="v3.26.1"
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/${CALICO_VERSION}/manifests/calico.yaml
```

### 6. No Logging

**Issue:** No logging of provisioner actions.

**Recommendation:** Add logging:
```bash
exec > >(tee -a /var/log/terraform-provision.log)
exec 2>&1
```

### 7. Missing Network Validation

**Issue:** No validation that network configuration is correct.

**Recommendation:** Add network connectivity tests.

### 8. No Firewall State Verification

**Issue:** Firewall rules applied but not verified.

**Recommendation:** Add verification:
```bash
firewall-cmd --list-all
```

### 9. Ceph Pool Sizes Not Configurable

**Issue:** Hardcoded PG numbers may not be optimal.

```bash
ceph osd pool create rbd 128 128  # ❌ Hardcoded
```

**Recommendation:** Calculate based on OSD count:
```bash
# PG count = (OSDs * 100) / replica_size
PG_COUNT=$(( (${OSD_COUNT} * 100) / 3 ))
```

### 10. No Disaster Recovery

**Issue:** No backup of Ceph configuration or Kubernetes state.

**Recommendation:** Implement automated backups.

### 11. Missing Security Hardening

**Issue:** No SELinux/AppArmor configuration.

**Recommendation:** Add security hardening steps.

### 12. No Documentation of Manual Steps

**Issue:** Some steps may require manual intervention but not documented.

**Recommendation:** Create runbook for manual steps.

---

## Informational (🟢)

### 1. Terraform State Management

**Observation:** No remote state backend configured.

**Recommendation:** Use S3/Azure Blob/GCS for state storage.

### 2. Module Versioning

**Observation:** Modules not versioned.

**Recommendation:** Use semantic versioning for modules.

### 3. Testing Strategy

**Observation:** No automated testing of Terraform code.

**Recommendation:** Implement:
- `terraform validate`
- `terraform fmt -check`
- `tflint`
- `terratest` for integration tests

### 4. Cost Estimation

**Observation:** No cost estimation before apply.

**Recommendation:** Use `terraform cost` or Infracost.

### 5. Documentation

**Observation:** Limited inline documentation.

**Recommendation:** Add more comments explaining complex logic.

---

## Remediation Plan

### Phase 1: Critical Fixes (Must Do Before Deployment)

**Priority:** P0  
**Estimated Time:** 4 hours

1. **Fix Missing Dependencies** (1 hour)
   - Remove references to non-existent resources
   - Update dependency chains
   - Test with `terraform validate`

2. **Add Error Handling** (1 hour)
   - Add error checking to all SSH commands
   - Implement retry logic
   - Add timeout handling

3. **Make Disk Device Configurable** (30 minutes)
   - Add variable for disk device
   - Update all references
   - Add validation

4. **Implement Idempotency** (1 hour)
   - Add checks before destructive operations
   - Use conditional logic
   - Test re-run scenarios

5. **Add Variable Validation** (30 minutes)
   - Add validation blocks
   - Test with invalid inputs
   - Document requirements

### Phase 2: Security Fixes (Should Do)

**Priority:** P1  
**Estimated Time:** 2 hours

1. **Fix SSH Security** (1 hour)
   - Use proper SSH key verification
   - Pre-populate known_hosts
   - Document SSH setup

2. **Add Security Hardening** (1 hour)
   - Configure SELinux/AppArmor
   - Harden SSH configuration
   - Implement least privilege

### Phase 3: Best Practices (Nice to Have)

**Priority:** P2  
**Estimated Time:** 6 hours

1. **Replace Sleep with Polling** (2 hours)
2. **Add Logging** (1 hour)
3. **Pin Software Versions** (1 hour)
4. **Add Monitoring** (2 hours)

### Phase 4: Testing & Documentation

**Priority:** P2  
**Estimated Time:** 4 hours

1. **Automated Testing** (2 hours)
2. **Documentation** (2 hours)

---

## Testing Checklist

Before deployment, verify:

- [ ] `terraform validate` passes
- [ ] `terraform fmt -check` passes
- [ ] `tflint` passes (if available)
- [ ] All variables have validation
- [ ] All SSH commands have error handling
- [ ] Idempotency tested (apply twice)
- [ ] Rollback procedure documented
- [ ] Manual steps documented
- [ ] Security review completed
- [ ] Cost estimation reviewed

---

## Recommendations

### Immediate Actions

1. **DO NOT DEPLOY** current code to production
2. Fix all critical issues (Phase 1)
3. Test in isolated environment
4. Document all manual steps

### Short-Term Actions

1. Implement security fixes (Phase 2)
2. Add automated testing
3. Create rollback procedures
4. Document disaster recovery

### Long-Term Actions

1. Implement best practices (Phase 3)
2. Add monitoring and alerting
3. Create operational runbooks
4. Establish change management process

---

## Conclusion

The Terraform bare metal modules contain several critical issues that must be fixed before deployment. The code demonstrates good structure and comprehensive coverage, but lacks production-readiness in error handling, security, and idempotency.

**Estimated Remediation Time:** 16 hours total
- Phase 1 (Critical): 4 hours
- Phase 2 (Security): 2 hours
- Phase 3 (Best Practices): 6 hours
- Phase 4 (Testing): 4 hours

**Recommendation:** Complete Phase 1 and Phase 2 before any deployment. Phase 3 and 4 can be done iteratively.

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-19  
**Next Review:** After remediation completion