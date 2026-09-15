---
sidebar_position: 3
sidebar_label: binglog详解
---

## 简单了解binlog

binlog是一个二进制格式的文件，**用于记录用户对数据库更新的sql语句信息，但是不包括select和show这类操作**，因为这类操作对数据本身并没有修改。然后，若操作本身并没有导致数据库发生变化，那么该操作也会写入二进制日志。

默认情况下，binlog日志是二进制格式的，**不能使用查看文本工具的命令（比如，cat，vi等）查看，而使用mysqlbinlog解析查看**。

一般来说开启二进制日志大概会有1%的性能损耗，其他介绍可以查看 [官网文档介绍](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html)


## binlog作用

### binlog日志有两个最重要的使用场景

- mysql主从复制

MySQL Replication在Master端开启binlog，Master把它的二进制日志传递给slaves来达到master-slave数据一致的目的。
可以参考：[《mysql 主从复制 基于binlog 简单实践》](https://www.codehui.net/info/64.html)

- 数据恢复

通过使用mysqlbinlog程序处理二进制日志文件，来使恢复数据。

### binlog日志包括两类文件

- 二进制日志索引文件（文件名后缀为.index）用于记录所有的二进制文件

- 二进制日志文件（文件名后缀为.00000*）记录数据库所有的DDL和DML(除了数据查询语句select)语句事件。在mysql 主从复制中有见到。

## 开启binlog日志

### 修改配置文件

可以通过如下命令查看mysql读取的配置文件，顺序排前的优先
```
root@ba586179fe4b:/# mysql --help|grep 'my.cnf'
                      order of preference, my.cnf, $MYSQL_TCP_PORT,
/etc/my.cnf /etc/mysql/my.cnf /usr/local/mysql/etc/my.cnf ~/.my.cnf
```

编辑配置文件，然后重启mysql

```
root@ba586179fe4b:/# vi /etc/my.cnf

[mysqld]
# 开启二进制日志功能，mysql-bin 是日志的基本名或前缀名
log-bin=mysql-bin
```

### 登录数据库 mysql -u root -p123456

查看binlog日志是否开启，log_bin为ON表示开启binlog日志

```
mysql> show variables like 'log_%';
+---------------------------------+-------+
| Variable_name                   | Value |
+---------------------------------+-------+
| log_bin                         | ON    |
| log_bin_trust_function_creators | OFF   |
| log_error                       |       |
| log_output                      | FILE  |
| log_queries_not_using_indexes   | OFF   |
| log_slave_updates               | OFF   |
| log_slow_queries                | OFF   |
| log_warnings                    | 1     |
+---------------------------------+-------+
8 rows in set (0.00 sec)
```

## binlog日志常用操作命令

### 查看所有binlog日志列表
```
mysql> show master logs;
+------------------+-----------+
| Log_name         | File_size |
+------------------+-----------+
| mysql-bin.000001 |      8184 |
| mysql-bin.000002 |       107 |
+------------------+-----------+
2 rows in set (0.00 sec)
```
### 查看master状态，即最后(最新)一个binlog日志的编号名称，及其最后一个操作事件pos结束点(Position)值

```
mysql> show master status;
+------------------+----------+--------------+------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB |
+------------------+----------+--------------+------------------+
| mysql-bin.000002 |      107 |              |                  |
+------------------+----------+--------------+------------------+
1 row in set (0.00 sec)
```

### 刷新log日志，自此刻开始产生一个新编号的binlog日志文件

```
mysql> flush logs;
Query OK, 0 rows affected (0.01 sec)
```

### 重置(清空)所有binlog日志

```
mysql> reset master;
Query OK, 0 rows affected (0.01 sec)
```

## 查看binlog日志内容，常用有两种方式

### 使用mysqlbinlog自带查看命令

> 注: binlog是二进制文件，**普通文件查看器cat more vi等都无法打开**，必须使用自带的 mysqlbinlog 命令查看，binlog日志与数据库文件在同目录中(我的环境配置安装是选择在/usr/local/mysql/data中) 在MySQL5.5以下版本使用mysqlbinlog命令时如果报错，就加上"--no-defaults"选项

mysql数据存放在/var/lib/mysql目录，通过mysqlbinlog打开日志文件

```
/usr/local/mysql/bin/mysqlbinlog /var/lib/mysql/mysql-bin.000001
```

截取最后一次执行的日志片段

```
# at 1778
#190221  6:58:51 server id 1  end_log_pos 1899  Query   thread_id=1 exec_time=0 error_code=0
SET TIMESTAMP=1550732331/*!*/;
INSERT INTO `proxy` (`id`, `name`) VALUES ('6', 'code')
/*!*/;
# at 1899
#190221  6:58:51 server id 1  end_log_pos 1926  Xid = 45
```

#### 主要参数解释：
- server id 1 ： 数据库主机的服务号；
- end_log_pos 1899： sql结束时的pos节点
- thread_id=1： 线程号

### 使用show binlog events命令查看

上面这种办法读取出binlog日志的全文内容较多，不容易分辨查看pos点信息，这里介绍一种更为方便的查询命令：

> mysql> show binlog events [IN 'log_name'] [FROM pos] [LIMIT [offset,] row_count];

选项解析：

- IN 'log_name' 指定要查询的binlog文件名(不指定就是第一个binlog文件)
- FROM pos 指定从哪个pos起始点开始查起(不指定就是从整个文件首个pos点开始算)
- LIMIT [offset,] 偏移量(不指定就是0)
- row_count 查询总条数(不指定就是所有行)

```
mysql> show master logs;
+------------------+-----------+
| Log_name         | File_size |
+------------------+-----------+
| mysql-bin.000001 |       326 |
+------------------+-----------+
1 row in set (0.00 sec)

mysql> show binlog events in 'mysql-bin.000001'\G;
*************************** 1. row ***************************
   Log_name: mysql-bin.000001
        Pos: 4
 Event_type: Format_desc
  Server_id: 1
End_log_pos: 107
       Info: Server ver: 5.5.62-log, Binlog ver: 4
*************************** 2. row ***************************
   Log_name: mysql-bin.000001
        Pos: 107
 Event_type: Query
  Server_id: 1
End_log_pos: 178
       Info: BEGIN
*************************** 3. row ***************************
   Log_name: mysql-bin.000001
        Pos: 178
 Event_type: Query
  Server_id: 1
End_log_pos: 299
       Info: use `codehui`; INSERT INTO `proxy` (`id`, `name`) VALUES ('6', 'code')
*************************** 4. row ***************************
   Log_name: mysql-bin.000001
        Pos: 299
 Event_type: Xid
  Server_id: 1
End_log_pos: 326
       Info: COMMIT /* xid=61 */
4 rows in set (0.00 sec)

ERROR: 
No query specified

mysql>
```

上面这条语句可以将**指定的binlog日志文件，分成有效事件行的方式返回**，并可使用limit指定pos点的起始偏移，查询条数。

- 查询第一个(最早)的binlog日志：

```
show binlog events;
```

- 指定查询 mysql-bin.000021 这个文件：

```
show binlog events in 'mysql-bin.000021';
```

- 指定查询 mysql-bin.000021 这个文件，从pos点:8224开始查起：

```
show binlog events in 'mysql-bin.000021' from 8224;
```

- 指定查询 mysql-bin.000021 这个文件，从pos点:8224开始查起，查询10条

```
show binlog events in 'mysql-bin.000021' from 8224 limit 10;
```

- 指定查询 mysql-bin.000021 这个文件，从pos点:8224开始查起，偏移2行，查询10条

```
show binlog events in 'mysql-bin.000021' from 8224 limit 2,10;
```

## 通过binlog数据恢复

### 数据准备
这个数据测试比较麻烦，我们先模拟个场景

> codehui数据库会在**每天凌晨1点使用计划任务进行一次备份**，这里先手动执行一下备份任务。然后就有了数据库**截止今天凌晨1点的数据库备份文件**。早上9点和中午12点数据库都执行了增删改操作，**然后下午18点直接删掉了codehui数据库**，场景大概就是这样，下面进行测试数据的恢复。

先在codehui数据库插入测试数据

```
mysql> use codehui;
Database changed
mysql> CREATE TABLE `test` (
    -> `id` int(11) NOT NULL AUTO_INCREMENT,\
    -> `name` varchar(255) CHARACTER SET utf8 DEFAULT NULL,
    -> PRIMARY KEY (`id`)
    -> ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
Query OK, 0 rows affected (0.10 sec)

mysql> desc test;
+-------+--------------+------+-----+---------+----------------+
| Field | Type         | Null | Key | Default | Extra          |
+-------+--------------+------+-----+---------+----------------+
| id    | int(11)      | NO   | PRI | NULL    | auto_increment |
| name  | varchar(255) | YES  |     | NULL    |                |
+-------+--------------+------+-----+---------+----------------+
2 rows in set (0.00 sec)

mysql> INSERT INTO `test` (`id`, `name`) VALUES ('1', 'code');
Query OK, 1 row affected (0.00 sec)

mysql> INSERT INTO `test` (`id`, `name`) VALUES ('2', 'php');
Query OK, 1 row affected (0.04 sec)

mysql> select * from test;
+----+------+
| id | name |
+----+------+
|  1 | code |
|  2 | php  |
+----+------+
2 rows in set (0.00 sec)

mysql>
```

### 数据备份
备份数据库方法mysqldump，详细请参见 [mysql 数据备份](https://www.codehui.net/info/67.html)

```
root@ba586179fe4b:/# /usr/local/mysql/bin/mysqldump -uroot -p123456 -B -F -R -x --master-data=2 codehui|gzip > /opt/backup/codehui.bak.sql.gz
root@ba586179fe4b:/# ls /opt/backup
codehui.bak.sql.gz
```
mysqldump备份方法参数说明：

- -B：指定数据库
- -F：刷新日志
- -R：备份存储过程等
- -x：锁表

--master-data：在备份语句里添加CHANGE MASTER语句以及binlog文件及位置点信息

由于上面在全备份的时候使用了-F选项，那么当**数据备份操作刚开始的时候系统就会自动刷新log**，这样就会自动产生一个新的binlog日志，这个新的binlog日志就会用来记录备份之后的数据库"增删改"操作

```
mysql> show master status;
+------------------+----------+--------------+------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB |
+------------------+----------+--------------+------------------+
| mysql-bin.000003 |      107 |              |                  |
+------------------+----------+--------------+------------------+
1 row in set (0.00 sec)
```

也就是说， mysql-bin.000003 是用来记录凌晨1点之后对数据库的所有"增删改"操作。

### 执行数据模拟操作

**早上9点对数据库进行"增"操作，新插入3条数据**

```
mysql> INSERT INTO `test` (`id`, `name`) VALUES ('3', 'java'),('4','golang'),('5','shell');
Query OK, 3 rows affected (0.02 sec)
Records: 3  Duplicates: 0  Warnings: 0

mysql> select * from test;
+----+--------+
| id | name   |
+----+--------+
|  1 | code   |
|  2 | php    |
|  3 | java   |
|  4 | golang |
|  5 | shell  |
+----+--------+
5 rows in set (0.00 sec)
```

**中午12点对数据库进行"改"操作，修改1条数据**

```
mysql> UPDATE `test` SET `name`='mysql' WHERE `id`='1';
Query OK, 1 row affected (0.02 sec)
Rows matched: 1  Changed: 1  Warnings: 0

mysql> select * from test;
+----+--------+
| id | name   |
+----+--------+
|  1 | mysql  |
|  2 | php    |
|  3 | java   |
|  4 | golang |
|  5 | shell  |
+----+--------+
5 rows in set (0.00 sec)
```

**下午18点，某程序员因心情不爽准备跑路，删掉了数据库codehui**

```
mysql> drop database codehui;
Query OK, 3 rows affected (0.14 sec)
```

### 全量恢复数据
**此刻先别慌，他忘记了我们还有大招，就是binlog日志。**

先仔细查看最后一个binlog日志，并记录下关键的pos点，到底是哪个pos点的操作导致了数据库的破坏(通常在最后几步)；

我们先备份一下最后一个binlog日志

```
root@ba586179fe4b:/# cp -v /var/lib/mysql/mysql-bin.000003 /opt/backup/
'/var/lib/mysql/mysql-bin.000003' -> '/opt/backup/mysql-bin.000003'
```

此时执行一次刷新日志索引操作，重新开始新的binlog日志记录文件。**理论说 mysql-bin.000003 这个文件不会再有后续写入了(便于我们分析原因及查找pos点)**，以后所有数据库操作都会写入到下一个日志文件；

```
mysql> flush logs;
Query OK, 0 rows affected (0.03 sec)

mysql> show master status;
+------------------+----------+--------------+------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB |
+------------------+----------+--------------+------------------+
| mysql-bin.000004 |      107 |              |                  |
+------------------+----------+--------------+------------------+
1 row in set (0.00 sec)
```

**读取日志 分析问题，读取日志方法上面已经说到，这里使用第二种**

```
mysql> show binlog events in 'mysql-bin.000003';
+------------------+------+-------------+-----------+-------------+----------------------------------------------------------------------------------------------------+
| Log_name         | Pos  | Event_type  | Server_id | End_log_pos | Info                                                                                               |
+------------------+------+-------------+-----------+-------------+----------------------------------------------------------------------------------------------------+
| mysql-bin.000003 |    4 | Format_desc |         1 |         107 | Server ver: 5.5.62-log, Binlog ver: 4                                                              |
| mysql-bin.000003 |  107 | Query       |         1 |         178 | BEGIN                                                                                              |
| mysql-bin.000003 |  178 | Query       |         1 |         327 | use `codehui`; INSERT INTO `test` (`id`, `name`) VALUES ('3', 'java'),('4','golang'),('5','shell') |
| mysql-bin.000003 |  327 | Xid         |         1 |         354 | COMMIT /* xid=184 */                                                                               |
| mysql-bin.000003 |  354 | Query       |         1 |         425 | BEGIN                                                                                              |
| mysql-bin.000003 |  425 | Query       |         1 |         544 | use `codehui`; INSERT INTO `proxy` (`id`, `name`) VALUES ('1', 'my')                               |
| mysql-bin.000003 |  544 | Xid         |         1 |         571 | COMMIT /* xid=188 */                                                                               |
| mysql-bin.000003 |  571 | Query       |         1 |         642 | BEGIN                                                                                              |
| mysql-bin.000003 |  642 | Query       |         1 |         784 | use `codehui`; UPDATE `proxy` SET `name`='mysql' WHERE (`id`='1') AND (`name`='my') LIMIT 1        |
| mysql-bin.000003 |  784 | Xid         |         1 |         811 | COMMIT /* xid=190 */                                                                               |
| mysql-bin.000003 |  811 | Query       |         1 |         882 | BEGIN                                                                                              |
| mysql-bin.000003 |  882 | Query       |         1 |         995 | use `codehui`; UPDATE `test` SET `name`='mysql' WHERE `id`='1'                                     |
| mysql-bin.000003 |  995 | Xid         |         1 |        1022 | COMMIT /* xid=192 */                                                                               |
| mysql-bin.000003 | 1022 | Query       |         1 |        1109 | drop database codehui                                                                              |
| mysql-bin.000003 | 1109 | Rotate      |         1 |        1152 | mysql-bin.000004;pos=4                                                                             |
+------------------+------+-------------+-----------+-------------+----------------------------------------------------------------------------------------------------+
15 rows in set (0.00 sec)
```

到这里是不很兴奋，**看到了备份之后执行的所有的"增删改"记录**。
通过分析，造成数据库破坏的pos点区间是**介于 1022--1109 之间**（这是按照日志区间的pos节点算的），只要恢复到1109前就可。

恢复凌晨1点的备份数据，也就是刚才手动备份的数据

```
root@ba586179fe4b:/# cd /opt/backup/
root@ba586179fe4b:/opt/backup# ls
codehui.bak.sql.gz  mysql-bin.000003
root@ba586179fe4b:/opt/backup# gzip -d codehui.bak.sql.gz
root@ba586179fe4b:/opt/backup# mysql -uroot -p123456 -v < codehui.bak.sql
```

这样就**恢复了截至当日凌晨(1:00)前的备份数据都恢复了**，之后的数据通过**binlog日志mysql-bin.000003进行恢复**。

```
mysql> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| codehui            |
| mysql              |
| performance_schema |
+--------------------+
4 rows in set (0.00 sec)

mysql> use codehui;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> show tables;
+-------------------+
| Tables_in_codehui |
+-------------------+
| demo              |
| proxy             |
| test              |
+-------------------+
3 rows in set (0.00 sec)

mysql> select * from test;
+----+------+
| id | name |
+----+------+
|  1 | code |
|  2 | php  |
+----+------+
2 rows in set (0.00 sec)
```

### 恢复增量binlog数据
**从binlog日志恢复数据**

恢复命令的语法格式：

> mysqlbinlog mysql-bin.0000xx | mysql -u用户名 -p密码 数据库名

**常用参数选项解释**

- --start-position=875 起始pos点
- --stop-position=954 结束pos点
- --start-datetime="2016-9-25 22:01:08" 起始时间点
- --stop-datetime="2019-9-25 22:09:46" 结束时间点
- --database=codehui 指定只恢复codehui数据库(一台主机上往往有多个数据库，只限本地log日志)

**不常用选项**

- -u --user=name 连接到远程主机的用户名
- -p --password[=name] 连接到远程主机的密码
- -h --host=name 从远程主机上获取binlog日志
- --read-from-remote-server 从某个MySQL服务器上读取binlog日志

> 小结：实际是**将读出的binlog日志内容，通过管道符传递给mysql命令**。这些命令、文件尽量写成绝对路径；

### 完全恢复

小结：实际是将读出的binlog日志内容，通过管道符传递给mysql命令。这些命令、文件尽量写成绝对路径；

温馨提示：在恢复全备数据之前必须将该binlog文件移出，否则恢复过程中，会继续写入语句到binlog，最终导致增量恢复数据部分变得比较混乱！

```
root@ba586179fe4b:/opt/backup# mysqlbinlog /opt/backup/mysql-bin.000003 > /opt/backup/000003.sql
root@ba586179fe4b:/opt/backup# vi /opt/backup/000003.sql #删除里面的drop语句
# 删掉drop语句前后的# at 到 /*！*/之间的内容

root@ba586179fe4b:/opt/backup# mysql -uroot -p123456 -v < /opt/backup/000003.sql
```

查看数据，已经恢复了

```
mysql> use codehui;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> select * from test;
+----+--------+
| id | name   |
+----+--------+
|  1 | mysql  |
|  2 | php    |
|  3 | java   |
|  4 | golang |
|  5 | shell  |
+----+--------+
5 rows in set (0.00 sec)

# 然后删除codehui数据库，测试第二种方法
mysql> drop database codehui;
Query OK, 3 rows affected (0.06 sec)

# 重新导入凌晨1点的备份数据，
root@ba586179fe4b:/opt/backup# mysql -uroot -p123456 -v < codehui.bak.sql
```

### 部分恢复

指定pos结束点恢复(部分恢复)

--stop-position=571 pos结束节点（按照事务区间算，是571）

> 此pos结束节点介于"test"表原始数据与更新"name='mysql'"之前的数据，这样就可以恢复到 更改"name='mysql'"之前的数据了。

操作如下

```
root@ba586179fe4b:/opt/backup# mysqlbinlog --stop-position=571 --database=codehui /var/lib/mysql/mysql-bin.000003 | mysql -uroot -p123456 -v codehui

mysql> use codehui;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> select * from test;
+----+--------+
| id | name   |
+----+--------+
|  1 | code   |
|  2 | php    |
|  3 | java   |
|  4 | golang |
|  5 | shell  |
+----+--------+
5 rows in set (0.00 sec)
```

### 指定pos点区间恢复(部分恢复)

> 更新 "name='mysql'" 这条数据，日志区间是Pos[882] --> End_log_pos[995]，按事务区间是：Pos[811] --> End_log_pos[1022]

单独恢复 "name='mysql'" 这步操作，可这样,按照binlog日志区间单独恢复：

```
root@ba586179fe4b:/opt/backup# mysqlbinlog --start-position=882 --stop-position=995 --database=codehui /var/lib/mysql/mysql-bin.000003 | mysql -uroot -p123456 -v codehui
```

#### 按照事务区间单独恢复

```
root@ba586179fe4b:/opt/backup# mysqlbinlog --start-position=811 --stop-position=1022 --database=codehui /var/lib/mysql/mysql-bin.000003 | mysql -uroot -p123456 -v codehui
```

如果要恢复区间内的多条日志，按事务区间恢复就可以。

```
mysql> use codehui;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> select * from test;
+----+--------+
| id | name   |
+----+--------+
|  1 | mysql  |
|  2 | php    |
|  3 | java   |
|  4 | golang |
|  5 | shell  |
+----+--------+
5 rows in set (0.00 sec)
```

查看数据库恢复了"name='mysql'"，这样就恢复了删除前的数据状态了。

### 指定时间区间恢复(部分恢复)

> 除了用pos点的办法进行恢复，也可以通过指定时间区间进行恢复，按时间恢复需要用mysqlbinlog命令读取binlog日志内容，找时间节点。

```

# 起始时间点
--start-datetime="YYYY-MM-DD H:I:S"
# 结束时间点
--stop-datetime ="YYYY-MM-DD H:I:S"

# 用法举例
mysqlbinlog --start-position=811 --start-datetime="YYYY-MM-DD H:I:S" --stop-datetime="YYYY-MM-DD H:I:S" --database=codehui /var/lib/mysql/mysql-bin.000003 | mysql -uroot -p123456 -v codehui
```

## 看是否开启了gtid

```
SHOW VARIABLES LIKE 'gtid_mode';
```

## 查看binlog的刷盘数据量
```
show variables like 'sync%';
```


## 对应的文章
> https://www.jianshu.com/p/e1cacf8cceff