---
sidebar_position: 11
sidebar_label: With子句
---

> https://clickhouse.com/docs/en/sql-reference/statements/select/with

```sql
-- with a as(??)
-- a 是个结果集
with  load_date_temp as (
  select
    str_to_date(video_publish_time, '%Y-%m-%d') video_publish_time
  from
    ods_video_info
  group by
    str_to_date(video_publish_time, '%Y-%m-%d')
  order by
    video_publish_time asc
)
select * from load_date_temp;
 
-- with (??) as a  
-- a 是一个值
with  (
  select
    str_to_date(video_publish_time, '%Y-%m-%d') video_publish_time
  from
    ods_video_info
  group by
    str_to_date(video_publish_time, '%Y-%m-%d')
  order by
    video_publish_time asc limit 1
) as load_date_temp
select
  *
from
  ods_video_info
where
  str_to_date(video_publish_time, '%Y-%m-%d') = load_date_temp limit 10;
```
