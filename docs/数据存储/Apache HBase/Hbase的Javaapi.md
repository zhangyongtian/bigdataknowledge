---
sidebar_position: 8
sidebar_label: Hbase的Javaapi
---

```java
public class HbaseUtil {
    public static Configuration conf;//管理HBase的配置信息
    public static Connection conn;//管理HBase的连接
    public static Admin admin;//管理HBase数据库的连接

    /**
     * 创建相关连接
     *
     * @throws IOException 可能出现的异常
     */
    public static void init() throws IOException {
        conf = HBaseConfiguration.create();
        conf.set("HADOOP_USER_NAME", "xx");
        conf.set("hbase.root.dir", "hdfs://xx/hbase");
        conf.set("hbase.zookeeper.quorum", "xx:2181,xx:2181,xx:2181");//配置Zookeeper的ip地址
        conf.set("hbase.zookeeper.property.dataDir", "/data/cloud/zookeeper/data");
        conf.set("zookeeper.znode.parent", "/xx");

        conn = ConnectionFactory.createConnection(conf);
        admin = conn.getAdmin();
    }

    /**
     * 关闭所有连接
     *
     * @throws IOException 可能出现的异常
     */
    public static void close() throws IOException {
        if (admin != null)
            admin.close();
        if (conn != null)
            conn.close();
    }

    /**
     * 创建表
     *
     * @param myTableName 表名
     * @param colFamily   列族名的数组
     * @throws IOException 可能出现的异常
     *                     create 'person3', {NAME=>'info', VERSIONS=>2,COMPRESSION=>'LZ4'}
     */
    public static void createTable(String myTableName, String[] colFamily) throws IOException {
        TableName tableName = TableName.valueOf(myTableName);
        if (admin.tableExists(tableName)) {
            System.out.println(myTableName + "表已经存在");
        } else {
            HTableDescriptor hTableDescriptor = new HTableDescriptor(tableName);
            for (String str : colFamily) {
                HColumnDescriptor hColumnDescriptor = new HColumnDescriptor(str);
                hColumnDescriptor.setMaxVersions(1);
                hColumnDescriptor.setCompactionCompressionType(Compression.Algorithm.LZ4);
                hTableDescriptor.addFamily(hColumnDescriptor);
            }
            admin.createTable(hTableDescriptor);
        }
    }

    /**
     * 添加数据
     *
     * @param tableName 表名
     * @param rowkey    行键
     * @param colFamily 列族
     * @param col       列
     * @param value     值
     * @throws IOException 可能出现的异常
     */
    public static void insertData(String tableName, String rowkey, String colFamily, String col, String value) throws IOException {
        Table table = conn.getTable(TableName.valueOf(tableName));
        Put put = new Put(rowkey.getBytes());
        put.addColumn(colFamily.getBytes(), col.getBytes(), value.getBytes());
        table.put(put);
        table.close();
    }

    /**
     * 根据行键删除数据
     *
     * @param tableName 表名
     * @param rowkey    行键
     * @throws IOException 可能出现的异常
     */
    public static void deleteData(String tableName, String rowkey) throws IOException {
        Table table = conn.getTable(TableName.valueOf(tableName));
        Delete delete = new Delete(rowkey.getBytes());
        table.delete(delete);
        table.close();
    }

    /**
     * 获取数据
     *
     * @param tableName 表名
     * @param rowkey    行键
     * @param colFamily 列族
     * @param col       列
     * @throws IOException 可能出现的异常
     */
    public static void getData(String tableName, String rowkey, String colFamily, String col) throws IOException {
        Table table = conn.getTable(TableName.valueOf(tableName));
        Get get = new Get(rowkey.getBytes());
        get.addColumn(colFamily.getBytes(), col.getBytes());
        Result result = table.get(get);
        System.out.println(new String(result.getValue(colFamily.getBytes(), col.getBytes())));
        table.close();
    }

// 简单操作 (新增) TODO 增
    @Test
    public void insertData() throws IOException {
        init();
        createTable("person4",new String[]{"info","info2"});
        Random random = new Random(10000);
        for (int i = 0; i < 5; i++) {
            Integer i1 = random.nextInt();
            Integer i2 = random.nextInt();
            String uuid = String.valueOf(UUID.randomUUID());
            insertData("person4", uuid,"info","name",uuid);
            insertData("person4",uuid,"info","age",i1.toString());
            insertData("person4",uuid,"info","score",i2.toString());
            insertData("person4",uuid,"info2","score",i2.toString());
        }
        getData("person","ffebf1c8-3010-4cda-ae9e-85db5dddc139","info","age");
        close();
    }

    // hbase的删除操作 TODO 删

    /**
     * delete 'person2', '16c26899-c7d0-44e8-96d3-f0ffe72566ce'
     *
     * @throws IOException
     */
    @Test
    public void deleteData() throws IOException {
        init();
//        deleteByRowKey(); // delete from table where id='' 删除整行
//        deleteByRowKeyColm(); // 删除指定列
//        deleteByRowKeyFam(); //删除指定列族
        deleteByRowKeyColmVersion();// 删除指定列特定版本删除
    }


    /**
     * 指定数据的版本删除
     * delete 'person3','a8ec52dd-ede0-45db-a950-afdfe312c672', 'info:age', 2024-02-22T16:44:26.393
     */
    public static void deleteByRowKeyColmVersion() {
        try {
            init();
            // 获取 HBase 连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person3");

            // 创建 Delete 对象
            Delete delete = new Delete(Bytes.toBytes("a8ec52dd-ede0-45db-a950-afdfe312c672"));

            // 指定要删除的列的版本
            SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS");
            Date timestamp = dateFormat.parse("2024-02-22T16:57:13.038");
            delete.addColumn(Bytes.toBytes("info"), Bytes.toBytes("name"), timestamp.getTime());

            // 获取表
            Table table = connection.getTable(tableName);

            // 执行删除操作
            table.delete(delete);

            // 关闭资源
            table.close();
            connection.close();
        } catch (ParseException e) {
            e.printStackTrace();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 删除指定列族
     * delete 'person2', '2aefb7f5-e0e4-4552-9e9e-b28182060d67', 'info'
     */
    public static void deleteByRowKeyFam() {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person2");

            // 创建 Delete 对象
            Delete delete = new Delete(Bytes.toBytes("2aefb7f5-e0e4-4552-9e9e-b28182060d67"));

            // 删除指定行的所有列族和列
            delete.deleteFamily(Bytes.toBytes("info"));

            // 获取表
            Table table = connection.getTable(tableName);

            // 执行删除操作
            table.delete(delete);

            // 关闭资源
            table.close();
            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 根据rowkey删除指定列
     * delete 'person2', '2aefb7f5-e0e4-4552-9e9e-b28182060d67', 'info:age'
     * 指定删除的版本（生产的时候建议只要一个版本）
     * delete 'your_table_name', 'your_row_key', 'info:your_column', your_timestamp
     */
    public static void deleteByRowKeyColm() {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person2");

            // 创建 Delete 对象
            Delete delete = new Delete(Bytes.toBytes("2aefb7f5-e0e4-4552-9e9e-b28182060d67"));

            // 删除指定列族下的指定列
            delete.addColumn(Bytes.toBytes("info"), Bytes.toBytes("age"));

            // 获取表
            Table table = connection.getTable(tableName);

            // 执行删除操作
            table.delete(delete);

            // 关闭资源
            table.close();
            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 根据row删除整行
     */
    public static void deleteByRowKey() {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person2");

            // 创建 Delete 对象
            Delete delete = new Delete(Bytes.toBytes("16c26899-c7d0-44e8-96d3-f0ffe72566ce"));

            // 获取表
            Table table = connection.getTable(tableName);

            // 执行删除操作
            table.delete(delete);

            // 关闭资源
            table.close();
            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    //    (基本操作) TODO 修改
    @Test
    public void updateData() throws IOException {
        init();
//        updateByKey(); // 根据key进行修改
        getALLVersionData(); //得到所有版本的数据
    }

    /**
     * get 'person4', '702e27ba-38aa-478d-88d1-4b3e8ba7ec19', {COLUMN => ['info:name'], VERSIONS => 5}
     */
    public static void getALLVersionData(){
        try {
            init();
            // 获取 HBase 连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person3");

            // 创建 Get 对象，指定行键
            Get get = new Get(Bytes.toBytes("a8ec52dd-ede0-45db-a950-afdfe312c672"));

            // 指定列族和列，并设置读取版本数
            get.addColumn(Bytes.toBytes("info"), Bytes.toBytes("name"));
            get.setMaxVersions(5);

            // 获取表
            Table table = connection.getTable(tableName);

            // 执行查询操作
            Result result = table.get(get);

            // 处理查询结果
            for (Cell cell : result.listCells()) {
                // 获取时间戳
                long timestamp = cell.getTimestamp();

                // 获取值
                byte[] value = CellUtil.cloneValue(cell);

                // 处理数据，例如打印或保存
                System.out.println("Timestamp: " + timestamp + ", Value: " + Bytes.toString(value));
            }

            // 关闭资源
            table.close();
            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * put 'person3', 'a8ec52dd-ede0-45db-a950-afdfe312c672', 'info:name', 'zhang'
     */
    public static void updateByKey(){
        try {
            init();
            // 获取 HBase 连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person4");

            // 创建 Put 对象，指定行键
            Put put = new Put(Bytes.toBytes("702e27ba-38aa-478d-88d1-4b3e8ba7ec19"));

            // 添加列族和列，设置值
            put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("name"), Bytes.toBytes("zhang"));

            // 获取表
            Table table = connection.getTable(tableName);

            // 执行插入操作
            table.put(put);

            // 关闭资源
            table.close();
            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

//（基本的查询）TODO 查
    @Test
    public void queryData() throws IOException {
        init();
//        singleColumnValueFilter(); // 等值列族下面列查询 select * from table1 where age=xx
//        familyFilter(); // 指定列族查询所有的列 select * from table1
//        zuhechaxun(); // 指定列族指定列返回查询 select xx,xx from table1
//        zuhechaxun1(); // 指定列族指定列返回查询 select xx,xx from table1 where score=xx
//        zuhechaxun2(); // 指定列族指定列返回查询 select xx,xx from table1 where score>xx
    }

    /**
     * 指定列族指定列查询的等值查询,返回指定行
     * scan 'person1', {FILTER => "FamilyFilter(=,'binary:info') AND SingleColumnValueFilter('info', 'score', >, 'binary:900425139') AND (QualifierFilter(=,'binary:score') OR QualifierFilter(=,'binary:age') OR QualifierFilter(=,'binary:name'))"}
     */
    public static void zuhechaxun2() {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person1");

            // 创建HBase表的扫描对象
            Scan scan = new Scan();

            // 创建FilterList
            FilterList filterList = new FilterList(FilterList.Operator.MUST_PASS_ALL);

            // 添加列族过滤器
            filterList.addFilter(new FamilyFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("info"))));

            // 添加 SingleColumnValueFilter
            filterList.addFilter(new SingleColumnValueFilter(
                    Bytes.toBytes("info"),  // 列族名
                    Bytes.toBytes("score"),  // 列名
                    CompareFilter.CompareOp.GREATER,  // 比较操作符
                    new BinaryComparator(Bytes.toBytes("900425139"))  // 期望的值
            ));

            // 创建 QualifierFilter 列过滤器
            FilterList qualifierFilterList = new FilterList(FilterList.Operator.MUST_PASS_ONE);
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("score"))));
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("age"))));
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("name"))));

            // 添加 QualifierFilter 到 FilterList
            filterList.addFilter(qualifierFilterList);

            // 设置 FilterList 为 Scan 对象的过滤器
            scan.setFilter(filterList);

            // 获取表的扫描器
            ResultScanner scanner = connection.getTable(tableName).getScanner(scan);

            int count = 0;
            // 遍历结果集
            for (Result result : scanner) {
                count++;
                // 处理查询结果
                // 例如：result.getValue(Bytes.toBytes("cf"), Bytes.toBytes("column"))
                System.out.println("==============");
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"))));
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("name"))));
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("score"))));
                System.out.println("==============");
            }
            System.out.println(count);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 指定列族指定列查询的等值查询,返回指定行
     * scan 'person1', {FILTER => "FamilyFilter(=,'binary:info') AND SingleColumnValueFilter('info', 'score', =, 'binary:736425139') AND (QualifierFilter(=,'binary:score') OR QualifierFilter(=,'binary:age') OR QualifierFilter(=,'binary:name'))"}
     */
    public static void zuhechaxun1() {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person1");

            // 创建HBase表的扫描对象
            Scan scan = new Scan();

            // 创建FilterList
            FilterList filterList = new FilterList(FilterList.Operator.MUST_PASS_ALL);

            // 添加列族过滤器
            filterList.addFilter(new FamilyFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("info"))));

            // 添加 SingleColumnValueFilter
            filterList.addFilter(new SingleColumnValueFilter(
                    Bytes.toBytes("info"),  // 列族名
                    Bytes.toBytes("score"),  // 列名
                    CompareFilter.CompareOp.EQUAL,  // 比较操作符
                    new BinaryComparator(Bytes.toBytes("736425139"))  // 期望的值
            ));

            // 创建 QualifierFilter 列过滤器
            FilterList qualifierFilterList = new FilterList(FilterList.Operator.MUST_PASS_ONE);
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("score"))));
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("age"))));
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("name"))));

            // 添加 QualifierFilter 到 FilterList
            filterList.addFilter(qualifierFilterList);

            // 设置 FilterList 为 Scan 对象的过滤器
            scan.setFilter(filterList);

            // 获取表的扫描器
            ResultScanner scanner = connection.getTable(tableName).getScanner(scan);

            int count = 0;
            // 遍历结果集
            for (Result result : scanner) {
                count++;
                // 处理查询结果
                // 例如：result.getValue(Bytes.toBytes("cf"), Bytes.toBytes("column"))
                System.out.println("==============");
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"))));
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("name"))));
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("score"))));
                System.out.println("==============");
            }
            System.out.println(count);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 查询指定列族下面的指定列数据
     * scan 'person1', {FILTER => "FamilyFilter(=,'binary:info') AND (QualifierFilter(=,'binary:age') OR QualifierFilter(=,'binary:name'))"}
     *
     * @throws IOException
     */
    public static void zuhechaxun() throws IOException {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person1");

            // 创建HBase表的扫描对象
            Scan scan = new Scan();
// 创建FilterList
            FilterList filterList = new FilterList(FilterList.Operator.MUST_PASS_ALL);

            // 添加列族过滤器
            filterList.addFilter(new FamilyFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("info"))));

            // 创建 QualifierFilter 列过滤器
            FilterList qualifierFilterList = new FilterList(FilterList.Operator.MUST_PASS_ONE);
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("age"))));
            qualifierFilterList.addFilter(new QualifierFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("name"))));

            // 添加 QualifierFilter 到 FilterList
            filterList.addFilter(qualifierFilterList);

            // 设置 FilterList 为 Scan 对象的过滤器
            scan.setFilter(filterList);

            // 获取表的扫描器
            ResultScanner scanner = connection.getTable(tableName).getScanner(scan);

            int count = 0;
            // 遍历结果集
            for (Result result : scanner) {
                count++;
                // 处理查询结果
                // 例如：result.getValue(Bytes.toBytes("cf"), Bytes.toBytes("column"))
                System.out.println("==============");
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"))));
                System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("name"))));
                System.out.println("==============");
            }
            System.out.println(count);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 等值列族下面列查询 scan 'person', {FILTER => "SingleColumnValueFilter('info', 'score', =, 'binary:736425139')"}
     * 非等值  scan 'person', {FILTER => "SingleColumnValueFilter('info', 'score', !=, 'binary:736425139')"}
     * 请注意，上述命令中的 binary 是指数据在HBase中的存储格式。如果你的数据是字符串类型，可以省略 binary。如果是其他类型，需要根据实际情况指定。
     *
     * @throws IOException
     */
    public static void singleColumnValueFilter() throws IOException {
        // 获取表名
        TableName tableName = TableName.valueOf("person");

        // 创建HBase表的扫描对象
        Scan scan = new Scan();

        // 设置查询条件
        Filter filter = new SingleColumnValueFilter(
                Bytes.toBytes("info"), // 列族名
                Bytes.toBytes("score"), // 列名
                CompareFilter.CompareOp.NOT_EQUAL, // 比较操作符,这里是简单的比较
                Bytes.toBytes("736425139") // 值
        );
        scan.setFilter(filter);

        // 获取表的扫描器
        ResultScanner scanner = conn.getTable(tableName).getScanner(scan);

        int count = 0;
        // 遍历结果集
        for (Result result : scanner) {
            count++;
            // 处理查询结果
            // 例如：result.getValue(Bytes.toBytes("cf"), Bytes.toBytes("column"))
            System.out.println("==============");
            System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("age"))));
            System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("name"))));
            System.out.println(new String(result.getValue(Bytes.toBytes("info"), Bytes.toBytes("score"))));
            System.out.println("==============");
        }
        System.out.println(count);
    }

    /**
     * 查询特定列族的所有行：
     * scan 'person1', {FILTER => "FamilyFilter(=, 'binary:test')"}
     *
     * @throws IOException
     */
    public static void familyFilter() throws IOException {
        try {
            init();
            // 获取HBase连接
            Connection connection = conn;

            // 获取表名
            TableName tableName = TableName.valueOf("person1");

            // 创建HBase表的扫描对象
            Scan scan = new Scan();

            // 创建FilterList
            FilterList filterList = new FilterList(FilterList.Operator.MUST_PASS_ALL);

            // 创建FamilyFilter
            Filter familyFilter = new FamilyFilter(CompareFilter.CompareOp.EQUAL, new BinaryComparator(Bytes.toBytes("test")));

            // 设置FamilyFilter为Scan对象的过滤器
            scan.setFilter(familyFilter);

            // 获取表的扫描器
            ResultScanner scanner = connection.getTable(tableName).getScanner(scan);

            int count = 0;
            // 遍历结果集
            for (Result result : scanner) {
                count++;
                System.out.println("==============");
                System.out.println(new String(result.getValue(Bytes.toBytes("test"), Bytes.toBytes("score"))));
                System.out.println("==============");
            }

            System.out.println(count);
            // 关闭资源
            scanner.close();
            connection.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```
