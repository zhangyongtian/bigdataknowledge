---
sidebar_position: 16
id: jindiansql
title: 经典SQL
---

## 知道每日计算上周六到这周五的数据
我有下面的表test表，下面是每日的数据，最后的数值是每日统计值，我想得到每周的数据，这里的每周是上周六到周五，sql怎么写？
```
binningdate,xx,xx,count
2018-12-07,xx,xx,1
2019-01-11,xx,xx,1
2019-01-18,xx,xx,1
2019-03-25,xx,xx,1
```

```sql
SELECT
  DATE_SUB(binningdate, INTERVAL (WEEKDAY(binningdate) + 2) DAY) AS week_start,
  DATE_ADD(binningdate, INTERVAL (4 - WEEKDAY(binningdate)) DAY) AS week_end,
  xx,
  xx,
  SUM(count) AS total_count
FROM test
GROUP BY
  DATE_SUB(binningdate, INTERVAL (WEEKDAY(binningdate) + 2)  DAY),
  DATE_ADD(binningdate, INTERVAL (4 - WEEKDAY(binningdate)) DAY),
  xx,
  xx
ORDER BY week_start desc;
```

## 分组求和不同类型数据不同处理方法
```sql
with every_week as (SELECT DATE_SUB(ship_binningdate, INTERVAL (WEEKDAY(ship_binningdate) + 2) DAY) AS week_start,
                           DATE_ADD(ship_binningdate, INTERVAL (4 - WEEKDAY(ship_binningdate)) DAY) AS week_end,
                           country,
                           shipmentport,
                           ship_deliverystore,
                           shipcontainer_container,
                           SUM(count_container)                                                     AS total_count_container
                    FROM dws_shipment_containers_per_day_temp
                    where (country != '美国' and country != '日本')
                       or shipcontainer_container != 'LCL'
                    GROUP BY DATE_SUB(ship_binningdate, INTERVAL (WEEKDAY(ship_binningdate) + 2) DAY),
                             DATE_ADD(ship_binningdate, INTERVAL (4 - WEEKDAY(ship_binningdate)) DAY),
                             country,
                             shipmentport,
                             ship_deliverystore,
                             shipcontainer_container
                    ORDER BY week_start desc)

select week_start,
       week_end,
       country,
       shipmentport,
       ship_deliverystore,
       CASE
           WHEN SUM(CASE WHEN shipcontainer_container = 'LCL' THEN 1 ELSE 0 END) > 0 THEN
               GROUP_CONCAT(
                       concat(shipcontainer_container, '*', if(total_count_container = 0, '', total_count_container)),
                       ';')
           ELSE
               CAST(SUM(
                       CASE
                           WHEN shipcontainer_container = '20GP'
                               THEN
                               total_count_container * 0.4
                           WHEN shipcontainer_container = '40HQ' OR shipcontainer_container = '45HQ' OR
                                shipcontainer_container = '40GP'
                               THEN
                               total_count_container
                           ELSE
                               0
                           END
                   ) AS CHAR)
           END AS                                                                                          calculated_container_info,
       GROUP_CONCAT(concat(shipcontainer_container, '*', if(total_count_container = 0, '', total_count_container)), ';') initdatainfo
from every_week
group by week_start, week_end, country, shipmentport, ship_deliverystore;
```

## 转换成json
```
select user_id,
       to_json(collect_list(struct_data)) function_summary_jsonarray
from (
         select user_id,
                function_id,
                function_name,
                sum(pv)               sum_pv,
                named_struct('id', function_id,
                             'name',
                             function_name, 'sum_pv',
                             sum(pv)) struct_data
         from app_pc_page_module_summary_init_data
         group by user_id, function_id, function_name
         order by sum_pv desc
         )
group by user_id
```

## 原始数据（解析json数组数据）
[{"deviceId":"Yb1noegphQ4DAJHlXPSOv63J","deviceName":"OPPO Reno7","lastLoginIp":"2409:895a:524d:8488:78b0:6fff:fe56:d122","lastLoginTime":"1712634767"},{"deviceId":"Yb1noegphQ4DAJHlXPSOv63J","deviceName":"OPPO Reno7","lastLoginIp":"2409:8938:7051:b7e:d49c:15ff:fe76:1220","lastLoginTime":"1731378900"}]

WITH exploded_data AS (
  SELECT 
    device.deviceId,
    device.lastLoginIp,
    CAST(device.lastLoginTime AS BIGINT) AS lastLoginTime
  FROM 
    (select * from applydata_bi_ads.ads_risk_user_trace_clean where dates=20250212 and guid='65109e37482f4a6185a3b30020d212b7') tmp
  LATERAL VIEW explode(
    from_json(
      device_info,
      'array<struct<deviceId:string,deviceName:string,lastLoginIp:string,lastLoginTime:string>>'
    )
  ) devices AS device
),
ranked_data AS (
  SELECT 
    deviceId,
    lastLoginIp,
    ROW_NUMBER() OVER (PARTITION BY deviceId ORDER BY lastLoginTime DESC) AS rn
  FROM 
    exploded_data
)
SELECT 
  deviceId,
  lastLoginIp 
FROM 
  ranked_data 
WHERE 
  rn = 1;