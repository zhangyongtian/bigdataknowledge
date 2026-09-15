---
sidebar_position: 17
sidebar_label: docker安装halo镜像
---

## 安装MySQL
```shell
sudo docker run -d \
  --name mysql-container \
  -e MYSQL_ROOT_PASSWORD=root \
  -p 3309:3306 \
  mysql:5.7
```

## 上传文件(这里有一些静态图片)
```shell
cd /root
tar -zxvf halo.gz
```

## 导入数据文件到mysql
**创建对应的数据库**
```sql
create database halodb character set utf8mb4 collate utf8mb4_bin;
```
```
halodb_2024-04-14_161253.sql
```

## 修改halo数据库配置文件
```shell
cd /root/halo
vim application.yaml
```

## 加载启动halo容器

### 加载镜像
```shell
docker load < /root/halo.tar
```

### 修改标签
```shell
docker tag 88bc94d xuxueli/halo:1.0.0
```
### 启动容器
```shell
docker run -it -d --name halo -p 90:8090 -v /root/halo:/root/.halo --restart=unless-stopped xuxueli/halo:1.0.0
```

## 直接使用阿里云镜像
```
docker run -it -d --name haloaliyun -p 92:8090 -v /root/halo:/root/.halo --restart=unless-stopped registry.cn-hangzhou.aliyuncs.com/haloblog/halo
```
