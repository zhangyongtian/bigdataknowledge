---
sidebar_position: 12
sidebar_label: docker安装nexus
---


## nexus

```shell
mkdir -p /docker/nexus/
chmod 755 /docker/nexus/
sudo docker run -d --restart always --name nexus3 -p 8081:8081 -v /docker/nexus:/var/nexus-data sonatype/nexus3
```

**内容过小时**
```shell
sudo docker run -d --restart=always --name=nexus3 -p8081:8081 --privileged=true -e INSTALL4J_ADD_VM_PARAMS="-Xms512M -Xmx512M -XX:MaxDirectMemorySize=512M" -v /docker/nexus:/var/nexus-data sonatype/nexus3
```

**查看密码**
用户名是admin

```
docker exec -it nexus3 /bin/bash
cat /nexus-data/admin.password
```