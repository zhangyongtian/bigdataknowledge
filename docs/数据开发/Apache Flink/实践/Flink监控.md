---
sidebar_position: 6
sidebar_label: Flink监控
---
> 前提：根据FlinkCDC配置的内容先配置好，然后启动一个flink集群。

## 安装pushgateway

```
sudo docker run -d -p 9091:9091 prom/pushgateway
```

## 下载prometheus

> https://prometheus.io/download/

```
链接：https://pan.baidu.com/s/1iNvHrO6QxvseiDraclxm8Q 
提取码：yyds 
--来自百度网盘超级会员V5的分享
```

### 配置prometheus

```
vi prometheus.yml
```

配置下面的作用是拉取pushgateway的监控数据。

```
  - job_name: 'pushgateway'
    static_configs:
    - targets: ['localhost:9091']
      labels:
        instance: pushgateway
```

### 启动prometheus

```
nohup ./prometheus --web.enable-lifecycle --config.file=prometheus.yml > ./prometheus.log 2>&1 &
```

关闭prometheus

```
curl -X POST http://localhost:9090/-/quit
```

## 安装grafana

```
docker run -d -p 23000:3000 grafana/grafana
```

## Flink相关

### 修改Flink配置文件

相关网址

> https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/deployment/metric_reporters/

```
metrics.reporter.promgateway.factory.class: org.apache.flink.metrics.prometheus.PrometheusPushGatewayReporterFactory
metrics.reporter.promgateway.hostUrl: http://localhost:9091
metrics.reporter.promgateway.jobName: flinkjob
metrics.reporter.promgateway.randomJobNameSuffix: true
metrics.reporter.promgateway.deleteOnShutdown: false
metrics.reporter.promgateway.groupingKey: k1=v1;k2=v2
metrics.reporter.promgateway.interval: 60 SECONDS
```

### 执行测试Flink案例
```
CREATE TABLE `Order`
(
    id         INT,
    product_id INT,
    quantity   INT,
    order_time TIMESTAMP,
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
      'connector' = 'datagen',
      'fields.id.kind' = 'sequence',
      'fields.id.start' = '1',
      'fields.id.end' = '100000',
      'fields.product_id.min' = '1',
      'fields.product_id.max' = '100',
      'rows-per-second' = '1'
);

CREATE TABLE `Product`
(
    id    INT,
    name  VARCHAR,
    price DOUBLE,
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
      'connector' = 'datagen',
      'fields.id.min' = '1',
      'fields.id.max' = '100',
      'rows-per-second' = '1'
);

CREATE TABLE `OrderDetails`
(
    id           INT,
    product_name VARCHAR,
    total_price  DOUBLE,
    order_time   TIMESTAMP,
    PRIMARY KEY (id) NOT ENFORCED
) WITH (
      'connector' = 'print'
);

INSERT INTO `OrderDetails`
SELECT o.id, p.name, o.quantity * p.price, o.order_time
FROM `Order` o
INNER JOIN
`Product` p
ON o.product_id = p.id;
```