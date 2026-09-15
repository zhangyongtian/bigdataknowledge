---
sidebar_position: 5
sidebar_label: 安装ssdb的web客户端
---

## 安装nginx

### 添加Nginx到YUM源

```
sudo rpm -Uvh http://nginx.org/packages/centos/7/noarch/RPMS/nginx-release-centos-7-0.el7.ngx.noarch.rpm
```

### 安装Nginx

```
sudo yum install -y nginx
```

### 启动Nginx

```
sudo systemctl start nginx.service
```

### 设置Nginx开机启动

```
sudo systemctl enable nginx.service
```

## 安装PHP 和php-fpm

> https://www.cnblogs.com/littlehb/p/7072687.html

## docker安装web界面

```shell
https://github.com/zhangyongtian/SSDBAdmin
```