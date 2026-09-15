---
sidebar_position: 5
sidebar_label: Hive相关解释
---

## 基本概念

### Metadata

Metadata即元数据，元数据包含用Hive创建的database、table、表的位置、类型、属性，字段顺序类型等元信息。元数据存储在关系型数据库中。如hive内置的Derby、或者第三方如MySQL等。

### Metastore

Metastore即元数据服务。Metastore服务的作用是管理metadata元数据，对外暴露服务地址，让各种客户端通过连接metastore服务，由metastore再去连接MySQL数据库来存取元数据。有了metastore服务，就可以有多个客户端同时连接，而且这些客户端不需要知道MySQL数据库的用户名和密码，只需要连接metastore 服务即可。

- **内嵌模式:**（Embedded Metastore）是metastore默认部署模式。此种模式下，元数据存储在内置的Derby数据库，并且Derby数据库和metastore服务都嵌入在主HiveServer进程中，当启动HiveServer进程时，Derby和metastore都会启动。 不需要额外起Metastore服务。 但是一次只能支持一个活动用户，适用于测试体验，不适用于生产环境。
- **本地模式:** 本地模式（Local Metastore）下，**Hive Metastore服务与主HiveServer进程在同一进程中运行**，但是存储元数据的数据库在单独的进程中运行，并且可以在单独的主机上。metastore服务将通过JDBC与metastore数据库进行通信。 本地模式采用外部数据库来存储元数据，推荐使用MySQL。 hive根据hive.metastore.uris 参数值来判断，如果为空，则为本地模式。 缺点是每启动一次hive服务，都内置启动了一个metastore。
- **远程模式:**（Remote Metastore）下，**Metastore服务在其自己的单独JVM上运行**，而不在HiveServer的JVM中运行。如果其他进程希望与Metastore服务器通信，则可以使用Thrift Network API进行通信。 在生产环境中，建议用远程模式来配置Hive Metastore。 在这种情况下，其他依赖hive的软件都可以通过Metastore访问hive。由于还可以完全屏蔽数据库层，因此这也带来了更好的可管理性/安全性。 远程模式下，需要配置hive.metastore.uris 参数来指定metastore服务运行的机器ip和端口，并且需要单独手动启动metastore服务。

## 实际操作远程模式

### 配置hive-site.xml

```
vi /home/bigdata/module/apache-hive-3.1.2-bin/conf/hive-site.xml

<!-- 远程模式部署metastore 服务地址,这个是连接远程启动的地址端口信息 -->
    <property>
        <name>hive.metastore.uris</name>
        <value>thrift://master1:9083</value>
    </property>
```

### 启动验证

如下，如果不能够查询了，那么就说明他是在请求远程的metastore服务了。
```
hive

show databases;

hive> show databases;
FAILED: HiveException java.lang.RuntimeException: Unable to instantiate org.apache.hadoop.hive.ql.metadata.SessionHiveMetaStoreClient

```

在远程模式下，必须首先启动Hive metastore服务才可以使用hive。因为metastore服务和hive server是两个单独的进程了。

启动metastore
```
/home/bigdata/module/apache-hive-3.1.2-bin/bin/hive --service metastore

nohup /home/bigdata/module/apache-hive-3.1.2-bin/bin/hive  --service metastore  > /home/bigdata/module/apache-hive-3.1.2-bin/hive.log 2>&1 &

nohup /home/bigdata/module/apache-hive-3.1.2-bin/bin/hive  --service metastore --hiveconf hive.root.logger=DEBUG > /home/bigdata/module/apache-hive-3.1.2-bin/hive.log 2>&1 &
```

启动成功以后会出现RunJar

```
[bigdata@master1 apache-hive-3.1.2-bin]$ jps
27792 Jps
19490 QuorumPeerMain
19811 JournalNode
20612 DFSZKFailoverController
20852 NodeManager
20037 NameNode
21046 JobHistoryServer
27638 RunJar
20743 ResourceManager
20185 DataNode
21146 HttpFSServerWebServer
27468 RunJar
```

验证是否启动成功

```
show databases;

create table test(id int,name string);
insert into test values(1,'hive');
select * from test;
```

## 其他美化配置

```
<property>
    <name>hive.cli.print.header</name>
    <value>true</value>
</property>
<property>
    <name>hive.cli.print.delimiter</name>
    <value>|</value>
</property>

```

启动 hiveserver2

```
nohup /home/bigdata/module/apache-hive-3.1.2-bin/bin/hive --service hiveserver2  > /home/bigdata/module/apache-hive-3.1.2-bin/hive.log 2>&1 &

```

连接hiveserver2

```
beeline -u jdbc:hive2://master1:10000 -n bigdata
```

效果
```
[bigdata@master1 apache-hive-3.1.2-bin]$ beeline -u jdbc:hive2://master1:10000 -n bigdata
Connecting to jdbc:hive2://master1:10000
Connected to: Apache Hive (version 3.1.2)
Driver: Hive JDBC (version 3.1.2)
Transaction isolation: TRANSACTION_REPEATABLE_READ
Beeline version 3.1.2 by Apache Hive
0: jdbc:hive2://master1:10000> show databases;
INFO  : Compiling command(queryId=bigdata_20231028195441_1a57ed81-9da6-4e03-b5db-6c496c4e6635): show databases
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:database_name, type:string, comment:from deserializer)], properties:null)
INFO  : Completed compiling command(queryId=bigdata_20231028195441_1a57ed81-9da6-4e03-b5db-6c496c4e6635); Time taken: 0.656 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=bigdata_20231028195441_1a57ed81-9da6-4e03-b5db-6c496c4e6635): show databases
INFO  : Starting task [Stage-0:DDL] in serial mode
INFO  : Completed executing command(queryId=bigdata_20231028195441_1a57ed81-9da6-4e03-b5db-6c496c4e6635); Time taken: 0.017 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+----------------+
| database_name  |
+----------------+
| default        |
+----------------+
1 row selected (0.908 seconds)
0: jdbc:hive2://master1:10000> select * from test;
INFO  : Compiling command(queryId=bigdata_20231028195506_0a3b9157-d6a2-46a2-89bc-e8f0c7a4651b): select * from test
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Semantic Analysis Completed (retrial = false)
INFO  : Returning Hive schema: Schema(fieldSchemas:[FieldSchema(name:test.id, type:int, comment:null), FieldSchema(name:test.name, type:string, comment:null)], properties:null)
INFO  : Completed compiling command(queryId=bigdata_20231028195506_0a3b9157-d6a2-46a2-89bc-e8f0c7a4651b); Time taken: 1.091 seconds
INFO  : Concurrency mode is disabled, not creating a lock manager
INFO  : Executing command(queryId=bigdata_20231028195506_0a3b9157-d6a2-46a2-89bc-e8f0c7a4651b): select * from test
INFO  : Completed executing command(queryId=bigdata_20231028195506_0a3b9157-d6a2-46a2-89bc-e8f0c7a4651b); Time taken: 0.0 seconds
INFO  : OK
INFO  : Concurrency mode is disabled, not creating a lock manager
+----------+------------+
| test.id  | test.name  |
+----------+------------+
| 1        | hive       |
| 1        | hive       |
+----------+------------+
2 rows selected (1.219 seconds)
```