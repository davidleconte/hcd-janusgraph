# banking-compliance-evidence-packager

## Purpose
Produce audit-ready evidence from deterministic runs and banking controls.

## Trigger when
- Stakeholders request AML/KYC/UBO evidence.
- Release readiness or audit checkpoint requires proof artifacts.

## Workflow
1. Use deterministic run artifacts:
- status JSON
- notebook report
- manifest/checksums
- service snapshot
2. Map artifacts to business controls:
- AML structuring
- Fraud detection
- Sanctions screening
- UBO discovery
3. Build evidence pack in dated folder under `docs/implementation/audits/`.

## Outputs
- Traceable evidence bundle with command provenance
- Control-to-artifact mapping table

## Guardrails
- Evidence must come from canonical deterministic pathway.
- Include run IDs, timestamps, commit SHA.

