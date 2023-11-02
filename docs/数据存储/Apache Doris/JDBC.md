---
sidebar_position: 9
sidebar_label: JDBC
---

## 基本使用

### 创建

```sql

CREATE CATALOG demo PROPERTIES (
    "type"="jdbc",
    "user"="demo",
    "password"="demo",
    "jdbc_url" = "jdbc:mysql://127.0.0.1:3306/demo?useUnicode=true&characterEncoding=utf-8&connectTimeout=5000000&useSSL=false",
    "driver_url" = "mysql-connector-java-8.0.25.jar",
    "driver_class" = "com.mysql.cj.jdbc.Driver"
);
```

### 查看catalog

```sql
show catalogs;

show create catalog demo;
```

### 切换catalogs

```sql
switch demo;
```

### 删除catalogs

```sql
drop catalog demo;
```

## 官网直达

> https://doris.apache.org/zh-CN/docs/1.2/lakehouse/multi-catalog/jdbc?_highlight=jdbc#%E4%BD%BF%E7%94%A8%E9%99%90%E5%88%B6