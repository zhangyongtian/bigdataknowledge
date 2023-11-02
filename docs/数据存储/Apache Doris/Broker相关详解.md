---
sidebar_position: 5
sidebar_label: Broker相关详解
---

## 查看

### 查看启动的节点信息
```sql
show broker;
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

## Broker相关日志

- apache_hdfs_broker.log: 所有相关信息。
- apache_hdfs_broker.out: 相关错误信息。