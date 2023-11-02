---
sidebar_position: 15
id: faq
title: FAQ
---

## Linux问题

### ssh-copy-id 配置免密以后无效的问题

Authentication refused: bad ownership or modes for directory

参考博客
> https://blog.csdn.net/weixin_42559574/article/details/129943394

> https://blog.csdn.net/andyguan01_2/article/details/100658905

查看安全相关的日志

```shell
sudo cat /var/log/secure
```

发现是免密文件的权限问题引起的，权限的文件是有一定的规定的不是越高越好，这个也算是linux的自我保护机制吧

```shell
chmod 600 /home/bigdata/.ssh/authorized_keys
chown bigdata:bigdata /home/bigdata/.ssh/authorized_keys
ls -l /home/bigdata/.ssh/authorized_keys
chmod 700 /home/bigdata/.ssh
chown bigdata:bigdata /home/bigdata/.ssh
ls -ld /home/bigdata/.ssh
chmod 755 /home/bigdata
chown bigdata:bigdata /home/bigdata
ls -ld /home/bigdata
chmod 600 /home/bigdata/.ssh/id_rsa
ls -l /home/bigdata/.ssh/id_rsa
```

## 大数据算法

### Uber H3算法

> https://h3geo.org/docs/highlights/aggregation

**相关博客**

> https://blog.csdn.net/allenlu2008/article/details/103029132

## 民间资料
### 大数据
#### 大数据指标体系

> https://zhuanlan.zhihu.com/p/448733810

#### Flume

> https://segmentfault.com/a/1190000040917955

#### Upsert-kafka-demo

> https://github.com/fsk119/flink-pageviews-demo

> https://www.ververica.com/blog/flink-sql-secrets-mastering-the-art-of-changelog-event-out-of-orderness

> https://cloud.tencent.com/developer/article/1806609

### 后端
#### 技术选型
> https://segmentfault.com/a/1190000023467005?utm_source=sf-similar-article

#### JAVA知识体系
> https://pdai.tech/

#### PostgreSQL

> https://segmentfault.com/a/1190000044048598?utm_source=sf-similar-article

### 机器学习

> https://www.showmeai.tech/tutorials/34?articleId=185

### 零度解说

> https://www.freedidi.com/

### 跨境电商

> https://blog.naibabiji.com/

### 爬虫谷歌驱动安装

> https://cuiqingcai.com/33043.html
> https://googlechromelabs.github.io/chrome-for-testing/
> https://www.cnblogs.com/laoluoits/p/17710501.html

