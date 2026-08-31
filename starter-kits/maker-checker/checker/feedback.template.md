# FAIL 反馈模板(压缩反馈)

> Checker 复制本模板填写。只写定位信息与原因,不复述产出全文——错误全文会炸 Maker 的上下文。

```text
VERDICT: FAIL
SCHEMA:  <缺失字段/类型错误清单,无则写 N/A>
RED-FLAGS: <命中的红线编号与内容,无则写 N/A>
ISSUES:
  1. [位置: <字段名/行号/段落>] 问题: <一句话原因> 期望: <应当是什么>
  2. ...
LIMIT: 本轮为第 <N> 次修订(上限 2),超限升级人工。
```

## 示例

```text
VERDICT: FAIL
SCHEMA:  缺 evidence[].source
RED-FLAGS: RF-2(引用来源未核实)
ISSUES:
  1. [位置: 第 3 节表 2] 问题: 用户数 1200 万无来源 期望: 补充可核实的引用或删除
LIMIT: 本轮为第 1 次修订(上限 2),超限升级人工。
```
