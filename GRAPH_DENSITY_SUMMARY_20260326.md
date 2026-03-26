# Graph Density Summary - 2026-03-26

**Created At:** 2026-03-26 20:14:59 CET  
**Date:** 2026-03-26  
**Scope:** Live JanusGraph/HCD graph density and storage-profile snapshot

---

## Source counts (live)

### JanusGraph (graph-level)
- Vertices: `6,285`
- Edges: `11,266`
- Vertex properties: `169,236`
- Edge properties: `12,421`
- Total properties: `181,657`

### HCD/Cassandra (`janusgraph` keyspace)
- Tables: `9`
  - `edgestore`
  - `edgestore_lock_`
  - `graphindex`
  - `graphindex_lock_`
  - `janusgraph_ids`
  - `system_properties`
  - `system_properties_lock_`
  - `systemlog`
  - `txlog`

Core storage row counts:
- `edgestore_rows`: `206,432`
- `graphindex_rows`: `386`
- `janusgraph_ids_rows`: `23`

---

## Derived graph density/profile metrics

Using:
- V = 6,285
- E = 11,266
- VP = 169,236
- EP = 12,421
- TP = 181,657
- Elements = V + E = 17,551

### Connectivity
- Edges per vertex: `E / V = 1.79`

### Property richness
- Avg vertex properties per vertex: `VP / V = 26.93`
- Avg edge properties per edge: `EP / E = 1.10`
- Avg total properties per graph element: `TP / (V+E) = 10.35`

### Storage-level directional ratios (HCD internals)
- `edgestore_rows / edges = 18.32`
- `edgestore_rows / vertices = 32.85`
- `edgestore_rows / elements = 11.76`

> Note: Cassandra row counts are storage internals and are not 1:1 business entity counts; use as operational density indicators.
