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
rpm  -ivh  *.rpm --nodeps --force
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
chmod 777 -R /var/lib/mysql
```

修改配置，添加最大的连接数
```
vi /etc/my.cnf

max_connections = 2000

vi  /usr/lib/systemd/system/mysqld.service
LimitNOFILE=65535
```

初始化mysql

```
sudo yum install libaio

mysqld --initialize --console
```


启动mysql
```

systemctl start mysqld
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