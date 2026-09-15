---
sidebar_position: 4
sidebar_label: Spark 集成实践
---

## 1. 版本 & Jar 准备

| 组件 | 推荐版本 | 说明 |
|---|---|---|
| Spark | **Spark 3.4.x / 3.5.x**（建议单独装，HDP 3.3.2 自带 Spark 3.1.x 用 Paimon 0.7.x 也行） | Spark 2.x 不支持 Paimon |
| Paimon Spark | **paimon-spark-3.4-0.9.0.jar**（跟 Spark 大版本强绑定，3.5 就用 `paimon-spark-3.5-*`） | 错版本直接 NoSuchMethodError |
| Paimon Hive Bundle | **paimon-hive-3.1-0.9.0.jar** | 跟 HDP 里的 Hive 3.1 对应 |

### 1.1 Jar 放到 Spark jars（所有 Spark 节点都放）

```bash
cp paimon-spark-3.4-0.9.0.jar   $SPARK_HOME/jars/
cp paimon-hive-3.1-0.9.0.jar    $SPARK_HOME/jars/
```

### 1.2 启动 Spark SQL / PySpark

```bash
# 推荐用 spark-sql 交互（HDP 环境要确保加载 hive-site.xml）
spark-sql \
  --master yarn \
  --deploy-mode client \
  --conf spark.sql.catalog.paimon=org.apache.paimon.spark.SparkCatalog \
  --conf spark.sql.catalog.paimon.warehouse=hdfs:///user/hive/warehouse/paimon \
  --conf spark.sql.catalog.paimon.metastore=hive \
  --conf spark.sql.catalog.paimon.uri=thrift://master1:9083
```

---

## 2. Spark 读 Paimon

### 2.1 最新快照读（普通批查询）

```sql
-- 用 SparkCatalog 的方式读
SELECT dt, order_status, count(*) AS cnt, sum(total_amount) AS gmv
FROM paimon.ods.ods_order_info
WHERE dt BETWEEN '2026-09-01' AND '2026-09-05'
GROUP BY dt, order_status
ORDER BY dt;
```

### 2.2 DataFrame 读

```python
# PySpark 示例
df = spark.read \
    .format("paimon") \
    .option("path", "hdfs:///user/hive/warehouse/paimon/ods.db/ods_order_info") \
    .load()
df.filter("dt = '2026-09-05'").show(20, False)
```

### 2.3 时间旅行 / 快照 / Tag 读

```sql
-- 按快照 ID
SELECT * FROM paimon.ods.ods_order_info VERSION AS OF 128;

-- 按时间戳
SELECT * FROM paimon.ods.ods_order_info TIMESTAMP AS OF '2026-09-05 09:00:00';

-- 按 Tag（月底结算神器）
SELECT * FROM paimon.ods.ods_order_info
  OPTIONS('tag' = 'daily_20260904');
```

---

## 3. Spark 写 Paimon（主要用于：离线补数 / T+1 ETL / 手动修复）

### 3.1 Insert Into / Insert Overwrite

```sql
-- 1）T+1 离线聚合直接进 Paimon DWS（如果 DWS 是主键表就自动做 Upsert）
INSERT INTO paimon.dws.dws_user_day_gmv
SELECT
  user_id,
  dt,
  sum(total_amount)  AS gmv,
  count(*)           AS order_cnt
FROM paimon.dwd.dwd_order_info
WHERE dt = '2026-09-04'
GROUP BY user_id, dt;

-- 2）按分区重跑（修复某天数据）
INSERT OVERWRITE paimon.dws.dws_user_day_gmv
PARTITION (dt = '2026-09-04')
SELECT user_id, sum(total_amount), count(*)
FROM paimon.dwd.dwd_order_info
WHERE dt = '2026-09-04'
GROUP BY user_id;
```

### 3.2 按主键 Delete / Update（合规擦除 / 数据修正场景）

```sql
-- 按主键删除（GDPR 擦除个人信息，不用像 Hive 一样整分区 overwrite）
DELETE FROM paimon.ods.ods_user_info WHERE id = 8888888;

-- 按条件 Update（比如把所有 2026-08 之前订单的测试状态修正）
UPDATE paimon.ods.ods_order_info
SET   order_status = -1, total_amount = 0
WHERE order_status = 99 AND create_time < TIMESTAMP '2026-08-01 00:00:00';

-- Merge Into（SCD2 维表、一次性补 CDC 数据非常好用）
MERGE INTO paimon.dwd.dwd_user t
USING (SELECT * FROM temp_user_patch) s
   ON t.id = s.id
 WHEN MATCHED THEN UPDATE SET t.phone = s.phone, t.user_level = s.user_level
 WHEN NOT MATCHED THEN INSERT (id, name, phone, user_level, create_time, update_time)
                       VALUES (s.id, s.name, s.phone, s.user_level, s.create_time, s.update_time);
```

---

## 4. Spark + Paimon 配合 Flink 的最佳实践

| 角色 | 用 Flink | 用 Spark |
|---|---|---|
| ODS 入湖 | ✅ Flink CDC 长期流式作业（实时追 Binlog）| ⭕ 偶尔全量回刷某张表 |
| DWD 清洗 | ✅ 分钟级流式清洗（实时给下游）| ✅ 凌晨 T+1 重跑补历史，对账 |
| DWS 汇总 | ✅ 流式聚合（T+0 分钟级）| ✅ 多日大区间聚合 / 复杂多 Join 跑批 |
| ADS 报表 | ⭕ 流式写 StarRocks/Doris 外表 | ✅ 离线报表直接出 Paimon ADS，BI 查 Paimon |
| 小文件治理 / Compaction | ✅ 流式 Checkpoint 自动做 | ✅ 每天凌晨用 Spark 对冷分区做大分区强制 `CALL sys.compact` |
| 快照 Tag 打标 | ⭕ 可以 | ✅ 跟跑批调度一起做，流程清晰 |

---

## 5. Spark 特有的坑

| 坑 | 原因 | 解法 |
|---|---|---|
| Spark SQL 查 Paimon 表列顺序不对 / 看不到列 | Spark 的 HiveCatalog 把 Paimon 当成原生 Hive 表读了，读不到 Paimon 的隐藏元数据 | 必须用 `spark.sql.catalog.paimon=org.apache.paimon.spark.SparkCatalog`，查询时库表名前加 `paimon.` 前缀 |
| HDP 自带 Spark 3.1.x 启动报类冲突 | Spark 3.1.x 的 Guava / Jackson 跟较新的 Paimon 不兼容 | 要么用 Paimon 0.7.x 搭配 Spark 3.1，要么单独装 Spark 3.4/3.5 |
| 写的时候报 `NoPrimaryKeyException` | 用 Spark 写主键表，DataFrame 里没带主键列或列名不对 | Spark 写 Paimon 主键表时要求 DataFrame 列名和表 DDL 完全一致（不区分大小写，但要有主键列），用 Merge Into 更稳 |
