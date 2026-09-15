---
sidebar_position: 10
sidebar_label: UDTF函数
---

## 简介

UDTF : User Defined Table-Generating Functions。用户定义表生成函数，一行输入，多行输出。

```sql
-- explode，炸裂函数
-- 就是将一行中复杂的 array 或者 map 结构拆分成多行
select explode(array('A','B','C')) as col;
select explode(map('a', 8, 'b', 88, 'c', 888));
-- UDTF's are not supported outside the SELECT clause, nor nested in expressions
-- SELECT pageid, explode(adid_list) AS myCol... is not supported
-- SELECT explode(explode(adid_list)) AS myCol... is not supported
-- lateral view 常与 表生成函数explode结合使用
-- lateral view 语法：
lateralView: LATERAL VIEW udtf(expression) tableAlias AS
columnAlias (',' columnAlias)*
fromClause: FROM baseTable (lateralView)*
-- lateral view 的基本使用

with t1 as (select 'OK' cola, split('www.lagou.com', '\\.') colb)
select cola, colc
from t1
lateral view explode(colb) t2 as colc;
```

## 案例

### 案例一
```sql
-- 数据(id tags)：
1 1,2,3
2 2,3
3 1,2
--编写sql,实现如下结果：
1 1
1 2
1 3
2 2
2 3
3 1
3 2
-- 建表加载数据
create table tab1(id int, tags string)
row format delimited fields terminated by '\t';
load data local inpath '/home/hadoop/data/tab1.dat' into table
tab1;

-- SQL
select id, split(tags, ',') from tab1;
select id, tag from tab1 lateral view explode(split(tags, ",")) t1 as tag;
```

### 案例二

```sql
-- 数据准备
lisi|Chinese:90,Math:80,English:70
wangwu|Chinese:88,Math:90,English:96
maliu|Chinese:99,Math:65,English:60

-- 创建表
create table studscore(
name string
,score map<String,string>)
row format delimited
fields terminated by '|'
collection items terminated by ','
map keys terminated by ':';
-- 加载数据
load data local inpath '/home/hadoop/data/score.dat' overwrite into table studscore;
-- 需求：找到每个学员的最好成绩
-- 第一步，使用 explode 函数将map结构拆分为多行
select explode(score) as (subject, socre) from studscore;
--但是这里缺少了学员姓名，加上学员姓名后出错。下面的语句有是错的
select name, explode(score) as (subject, socre) from studscore;
-- 第二步：explode常与 lateral view 函数联用，这两个函数结合在一起能关联其他字段
select name, subject, score1 as score from studscore lateral view explode(score) t1 as subject, score1;
-- 第三步：找到每个学员的最好成绩
select name, max(mark) maxscore
from (select name, subject, mark
from studscore lateral view explode(score) t1 as
subject, mark) t1
group by name;


with tmp as (
select name, subject, mark
from studscore lateral view explode(score) t1 as subject,
mark
)
select name, max(mark) maxscore
from tmp
group by name;
```