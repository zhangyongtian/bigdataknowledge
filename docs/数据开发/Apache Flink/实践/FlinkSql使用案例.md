---
sidebar_position: 20
sidebar_label: FlinkSql使用案例
---

```sql

SET jobmanager.memory.process.size=8192000000;
SET table.exec.state.ttl=5616000000;

create table t_tb_worktime (
                worktime_id  varchar(64)  ,
                proctime AS PROCTIME(),
            PRIMARY KEY (worktime_id) NOT ENFORCED
            )WITH (
                'connector' = 'mysql-cdc',
                'hostname' = '',
                'port' = '3306',
                'username' = '',
                'password' = '',
                'database-name' = '',
                'table-name' = '' ,
                'server-id' = '20035-20040' ,
                'connect.timeout' = '180s',
                'scan.startup.mode' = 'initial',
                'scan.incremental.snapshot.chunk.size' = '16192',
                'jdbc.properties.useSSL' = 'false'
                );


create table users (
                id     int ,
            PRIMARY KEY (id) NOT ENFORCED
            )WITH (
                'connector' = 'mysql-cdc',
                'hostname' = '',
                'port' = '3306',
                'username' = '',
                'password' = '',
                'database-name' = '',
                'table-name' = '' ,
                'connect.timeout' = '180s',
                'server-id' = '20040-20045' ,
                'scan.startup.mode' = 'initial',
                'scan.incremental.snapshot.chunk.size' = '16192',
                'jdbc.properties.useSSL' = 'false'
                );



create table t_tb_task (
                    task_id             varchar(64)     ,
            PRIMARY KEY (task_id) NOT ENFORCED
            )WITH (
                'connector' = 'mysql-cdc',
                'hostname' = '',
                'port' = '',
                'username' = '',
                'password' = '',
                'database-name' = '',
                'table-name' = '' ,
                'connect.timeout' = '180s',
                'server-id' = '20045-20050' ,
                'scan.startup.mode' = 'initial',
                'scan.incremental.snapshot.chunk.size' = '16192',
                'jdbc.properties.useSSL' = 'false'
                );



create table t_tb_budget_project (
                    project_no                   varchar(100)            ,
                PRIMARY KEY (project_no) NOT ENFORCED
            )WITH (
                'connector' = 'jdbc',
                'url' = '/test?autoReconnect=true&useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai&useSSL=false',
                'username' = '',
                'password' = '',
                'table-name' = ''
                );





create table tb_workhours_detail(
                worktimeid   varchar(500) ,
                PRIMARY KEY (worktimeid) NOT ENFORCED
            )WITH (
                'connector' = 'jdbc',
                'url'='/test?autoReconnect=true&useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai&useSSL=false',
                'table-name' = '',
                'username' = '',
                'password' = ''
            );



CREATE VIEW  workhours  AS
SELECT
*
FROM t_tb_worktime
where date_format(`date`,'yyyy-MM-01') >= date_format(TIMESTAMPADD(month,-1,current_timestamp),'yyyy-MM-01');




INSERT INTO  tb_workhours_detail
SELECT
  IFNULL(t.budget_project_name, p.budget_project_name) AS ttitle,
  u.name,
  now() as into_time
FROM
  workhours  wt
  INNER JOIN t_tb_task t ON t.task_id = wt.task_id
  INNER JOIN users u ON wt.user_id = u.uid
  LEFT JOIN t_tb_budget_project FOR SYSTEM_TIME AS OF wt.proctime  AS p ON p.budget_project_name = t.budget_project_name
WHERE
  t.is_archived = 0 ;
```