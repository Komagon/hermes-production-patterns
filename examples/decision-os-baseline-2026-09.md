# 决策契约实测基线（2026-09-30）

> 本文件是 [`conventions/decision-contract.md`](../conventions/decision-contract.md) 的**验证案例**：不是描述「应该怎么做」，而是把**真实跑出来的输出**留在这里当证据锚点。
> 所有数字来自 `hermes-decision eval <id> --fresh`（`--fresh` = 绕过 replay，重新问后端），数据集在 `~/.hermes/decision-os/datasets/`。

## 复现步骤

```bash
# 1. 列决策与后端可用性
hermes-decision list
hermes-decision doctor          # 期望 backends_available 里 rule/cache/local/jev/llm/human 全 true

# 2. 跑离线评测（--fresh 重新问后端；不带 --fresh 走 replay，用于稳定回归）
hermes-decision eval task.complete --fresh

# 3. 看收据里的降级轨迹（审计用）
hermes-decision receipts --days 1
hermes-decision metrics
```

## 8 个决策的真实基线

| decision | type | n | accuracy | accuracy_answered | 差一档内 | 弃权率 | 备注 |
|:---|:---|---:|---:|---:|---:|---:|:---|
| intent.route | choice | 26 | 1.000 | 1.000 | – | 0.000 | 确定性打分 26/26 |
| context.select | choice | 12 | 1.000 | 1.000 | – | 0.000 | |
| tool.route | choice | 3 | 1.000 | 1.000 | – | 0.000 | |
| task.complete | noul | 13 | 1.000 | 1.000 | – | 0.000 | 规则 4 + 模型 9 |
| retry.should | noul | 12 | 1.000 | 1.000 | – | 0.000 | 修完置信度语义后 |
| human.escalate | noul | 12 | 0.917 | **1.000** | – | 0.083 | 唯一未命中是弃权 |
| task.complexity | score | 8 | 0.750 | 0.750 | – | 0.000 | 2 行差一档 |
| memory.relevance | choice | 18 | 0.722 | 0.722 | **0.944** | 0.000 | 平均档位距离 0.333 |

## 证据 1：弃权不是答错（human.escalate 的真实一行）

```json
{"i": 11, "expected": true, "got": "__escalate__", "ok": false, "abstained": true,
 "band": "low", "confidence": 1.0, "backend": "human",
 "trail": ["rule:no-match", "jev:answered", "human:answered-fallback"],
 "meta": {"path": "jev"}, "accepted": false}
```

读法：规则没命中 → 后端答了但置信度低 → 三段门降到 `escalate` → fallback 到 human 弃权。
对「该不该升人类」这个决策，**弃权本身就等于升级人类**，结果等价；但它如果被算成答错，整体准确率就会从 1.000 掉到 0.917。`trail` 字段就是审计链：一眼看出结果不是第一个后端给的，而是降级到 human 兜底。

## 证据 2：有序档位要看「差几档」（memory.relevance 的真实错行）

```json
{"i": 5, "expected": "primary", "got": "weak", "ok": false,
 "rank_distance": 2, "band": "medium", "confidence": 0.82, "backend": "jev",
 "trail": ["cache:no-match", "jev:answered"], "accepted": true}
```

18 行里 6 行未命中，但**全部只差一档**（`near_accuracy` 0.944、`mae_rank` 0.333）——用精确匹配看是 0.722，用档位距离看是「基本可用、边界有争议」。这类有序判断的读数必须两个都给。

## 证据 3：修一个语义，两个决策从「不及格」变「满分」

同一个 noul 判断族，把置信度从「离 0.5 的距离」（后端返回的 margin）改成「所选值的概率」`max(p, 1-p)` 之后：

| decision | 改前 accuracy | 改后 accuracy | 原因 |
|:---|---:|---:|:---|
| retry.should | 0.917 | 1.000 | p=0.8 的明确 yes 不再被压成 0.6 而降级 |
| human.escalate | 0.583 | 0.917 | 弃权行从 5 行降到 1 行 |

改前那 5 次弃权不是判断错，而是**置信度算错导致的过度降级** —— 这就是「阈值不能治质量问题」的镜像：**置信度算法错了，阈值再准也没用**。

## 证据 4：候选集错一个字段，准确率 0.31 → 1.00

路由决策的候选集从既有资产（路由规则表）动态取。原实现把规则里的**字段名**当成了候选值，真正的候选一个都没进集合，26 行里错 18 行。

```
修复前: intent.route  n=26  accuracy=0.308  accepted=0.462   （候选集里混着字面串 "primary"）
修复后: intent.route  n=26  accuracy=1.000  accepted=1.000   （候选 59 个，抽样目视核对过）
```

**教训**：动态候选集必须加「候选数量 + 抽样目视」检查。判断算法再准，候选集错了就是全错。

## 证据 5：score 的刻度由「声明的档数」决定

契约文本写 0-3，但只声明了 3 个档位 → 后端返回的概率只有 `0/1/2` 三档，分数 = 各档期望，理论上限 2.0。一个**直接命中**的文档实测只拿到 1.95：

```json
{"value": 1.95, "confidence": 0.92, "probabilities": {"0": 0.01, "1": 0.03, "2": 0.96}}
```

补成 4 档后（`probabilities` 出现 `"3"`）：

```json
{"value": 2.93, "confidence": 0.93, "probabilities": {"0": 0.0, "1": 0.0, "2": 0.06, "3": 0.94}}
```

同一个文档、同一句话，只是档位声明对了，「满分」才拿得到。另加刻度校正后，原始分会写回 `probabilities._raw_score` 备查。

## 这批数据的成熟度判定

- 8 个决策有 labeled dataset + 基线，全部可 `--fresh` 复跑；关键结论（弃权语义、档位距离、margin 置信度）都有可复现的真实输出。
- 但运行时间短（单日）、覆盖 8/10 个决策，两个决策（模型路由、恢复策略）仍无数据集。
- 因此 `decision-contract` 标为 **beta（🟡）**：有初步验证数据与真实场景，尚未 ≥30 天长期运行。
