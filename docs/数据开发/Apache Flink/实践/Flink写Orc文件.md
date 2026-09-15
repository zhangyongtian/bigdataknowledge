---
sidebar_position: 15
sidebar_label: Flink写Orc文件
---

## Flink写入ORC的sink

```java
public class EventDayTimeLogFileOrcSink<T> implements Serializable {
    public StreamingFileSink<T> createRowFileSink(String outputBasePath, Class<T> clazz) {
        // 获取类 T 中所有字段，并构建 schema 字符串,这里的schema主要是对应hive里面的建表字段
        String orcTableSchema = Arrays.stream(clazz.getDeclaredFields())
                .map(this::toOrcTableSchemaEntry)
                .collect(Collectors.joining(",",
                        "struct<", ">"));
        // 这里要处理的主要是为了得到java对象数据
        String orcObjectDataschema = Arrays.stream(clazz.getDeclaredFields())
                .map(this::toOrcObjectDataschema)
                .collect(Collectors.joining(",",
                        "struct<", ">"));

        ClazzVectorizer<T> clazzVectorizer = new ClazzVectorizer<>(orcTableSchema, orcObjectDataschema);
        OrcBulkWriterFactory orcBulkWriterFactory = new OrcBulkWriterFactory<>(clazzVectorizer);
        LocalDateTime now = LocalDateTime.now();
        String formattedTimestamp = now.format(DateTimeFormatter.ofPattern("_yyyy_MM_dd_HH_mm_ss"));
        OutputFileConfig config = OutputFileConfig
                .builder()
                .withPartPrefix(clazz.getSimpleName().toLowerCase().replaceAll("\\.","_") + formattedTimestamp + "_")
                .withPartSuffix(".orc")
                .build();

        return StreamingFileSink.forBulkFormat(new Path(outputBasePath), orcBulkWriterFactory)
                .withRollingPolicy(OnCheckpointRollingPolicy.build())
                .withBucketAssigner(new EventDayTimeBucketAssigner()).withOutputFileConfig(config)
                .build();

    }

    private String toOrcObjectDataschema(Field field) {
        Class<?> fieldType = field.getType();
        String typeName = getTypeName(fieldType);
        return field.getName() + ":" + typeName;
    }

    private String toOrcTableSchemaEntry(Field field) {
        Class<?> fieldType = field.getType();
        String typeName;
        typeName = getTypeName(fieldType);
        return camelToUnderscore(field.getName()) + ":" + typeName;
    }

    @NotNull
    private static String getTypeName(Class<?> fieldType) {
        String typeName;
        if (fieldType.equals(Integer.TYPE) || fieldType.equals(Integer.class)) {
            typeName = "int";
        } else if (fieldType.equals(Long.TYPE) || fieldType.equals(Long.class)) {
            typeName = "bigint";
        } else if (fieldType.equals(Double.TYPE) || fieldType.equals(Double.class)) {
            typeName = "double";
        } else if (fieldType.equals(Boolean.TYPE) || fieldType.equals(Boolean.class)) {
            typeName = "boolean";
        } else if (fieldType.equals(String.class)) {
            typeName = "string";
        } else if (fieldType.equals(LocalDate.class)) {
            typeName = "date";
        } else if (fieldType.equals(Timestamp.class)) {
            typeName = "timestamp";
        } else {
            // 对于未处理的类型，这里假设默认为 string 类型，但根据实际情况可能需要定制处理
            typeName = "string";
            // 或抛出异常，表明不支持该字段类型
            // throw new UnsupportedOperationException("Unsupported field type: " + fieldType.getName());
        }
        return typeName;
    }

    public static String camelToUnderscore(String camelCase) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < camelCase.length(); i++) {
            char ch = camelCase.charAt(i);
            if (Character.isUpperCase(ch)) { // 处理大写字母
                if (i > 0) {
                    builder.append('_');
                }
                builder.append(Character.toLowerCase(ch));
            } else { // 处理小写字母和数字
                builder.append(ch);
            }
        }
        return builder.toString();
    }
}
```

## Orc的BucketAssigner
```java
public class EventDayTimeBucketAssigner<IN> implements BucketAssigner<IN, String> {

    private static final long serialVersionUID = 1L;

    private static final String DEFAULT_FORMAT_STRING = "yyyy/MM/dd";
//    private static final String DEFAULT_FORMAT_STRING = "yyyy";

    private static final ZoneId ZONE_ID = ZoneId.of("Asia/Shanghai");

    private transient DateTimeFormatter dateTimeFormatter;

    @Override
    public String getBucketId(IN element, Context context) {
        if (dateTimeFormatter == null) {
            dateTimeFormatter = DateTimeFormatter.ofPattern(DEFAULT_FORMAT_STRING).withZone(ZONE_ID);
        }

        Long eventTimestamp = context.timestamp();
        assert eventTimestamp != null;
        return dateTimeFormatter.format(Instant.ofEpochMilli(eventTimestamp));
    }

    @Override
    public SimpleVersionedSerializer<String> getSerializer() {
        return SimpleVersionedStringSerializer.INSTANCE;
    }
}

```

## 小文件合并
```sql
alter table test partition(year='2024', month='03', day='14') concatenate;
```