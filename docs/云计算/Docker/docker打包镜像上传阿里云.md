---
sidebar_position: 16
sidebar_label: docker打包镜像上传阿里云
---


## 上传镜像到阿里云

```shell
docker commit -a "halo" -m "myhalo" fc43df5  halo:v1 
#username后面就是你的阿里云账号，然后 输入密码时 是你 刚才申请镜像仓库设置的密码
sudo docker login --username=xx registry.cn-hangzhou.aliyuncs.com
#给镜像打标签，格式必须为 “registry.cn-hangzhou.aliyuncs.com” 这个开头, “yl_hmbb” 换成你自己的 阿里云命名空间名称 即可，后面的 “yl-nginx:v1” 镜像名称和版本号 自行取名即可
docker tag 88bc94d0 registry.cn-hangzhou.aliyuncs.com/haloblog/halo:v1
#推送本地镜像上去
docker push registry.cn-hangzhou.aliyuncs.com/haloblog/halo:v1

```

## 保存镜像
```shell
docker save 88bc94 > /home/halo.tar
```

## 加载镜像
```shell
docker load < /home/halo.tar
```

## 修改标签
```shell
docker tag 999c20aee5da xuxueli/xxl-job-admin:2.2.0
```
