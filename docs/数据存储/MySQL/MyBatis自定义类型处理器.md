---
sidebar_position: 7
sidebar_label: MyBatis自定义类型处理器
---

## 相关代码
```java
public class ProductAnalysisBlobSmartZipTypeHandler extends BaseTypeHandler<ProductAnalysis> {

    private static final int zipThreadshold = 100;
    private static final float zipRatioThreadshold = 0.75f;

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, ProductAnalysis parameter, JdbcType jdbcType)
            throws SQLException {
        byte[] bytes = JSON.toJSONString(parameter).getBytes();
        int sourceLength = bytes.length;
        if (sourceLength > zipThreadshold) {
            byte[] cBytes = CompressUtil.GZIP.compress(bytes);
            if (cBytes.length < zipRatioThreadshold * sourceLength) {
                bytes = formatBytes(cBytes, true);
            } else {
                bytes = formatBytes(bytes, false);
            }
        } else {
            bytes = formatBytes(bytes, false);
        }
        ByteArrayInputStream bis = new ByteArrayInputStream(bytes);
        ps.setBinaryStream(i, bis, bytes.length);
    }

    @Override
    public ProductAnalysis getNullableResult(ResultSet rs, String columnName) throws SQLException {
        Blob blob = rs.getBlob(columnName);
        return deserialize(blob);
    }

    @Override
    public ProductAnalysis getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        Blob blob = rs.getBlob(columnIndex);
        return deserialize(blob);
    }

    @Override
    public ProductAnalysis getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        Blob blob = cs.getBlob(columnIndex);
        return deserialize(blob);
    }

    private ProductAnalysis deserialize(Blob blob) throws SQLException {
        if (null != blob) {
            try {
                byte[] bytes = blob.getBytes(1, (int) blob.length());
                byte[] sourceBytes = new byte[bytes.length - 1];
                System.arraycopy(bytes, 1, sourceBytes, 0, bytes.length - 1);
                if (bytes[0] == 1) {
                    sourceBytes = CompressUtil.GZIP.decompress(sourceBytes);
                }
                String str = new String(sourceBytes);                
                return JSON.parseObject(str, ProductAnalysis.class);
            } catch(Exception e) {
                e.printStackTrace();
            }
        }
        return null;
    }

    private byte[] formatBytes(byte[] bytes, boolean compress) {
        byte[] result = new byte[bytes.length + 1];
        if (compress) {
            result[0] = 1;
        }
        System.arraycopy(bytes, 0, result, 1, bytes.length);
        return result;
    }
}
```

## 使用
```
		<foreach collection="list" item="item" index="index" separator=",">
		(
		#{item.slug}
		,#{item.value, jdbcType=BLOB, typeHandler=com.duomai.bigdata.bj.dao.typehandler.ProductAnalysisBlobSmartZipTypeHandler}
		)
```