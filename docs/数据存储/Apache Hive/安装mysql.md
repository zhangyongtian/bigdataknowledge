---
sidebar_position: 2
sidebar_label: 安装MySQL
---

## 安装前准备

```
【超级会员V5】通过百度网盘分享的文件：mysql
链接:https://pan.baidu.com/s/1VOAylDAn2o9uCkaU-vHS_w 
提取码:4dgd
复制这段内容打开「百度网盘APP 即可获取」
```

创建用户

```
useradd bigdata
passwd bigdata
```

创建目录

```
mkdir /home/bigdata/module
mkdir /home/bigdata/software
mkdir /home/bigdata/shell
chown bigdata:bigdata /home/bigdata/module
chown bigdata:bigdata /home/bigdata/software
chown bigdata:bigdata /home/bigdata/shell
```

卸载原有的MySQL

```
rpm -qa | grep -i mysql

rpm -ev mysql-community-libs-5.7.27-1.el6.x86_64 --nodeps

删除相关文件

find / -name mysql

rm -rf /var/lib/mysql
rm -rf /var/lib/mysql/mysql
rm -rf /etc/logrotate.d/mysql
rm -rf /usr/share/mysql
rm -rf /usr/bin/mysql
rm -rf /usr/lib64/mysql

再次查询

rpm -qa | grep -i mysql
```

## rpm安装

### 安装
```
[root@prod-vm software]# ll
total 184536
-rw-r--r-- 1 root root    277604 Oct 28 17:14 01_mysql-community-common-5.7.16-1.el7.x86_64.rpm
-rw-r--r-- 1 root root   2237116 Oct 28 17:14 02_mysql-community-libs-5.7.16-1.el7.x86_64.rpm
-rw-r--r-- 1 root root   2112700 Oct 28 17:14 03_mysql-community-libs-compat-5.7.16-1.el7.x86_64.rpm
-rw-r--r-- 1 root root  25034716 Oct 28 17:14 04_mysql-community-client-5.7.16-1.el7.x86_64.rpm
-rw-r--r-- 1 root root 159295840 Oct 28 17:14 05_mysql-community-server-5.7.16-1.el7.x86_64.rpm
```

```
sudo rpm  -ivh  *.rpm --nodeps --force
```

查看mysql安装的位置

```
[root@prod-vm software]# whereis mysql
mysql: /usr/bin/mysql /usr/lib64/mysql /usr/share/mysql /usr/share/man/man1/mysql.1.gz
```

查看mysql的运行状态

```
systemctl status mysqld
```

目录授权,这里是存储数据的地方，在/etc/my.cnf中配置。如果权限不够，那么会启动不起来。

```
sudo chmod 777 -R /var/lib/mysql
```

修改配置，添加最大的连接数
```
vi /etc/my.cnf
validate_password_policy=0
validate_password_length=1
max_connections = 2000
```

初始化mysql

```
sudo yum install libaio

mysqld --initialize --console
```

查看Mysql的密码。运行时出错，也可以查看这个文件。

```
cat /var/log/mysqld.log

2023-10-28T09:28:08.553828Z 1 [Note] A temporary password is generated for root@localhost: /fhl:;!3;y_G
```

启动mysql
```
systemctl stop mysqld
systemctl start mysqld
systemctl enable mysqld
systemctl status mysqld
```

登录mysql

```
mysql -u root -p/fhl:;!3;y_G
```

远程登录授权

```
ALTER USER 'root'@'localhost' IDENTIFIED BY '123456';
SHOW databases;	
USE mysql;
UPDATE user SET host = "%" WHERE user='root';
SELECT host, user, authentication_string, plugin FROM user;
FLUSH privileges;

```

创建用户
```
CREATE USER 'hive'@'%'   IDENTIFIED BY 'hive'  WITH MAX_USER_CONNECTIONS 1000;
grant all privileges on *.* to 'hive'@'%' with grant option;
FLUSH PRIVILEGES;
```

### 卸载mysql

```
rpm -qa|grep mysql

sudo yum remove $(rpm -qa|grep mysql)

rm -rf /var/lib/mysql/*
```


## 常见报错
下面的报错是因为存储目录没有写入权限。

```
2023-10-28T10:08:53.327713Z 0 [ERROR] InnoDB: The innodb_system data file 'ibdata1' must be writable
2023-10-28T10:08:53.327725Z 0 [ERROR] InnoDB: The innodb_system data file 'ibdata1' must be writable
```
