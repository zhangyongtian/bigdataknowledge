---
sidebar_position: 3
sidebar_label: 安装Hive
---

## 安装包下载

```
链接：https://pan.baidu.com/s/1Bq09-QgxWubrH9DzfftaAA 
提取码：yyds 
```

## 安装
### 解压

```
tar -zxvf apache-hive-3.1.2-bin.tar.gz -C ../module
```

### 配置环境变量

```
sudo vi /etc/profile.d/my_env.sh

#HIVE_HOME

export HIVE_HOME=/home/bigdata/module/apache-hive-3.1.2-bin
export PATH=$PATH:$HIVE_HOME/bin
```

```
source /etc/profile.d/my_env.sh
```

### 修改hive的配置文件

解决hadoop依赖冲突问题

```
cd /home/bigdata/module/apache-hive-3.1.2-bin/lib
mv  log4j-slf4j-impl-2.10.0.jar log4j-slf4j-impl-2.10.0.jar.bak
```

添加mysql的jar包,

```
[bigdata@master1 lib]$ ll | grep mysql-connector-java-5.1.49.jar
-rw-r--r-- 1 root    root     1006904 Oct 28 18:24 mysql-connector-java-5.1.49.jar
```

创建对应的用户

```
CREATE USER 'hive'@'%'   IDENTIFIED BY 'hive'  WITH MAX_USER_CONNECTIONS 1000;
grant all privileges on *.* to 'hive'@'%' with grant option;
FLUSH PRIVILEGES;
```

修改hive-site.xml

```
vi conf/hive-site.xml
```

```xml
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:mysql://192.168.61.202:3306/hivemetastore?useSSL=false&amp;useUnicode=true&amp;characterEncoding=UTF-8</value>
    </property>
 
    <property>
        <name>javax.jdo.option.ConnectionDriverName</name>
        <value>com.mysql.jdbc.Driver</value>
    </property>
 
    <property>
        <name>javax.jdo.option.ConnectionUserName</name>
        <value>hive</value>
    </property>
 
    <property>
        <name>javax.jdo.option.ConnectionPassword</name>
        <value>hive</value>
    </property>
 
    <property>
        <name>hive.metastore.warehouse.dir</name>
        <value>/user/hive/warehouse</value>
    </property>
 
    <property>
        <name>hive.metastore.schema.verification</name>
        <value>false</value>
    </property>
 
 <!-- H2S运行绑定 port -->
    <property>
    <name>hive.server2.thrift.port</name>
    <value>10000</value>
    </property>

    <!-- H2S运行绑定host -->
    <property>
        <name>hive.server2.thrift.bind.host</name>
        <value>hadoop1</value>
    </property>
 
    <property>
        <name>hive.metastore.event.db.notification.api.auth</name>
        <value>false</value>
    </property>

    <property>
        <!-- 在命令行中，显示当前操作的数据库 -->
        <name>hive.cli.print.current.db</name>
        <value>true</value>
        <description>Whether to include the current database in the Hive prompt.</description>
     </property>

    <property>
        <!-- 在命令行中，显示数据的表头 -->
        <name>hive.cli.print.header</name>
        <value>true</value>
    </property>
   
   <property>
       <!-- 操作小规模数据时，使用本地模式，提高效率 -->
       <name>hive.exec.mode.local.auto</name>
       <value>true</value>
       <description>Let Hive determine whether to run in local mode automatically</description>
    </property>

    <property>
       <name>hive.cli.print.delimiter</name>
       <value>|</value>
    </property>

</configuration>
```

> 备注：当 Hive 的输入数据量非常小时，Hive 通过本地模式在单台机器上处理所有的任务。对于小数据集，执行时间会明显被缩短。当一个job满足如下条件才能真正使。

用本地模式：

- job的输入数据量必须小于参数：hive.exec.mode.local.auto.inputbytes.max(默认128MB)。
- job的map数必须小于参数：hive.exec.mode.local.auto.tasks.max (默认4)。
- job的reduce数必须为0或者1。

初始化元数据

创建数据库
```
mysql -u hive -phive
create database hivemetastore;
exit;
```

初始化
```
schematool -initSchema -dbType mysql -verbose
```

### 修改日志位置

Hive的log默认存放在 /tmp/root 目录下（root为当前用户名）；这个位置可以修改。

```
cp /home/bigdata/module/apache-hive-3.1.2-bin/conf/hive-log4j2.properties.template /home/bigdata/module/apache-hive-3.1.2-bin/conf/hive-log4j2.properties
vi /home/bigdata/module/apache-hive-3.1.2-bin/conf/hive-log4j2.properties
# 添加以下内容：
property.hive.log.dir = /home/bigdata/module/apache-hive-3.1.2-bin/logs
```
### 启动

```

hive

show databases;
create table test(id int,name string);
insert into test values(1,'hive');
select * from test;
```

```
hive> select * from test;
OK
1       hive
Time taken: 0.135 seconds, Fetched: 1 row(s)
```