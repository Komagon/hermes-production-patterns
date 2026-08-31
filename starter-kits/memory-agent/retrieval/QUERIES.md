# 召回查询清单

> 预定义的召回查询。检索时从这里选,不临场发挥整层倾倒。
> 格式:每条查询 = 用途 + 查询词 + 目标层 + 返回上限。

## 查询模板

```yaml
- id: q-001
  purpose: 任务开始前召回相关历史经验
  terms: ["<任务关键词>", "<领域词>"]
  layers: [experience, long-term]
  limit: 5
- id: q-002
  purpose: 写入前查重,避免重复条目
  terms: ["<新条目关键词>"]
  layers: [long-term]
  limit: 3
- id: q-003
  purpose: 复盘时召回本周 working 层条目
  terms: ["<本周任务主题>"]
  layers: [working]
  limit: 20
```

## 纪律

- 每次召回只打目标层,不跨全库
- 返回超限时按相关性截断,不全部进上下文
- 召回结果附带来源;来源失效 → 记入复盘淘汰清单
