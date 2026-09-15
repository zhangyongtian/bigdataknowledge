---
sidebar_position: 9
sidebar_label: Flink 任务维护
---

## savepoint 的使用

### 触发savepoint

```
bin/flink savepoint :jobId [:targetDirectory] -yid :yarnAppId
```

**示例**

```
bin/flink savepoint b5d4b1bf767efa4925d80a19930638d0 -yid application_1701935034030_0003
```

**执行完以后打印如下**

```
Waiting for response...
Savepoint completed. Path: hdfs://bigdatacluster/user/flink/savepoints/savepoint-b5d4b1-07324c8c9c3d
You can resume your program from this savepoint with the run command.
```

### 从savepoint恢复

```
bin/flink run -s :savepointPath [:runArgs]
```

**示例**

```
bin/flink run -s hdfs://bigdatacluster/user/flink/savepoints/savepoint-b5d4b1-07324c8c9c3d [:runArgs]
```

### doris 同步案例

```
./bin/flink run  -t yarn-per-job \
     -Dexecution.checkpointing.interval=10s \
     -Dparallelism.default=1 \
     -c org.apache.doris.flink.tools.cdc.CdcTools \
     lib/flink-doris-connector-1.16-1.5.0.jar \
     mysql-sync-database \
     --database test_db \
     --mysql-conf hostname=xxx \
     --mysql-conf port=3306 \
     --mysql-conf username=xxx \
     --mysql-conf password="xxx" \
     --mysql-conf database-name=xx \
     --including-tables "xx|xx" \
     --sink-conf fenodes=xxx:8030 \
     --sink-conf username=test \
     --sink-conf password=test \
     --sink-conf jdbc-url=jdbc:mysql://xxx:9030 \
     --sink-conf sink.label-prefix=prelabel_5 \
     --table-conf replication_num=3 \
     --mysql-conf server-time-zone=UTC \
     --mysql-conf scan.startup.mode=latest-offset

     --excluding-tables "order_dhl.*|cache_oop|calendar" \


# 如下可以看到，没有用 --mysql-conf scan.startup.mode=latest-offset 他也没有全量读取，说明断点续传成功了。在flinkui的checkpoint也能看到last savepoint的信息。

./bin/flink run -s hdfs://bigdatacluster/user/flink/savepoints/savepoint-b5d4b1-07324c8c9c3d -t yarn-per-job \
     -Dexecution.checkpointing.interval=10s \
     -Dparallelism.default=1 \
     -c org.apache.doris.flink.tools.cdc.CdcTools \
     lib/flink-doris-connector-1.16-1.5.0.jar \
     mysql-sync-database \
     --database test_db \
     --mysql-conf hostname=xxx \
     --mysql-conf port=3306 \
     --mysql-conf username=xxx \
     --mysql-conf password="xxx" \
     --mysql-conf database-name=xx \
     --including-tables "xx|xx" \
     --sink-conf fenodes=xxx:8030 \
     --sink-conf username=test \
     --sink-conf password=test \
     --sink-conf jdbc-url=jdbc:mysql://xxx:9030 \
     --sink-conf sink.label-prefix=prelabel_5 \
     --table-conf replication_num=3 \
     --mysql-conf server-time-zone=UTC

     --excluding-tables "order_dhl.*|cache_oop|calendar" \
```