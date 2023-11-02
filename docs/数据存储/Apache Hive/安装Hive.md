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
cd lib
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

```
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:mysql://ip:3306/hivemetastore?useSSL=false&amp;useUnicode=true&amp;characterEncoding=UTF-8</value>
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
        <value>master1</value>
    </property>
 
    <property>
        <name>hive.metastore.event.db.notification.api.auth</name>
        <value>false</value>
    </property>
   
</configuration>
```

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