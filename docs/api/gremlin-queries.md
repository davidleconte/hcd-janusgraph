# Gremlin Query Reference

**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
**Contact:**

## Basic Queries

### Count Vertices

```gremlin
g.V().count()
```

### Find by Property

```gremlin
g.V().has('person', 'name', 'John Doe')
```

### Get Properties

```gremlin
g.V().has('person', 'id', '12345').valueMap()
```

## Traversal Patterns

### Find Neighbors

```gremlin
g.V().has('person', 'id', '12345')
  .both()
  .dedup()
  .valueMap('name', 'type')
```

### Transaction Path

```gremlin
g.V().has('account', 'id', 'A123')
  .repeat(out('transfers_to'))
  .times(3)
  .path()
  .by('id')
```

### Fraud Ring Detection

```gremlin
g.V().has('type', 'account')
  .as('start')
  .repeat(out('transfers_to').simplePath())
  .until(eq('start').or().loops().is(5))
  .path()
```

## Analytics Queries

### Customer 360

```gremlin
g.V().has('person', 'id', personId)
  .project('person', 'accounts', 'transactions', 'companies')
    .by(valueMap())
    .by(out('owns').valueMap().fold())
    .by(out('owns').out('transferred').limit(100).valueMap().fold())
    .by(out('works_for').valueMap().fold())
```

### UBO Discovery

```gremlin
g.V().has('company', 'id', companyId)
  .repeat(in('owns').simplePath())
  .until(hasLabel('person'))
  .path()
  .by('name')
```

## Performance Tips

1. Use indexes: `has()` with indexed properties
2. Limit results: `limit()` on large traversals
3. Use `simplePath()` to avoid cycles
4. Profile queries: `profile()` step
