// JanusGraph initialization script - Direct graph creation
// Opens graph via JanusGraphFactory and binds to global scope
// Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team

// Open graph directly using JanusGraphFactory (bypassing JanusGraphManager)
graph = org.janusgraph.core.JanusGraphFactory.open('/opt/janusgraph/conf/janusgraph-hcd.properties')
g = graph.traversal()

// Return globals map with bindings
def globals = [:]
globals << [graph : graph]
globals << [g : g]

// Add lifecycle hook for clean shutdown
globals << [hook : [
    onStartUp: { ctx ->
        ctx.logger.info("JanusGraph HCD graph initialized successfully")
    },
    onShutDown: { ctx ->
        ctx.logger.info("JanusGraph shutting down - closing graph...")
        try {
            if (graph != null && graph.isOpen()) {
                graph.close()
                ctx.logger.info("Graph closed successfully")
            }
        } catch (Exception e) {
            ctx.logger.error("Error closing graph: " + e.getMessage())
        }
    }
] as LifeCycleHook]

globals
