---
sidebar_position: 3
sidebar_label: Fe相关详解
---

## 查看

### 查看启动的节点信息
```sql
show frontends;
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

## Fe配置相关

> https://doris.apache.org/zh-CN/docs/dev/admin-manual/config/fe-config

## Fe元数据原理

> https://doris.apache.org/zh-CN/community/design/metadata-design

## Fe相关日志

- fe.audit.log：FE 审计日志（常看）。

作用: 根据be宕机的时候查看对应的日志来过滤出query_id，查看具体执行的SQL相关信息，用来场景复现。

```log
2021-02-16 00:00:08,992 [query] |Client=127.0.0.1:59253|User=root|Db=|State=EOF|ErrorCode=0|ErrorMessage=|Time=133|ScanBytes=0|ScanRows=0|ReturnRows=3|StmtId=15843271|QueryId=30d550dff51a40ee-b277863a4772d637|IsQuery=true|feIp=127.0.0.1|Stmt=SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'bigdata_data_result'UNION SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'bigdata_data_result'UNION SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA = 'bigdata_data_result'|CpuTimeMS=19|SqlHash=267ddf0847c5d49161ccf1cfed6d31fa|peakMemoryBytes=2859160|SqlDigest=|TraceId=|FuzzyVariables=
```

- fe.gc.log： 当出现内存溢出时会打印相关的GC日志，以帮助你分析内存问题（常看）。
- fe.log：所有fe相关的日志信息（常看）。
- fe.warn.log：fe.log过滤出的warn信息（常看）。
- fe.out：相关的异常信息。


