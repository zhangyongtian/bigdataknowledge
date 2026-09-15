---
sidebar_position: 6
sidebar_label: 配置Spark引擎
---

## 安装包下载

```
链接：https://pan.baidu.com/s/1iM3nZ5UEyISabpAYh2NgDw 
提取码：yyds 
--来自百度网盘超级会员V5的分享
```

## 安装步骤

解压安装包

```
tar -zxvf spark-3.0.0-bin-hadoop3.2.tgz -C ../module/
tar -zxvf spark-3.0.0-bin-without-hadoop.tgz -C ../module
```

修改环境变量
```
sudo vim /etc/profile.d/my_env.sh

# SPARK_HOME
export SPARK_HOME=/home/bigdata/module/spark-3.0.0-bin-hadoop3.2
export PATH=$PATH:$SPARK_HOME/bin

source /etc/profile.d/my_env.sh
```

在hive中创建spark配置文件

```
vi /home/bigdata/module/apache-hive-3.1.2-bin/conf/spark-defaults.conf

spark.master                            yarn
spark.eventLog.enabled           true
spark.eventLog.dir                   hdfs://bigdatacluster/spark-history
spark.executor.memory           2g
spark.driver.memory	 4g
```

在hdfs上面创建spark-history文件夹

```
hadoop fs -mkdir /spark-history
```

上传Spark纯净版jar包到HDFS

```
hadoop fs -mkdir /spark-jars
hadoop fs -put /home/bigdata/module/spark-3.0.0-bin-without-hadoop/jars/* /spark-jars
```

修改hive-site.xml文件

```
vi /home/bigdata/module/apache-hive-3.1.2-bin/conf/hive-site.xml
```

```
<!--Spark依赖位置（注意：端口号8020必须和namenode的端口号一致）-->
<property>
    <name>spark.yarn.jars</name>
    <value>hdfs://bigdatacluster/spark-jars/*</value>
</property>
  
<!--Hive执行引擎-->
<property>
    <name>hive.execution.engine</name>
    <value>spark</value>
</property>
```

测试spark是否成功

```
hive
create table student(id int, name string);
insert into table student values(1,'abc');
select * from student;
```

```
Query Hive on Spark job[0] stages: [0, 1]
Spark job[0] status = RUNNING
--------------------------------------------------------------------------------------
          STAGES   ATTEMPT        STATUS  TOTAL  COMPLETED  RUNNING  PENDING  FAILED  
--------------------------------------------------------------------------------------
Stage-0 ........         0      FINISHED      1          1        0        0       0  
Stage-1 ........         0      FINISHED      1          1        0        0       0  
--------------------------------------------------------------------------------------
STAGES: 02/02    [==========================>>] 100%  ELAPSED TIME: 4.21 s     
--------------------------------------------------------------------------------------
Spark job[0] finished successfully in 4.21 second(s)
Loading data to table default.student
```

## 不同计算引擎的切换。

```
set hive.execution.engine=spark;
set hive.execution.engine=mr;
```