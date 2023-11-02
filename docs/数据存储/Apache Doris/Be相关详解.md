---
sidebar_position: 5
sidebar_label: Be相关详解
---

## 查看


### 查看启动的节点信息
```sql
show backends;
```

### 使用Supervisor启停查看

```shell
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
sudo supervisorctl start <process_name> sudo supervisorctl start dorisfe
sudo supervisorctl stop <process_name> sudo supervisorctl stop dorisfe
sudo supervisorctl restart <process_name> sudo supervisorctl restart dorisfe
```

## Be配置相关

> https://doris.apache.org/zh-CN/docs/dev/admin-manual/config/be-config

## Be相关日志

- be.gc.log：当出现内存溢出时会打印相关的GC日志，以帮助你分析内存问题（常看）。
- be.INFO -> be.INFO.log.20230816-143642： be.INFO是最新的be.INFO.log软连接，包括所有的info类型的信息（常看）。
- be.out：包括内存溢出等等错误信息（常看）。
- be.WARNING -> be.WARNING.log.20230423-143218: 警告信息。