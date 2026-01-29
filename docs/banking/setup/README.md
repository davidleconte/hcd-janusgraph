# Banking Module Setup Documentation

This directory contains setup and configuration documentation for the banking compliance and fraud detection modules.

## Contents

### Setup Guides

**00_OVERVIEW.md**
- Banking module architecture overview
- Component relationships
- Integration points with JanusGraph and OpenSearch

**01_AML_PHASE1_SETUP.md**
- Anti-Money Laundering (AML) module setup
- Phase 1 implementation guide
- Data loading and schema configuration

## Related Documentation

### Main Banking Documentation
- **User Guide:** [`../USER_GUIDE.md`](../USER_GUIDE.md)
- **API Reference:** [`../API_REFERENCE.md`](../API_REFERENCE.md)
- **Architecture:** [`../ARCHITECTURE.md`](../ARCHITECTURE.md)

### Implementation Documentation
- **Phase 5:** [`../PHASE5_VECTOR_AI_FOUNDATION.md`](../PHASE5_VECTOR_AI_FOUNDATION.md)
- **Phase 8:** [`../PHASE8_COMPLETE.md`](../PHASE8_COMPLETE.md)
- **Production Deployment:** [`../PRODUCTION_DEPLOYMENT_GUIDE.md`](../PRODUCTION_DEPLOYMENT_GUIDE.md)

### Code Modules
- **AML Detection:** [`../../aml/`](../../aml/)
- **Fraud Detection:** [`../../fraud/`](../../fraud/)
- **Data Generators:** [`../../data_generators/`](../../data_generators/)

## Quick Start

1. **Read Overview:** Start with `00_OVERVIEW.md` for architecture understanding
2. **Follow Setup:** Use `01_AML_PHASE1_SETUP.md` for initial configuration
3. **Load Data:** Follow data loading procedures in setup guides
4. **Verify:** Run verification queries to confirm setup

## Prerequisites

- JanusGraph with HCD backend running
- OpenSearch 3.4.0+ configured
- Python 3.11+ environment
- Required dependencies installed (see [`../../requirements.txt`](../../requirements.txt))

## Support

For issues or questions:
- Review troubleshooting sections in setup guides
- Check main project [`TROUBLESHOOTING.md`](../../TROUBLESHOOTING.md)
- Consult [`../USER_GUIDE.md`](../USER_GUIDE.md) for common scenarios

---

**Last Updated:** 2026-01-28  
**Status:** Active Documentation