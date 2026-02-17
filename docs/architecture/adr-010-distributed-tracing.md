# ADR-010: OpenTelemetry and Jaeger for Distributed Tracing

**Status**: Accepted
**Date**: 2026-01-24
**Deciders**: Operations Team, Development Team
**Technical Story**: Performance Optimization P3-001

## Context

As the HCD JanusGraph system grew in complexity with multiple components (JanusGraph, HCD/Cassandra, monitoring services, caching layers), debugging performance issues and understanding request flows became increasingly difficult. We needed a distributed tracing solution to:

- Track requests across multiple services
- Identify performance bottlenecks
- Understand service dependencies
- Debug complex query execution paths
- Monitor system health in production

### Problem Statement

How do we implement comprehensive distributed tracing that provides visibility into request flows across all system components while maintaining low overhead and enabling effective troubleshooting?

### Constraints

- Must support Python, Java (JanusGraph), and Cassandra
- Should integrate with existing monitoring (Prometheus/Grafana)
- Must have minimal performance impact (<5% overhead)
- Should support both synchronous and asynchronous operations
- Must be open-source and vendor-neutral

### Assumptions

- Tracing data will be stored separately from application data
- Sampling may be needed for high-volume production systems
- Team has capacity to learn new tracing tools
- Infrastructure can support additional services

## Decision Drivers

- **Observability**: Complete visibility into request flows
- **Performance**: Minimal overhead on application performance
- **Standards**: Industry-standard, vendor-neutral solution
- **Integration**: Works with existing monitoring stack
- **Flexibility**: Supports multiple languages and frameworks
- **Community**: Active development and strong community support

## Considered Options

### Option 1: Zipkin

**Pros:**

- Mature, battle-tested solution
- Good UI for trace visualization
- Wide language support
- Simple architecture

**Cons:**

- Less active development than alternatives
- Limited advanced features
- Smaller community
- Less flexible data model

### Option 2: OpenTelemetry + Jaeger

**Pros:**

- Industry standard (CNCF project)
- Vendor-neutral, future-proof
- Excellent language support (Python, Java, Go, etc.)
- Rich ecosystem and integrations
- Active development and community
- Flexible backend (Jaeger, Zipkin, custom)
- Built-in metrics and logs correlation
- Automatic instrumentation available

**Cons:**

- More complex setup (two components)
- Steeper learning curve
- Requires more infrastructure

### Option 3: AWS X-Ray / Cloud-Specific Solutions

**Pros:**

- Managed service (no infrastructure)
- Deep cloud integration
- Automatic instrumentation for AWS services

**Cons:**

- Vendor lock-in
- Limited to cloud provider
- Higher cost at scale
- Less flexibility
- Not suitable for on-premises deployment

### Option 4: Custom Logging Solution

**Pros:**

- Full control
- No additional dependencies
- Simple to understand

**Cons:**

- Significant development effort
- Lacks standard features
- Difficult to correlate across services
- No visualization tools
- Maintenance burden

## Decision

**We will use OpenTelemetry for instrumentation with Jaeger as the tracing backend.**

### Architecture

1. **OpenTelemetry SDK**: Instrument Python and Java applications
2. **OpenTelemetry Collector**: Receive, process, and export traces
3. **Jaeger**: Store and visualize traces
4. **Integration**: Connect with Prometheus for metrics correlation

### Implementation Details

- **Python**: OpenTelemetry Python SDK with automatic instrumentation
- **JanusGraph**: OpenTelemetry Java agent
- **Sampling**: Adaptive sampling (100% in dev, 10% in production)
- **Storage**: Jaeger with Cassandra backend for production
- **Retention**: 7 days for traces, 30 days for aggregated metrics

### Rationale

OpenTelemetry + Jaeger provides the best combination of:

- **Standards Compliance**: CNCF-backed, vendor-neutral standard
- **Flexibility**: Works with multiple backends and languages
- **Future-Proof**: Industry moving toward OpenTelemetry
- **Rich Features**: Spans, metrics, logs, context propagation
- **Community**: Large, active community and ecosystem
- **Integration**: Works seamlessly with Prometheus and Grafana

## Consequences

### Positive

- **Complete Visibility**: End-to-end request tracing across all services
- **Performance Insights**: Identify slow queries and bottlenecks quickly
- **Debugging**: Faster root cause analysis for production issues
- **Service Dependencies**: Clear visualization of service interactions
- **Metrics Correlation**: Link traces with metrics and logs
- **Standards-Based**: Easy to switch backends if needed
- **Automatic Instrumentation**: Minimal code changes required
- **Production Ready**: Battle-tested in large-scale systems

### Negative

- **Infrastructure Overhead**: Additional services to deploy and maintain
- **Storage Requirements**: Traces consume significant storage
- **Learning Curve**: Team needs training on OpenTelemetry concepts
- **Performance Impact**: ~2-3% overhead (acceptable)
- **Complexity**: More moving parts in the system

### Neutral

- **Sampling Required**: May miss some traces in high-volume scenarios
- **Data Retention**: Need to balance storage costs vs. retention period
- **Configuration**: Requires tuning for optimal performance

## Implementation

### Required Changes

1. **Infrastructure** (tracing compose overlay):
   - Jaeger all-in-one container
   - OpenTelemetry Collector
   - Cassandra backend for production

2. **Python Instrumentation** (`src/python/utils/tracing.py`):
   - OpenTelemetry SDK initialization
   - Automatic instrumentation for requests, gremlin
   - Custom span decorators
   - Context propagation

3. **Configuration** (`config/tracing/`):
   - OpenTelemetry Collector configuration
   - Sampling strategies
   - Exporter settings

4. **Monitoring Integration**:
   - Grafana dashboards for traces
   - Prometheus metrics from traces
   - Alert rules for trace anomalies

5. **Documentation**:
   - Tracing setup guide
   - Best practices for adding custom spans
   - Troubleshooting guide

### Migration Path

**Phase 1: Development Environment**

1. Deploy Jaeger and OpenTelemetry Collector
2. Instrument Python client library
3. Add custom spans to critical paths
4. Validate trace collection and visualization

**Phase 2: Staging Environment**

1. Deploy production-grade Jaeger with Cassandra
2. Configure sampling strategies
3. Performance testing with tracing enabled
4. Team training on trace analysis

**Phase 3: Production Rollout**

1. Deploy with conservative sampling (1%)
2. Monitor performance impact
3. Gradually increase sampling rate
4. Enable for all services

**Phase 4: Optimization**

1. Fine-tune sampling strategies
2. Add custom instrumentation where needed
3. Create dashboards and alerts
4. Document common trace patterns

### Rollback Strategy

If tracing causes issues:

1. Disable OpenTelemetry instrumentation via environment variable
2. Stop Jaeger and Collector services
3. Remove tracing configuration
4. Revert to log-based debugging
5. Analyze root cause before re-enabling

## Compliance

- [x] Security review completed (no sensitive data in traces)
- [x] Performance impact assessed (2-3% overhead acceptable)
- [x] Documentation updated
- [x] Team trained on OpenTelemetry concepts
- [x] Infrastructure capacity verified

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
- [CNCF OpenTelemetry](https://www.cncf.io/projects/opentelemetry/)
- [Distributed Tracing Best Practices](https://opentelemetry.io/docs/concepts/signals/traces/)

## Notes

### Trace Structure

Each trace consists of:

- **Trace ID**: Unique identifier for the entire request
- **Span ID**: Unique identifier for each operation
- **Parent Span ID**: Links spans in a hierarchy
- **Attributes**: Key-value pairs with context
- **Events**: Timestamped log messages
- **Status**: Success, error, or unset

### Key Metrics to Track

1. **Latency**: P50, P95, P99 response times
2. **Error Rate**: Percentage of failed requests
3. **Throughput**: Requests per second
4. **Service Dependencies**: Call graphs and dependencies
5. **Resource Usage**: CPU, memory per operation

### Best Practices

1. **Span Naming**: Use consistent, descriptive names
2. **Attributes**: Add relevant context (user ID, query type, etc.)
3. **Sampling**: Use adaptive sampling in production
4. **Sensitive Data**: Never include passwords or PII in traces
5. **Performance**: Keep span creation lightweight
6. **Context Propagation**: Always propagate trace context

### Future Enhancements

- **Logs Integration**: Correlate logs with traces using trace IDs
- **Metrics Integration**: Link Prometheus metrics with traces
- **Custom Exporters**: Export to multiple backends
- **Advanced Sampling**: ML-based adaptive sampling
- **Trace Analysis**: Automated anomaly detection
- **Service Mesh**: Integration with Istio/Linkerd
