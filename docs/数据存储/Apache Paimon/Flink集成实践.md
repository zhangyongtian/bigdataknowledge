---
sidebar_position: 3
sidebar_label: Flink 集成实践
---

## 部署前置常量区（所有章节统一引用，不要硬编码）

| 类别 | 常量 | 值 |
|---|---|---|
| **版本矩阵** | Flink | `flink-1.20.5-bin-scala_2.12` |
| | Paimon | `2.0.0`（paimon-flink-1.20、paimon-flink-action、paimon-hive-connector-3.1） |
| | Flink MySQL CDC | `flink-sql-connector-mysql-cdc-3.1.1`（groupId=org.apache.flink，fat jar 带 sql- 前缀） |
| | MySQL JDBC | `mysql-connector-j-8.0.33` |
| | StreamPark | `apache-streampark_2.12-2.2.0` |
| **主机 & 端口** | 集群节点 | `master1`、`master2`、`node1`、`node2` |
| | Ambari Server / MySQL | `master1`（MySQL root/123456，端口 3306） |
| | Hive Metastore | `thrift://master1:9083` |
| | ZooKeeper Quorum | `master1:2181,master2:2181,node1:2181` |
| | Flink Web UI | `http://master1:8082` |
| | StreamPark（独立） | `http://master1:10001`（Ambari 自带 10000） |
| **本地目录规则** | Flink 实际解压目录 | `/home/bigdata/module/flink-1.20.5`（拷 Jar/改 conf/rsync 统一走这里，不依赖软链） |
| | Flink 软链（$FLINK_HOME） | `/home/bigdata/module/flink-1.20` → `flink-1.20.5`（仅环境变量和命令行引用） |
| | Flink 干净配置目录（终态） | `$FLINK_HOME/../flink-1.20.5/conf.clean`（扁平 config.yaml，每次启动重建，避免旧缓存） |
| | 临时目录（1777 sticky bit，JaasModule 写 jaas-*.conf 必用） | `/tmp/flink-bigdata/tmp`（io.tmp.dirs / java.io.tmpdir）<br />`/tmp/flink-bigdata/upload`（web.upload.dir）<br />`/tmp/flink-bigdata/web-tmp`（web.tmpdir） |
| | 运维脚本目录 | `/home/bigdata/shell`（所有自定义脚本统一放这里） |
| **HDFS 路径** | Flink Checkpoint / Savepoint / HA | `hdfs:///user/flink/checkpoints`、`hdfs:///user/flink/savepoints`、`hdfs:///user/flink/ha` |
| | Paimon Warehouse（复用 HMS） | `hdfs:///user/hive/warehouse/paimon` |
| **硬编码规范** | Flink CLI `-D` 参数 | **连写无空格** `-Dkey=value`，JCommander 会丢带空格的 `-D key=value` |
| | 写 `/etc/profile.d/*.sh` | 必须 `sudo tee << 'EOF' > /dev/null`（`sudo cat >` 的重定向不继承 sudo） |
| | HDFS `/user` 下 mkdir/chown | 必须 `sudo -u hdfs hdfs dfs ...`（`/user` 属主 hdfs:hdfs，普通用户不能写） |
| | HADOOP_CLASSPATH | **瘦化**：只 `$(hadoop classpath):/etc/hive/conf`，严禁 `hive-client/lib/*`（HDP Hive 2.3 带 Jackson 2.6 会冲掉 Flink 1.20 要的 Jackson 2.15+） |
| | Flink config.yaml 格式 | **全扁平 key-value**（`a.b.c: v`），严禁 nested map 写法（`a:\n  b:\n    c: v`），否则命令行 -D 扁平 key 会触发 ClassCastException |

---

## 目录索引

```text
0. 先说结论（照抄顺序，别跳步）
1. 下载所有包（Flink 1.20.5 / Paimon 2.0 / CDC 3.1.1 / JDBC / StreamPark）
2. 解压 + 软链 + 拷 Jar + 同步到 4 节点
3. 配置（3.0 建 tmp 目录 → 3.1 HDP conf 软链 → 3.2 三套扁平 config.yaml → 3.3 setenv.sh 瘦 classpath → 3.4 HDFS 授权 → 3.5 rsync）
4. 环境变量（/etc/profile.d/flink120.sh，瘦 HADOOP_CLASSPATH，PATH 去 HDP 老 flink）
5. 启动 Flink on YARN Session
   5.0 终极 0→1 命令链（推荐，一键串完所有前置检查）
   5.1 三套启动命令 C / A / B（与 3.2 配置严格对齐）
   5.2 Flink Web UI 检查
   5.3 Flink SQL Client 登录
6. Paimon Quick Start（6 步：SET → Catalog → 建表 → datagen 写流 → 批读 → 退出）
7. StreamPark 2.2.x（7.0 独立安装 → 7.1 登录 → 7.2 Flink Home → 7.3 Cluster → 7.4 资源 → 7.5 新建 SQL 作业）
8. 常见坑速查（12 条，按实际踩坑顺序：现象 / 根因 / 修法）
```

---

## 0. 先说结论（照这个顺序一步步复制粘贴，别跳步）

```text
第 1 步：master1 上下载 Flink 1.20 + Paimon 2.0 相关包        → 本文档 1.x
第 2 步：解压 + 软链 + 同步到 master2/node1/node2            → 本文档 2.x
第 3 步：Flink 配置（加载 HDP Hadoop/Hive 配置、SQL Gateway 端口）→ 本文档 3.x
第 4 步：配置环境变量 / etc/profile（所有节点）               → 本文档 4.x
第 5 步：启动 Flink on YARN Session，测试 sql-client         → 本文档 5.x（推荐直接跑 5.0 终极 0→1 链）
第 6 步：创建 Paimon Catalog，跑 Quick-Start Hello World     → 本文档 6.x
第 7 步：StreamPark 里配置 Flink Home + 提交 Flink SQL 作业   → 本文档 7.x
```

> ⚠️ 全程不要覆盖 HDP 3.3.2 自带的 `/usr/hdp/current/flink`，HDP 自己的 Flink 1.15 还留给 Ambari 管理的 Flink Service 用，我们自己的 Flink 1.20 就装在 `/home/bigdata/module/flink-1.20` 下，互不干扰。

---

## 1. 下载所有需要的包（master1 上执行，下载到 `/home/bigdata/software`）

> 所有下载链接都是 Apache 官方，可直接复制 wget。如果集群没外网，先在你电脑上下载好再用 WinSCP/rz 上传到同一个目录，照样往下走。

### 1.1 先建下载目录

```bash
mkdir -p /home/bigdata/software
cd /home/bigdata/software
```

### 1.2 下载 Flink 1.20（Scala 2.12，跟 HDP 3.3.2 的 Spark/Hive Scala 版本一致）

> ⚠️ 注意：Flink 1.20.0 已从清华 TUNA 下架（报 403 Forbidden）。统一用 **1.20.5**。

```bash
# ① 首选：华为云镜像（国内速度快）
wget -c https://mirrors.huaweicloud.com/apache/flink/flink-1.20.5/flink-1.20.5-bin-scala_2.12.tgz -O flink-1.20.5-bin-scala_2.12.tgz

# ② 兜底 1：阿里云镜像（华为云挂了就跑这条）
# wget -c https://mirrors.aliyun.com/apache/flink/flink-1.20.5/flink-1.20.5-bin-scala_2.12.tgz -O flink-1.20.5-bin-scala_2.12.tgz

# ③ 兜底 2：Apache 官方归档（国外源，慢但必能下到）
# wget -c https://archive.apache.org/dist/flink/flink-1.20.5/flink-1.20.5-bin-scala_2.12.tgz -O flink-1.20.5-bin-scala_2.12.tgz
```

### 1.3 下载 Paimon 2.0（stable）的 4 个 Jar

> ⚠️ 下面两个 Jar 名容易写错，照抄：
> - **Hive 3.1 Bundle**：artifactId 是 `paimon-hive-connector-3.1`（少写 `connector-` 会 404）
> - **Flink CDC MySQL**：Flink CDC 3.0+ 已捐给 Apache，groupId=`org.apache.flink`，SQL Client 必须带 `sql-` 前缀的 fat jar（瘦 jar 会 ClassNotFound）

```bash
# ① Flink 1.20 用的 Paimon Bundled Jar
wget -c https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.20/2.0.0/paimon-flink-1.20-2.0.0.jar -O paimon-flink-1.20-2.0.0.jar

# ② Flink Action Jar（compact / create_tag / remove_orphan_files 系统过程）
wget -c https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-action/2.0.0/paimon-flink-action-2.0.0.jar -O paimon-flink-action-2.0.0.jar

# ③ Hive 3.1 Connector Jar（复用 HDP HMS，artifactId=paimon-hive-connector-3.1）
wget -c https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-hive-connector-3.1/2.0.0/paimon-hive-connector-3.1-2.0.0.jar -O paimon-hive-connector-3.1-2.0.0.jar

# ④ Flink CDC MySQL Connector（fat jar，groupId=org.apache.flink）
wget -c https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-mysql-cdc/3.1.1/flink-sql-connector-mysql-cdc-3.1.1.jar -O flink-sql-connector-mysql-cdc-3.1.1.jar
```

### 1.4 下载 MySQL JDBC Driver（Hive / CDC / Paimon HMS 统一复用）

```bash
wget -c https://repo.maven.apache.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar -O mysql-connector-j-8.0.33.jar
```

### 1.5 校验 6 个文件是否都下齐（大小 0 的重下）

```bash
ls -lh /home/bigdata/software | grep -E 'flink-1.20|paimon|mysql-connector|flink-connector-mysql'
```

期望看到 6 个文件：
- `flink-1.20.5-bin-scala_2.12.tgz`（~350MB）
- `paimon-flink-1.20-2.0.0.jar`
- `paimon-flink-action-2.0.0.jar`
- `paimon-hive-connector-3.1-2.0.0.jar`
- `flink-sql-connector-mysql-cdc-3.1.1.jar`
- `mysql-connector-j-8.0.33.jar`

---

## 2. 解压 Flink 1.20 + 放 Jar + 同步到所有节点

### 2.1 安装到 `/home/bigdata/module/flink-1.20.5`，并做软链

> ⚠️ 软链 `flink-1.20 -> flink-1.20.5` 断了会导致 Flink 读到默认 conf（报 64MB/128MB 错），必须按下面 `ls` 校验输出。

```bash
mkdir -p /home/bigdata/module
cd /home/bigdata/software
tar -zxf flink-1.20.5-bin-scala_2.12.tgz -C /home/bigdata/module/

# 强制 overwrite 软链
ln -sfn /home/bigdata/module/flink-1.20.5 /home/bigdata/module/flink-1.20

# ====== 必须跟下面期望完全一致 ======
ls -ld /home/bigdata/module/flink-1.20*
# 期望：
# lrwxrwxrwx. 1 bigdata hadoop  38 ... flink-1.20 -> /home/bigdata/module/flink-1.20.5
# drwxr-xr-x. 9 bigdata hadoop 149 ... flink-1.20.5

# 软链穿透检查
ls /home/bigdata/module/flink-1.20/conf/config.yaml
# 期望：能打印出文件路径，不是 No such file or directory（Flink 1.20 自带 config.yaml，不是 flink-conf.yaml）
```

### 2.2 把 5 个 Jar 拷进 Flink lib（必须放，sql-client 启动会 ClassNotFound）

> 直接用实际解压目录 `flink-1.20.5`，不依赖软链是否创建成功。

```bash
cd /home/bigdata/software
cp paimon-flink-1.20-2.0.0.jar              /home/bigdata/module/flink-1.20.5/lib/
cp paimon-flink-action-2.0.0.jar            /home/bigdata/module/flink-1.20.5/lib/
cp paimon-hive-connector-3.1-2.0.0.jar      /home/bigdata/module/flink-1.20.5/lib/
cp flink-sql-connector-mysql-cdc-3.1.1.jar  /home/bigdata/module/flink-1.20.5/lib/
cp mysql-connector-j-8.0.33.jar             /home/bigdata/module/flink-1.20.5/lib/

# 确认 5 个都在
ls -lh /home/bigdata/module/flink-1.20.5/lib | grep -E 'paimon|mysql|cdc'
```

### 2.3 把整个 `/home/bigdata/module/flink-1.20.5` + 软链同步到 master2、node1、node2

> 前提：4 台 bigdata 用户 SSH 免密已配好。

```bash
for host in master2 node1 node2; do
  echo "===== sync to $host ====="
  ssh $host "mkdir -p /home/bigdata/module"
  rsync -avz --delete /home/bigdata/module/flink-1.20.5/ $host:/home/bigdata/module/flink-1.20.5/
  ssh $host "ln -sfn /home/bigdata/module/flink-1.20.5 /home/bigdata/module/flink-1.20"
done

# 4 台 Jar 数量校验
for host in master1 master2 node1 node2; do
  echo "===== $host ====="
  ssh $host "ls /home/bigdata/module/flink-1.20.5/lib | grep -E 'paimon|mysql|cdc' | wc -l"
done
```

4 台都显示 **5** 就 OK。

---

## 3. Flink 1.20 配置（master1 改完 rsync 到其他 3 台）

> 所有文件操作统一走**实际解压目录** `/home/bigdata/module/flink-1.20.5/`；软链仅给 $FLINK_HOME 和命令行调用。
> 临时目录**必须全放** `/tmp/flink-bigdata/*`（1777 sticky bit），严禁放在 `/home/bigdata/*`（YARN Container 内部映射用户写家目录会 AccessDenied）。

### 3.0 先建 4 台机器的临时目录（/tmp 下 sticky 1777，JaasModule 必用）

> ⚠️ 残余目录属主可能不是 bigdata，导致后续 `chown 不允许的操作`，所以先 `sudo rm -rf` 清干净，再 `sudo -u bigdata` 重新建。

```bash
for host in master1 master2 node1 node2; do
  echo "===== $host ===== build /tmp/flink-bigdata (1777 sticky)"
  ssh $host "
    sudo rm -rf /tmp/flink-bigdata
    sudo -u bigdata mkdir -p /tmp/flink-bigdata/tmp /tmp/flink-bigdata/upload /tmp/flink-bigdata/web-tmp
    sudo chmod -R 1777 /tmp/flink-bigdata
    ls -ld /tmp/flink-bigdata /tmp/flink-bigdata/tmp /tmp/flink-bigdata/upload /tmp/flink-bigdata/web-tmp
  "
done
```

### 3.1 加载 HDP 自带 Hadoop/Hive 配置软链（master1 上做，后面 rsync 带过去）

```bash
cd /home/bigdata/module/flink-1.20.5/conf
ln -sfn /etc/hadoop/conf/core-site.xml   core-site.xml
ln -sfn /etc/hadoop/conf/hdfs-site.xml   hdfs-site.xml
ln -sfn /etc/hadoop/conf/yarn-site.xml   yarn-site.xml
ln -sfn /etc/hadoop/conf/mapred-site.xml mapred-site.xml
ln -sfn /etc/hive/conf/hive-site.xml     hive-site.xml

ls -lh /home/bigdata/module/flink-1.20.5/conf/*.xml
```

应该能看到 5 个软链。

### 3.2 写三套 `config.yaml`（扁平 key-value，终态 conf.clean 从这里挑一套）

> ⚠️ 三套配置三选一，别混着用，按 YARN Scheduler Avail 值选：
> - **配置 C（现在就用这个）**：每台 Avail Mem ≈ 3GB **且 Avail vCores = 1**（4 台都是 1 vCore 可用，极限压最小）
> - **配置 A（升级 2~3 vCores 后切）**：每台 Avail Mem ≈ 3GB 且 Avail vCores ≥ 2
> - **配置 B（扩容 ≥8G 4 核后切）**：每台 Avail Mem ≥ 8GB / Avail vCores ≥ 4

> ⚠️ **格式硬约束**：config.yaml 必须**全扁平 key-value**（`jobmanager.memory.process.size: 512 mb`，冒号后空格 + 数字 + 空格 + 单位），严禁 nested map；否则命令行 `-Dflat.key=v` 会触发 `YamlParserUtils.convertAndDumpYamlFromFlatMap ClassCastException`。

---

#### 配置 C — 极限丐版（单节点 3GB / 仅 1 vCore 可用，跑通优先）

```bash
cat > /home/bigdata/software/config_C.yaml << 'EOF'
# ============================================================
#  HiDataPlus HDP 3.3.2 + Paimon 2.0 — 极限丐版（扁平 key-value）
#  适用：每台 NM ~3GB / Avail vCores = 1
# ============================================================
jobmanager.rpc.address: master1
jobmanager.rpc.port: 6123
jobmanager.memory.process.size: 512 mb
jobmanager.memory.jvm-overhead.min: 32 mb
jobmanager.memory.off-heap.size: 0 mb
taskmanager.memory.process.size: 1024 mb
taskmanager.memory.jvm-overhead.min: 64 mb
taskmanager.memory.framework.off-heap.size: 64 mb
taskmanager.memory.network.min: 64 mb
taskmanager.numberOfTaskSlots: 1
parallelism.default: 2
rest.port: 8082
rest.address: master1
io.tmp.dirs: /tmp/flink-bigdata/tmp
env.hadoop.conf.dir: /etc/hadoop/conf
env.yarn.conf.dir: /etc/hadoop/conf
env.hive.conf.dir: /etc/hive/conf
state.backend: filesystem
state.checkpoints.dir: hdfs:///user/flink/checkpoints
state.savepoints.dir: hdfs:///user/flink/savepoints
state.checkpoints.num-retained: 3
yarn.application-attempts: 5
yarn.application-master.port: 0
web.submit.enable: true
web.upload.dir: /tmp/flink-bigdata/upload
web.tmpdir: /tmp/flink-bigdata/web-tmp
classloader.check-leaked-classloader: false
env.java.opts.all: -Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8
execution.checkpointing.interval: 10 min
execution.checkpointing.mode: EXACTLY_ONCE
execution.checkpointing.timeout: 20 min
execution.checkpointing.tolerable-failed-checkpoints: 10
taskmanager.memory.managed.fraction: 0.2
taskmanager.memory.network.fraction: 0.08
taskmanager.memory.jvm-overhead.fraction: 0.1
pipeline.operator-chaining: true
pipeline.name: paimon-hdp332-minimal
EOF
```

---

#### 配置 A — 小资源版（单节点 3GB / 2~3 vCores 可用）

```bash
cat > /home/bigdata/software/config_A.yaml << 'EOF'
# ============================================================
#  HiDataPlus HDP 3.3.2 + Paimon 2.0 — 小资源版（扁平 key-value）
#  适用：每台 NM ~3GB / Avail vCores = 2~3
# ============================================================
jobmanager.rpc.address: master1
jobmanager.rpc.port: 6123
jobmanager.memory.process.size: 1024 mb
jobmanager.memory.jvm-overhead.min: 64 mb
taskmanager.memory.process.size: 2048 mb
taskmanager.memory.jvm-overhead.min: 128 mb
taskmanager.memory.framework.off-heap.size: 128 mb
taskmanager.memory.network.min: 128 mb
taskmanager.numberOfTaskSlots: 2
parallelism.default: 4
rest.port: 8082
rest.address: master1
io.tmp.dirs: /tmp/flink-bigdata/tmp
env.hadoop.conf.dir: /etc/hadoop/conf
env.yarn.conf.dir: /etc/hadoop/conf
env.hive.conf.dir: /etc/hive/conf
state.backend: filesystem
state.checkpoints.dir: hdfs:///user/flink/checkpoints
state.savepoints.dir: hdfs:///user/flink/savepoints
state.checkpoints.num-retained: 5
high-availability.type: zookeeper
high-availability.zookeeper.quorum: master1:2181,master2:2181,node1:2181
high-availability.storageDir: hdfs:///user/flink/ha/
high-availability.zookeeper.path.root: /flink-1.20
yarn.application-attempts: 10
yarn.application-master.port: 0
web.submit.enable: true
web.upload.dir: /tmp/flink-bigdata/upload
web.tmpdir: /tmp/flink-bigdata/web-tmp
classloader.check-leaked-classloader: false
env.java.opts.all: -Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8
execution.checkpointing.interval: 5 min
execution.checkpointing.mode: EXACTLY_ONCE
execution.checkpointing.timeout: 15 min
execution.checkpointing.tolerable-failed-checkpoints: 5
taskmanager.memory.managed.fraction: 0.3
pipeline.operator-chaining: true
pipeline.name: paimon-hdp332-small
EOF
```

---

#### 配置 B — 生产版（单节点 ≥8GB / ≥4 vCores，以后扩容切）

```bash
cat > /home/bigdata/software/config_B.yaml << 'EOF'
# ============================================================
#  HiDataPlus HDP 3.3.2 + Paimon 2.0 — 生产版（扁平 key-value）
#  适用：每台 NM ≥8GB / Avail vCores ≥ 4
# ============================================================
jobmanager.rpc.address: master1
jobmanager.rpc.port: 6123
jobmanager.memory.process.size: 2048 mb
taskmanager.memory.process.size: 4096 mb
taskmanager.numberOfTaskSlots: 4
parallelism.default: 4
rest.port: 8082
rest.address: master1
io.tmp.dirs: /tmp/flink-bigdata/tmp
env.hadoop.conf.dir: /etc/hadoop/conf
env.yarn.conf.dir: /etc/hadoop/conf
env.hive.conf.dir: /etc/hive/conf
state.backend: filesystem
state.checkpoints.dir: hdfs:///user/flink/checkpoints
state.savepoints.dir: hdfs:///user/flink/savepoints
state.checkpoints.num-retained: 10
high-availability.type: zookeeper
high-availability.zookeeper.quorum: master1:2181,master2:2181,node1:2181
high-availability.storageDir: hdfs:///user/flink/ha/
high-availability.zookeeper.path.root: /flink-1.20
yarn.application-attempts: 10
yarn.application-master.port: 0
web.submit.enable: true
web.upload.dir: /tmp/flink-bigdata/upload
web.tmpdir: /tmp/flink-bigdata/web-tmp
classloader.check-leaked-classloader: false
env.java.opts.all: -Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8
execution.checkpointing.interval: 3 min
execution.checkpointing.mode: EXACTLY_ONCE
execution.checkpointing.timeout: 10 min
execution.checkpointing.tolerable-failed-checkpoints: 3
pipeline.operator-chaining: true
pipeline.name: paimon-hdp332-default
EOF
```

> 说明：HDP 自带 ZooKeeper 端口 2181，三台 master1/master2/node1。

### 3.3 写 YARN 提交用的 `setenv.sh`（瘦 HADOOP_CLASSPATH，禁塞 hive-client/lib/*）

```bash
cat > /home/bigdata/module/flink-1.20.5/bin/setenv.sh << 'EOF'
#!/bin/bash
# HiDataPlus HDP 3.3.2 专用：瘦 HADOOP_CLASSPATH，只 hadoop classpath + /etc/hive/conf
# 严禁 find /usr/hdp/current/hive-client/lib -name '*.jar' — 会把 HDP Hive 2.3 的 Jackson 2.6 带进来冲掉 Flink 1.20 要的 Jackson 2.15+

export HADOOP_HOME=/usr/hdp/current/hadoop-client
export HADOOP_CONF_DIR=/etc/hadoop/conf
export YARN_CONF_DIR=/etc/hadoop/conf
export HIVE_HOME=/usr/hdp/current/hive-client
export HIVE_CONF_DIR=/etc/hive/conf

export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath):$HIVE_CONF_DIR

export FLINK_ENV_JAVA_OPTS="-Dhdp.version.current=${HDP_VERSION:-3.3.2.0-013} -Dfile.encoding=UTF-8"

export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-1.8.0}
export JVM_ARGS="-Xms256m -Xmx512m -XX:+UseConcMarkSweepGC -XX:+UseCMSInitiatingOccupancyOnly -XX:CMSInitiatingOccupancyFraction=75"
EOF
chmod +x /home/bigdata/module/flink-1.20.5/bin/setenv.sh
```

### 3.4 写好 HDFS 上的目录 + 授权（必须 sudo -u hdfs，`/user` 属主 hdfs:hdfs）

```bash
sudo -u hdfs hdfs dfs -mkdir -p /user/flink/checkpoints
sudo -u hdfs hdfs dfs -mkdir -p /user/flink/savepoints
sudo -u hdfs hdfs dfs -mkdir -p /user/flink/ha
sudo -u hdfs hdfs dfs -mkdir -p /user/hive/warehouse/paimon
sudo -u hdfs hdfs dfs -mkdir -p /user/bigdata
sudo -u hdfs hdfs dfs -chown -R bigdata:hadoop /user/flink /user/hive/warehouse/paimon /user/bigdata
sudo -u hdfs hdfs dfs -chmod -R 775 /user/flink /user/hive/warehouse/paimon /user/bigdata
```

### 3.5 配置同步到 master2/node1/node2（`--delete` 强制覆盖）

```bash
for host in master2 node1 node2; do
  echo "===== sync conf / setenv to $host ====="
  rsync -avz --delete /home/bigdata/module/flink-1.20.5/conf/  $host:/home/bigdata/module/flink-1.20.5/conf/
  rsync -avz --delete /home/bigdata/module/flink-1.20.5/bin/   $host:/home/bigdata/module/flink-1.20.5/bin/
  rsync -avz /home/bigdata/software/config_{A,B,C}.yaml         $host:/home/bigdata/software/
done

# 4 台 setenv.sh 校验（瘦 classpath 没 hive-client/lib/*）
for host in master1 master2 node1 node2; do
  echo "===== $host ====="
  ssh $host "grep HADOOP_CLASSPATH= /home/bigdata/module/flink-1.20.5/bin/setenv.sh"
done
```

---

## 4. 写环境变量（所有节点 `/etc/profile.d/flink120.sh`，瘦 HADOOP_CLASSPATH + PATH 去 HDP 老 flink）

> ⚠️ `/etc/profile.d/` root 属主，用 `sudo tee`；别用 `sudo cat >`，重定向 `>` 不继承 sudo。

```bash
# 1）master1 写
sudo tee /etc/profile.d/flink120.sh << 'EOF' > /dev/null
# Flink 1.20 + HiDataPlus HDP 3.3.2
export FLINK_HOME=/home/bigdata/module/flink-1.20
export FLINK_CONF_DIR=$FLINK_HOME/conf
# PATH 顺序：我们的 Flink 1.20 放最前面，避免 HDP 自带 /usr/hdp/*/flink/bin 把 1.15 顶上来
export PATH=$FLINK_HOME/bin:$PATH

export HADOOP_HOME=/usr/hdp/current/hadoop-client
export HADOOP_CONF_DIR=/etc/hadoop/conf
export YARN_CONF_DIR=/etc/hadoop/conf
export HIVE_HOME=/usr/hdp/current/hive-client
export HIVE_CONF_DIR=/etc/hive/conf
# 瘦化：只 hadoop classpath + /etc/hive/conf；禁塞 hive-client/lib/*
export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath):$HIVE_CONF_DIR
EOF
sudo chmod 644 /etc/profile.d/flink120.sh

# 2）分发到 master2 / node1 / node2（ssh + sudo tee）
for host in master2 node1 node2; do
  echo "===== deploy env to $host ====="
  cat /etc/profile.d/flink120.sh | ssh $host "sudo tee /etc/profile.d/flink120.sh > /dev/null && sudo chmod 644 /etc/profile.d/flink120.sh"
done

# 3）4 台 source 并校验版本
for host in master1 master2 node1 node2; do
  echo "===== $host ====="
  ssh $host "source /etc/profile.d/flink120.sh && which flink && flink --version"
done
```

每台都打印 **Version: 1.20.5, Commit ID: ...** 就 OK。

---

## 5. 启动 Flink 1.20 on YARN Session（长驻）

### 5.0 终极 0→1 命令链（推荐！所有前置检查 + conf.clean 重建 + 启动一条 `&& \` 串完）

> ⚠️ 这是最干脆的一键命令，跳过了 5.1 繁琐的校验步骤。直接复制粘贴在 **master1** 上执行（按你的资源把第 2 行的 `CONFIG_LETTER=C` 改成 A/B/C 即可）。

```bash
# =====================================================
# 0→1 一键启动链（master1 上整段复制粘贴运行）
# =====================================================
export CONFIG_LETTER=C && \
export CLEAN_FLINK_CONF_DIR=/home/bigdata/module/flink-1.20.5/conf.clean && \
export FLINK_DIST=/home/bigdata/module/flink-1.20.5 && \
source /etc/profile.d/flink120.sh && \
\
echo "[1/7] 校验 PATH 指向新 Flink（不能是 HDP 1.15）" && \
test "$(which flink)" = "/home/bigdata/module/flink-1.20/bin/flink" && \
flink --version | grep -q 'Version: 1.20.5' && \
\
echo "[2/7] 清理 + 重建 conf.clean（每次都重建，避免旧缓存）" && \
rm -rf $CLEAN_FLINK_CONF_DIR && mkdir -p $CLEAN_FLINK_CONF_DIR && \
rsync -av $FLINK_DIST/conf/ $CLEAN_FLINK_CONF_DIR/ \
  --exclude='*.bak*' --exclude='flink-conf*.yaml*' --exclude='config.yaml*' && \
cp /home/bigdata/software/config_${CONFIG_LETTER}.yaml $CLEAN_FLINK_CONF_DIR/config.yaml && \
ls $CLEAN_FLINK_CONF_DIR/config.yaml && \
grep -E 'jobmanager.memory.process.size|taskmanager.memory.process.size|io.tmp.dirs' $CLEAN_FLINK_CONF_DIR/config.yaml && \
\
echo "[3/7] 4 台重建 /tmp/flink-bigdata 1777 sticky（清残余属主问题）" && \
for host in master1 master2 node1 node2; do
  ssh $host "
    sudo rm -rf /tmp/flink-bigdata
    sudo -u bigdata mkdir -p /tmp/flink-bigdata/tmp /tmp/flink-bigdata/upload /tmp/flink-bigdata/web-tmp
    sudo chmod -R 1777 /tmp/flink-bigdata
  "
done && \
\
echo "[4/7] HDFS 授权（sudo -u hdfs 写 /user 目录）" && \
sudo -u hdfs hdfs dfs -mkdir -p /user/flink/checkpoints /user/flink/savepoints /user/flink/ha /user/hive/warehouse/paimon /user/bigdata && \
sudo -u hdfs hdfs dfs -chown -R bigdata:hadoop /user/flink /user/hive/warehouse/paimon /user/bigdata && \
sudo -u hdfs hdfs dfs -chmod -R 775 /user/flink /user/hive/warehouse/paimon /user/bigdata && \
\
echo "[5/7] 瘦 HADOOP_CLASSPATH（禁 hive-client/lib/*，防 Jackson/Netty 版本冲突）" && \
export HADOOP_CLASSPATH=$(/usr/hdp/current/hadoop-client/bin/hadoop classpath):/etc/hive/conf && \
export FLINK_CONF_DIR=$CLEAN_FLINK_CONF_DIR && \
\
echo "[6/7] 前置校验：conf.clean 存在 + 内存参数真读到了" && \
test -d $FLINK_CONF_DIR && \
grep -q 'jobmanager.memory.process.size' $FLINK_CONF_DIR/config.yaml && \
\
echo "[7/7] 启动 YARN Session（-D 全连写无空格；绝对路径 bin/yarn-session.sh，不依赖软链穿透）" && \
case $CONFIG_LETTER in
  C) JM_MB=512 ; TM_MB=1024 ; SLOTS=1 ;;
  A) JM_MB=1024; TM_MB=2048 ; SLOTS=2 ;;
  B) JM_MB=2048; TM_MB=4096 ; SLOTS=4 ;;
  *) echo "CONFIG_LETTER must be C/A/B" >&2 ; exit 1 ;;
esac && \
$FLINK_DIST/bin/yarn-session.sh \
  -d \
  -jm $JM_MB \
  -tm $TM_MB \
  -s $SLOTS \
  -nm paimon-1.20 \
  -qu default \
  -Djobmanager.memory.process.size="${JM_MB} mb" \
  -Dtaskmanager.memory.process.size="${TM_MB} mb" \
  -Dtaskmanager.numberOfTaskSlots=$SLOTS \
  -Dio.tmp.dirs=/tmp/flink-bigdata/tmp \
  -Denv.java.opts.all="-Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8" \
  -Dclassloader.check-leaked-classloader=false

# 成功最后一行会打印：The Web frontend of the YARN session cluster is located at: http://master1:8082
```

### 5.1 三套启动命令（与 3.2 配置严格对齐；前置 conf.clean、/tmp、HDFS 授权 5.0 已做完的话，这三条只保留提交部分）

> ⚠️ **操作约束**：所有提交统一在 **master1** 上跑；`-D` 全连写无空格；`FLINK_CONF_DIR` 显式指向 `conf.clean`。

#### 命令 C — 极限丐版（配置 C：JM 512M / TM 1G / 1 slot）

```bash
source /etc/profile.d/flink120.sh
export CLEAN_FLINK_CONF_DIR=/home/bigdata/module/flink-1.20.5/conf.clean
export FLINK_CONF_DIR=$CLEAN_FLINK_CONF_DIR
export HADOOP_CLASSPATH=$(/usr/hdp/current/hadoop-client/bin/hadoop classpath):/etc/hive/conf

/home/bigdata/module/flink-1.20.5/bin/yarn-session.sh \
  -d -jm 512 -tm 1024 -s 1 -nm paimon-1.20 -qu default \
  -Djobmanager.memory.process.size="512 mb" \
  -Dtaskmanager.memory.process.size="1024 mb" \
  -Dtaskmanager.memory.managed.fraction=0.2 \
  -Dtaskmanager.memory.network.fraction=0.08 \
  -Dtaskmanager.memory.jvm-overhead.fraction=0.1 \
  -Dio.tmp.dirs=/tmp/flink-bigdata/tmp \
  -Denv.java.opts.all="-Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8" \
  -Dclassloader.check-leaked-classloader=false
```

#### 命令 A — 小资源版（配置 A：JM 1G / TM 2G / 2 slot）

```bash
source /etc/profile.d/flink120.sh
export CLEAN_FLINK_CONF_DIR=/home/bigdata/module/flink-1.20.5/conf.clean
export FLINK_CONF_DIR=$CLEAN_FLINK_CONF_DIR
export HADOOP_CLASSPATH=$(/usr/hdp/current/hadoop-client/bin/hadoop classpath):/etc/hive/conf

/home/bigdata/module/flink-1.20.5/bin/yarn-session.sh \
  -d -jm 1024 -tm 2048 -s 2 -nm paimon-1.20 -qu default \
  -Djobmanager.memory.process.size="1024 mb" \
  -Dtaskmanager.memory.process.size="2048 mb" \
  -Dtaskmanager.memory.managed.fraction=0.3 \
  -Dio.tmp.dirs=/tmp/flink-bigdata/tmp \
  -Denv.java.opts.all="-Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8" \
  -Dclassloader.check-leaked-classloader=false
```

#### 命令 B — 生产版（配置 B：JM 2G / TM 4G / 4 slot）

```bash
source /etc/profile.d/flink120.sh
export CLEAN_FLINK_CONF_DIR=/home/bigdata/module/flink-1.20.5/conf.clean
export FLINK_CONF_DIR=$CLEAN_FLINK_CONF_DIR
export HADOOP_CLASSPATH=$(/usr/hdp/current/hadoop-client/bin/hadoop classpath):/etc/hive/conf

/home/bigdata/module/flink-1.20.5/bin/yarn-session.sh \
  -d -jm 2048 -tm 4096 -s 4 -nm paimon-1.20 -qu default \
  -Djobmanager.memory.process.size="2048 mb" \
  -Dtaskmanager.memory.process.size="4096 mb" \
  -Dio.tmp.dirs=/tmp/flink-bigdata/tmp \
  -Denv.java.opts.all="-Djava.io.tmpdir=/tmp/flink-bigdata/tmp -Dfile.encoding=UTF-8" \
  -Dclassloader.check-leaked-classloader=false
```

### 5.2 Flink Web UI 检查

```text
浏览器打开：http://master1:8082
```

- Task Managers Tab：至少 2 台 TM；
- Slots Tab：丐版总 Slots ≥ 3（3 台 × 1），A 版 ≥ 4（2 台 × 2），B 版 ≥ 8；
- Job 页空 → 正常。

### 5.3 进入 Flink SQL Client（连 YARN Session）

```bash
source /etc/profile.d/flink120.sh
export CLEAN_FLINK_CONF_DIR=/home/bigdata/module/flink-1.20.5/conf.clean
export FLINK_CONF_DIR=$CLEAN_FLINK_CONF_DIR
$FLINK_HOME/bin/sql-client.sh embedded -s yarn-session
```

出现大绿色 `Flink SQL>` 就 OK。ClassNotFound 回 2.2；hdfs:// scheme 找不到回 3.1 + 3.3。

---

## 6. Paimon Quick-Start Hello World（复制粘贴一条一条执行）

> 全在 `Flink SQL>` 里跑，分 6 步。

### 6.1 SET 全局参数

```sql
SET 'execution.checkpointing.interval' = '3min';
SET 'execution.checkpointing.mode'      = 'EXACTLY_ONCE';
SET 'sink.use-managed-memory-allocator' = 'true';
SET 'sink.managed.writer-buffer-memory' = '256M';
SET 'sql-client.execution.result-mode' = 'tableau';
```

### 6.2 创建 Paimon Catalog（复用 HDP HMS，master1:9083）

```sql
CREATE CATALOG paimon WITH (
  'type'            = 'paimon',
  'metastore'       = 'hive',
  'uri'             = 'thrift://master1:9083',
  'warehouse'       = 'hdfs:///user/hive/warehouse/paimon',
  'hive-conf-dir'   = '/etc/hive/conf',
  'hadoop-conf-dir' = '/etc/hadoop/conf'
);

USE CATALOG paimon;
CREATE DATABASE IF NOT EXISTS demo;
USE demo;

SHOW DATABASES;
```

### 6.3 建 Paimon 主键表 word_count

```sql
CREATE TABLE word_count (
  word STRING,
  cnt  BIGINT,
  PRIMARY KEY (word) NOT ENFORCED
) WITH (
  'bucket'             = '1',
  'changelog-producer' = 'input'
);

SHOW TABLES;
DESC word_count;
```

### 6.4 开流作业：datagen 随机单词 → Paimon

```sql
CREATE TEMPORARY TABLE datagen_word (
  word STRING
) WITH (
  'connector' = 'datagen',
  'rows-per-second'    = '1000',
  'fields.word.length' = '1'
);

SET 'pipeline.name' = 'paimon_quickstart_wordcount_write';
INSERT INTO word_count
SELECT word, COUNT(*) AS cnt
FROM datagen_word
GROUP BY word;
```

到 Flink Web UI http://master1:8082 看作业 Running，连续 3 个 CP 成功 → 写通路 OK。

### 6.5 批读 Paimon 表验证

```sql
RESET 'execution.checkpointing.interval';
SET 'execution.runtime-mode' = 'batch';

SELECT * FROM word_count ORDER BY cnt DESC LIMIT 20;
```

能看到 20 行结果 → **Paimon 2.0 + Flink 1.20 + HDP 3.3.2 全链路通了**。

### 6.6 退出 SQL Client + 停 demo 作业（可选）

```text
Flink SQL> EXIT;
```

Flink Web UI 里 Cancel 掉 `paimon_quickstart_wordcount_write`。跑真实湖仓分层跳到 [湖仓一体案例.md](./湖仓一体案例.md)。

---

## 7. StreamPark 2.2.x 独立安装 + 提交 Paimon 作业（推荐）

> 推荐**独立安装** StreamPark 2.2.x 到 `/home/bigdata/module/streampark`，端口 **10001**；不要用 Ambari 自带的 10000（版本老且依赖 Ambari 升级）。
> 路线二选一：
> - **路线 A（推荐）**：走 7.0 独立安装 → 7.1 起
> - **路线 B**：用 Ambari 自带 → 直接跳到 7.1，所有端口 10001 → 10000

### 7.0 下载安装 StreamPark（独立，master1）

#### 7.0.1 下包（master1 `/home/bigdata/software`）

```bash
cd /home/bigdata/software

# ① MySQL Driver（复用 1.4 已下的）
ls mysql-connector-j-8.0.33.jar || \
  wget -c https://repo.maven.apache.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar -O mysql-connector-j-8.0.33.jar

# ② StreamPark 2.2.0
wget -c https://mirrors.huaweicloud.com/apache/streampark/2.2.0/apache-streampark_2.12-2.2.0-bin.tar.gz -O apache-streampark_2.12-2.2.0-bin.tar.gz
# 兜底 1：阿里云
# wget -c https://mirrors.aliyun.com/apache/streampark/2.2.0/apache-streampark_2.12-2.2.0-bin.tar.gz -O apache-streampark_2.12-2.2.0-bin.tar.gz
# 兜底 2：Apache 归档
# wget -c https://archive.apache.org/dist/streampark/2.2.0/apache-streampark_2.12-2.2.0-bin.tar.gz -O apache-streampark_2.12-2.2.0-bin.tar.gz

ls -lh /home/bigdata/software | grep -E 'apache-streampark|mysql-connector-j'
```

#### 7.0.2 解压 + 软链 + 拷 MySQL Driver

```bash
mkdir -p /home/bigdata/module
cd /home/bigdata/software
tar -zxf apache-streampark_2.12-2.2.0-bin.tar.gz -C /home/bigdata/module/
ln -sfn /home/bigdata/module/apache-streampark_2.12-2.2.0 /home/bigdata/module/streampark

cp /home/bigdata/software/mysql-connector-j-8.0.33.jar /home/bigdata/module/streampark/lib/
ls -lh /home/bigdata/module/streampark/lib/mysql-connector-j-8.0.33.jar
```

#### 7.0.3 在 master1 MySQL 给 StreamPark 建库 + 用户

```sql
mysql -uroot -p123456
```

```sql
CREATE DATABASE IF NOT EXISTS streampark DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'streampark'@'%'       IDENTIFIED BY 'Streampark@123456';
GRANT ALL PRIVILEGES ON streampark.* TO 'streampark'@'%' WITH GRANT OPTION;
CREATE USER IF NOT EXISTS 'streampark'@'localhost' IDENTIFIED BY 'Streampark@123456';
GRANT ALL PRIVILEGES ON streampark.* TO 'streampark'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

#### 7.0.4 改 StreamPark Console 配置：端口 10001 + MySQL

```bash
cd /home/bigdata/module/streampark/conf
cp application.yml application.yml.bak

cat > application.yml << 'EOF'
server:
  port: 10001
  servlet:
    context-path: /
  compression:
    enabled: true
    mime-types: application/javascript,application/json,application/xml,text/html,text/xml,text/plain,text/css,image/*

spring:
  profiles:
    active: mysql
  servlet:
    multipart:
      max-file-size: 500MB
      max-request-size: 500MB
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://master1:3306/streampark?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true
    username: streampark
    password: Streampark@123456
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: GMT+8

mybatis-plus:
  mapper-locations: classpath:mapper/*Mapper.xml
  type-aliases-package: org.apache.streampark.console.*.entity
  configuration:
    map-underscore-to-camel-case: true
    cache-enabled: false
    call-setters-on-nulls: true
    jdbc-type-for-null: 'null'

streampark:
  console:
    auth:
      ttl: 12h
  home: ${STREAMPARK_HOME:/home/bigdata/module/streampark}
EOF
```

#### 7.0.5 启动 StreamPark Console（首次自动建表）

```bash
source /etc/profile.d/flink120.sh
export HADOOP_HOME=/usr/hdp/current/hadoop-client
export HADOOP_CONF_DIR=/etc/hadoop/conf
export HIVE_CONF_DIR=/etc/hive/conf
export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath):$HIVE_CONF_DIR
export FLINK_HOME=/home/bigdata/module/flink-1.20
export STREAMPARK_HOME=/home/bigdata/module/streampark

cd /home/bigdata/module/streampark/bin
bash startup.sh
```

等 30~60 秒：

```text
http://master1:10001
账号：admin
密码：streampark（首次登录强制改强密码，例如 Admin123456!）
```

> 停：`cd /home/bigdata/module/streampark/bin && bash shutdown.sh`
> 日志：`tail -100f /home/bigdata/module/streampark/logs/console.out`

---

### 7.1 登录 StreamPark Console

- 独立版：http://master1:10001
- Ambari 自带：http://master1:10000
- 账号 `admin` / 初始密码 `streampark`

### 7.2 Settings → Flink Home 登记 Flink 1.20

左侧：**Settings → Flink Home → New**

| 字段 | 填法 |
|---|---|
| Flink Home Name | `Flink 1.20 Paimon` |
| Flink Home Path | `/home/bigdata/module/flink-1.20`（软链路径）|
| Flink Version | 选 `1.20`，没有就写 `1.20.0` |
| 备注 | Paimon 2.0 专用 |

Save → Sync → 绿色对勾。

### 7.3 Resource Center → Cluster 添加 YARN Session

左侧：**Resource Center → Cluster → New Cluster**

| 字段 | 填法 |
|---|---|
| Cluster Name | `paimon-yarn-session` |
| Execution Mode | `YARN Session` |
| Yarn Queue | `default` |
| 集群地址 | 空（自动读 yarn-site.xml）|
| Flink 版本 | 选 7.2 的 `Flink 1.20 Paimon` |
| Yarn Session Name | `paimon-1.20`（与 5.0/5.1 `-nm` 对齐，自动 Attach）|

Save → Check Status → 绿色 **Running**。

### 7.4 上传 Paimon Jar 到 Resource Center → Upload

把 `/home/bigdata/module/flink-1.20.5/lib` 下 5 个 Jar 全传：
- `paimon-flink-1.20-2.0.0.jar`
- `paimon-flink-action-2.0.0.jar`
- `paimon-hive-connector-3.1-2.0.0.jar`
- `flink-sql-connector-mysql-cdc-3.1.1.jar`
- `mysql-connector-j-8.0.33.jar`（可选）

### 7.5 新建 Flink SQL 作业（示例：paimon_quickstart_wordcount_write）

左侧：**Application → New Application**

| 字段 | 填法 |
|---|---|
| Execution Mode | **Flink SQL** |
| Flink Cluster | 7.3 的 `paimon-yarn-session` |
| Flink Version | `Flink 1.20 Paimon` |
| SQL 内容 | 6.1 ~ 6.4 所有 SQL（SET + CREATE CATALOG + CREATE DATABASE + CREATE TABLE + CREATE TEMP TABLE + INSERT INTO）完整粘进去 |
| Dependencies | 勾选 7.4 上传的 Paimon 4 个 Jar |
| Checkpoint Interval | `180000`（毫秒） |
| Savepoint Strategy | `LATEST` |
| Parallelism | `4`（丐版写 `2`） |
| 告警通知（可选）| 钉钉 Webhook |

Save → **Launch** → Flink Web UI `http://master1:8082` 看作业 Running + StreamPark 列表绿 → **全链路通**。

---

## 8. 常见坑速查（按实际踩坑顺序，每行现象 / 根因 / 修法）

| # | 现象 | 根因 90% | 马上跑的修法 |
|---|---|---|---|
| 1 | `wget https://.../flink-1.20.0-... 403 Forbidden`（清华 TUNA） | Flink 1.20.0 已下架 | 统一升级到 **1.20.5**，用华为云 / 阿里云镜像（1.2 节三条，第一条首选） |
| 2 | `wget paimon-hive-3.1-2.0.0.jar 404` 或 `flink-connector-mysql-cdc-3.1.0 (com.ververica) 404` | ① artifactId 少写了 `connector-` 前缀（正确：`paimon-hive-connector-3.1`）<br />② CDC 3.0+ 已捐 Apache，groupId 应 `org.apache.flink`，SQL 用 fat jar 带 `sql-` 前缀（正确：`flink-sql-connector-mysql-cdc-3.1.1.jar`） | 1.3 节四条 wget 全量重跑；artifactId 严格抄前置常量区 |
| 3 | `mkdir: 无法创建目录"/data1": 权限不够` | `/data1` root 属主 755，普通用户不能写 | 临时目录**统一全迁** `/tmp/flink-bigdata/*`（1777 sticky bit），跑 3.0 节 for 循环；严禁再用 `/data1` 或 `/home/bigdata/flink` |
| 4 | 写 `/etc/profile.d/flink120.sh` 报 `权限不够` / `sudo cat > /etc/profile.d/...` 还是权限不够 | `/etc/profile.d/` root 属主；`sudo cat > file` 的重定向 `>` 不继承 sudo | 用 `sudo tee << 'EOF' > /dev/null` 写法（4 节已写好）；分发用 `cat 文件 \| ssh host 'sudo tee 目标 > /dev/null'` |
| 5 | `JaasModule NoSuchFileException: /home/bigdata/flink`（YARN AM Container 启动时） | Flink JaasModule 写 jaas 临时文件用 `Path.toRealPath()` —— **父目录必须存在**；且 `/home/bigdata/` 是 700，YARN NM 映射用户和家目录属主不一致会炸 | ① 临时目录全迁 `/tmp/flink-bigdata/*`（3.0 节 1777）；② `env.java.opts.all` 显式 `-Djava.io.tmpdir=/tmp/flink-bigdata/tmp`；③ `io.tmp.dirs` 必须对齐同一目录 |
| 6 | `IllegalConfigurationException: Total Flink Memory (64MB) < Off-heap Memory (128MB)`（反复出现） | 四层叠加：<br />① 软链 `flink-1.20` 断了 → Flink 读默认空值<br />② PATH 被 HDP 自带 `/usr/hdp/*/flink/bin` 覆盖 → 实际跑 1.15<br />③ `-D key=value`（带空格）被 JCommander 整参数丢弃<br />④ **终极大坑**：Flink 1.20 默认配置文件已从 `flink-conf.yaml` 升级为**扁平 `config.yaml`**，我们一直写的 flink-conf 根本不被读；且如果 config.yaml 用 nested map（`a:\n  b: v`）和 -D 扁平 key 混用 → 触发 `ClassCastException String cannot cast to Map @ YamlParserUtils.convertAndDumpYamlFromFlatMap` | **按顺序修**：<br />① `ln -sfn /home/bigdata/module/flink-1.20.5 /home/bigdata/module/flink-1.20`<br />② `which flink` 必须指向 1.20（不是 HDP 1.15）→ `source /etc/profile.d/flink120.sh`<br />③ `-D` 全**连写无空格** `-Dkey=value`<br />④ 统一用 `conf.clean/config.yaml`（**全扁平 key-value**，禁 nested map）→ 直接跑 **5.0 终极 0→1 链**（会重建 conf.clean，100% 绕开这个坑） |
| 7 | `ClassCastException: class java.lang.String cannot be cast to class java.util.Map` @ `YamlParserUtils.convertAndDumpYamlFromFlatMap` | config.yaml 写了 nested map（如 `jobmanager:\n  memory:\n    process.size: 512`），但命令行 -D 是扁平 key；两者互相转换时炸 | config.yaml 强制**全扁平 key-value**（`jobmanager.memory.process.size: 512 mb`），与 -D 格式完全一致；跑 5.0 时 config_*.yaml 已按扁平写好 |
| 8 | `AccessControlException: user=bigdata access=WRITE inode="/user":hdfs:hdfs:drwxr-xr-x` | HDFS `/user` 属主 hdfs:hdfs，普通用户不能 mkdir | 一律 `sudo -u hdfs hdfs dfs -mkdir -p ...` + `chown -R bigdata:hadoop ...`（3.4 节和 5.0 [4/7] 已内置） |
| 9 | YARN AM FAILED exitCode:1，`prelaunch.err Last 4096 bytes:` 整段为空（尾部没堆栈） | YARN Diagnostics 只截尾部 4KB；真实堆栈在 stderr/syslog 的头部 / 中部；或者直接上 NM 本地容器目录 | `yarn logs -applicationId APP_ID -am ALL 2>&1 | grep -A 40 -E 'Error|Exception|ClassNotFound'`；没开日志聚合就上对应 NM 看 `/hadoop/yarn/local/usercache/bigdata/appcache/APP_ID/container_*/stderr`；90% 根因是 **ClassNotFound（胖 HADOOP_CLASSPATH 带了 hive-client/lib 老 Jackson/Netty）** 或 **Jaas AccessDenied（家目录写不了）** |
| 10 | `JaasModule AccessDeniedException: /tmp/flink-bigdata/tmp/jaas-*.conf`（Container 内部）或 `/tmp/flink-bigdata chown: 不允许的操作` | ① `/tmp/flink-bigdata` 残余目录是**之前其他进程/root 创建的**，属主不是 bigdata，bigdata 自己 `chown` 被拒<br />② Container 映射用户 ≠ bigdata，写家目录 700 必炸 | 每次启动前**先清残余再重建**（5.0 [3/7] 已内置）：`sudo rm -rf /tmp/flink-bigdata && sudo -u bigdata mkdir -p ... && sudo chmod -R 1777 /tmp/flink-bigdata`（1777 sticky bit：任何用户可写自己的文件但不能删别人的，完美适配 YARN 任意映射用户） |
| 11 | `SLF4J Reconfiguration failed: No configuration found for 'xxx' in 'null'` 紧接着 `RuntimeException: The configuration directory '.../conf.clean' does not exist` | 启动时直接指定了 `FLINK_CONF_DIR=conf.clean`，但跳过了「建 conf.clean + rsync 原 conf 的 log4j/logback/config.yaml」步骤 | 不要跳步骤，直接跑 **5.0 终极 0→1 链**，[2/7] 段会先 `rm -rf conf.clean && mkdir && rsync 原 conf（除 flink-conf*）&& cp config_*.yaml → config.yaml`，全链路闭环 |
| 12 | `flink --version` 还是 `1.15`（HDP 自带）或 `which flink` 指向 `/usr/hdp/.../flink/bin/flink` | HDP 自带 `/usr/hdp/current/flink/bin` 在 PATH 前面；或者 `/etc/profile.d/flink120.sh` 没 source | ① `/etc/profile.d/flink120.sh` 必须写 `export PATH=$FLINK_HOME/bin:$PATH`（$FLINK_HOME 放最前）（4 节已内置）<br />② 每次手动跑脚本前 `source /etc/profile.d/flink120.sh`（5.0 [1/7] 已校验） |
