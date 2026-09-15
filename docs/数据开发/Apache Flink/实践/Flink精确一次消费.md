---
sidebar_position: 16
sidebar_label: Flink精确一次消费
---
## 官方资料
> https://flink.apache.org/2018/02/28/an-overview-of-end-to-end-exactly-once-processing-in-apache-flink-with-apache-kafka-too/

## Maven依赖
```xml
		<dependency>
			<groupId>org.apache.flink</groupId>
			<artifactId>flink-connector-kafka</artifactId>
			<version>1.15.4</version>
		</dependency>
```
## 精确一次代码

### kafka生成者
```java
public class FlinkKafkaProducerTest {
    private static  String taskName= FlinkKafkaProducerTest.class.getSimpleName();
    public static final Random random = new Random();
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        //kafka sink配置
        Properties sinkProperties = new Properties();
        KafkaSink<String> sink = KafkaSink.<String>builder()
                .setBootstrapServers("192.168.61.202:9092")
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                        .setTopic("topic-name")
                        .setValueSerializationSchema(new SimpleStringSchema())
                        .build()
                )
                .setDeliverGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
                .build();
        env.addSource(new SourceFunction<String>() {
            @Override
            public void run(SourceContext<String> context) throws Exception {
                while (true) {
                    TimeZone tz = TimeZone.getTimeZone("Asia/Shanghai");
                    Instant instant = Instant.ofEpochMilli(System.currentTimeMillis() + tz.getOffset(System.currentTimeMillis()));
                    String outline = String.format(
                            "{\"ts\": \"%s\",\"user_id\": \"%s\", \"item_id\":\"%s\", \"category_id\": \"%s\"}",
                            instant.toString(),
                            random.nextInt(10),
                            random.nextInt(100),
                            random.nextInt(1000)
                    );
                    System.out.println(outline);
                    context.collect(outline);
                    Thread.sleep(1000);
                }
            }

            @Override
            public void cancel() {

            }
        }).sinkTo(sink).name("kafkaSink");

        env.execute(taskName);
    }
}
```

### 精准一次End_TO_End
```java
public class FlinkKafkaEndToEndTest {
    private static  String taskName= FlinkKafkaEndToEndTest.class.getSimpleName();

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        //restart策略
        env.setRestartStrategy(RestartStrategies.noRestart());
        //本地checkpoint配置
        env.enableCheckpointing(1000*10L);
        CheckpointConfig checkpointConf = env.getCheckpointConfig();
        checkpointConf.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
        checkpointConf.setMinPauseBetweenCheckpoints(1000*5L);
        checkpointConf.setCheckpointTimeout(1000*60L);
        checkpointConf.enableExternalizedCheckpoints(CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
        env.setStateBackend(new FsStateBackend("file:///C:/Users/nihao/Desktop/testflink/"+taskName));
        //kafka source配置
        Properties sourceProperties = new Properties();
        sourceProperties.setProperty("bootstrap.servers", "192.168.61.202:9092");
        sourceProperties.setProperty("group.id", "testflink");
        sourceProperties.put("auto.offset.reset", "latest");
//        sourceProperties.setProperty("client.id", "flinkclent");
        FlinkKafkaConsumer<String> kafkaSource = new FlinkKafkaConsumer<String>("topic-name", new SimpleStringSchema(), sourceProperties);



        //添加sink
        Properties sinkProperties = new Properties();
        sinkProperties.setProperty("bootstrap.servers", "192.168.61.202:9092");
        //端到端一致性：需要指定transaction.timeout.ms(默认为1小时)的值，需要小于transaction.max.timeout.ms(默认为15分钟)
        sinkProperties.setProperty("transaction.timeout.ms", 1000*60*2+"");
        //端到端一致性：FlinkKafkaProducer011需要指定为Semantic.EXACTLY_ONCE
        FlinkKafkaProducer<String> kafkaSink = new FlinkKafkaProducer<String>("flink_output_topic",new KeyedSerializationSchemaWrapper(new SimpleStringSchema()),sinkProperties, org.apache.flink.streaming.connectors.kafka.FlinkKafkaProducer.Semantic.EXACTLY_ONCE);
        env.addSource(kafkaSource).name("kafkaSource").uid("kafkaSource").addSink(kafkaSink);
        env.execute(taskName);
    }
}
```
> 验证发生异常情况，在checkpoint执行10秒直接关闭程序，发现虽然数据写入到了Kafka但是状态是uncommitted，所以要End to End下游消费者要read_committed就行了。

## Kafka消费者
```java
public class FlinkKafkaConsumerTest {
    private static  String taskName= FlinkKafkaConsumerTest.class.getSimpleName();
    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        Properties sourceProperties = new Properties();
        sourceProperties.setProperty("bootstrap.servers", "192.168.61.202:9092");
        sourceProperties.setProperty("group.id", "testkafkaConsumerGroup");
        //端到端一致性：消费数据时需要配置isolation.level=read_committed(默认值为read_uncommitted)
        sourceProperties.put("isolation.level", "read_committed");
//        sourceProperties.put("isolation.level", "read_uncommitted");
        sourceProperties.put("enable.auto.commit", "true");
        FlinkKafkaConsumer<String> kafkaSource = new FlinkKafkaConsumer<String>("flink_output_topic", new SimpleStringSchema(), sourceProperties);
//        kafkaSource.setStartFromLatest();
//        kafkaSource.setStartFromEarliest();
        env.addSource(kafkaSource).name("kafkaSource").print();
        env.execute(taskName);
    }
}
```

### 原理

> 相关原理是通过每次checkpoint时，记录Kafka source端偏移量，Kafka sink通过2阶段事务提交在checkpoint时将已经提交的数据更改为已提交。后续消费该Kafka sink 的topic时需要指定isolation.level=read_committed，在消费端观察会发现数据会在每次checkpoint时批量读取到checkpoint间隔的所有数据，这也就意味着数据延迟间隔为已完成checkpoint间的平均时间。如果消费端未指定isolation.level为read_committed，默认读取read_uncommitted，则消费端数据是实时消费的。

### Kafka端到端一致性需要注意的点

1. Flink任务需要开启checkpoint配置为CheckpointingMode.EXACTLY_ONCE
2. Flink任务FlinkKafkaProducer配置需要配置transaction.timeout.ms,checkpoint间隔(代码指定)<transaction.timeout.ms(默认为1小时)<transaction.max.timeout.ms(默认为15分钟)
消费端在消费FlinkKafkaProducer的topic时需要指定isolation.level(默认为read_uncommitted)为read_committed

## 参考
> https://zhuanlan.zhihu.com/p/272087368?utm_id=0