---
sidebar_position: 21
sidebar_label: FlinkSQL状态越来越多,怎么办
---

在上一篇文章中，介绍了 Flink State TTL 机制，这项机制对于应对通用的状态暴增特别有效。然而，这个特性也有其缺陷，**例如不能保证一定可以及时清理掉失效的状态，以及目前仅支持 Processing Time 时间模式等等**，另外对于旧版本的 Flink（1.6 之前），State TTL 功能也无法使用。

**针对 Table API 和 SQL 模块的持续查询/聚合语句，Flink 还提供了另一项失效状态清理机制，这就是本文要提到的 Idle State Retention Time 选项**，Flink 很早就提供了这个选项，该特性是借助 Query Configuration 配置项来定义的，但很多人并未启用，也不理解其中隐藏的暗坑。本文将对这一特性做说明，并给出一些使用建议。

## 问题引入

同样以官网文档的案例为起点，这是一个持续查询的 GROUP BY 语句，它没有时间窗口的定义，理论上会无限地计算下去：
```sql
SELECT sessionId, COUNT(*) FROM clicks GROUP BY sessionId;
```

这就带来了一个问题：随着时间的不断推进，**内存中积累的状态会越来越多，因为数据流是无穷无尽、持续流入的，Flink 并不知道如何丢弃旧的数据**。在这种情况下，如果放任不管，那么迟早有一天作业的状态数达到了存储系统的容量极限，从而造成作业的崩溃。

针对这个问题，Flink 提出了空闲状态保留时间（Idle State Retention Time）的概念。**通过为每个状态设置 Timer，如果这个状态中途被访问过，则重新设置 Timer；否则（如果状态一直未被访问，长期处于 Idle 状态）则在 Timer 到期时做状态清理**。这样，就可以确保每个状态都能得到及时的清理。

通过调用 StreamQueryConfig 的 withIdleStateRetentionTime 方法，可以为这个 QueryConfig 对象设置最小和最大的清理周期。这样，Flink 可以保证最早和最晚的状态清理时间。

需要注意的是，旧版本 Flink 允许只指定一个参数，表示最早和最晚清理周期相同，但是这样可能会导致同一时间段有很多状态都到期，从而造成瞬间的处理压力。新版本的 Flink 要求两个参数之间的差距至少要达到 5 分钟，从而避免大量状态瞬间到期，对系统造成的冲击。

```sql
StreamQueryConfig qConfig = ...

// set idle state retention time: min = 12 hours, max = 24 hours
qConfig.withIdleStateRetentionTime(Time.hours(12), Time.hours(24));
```

这里需要注意一点，默认情况下 StreamQueryConfig 的设置并不是全局的。因此当设置了清理周期以后，需要在 StreamTableEnvironment 类调用 toAppendStream 或 toRetractStream 将 Table 转为 DataStream 时，显式传入这个 QueryConfig 对象作为参数，才可以令该功能生效。

新版本的 Flink 提供了一个 QueryConfigProvider 类（它实现了 PlannerConfig 接口，允许嵌入一个 StreamQueryConfig 对象），可以通过对 TableConfig 设置 PlannerConfig 的方式（调用 addPlannerConfig 方法），来传入设置好 StreamQueryConfig 对象的 QueryConfigProvider.  这样，当 StreamPlanner 将定义的 Table 翻译为 Plan 时，可以自动使用之前定义的 StreamQueryConfig，从而实现全局的 StreamQueryConfig 设定。对于旧的 Flink 版本，只能通过修改源码的方式来设置，较为繁琐。

## 实现方式

Idle State Retention Time 的代码完全位于 flink-table 相关模块下，因此只有 Table API / SQL 的编程方式才可以用到这个特性。

具体来说，在 org.apache.flink.table.plan.nodes.datastream 包下，有三个类：DataStreamGroupAggregateBase（对应无时间窗口限定的 GROUP BY 语句）、DataStreamGroupWindowAggregateBase（对应有时间窗口限定的 GROUP BY 语句）、DataStreamOverAggregate（对应 OVER 语句）。当调用这三个类的 translateToPlan 方法时，如果没有指定 Idle State Retention Time，则会打印一行 WARNING 级别的日志，表明状态会无限增长。

而在 org.apache.flink.table.runtime.aggregate 包下，Flink 定义了名为 CleanupState 的 Scala Trait， 代码如下：

```java
trait CleanupState {

  def registerProcessingCleanupTimer(
      cleanupTimeState: ValueState[JLong],  // 上次注册的 Timer 时间戳
      currentTime: Long,                    // 当前时间戳
      minRetentionTime: Long,               // 空闲状态最短保留时间
      maxRetentionTime: Long,               // 空闲状态最长保留时间
      timerService: TimerService): Unit = {

    // 获取本状态上次注册的 Timer 时间戳
    val curCleanupTime = cleanupTimeState.value()

    // 检查是否注册过清理的 Timer, 如果注册过则检查是否还未到期
    if (curCleanupTime == null || (currentTime + minRetentionTime) > curCleanupTime) {
      // 如果没有注册过 Timer, 或者注册过但是还没到期, 那就更新一个新的 Timer
      val cleanupTime = currentTime + maxRetentionTime
      timerService.registerProcessingTimeTimer(cleanupTime)
      // 删除旧的 Timer
      if (curCleanupTime != null) {
        timerService.deleteProcessingTimeTimer(curCleanupTime)
      }
      cleanupTimeState.update(cleanupTime)
    }
  }
}
```

可以看到，在新版本的 Flink 内部实现中，Timer 的时间戳也是作为一种 ValueState 来保存的，这样可以和其他的 Keyed 状态一起，统一管理。同时也能得到 Flink 刷新时间戳的逻辑。

从 Flink 的实现原理上我们知道，对于 KeyedProcessFunction，都有一个 

```java
public void onTimer(long timestamp, OnTimerContext ctx, Collector<O> out) throws Exception {}
```

> https://cloud.tencent.com/developer/article/1452854