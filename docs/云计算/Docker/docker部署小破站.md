---
sidebar_position: 13
sidebar_label: docker部署小破站
---
## 官网
> https://v1.legacy-docs.halo.run/getting-started/install/docker

## 安装MySQL
### mysql5.7
```shell
sudo docker run -d \
  --name mysql-container \
  -e MYSQL_ROOT_PASSWORD=root \
  -p 3309:3306 \
  mysql:5.7
```
```sql
create database halodb character set utf8mb4 collate utf8mb4_bin;
```

## 安装halo
```shell
mkdir /root/halo && cd /root/halo
wget https://dl.halo.run/config/application-template.yaml -O ./application.yaml
vim application.yaml
docker pull halohub/halo:1.6.0
docker run -it -d --name halo -p 80:8090 -v /root/halo:/root/.halo --restart=unless-stopped halohub/halo:1.6.0
```

## 主题配置
> https://github.com/qinhua/halo-theme-joe2.0/tree/master?tab=readme-ov-file


## oss配置
> 配置为公共读，然后RAM权限写入。
