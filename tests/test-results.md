# HCD + JanusGraph Test Results

**Date**: Tue Jan 27 22:32:16 CET 2026

---


## Test 1: Container Status

❌ **FAILED**: HCD container not running

❌ **FAILED**: JanusGraph container not running


## Test 2: HCD Database

✅ **PASSED**: HCD cluster healthy (UN status)

✅ **PASSED**: JanusGraph keyspace exists


## Test 3: Schema and Data Initialization

Current vertices: 

❌ **FAILED**: Schema initialization failed

	at org.apache.tinkerpop.gremlin.console.Console$_executeInShell_closure17.doCall(Console.groovy:491)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(Unknown Source)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(Unknown Source)
	at java.base/java.lang.reflect.Method.invoke(Unknown Source)
	at org.codehaus.groovy.reflection.CachedMethod.invoke(CachedMethod.java:343)
	at groovy.lang.MetaMethod.doMethodInvoke(MetaMethod.java:328)
	at org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeMethod(ClosureMetaClass.java:279)
	at groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1007)
	at groovy.lang.Closure.call(Closure.java:433)
	at org.codehaus.groovy.runtime.DefaultGroovyMethods.eachWithIndex(DefaultGroovyMethods.java:2310)
	at org.codehaus.groovy.runtime.DefaultGroovyMethods.eachWithIndex(DefaultGroovyMethods.java:2290)
	at org.codehaus.groovy.runtime.DefaultGroovyMethods.eachWithIndex(DefaultGroovyMethods.java:2340)
	at org.codehaus.groovy.runtime.dgm$220.doMethodInvoke(Unknown Source)
	at org.codehaus.groovy.vmplugin.v8.IndyInterface.fromCache(IndyInterface.java:321)
	at org.apache.tinkerpop.gremlin.console.Console.executeInShell(Console.groovy:468)
	at org.codehaus.groovy.vmplugin.v8.IndyInterface.fromCache(IndyInterface.java:321)
	at org.apache.tinkerpop.gremlin.console.Console.<init>(Console.groovy:170)
	at org.codehaus.groovy.vmplugin.v8.IndyInterface.fromCache(IndyInterface.java:321)
	at org.apache.tinkerpop.gremlin.console.Console.main(Console.groovy:574)
❌ **FAILED**: Data loading failed

	at org.apache.tinkerpop.gremlin.console.Console$_executeInShell_closure17.doCall(Console.groovy:491)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(Unknown Source)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(Unknown Source)
	at java.base/java.lang.reflect.Method.invoke(Unknown Source)
	at org.codehaus.groovy.reflection.CachedMethod.invoke(CachedMethod.java:343)
	at groovy.lang.MetaMethod.doMethodInvoke(MetaMethod.java:328)
	at org.codehaus.groovy.runtime.metaclass.ClosureMetaClass.invokeMethod(ClosureMetaClass.java:279)
	at groovy.lang.MetaClassImpl.invokeMethod(MetaClassImpl.java:1007)
	at groovy.lang.Closure.call(Closure.java:433)
	at org.codehaus.groovy.runtime.DefaultGroovyMethods.eachWithIndex(DefaultGroovyMethods.java:2310)
	at org.codehaus.groovy.runtime.DefaultGroovyMethods.eachWithIndex(DefaultGroovyMethods.java:2290)
	at org.codehaus.groovy.runtime.DefaultGroovyMethods.eachWithIndex(DefaultGroovyMethods.java:2340)
	at org.codehaus.groovy.runtime.dgm$220.doMethodInvoke(Unknown Source)
	at org.codehaus.groovy.vmplugin.v8.IndyInterface.fromCache(IndyInterface.java:321)
	at org.apache.tinkerpop.gremlin.console.Console.executeInShell(Console.groovy:468)
	at org.codehaus.groovy.vmplugin.v8.IndyInterface.fromCache(IndyInterface.java:321)
	at org.apache.tinkerpop.gremlin.console.Console.<init>(Console.groovy:170)
	at org.codehaus.groovy.vmplugin.v8.IndyInterface.fromCache(IndyInterface.java:321)
	at org.apache.tinkerpop.gremlin.console.Console.main(Console.groovy:574)

## Test 4: JanusGraph Queries

❌ **FAILED**: Unexpected vertex count:  (expected 11)

❌ **FAILED**: Unexpected edge count:  (expected 19)

❌ **FAILED**: Person vertices not found

❌ **FAILED**: Traversal queries failed


## Test 5: Python Client

❌ **FAILED**: gremlin_python not installed

❌ **FAILED**: Python client tests failed


---

## Summary

- **Passed**: 2
- **Failed**: 10
- **Total**: 12

❌ 10 TEST(S) FAILED
