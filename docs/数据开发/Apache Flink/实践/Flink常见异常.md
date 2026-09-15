---
sidebar_position: 14
sidebar_label: Flink常见异常
---

## Could not forward element to next operator

看下下游的算子是不是报错了。

## /libtensorflow_jni.so: libtensorflow_framework.so.1: 无法打开共享对象文件: 没有那个文件或目录

### 旧版本

> https://www.tensorflow.org/install/lang_java_legacy?hl=zh-cn

```
#LD_LIBRARY_PATH是tensorflow的依赖,就是官网需要配置第三方依赖的包路径
export LD_LIBRARY_PATH=/data/app/flink-1.18.1/ini

java -jar  frauddetection-0.1.jar
```

可能会遇到的错误

> https://www.jianshu.com/p/5eee15182ff6

> https://www.imqianduan.com/linux/gcc-update-libstdc.html

```
编译程序或运行程序时，出现类似/usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.21’ not found的报错。

这是因为升级gcc时，生成的动态库没有替换老版本gcc的动态库，将gcc最新版本的动态库替换掉老版本的动态库即可。

```

```
(base) [bin]$ strings /usr/lib64/libstdc++.so.6 | grep GLIBCXX
GLIBCXX_3.4
GLIBCXX_3.4.1
GLIBCXX_3.4.2
GLIBCXX_3.4.3
GLIBCXX_3.4.4
GLIBCXX_3.4.5
GLIBCXX_3.4.6
GLIBCXX_3.4.7
GLIBCXX_3.4.8
GLIBCXX_3.4.9
GLIBCXX_3.4.10
GLIBCXX_3.4.11
GLIBCXX_3.4.12
GLIBCXX_3.4.13
GLIBCXX_3.4.14
GLIBCXX_3.4.15
GLIBCXX_3.4.16
GLIBCXX_3.4.17
GLIBCXX_3.4.18
GLIBCXX_3.4.19
GLIBCXX_DEBUG_MESSAGE_LENGTH
```

### 新版本

> https://www.tensorflow.org/install/lang_java?hl=zh-cn

## Cannot find TensorFlow native library for OS: linux, architecture: x86_64

引入依赖的问题，使用下面的libtensorflow替换成tensorflow就行了
```
		<dependency>
			<groupId>org.tensorflow</groupId>
			<artifactId>libtensorflow</artifactId>
			<version>1.15.0</version>
		</dependency>
```
```
		<dependency>
			<groupId>org.tensorflow</groupId>
			<artifactId>tensorflow</artifactId>
			<version>1.15.0</version>
		</dependency>
```

## 查看taskmanage的历史日志
```
http://offline-011.ld-hadoop.com（替换host）:8042/node/containerlogs/container_e57_1726053181591_1704160_01_000443(替换容器id)/hive/taskmanager.log/?start=0
```

##
```
历史日志 - 任务已经失败
需要通过 Yarn 的日志归档来查看
任务正常启动的 TM 日志可以通过 WebUI 来查看，在任务失败之后， TM 日志需要自己组装URL来查看。
在 JM 日志中找到对应 TM 的 container ID 和所在的机器信息

1) 在 Yarn Web 点击 logs 会默认打开 JM 的日志.
http://hd-102.ld-hadoop.com:19888/jobhistory/logs/hd-114.ld-hadoop.com:8041/container_e10_1625910636054_4731_01_000001/container_e10_1625910636054_4731_01_000001/root/jobmanager.log/?start=0

hd-114.ld-hadoop.com : 宿主机节点

可在JM日志中搜索 :TaskExecutor container_e14_1660342938023_5269_01_000002 will be started on hd-114.ld-hadoop.com

container_e10_1625910636054_4731_01_000001 : Container ID

2) 在 JM 的日志中找到运行的 TM 的 宿主机节点 和 Container ID（※TM会有多个）
Registering TaskManager with ResourceID container_e10_1625910636054_4731_01_000002 (akka.tcp://flink@hd-124.ld-hadoop.com:43958/user/rpc/taskmanager_0) at ResourceManager

宿主机节点  : hd-124.ld-hadoop.com

Container ID : container_e10_1625910636054_4731_01_000002 

3) 替换JM日志链接中的 宿主机节点 、Container ID、jobmanager → taskmanager
http://hd-102.ld-hadoop.com:19888/jobhistory/logs/hd-124.ld-hadoop.com:8041/container_e10_1625910636054_4731_01_000002/container_e10_1625910636054_4731_01_000002/root/taskmanager.log

4) 打开替换完的链接就是TM的日志


※ 单个日志文件过大，导致打开缓慢或者浏览器卡死，可以通过 ?start=1212&end=1314 来控制日志打开的大小, url/taskmanager.log?start=1212&end=1314



任务运行中
Flink UI 正常的情况，在 Flink UI 内打开 jobmanager 日志，找到对应 taskmanager container 所在的节点
TaskExecutor container_e27_1699498988019_25512_01_000011 will be started on hd-183.ld-hadoop.com

替换下面的 host 和 container id 编辑网址为：

http://hd-183.ld-hadoop.com:8042/node/containerlogs/container_e27_1699498988019_25512_01_000011/hive/

Flink UI 异常的情况
由于任务启动失败，导致 Flink UI 不能正常打开日志，直接在 yarn 搜索当前任务名，通过 yarn 打开 jobmanger 日志，在日志中找到 上面一样的 taskmanager 所在的节点，使用类似的链接打开。



E.G.

http://hd-119.ld-hadoop.com:8042/node/containerlogs/container_e14_1660342938023_5177_01_000001/hive/
```

## 关联广播表异常
> 在有关联广播表的时候，有sink到下游kafka的任务，比如在关联广播表后面，不然会报错。