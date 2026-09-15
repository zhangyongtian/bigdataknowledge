---
sidebar_position: 11
sidebar_label: docker安装Ansible可视化
---


## Ansible

### 官网
> https://github.com/semaphoreui/semaphore

### 启动容器

```shell
docker run -d -p 3000:3000 --name semaphore \
  -e SEMAPHORE_DB_DIALECT=bolt \
  -e SEMAPHORE_ADMIN=admin \
  -e SEMAPHORE_ADMIN_PASSWORD=changeme \
  -e SEMAPHORE_ADMIN_NAME=Admin \
  -e SEMAPHORE_ADMIN_EMAIL=admin@localhost \
  -d semaphoreui/semaphore:latest
```