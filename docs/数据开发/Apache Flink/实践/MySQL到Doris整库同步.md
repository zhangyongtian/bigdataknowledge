---
sidebar_position: 8
sidebar_label: MySQL到Doris整库同步
---

## Flink 相关

### 环境

- Doris 2.0.3
- flink-doris-connector-1.16-1.5.0.jar
- flink-1.16.0
- flink-sql-connector-mysql-cdc-2.4.2.jar (有时区影响)

> flink-sql-connector-mysql-cdc-2.2.1.jar 这个cdc版本没有时区影响的问题。

### 配置文件

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
execution.checkpointing.interval: 5min
execution.checkpointing.max-concurrent-checkpoints: 1
execution.checkpointing.min-pause: 2min
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

## Doris 相关

### Flink 执行命令

```
./bin/flink run  -t yarn-per-job \
     -Dexecution.checkpointing.interval=10s \
     -Dparallelism.default=1 \
     -c org.apache.doris.flink.tools.cdc.CdcTools \
     flink-doris-connector-1.16-1.5.0.jar \
     mysql-sync-database \
     --database test_db \
     --mysql-conf hostname=xx \
     --mysql-conf port=xx \
     --mysql-conf username=xx \
     --mysql-conf password="xx" \
     --mysql-conf database-name=xx \
     --sink-conf fenodes=xx:8030 \
     --sink-conf username=test \
     --sink-conf password=test \
     --sink-conf jdbc-url=jdbc:mysql://xx:9030 \
     --sink-conf sink.label-prefix=prelabel \
     --table-conf replication_num=3 \
     --mysql-conf server-time-zone=UTC
```

> Asia/Shanghai

### 如果字段有汉字

```
set global enable_unicode_name_support = true;
```

## Flink Doris Connector 下载地址

> https://repository.apache.org/content/repositories/orgapachedoris-1039/org/apache/doris/
