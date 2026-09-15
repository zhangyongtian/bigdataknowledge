---
sidebar_position: 12
sidebar_label: 结合flink相关配置
---

## flink1.16对应配置

```
#jobmanager.archive.per-user: true
jobmanager.heap.size: 1024m
jobmanager.memory.process.size: 2048m

assloader.check-leaked-classloader: false

taskmanager.memory.managed.fraction: 0.2
taskmanager.memory.network.fraction: 0.1
taskmanager.memory.network.max: 2048m
taskmanager.memory.process.size: 4096m
taskmanager.numberOfTaskSlots: 1
parallelism.default: 1
#sink.shuffle-by-partition.enable: true
slotmanager.number-of-slots.max: 50


#yarn.application-attempts: 5
#yarn.maximum-failed-containers: 100
#yarn.tags: flink


state.backend: ROCKSDB
state.backend.incremental: true
#state.backend.local-recovery: true
state.backend.rocksdb.memory.high-prio-pool-ratio: 0.1
state.backend.rocksdb.memory.managed: true
state.backend.rocksdb.memory.write-buffer-ratio: 0.5
state.backend.rocksdb.predefined-options: DEFAULT
state.backend.rocksdb.timer-service.factory: ROCKSDB
state.savepoints.dir: hdfs:///user/flink/savepoints

#execution.buffer-timeout: 100
execution.checkpointing.externalized-checkpoint-retention: RETAIN_ON_CANCELLATION
state.checkpoints.num-retained: 10
execution.checkpointing.interval: 2min
execution.checkpointing.max-concurrent-checkpoints: 1
execution.checkpointing.min-pause: 1min
execution.checkpointing.mode: EXACTLY_ONCE
#execution.checkpointing.snapshot-compression: false
execution.checkpointing.timeout: 30min
execution.checkpointing.unaligned: false
execution.checkpointing.tolerable-failed-checkpoints: 10
state.checkpoints.dir: hdfs:///user/flink/checkpoints


env.java.opts: -Dfile.encoding=UTF-8

high-availability: zookeeper
high-availability.zookeeper.quorum: node1:2181,node2:2181,node3:2181
high-availability.zookeeper.path.root: /flink
high-availability.storageDir: hdfs:///user/flink/recovery

#jobmanager.execution.failover-strategy: region
#restart-strategy: fixed-delay
#restart-strategy.fixed-delay.attempts: 3
#restart-strategy.fixed-delay.delay: 10 s

jobmanager.archive.fs.dir: hdfs:///user/flink/applicationHistory
historyserver.web.address: 0.0.0.0
historyserver.web.port: 8082
historyserver.web.ssl.enabled: false
historyserver.security.spnego.auth.enabled: false
historyserver.archive.fs.dir: hdfs:///user/flink/applicationHistory
historyserver.cli.fallback: true



#metrics.latency.interval: 60
#metrics.reporter.promgateway.class: org.apache.flink.metrics.prometheus.PrometheusPushGatewayReporter

#metrics.reporter.promgateway.host: node2
#metrics.reporter.promgateway.port: 9091
#metrics.reporter.promgateway.jobName: wms
#metrics.reporter.promgateway.randomJobNameSuffix: true
#metrics.reporter.promgateway.deleteOnShutdown: false
#metrics.reporter.promgateway.interval: 20 SECONDS
```

## 本地集群相关配置

```
taskmanager.host: 192.168.66.10
taskmanager.bind-host: 0.0.0.0
jobmanager.rpc.port: 6123
jobmanager.rpc.address: 192.168.66.10
```