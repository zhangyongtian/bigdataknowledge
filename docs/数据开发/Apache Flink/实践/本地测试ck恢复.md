---
sidebar_position: 13
sidebar_label: 本地测试ck恢复
---

## 概述

在本地IDEA测试中，使用本地文件存储系统，作为checkpoint的存储系统，将备份数据存储到本地文件中，作业停止后，从本地备份数据启动Flink程序。

主要分为两步：

1）备份数据

2）从备份数据启动

## 备份数据

备份数据的配置，和使用HDFS文件体统类似，只不过路径填写成本地文件系统的路径，注意格式需要是 file:///******/******/，和HDFS文件系统的配置略有不同。文件具体存储的位置，在idea安装路径的根路径下。比如本人IDEA安装在D盘下，checkpoint地址配置为 file:///Users/flink/checkpoints/TestCheckPoint，那么生成的备份点数据在 D:\Users\flink\checkpoints\TestCheckPoint 目录下。

### 生成ck相关代码

```java
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
 
        // 禁用全局任务链
        env.disableOperatorChaining();
 
        String brokers = "********.com:9092,********.com:9092,********.com:9092";
        String sourceTopic = "0000-checkpoint-test-source";
        String resultTopic = "0000-checkpoint-test-result";
        String groupId = "demo";
        
        String checkPointPath = "file:///Users/flink/checkpoints/TestCheckPoint";
 
        StateBackend backend = new EmbeddedRocksDBStateBackend(true);
        env.setStateBackend(backend);
 
        CheckpointConfig conf = env.getCheckpointConfig();
        // 任务流取消和故障应保留检查点
        conf.enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
        conf.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
        conf.setCheckpointInterval(10000);//milliseconds
        conf.setCheckpointTimeout(10 * 60 * 1000);//milliseconds
        conf.setMinPauseBetweenCheckpoints(10 * 1000);//相邻两次checkpoint之间的时间间隔
        conf.setCheckpointStorage(checkPointPath);
```

### 从ck恢复

主要区别，在从备份点数据恢复运行程序。

如果是在yarn集群运行，在启动指令中加入 -s hdfs://ns1/flink/***/chk-*** \ 即可；而在本地运行，需要将备份点路径设置到运行环境中，可以通过启动指令设置，也可以在代码中直接设置。为了展示方便，这里直接在代码中设置。

比如，从备份点  D:\Users\flink\checkpoints\TestCheckPoint\3fc3902734d9316b3d8947508e95eabd\chk-9 恢复运行，需要将备份点设置到环境变量中，部分代码如下：

```java
        Configuration configuration = new Configuration();
        configuration.setString("execution.savepoint.path", "file:///Users/flink/checkpoints/TestCheckPoint/3fc3902734d9316b3d8947508e95eabd/chk-9");
 
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
 
        // 禁用全局任务链
        env.disableOperatorChaining();
 
        String brokers = "kafka-log1.test.xl.com:9092,kafka-log2.test.xl.com:9092,kafka-log3.test.xl.com:9092";
        String sourceTopic = "0000-checkpoint-test-source";
        String resultTopic = "0000-checkpoint-test-result";
        String groupId = "demo";
 
        String checkPointPath = "file:///Users/flink/checkpoints/TestCheckPoint";
 
        StateBackend backend = new EmbeddedRocksDBStateBackend(true);
        env.setStateBackend(backend);
 
        CheckpointConfig conf = env.getCheckpointConfig();
        // 任务流取消和故障应保留检查点
        conf.enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
        conf.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
        conf.setCheckpointInterval(10000);//milliseconds
        conf.setCheckpointTimeout(10 * 60 * 1000);//milliseconds
        conf.setMinPauseBetweenCheckpoints(10 * 1000);//相邻两次checkpoint之间的时间间隔
        conf.setCheckpointStorage(checkPointPath);
```

## 相关文章

> https://blog.csdn.net/Johnson8702/article/details/129275893

