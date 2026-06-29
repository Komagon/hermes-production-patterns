# 示例：Maker/Checker 文章生产管线

> 演示 Maker/Checker 分离的完整流程

## 管线流程

```
1. 选题 → Maker（生成初稿）→ Checker（五维评分）
2. PASS? → 输出
3. FAIL? → Maker 根据评分修改 → 最多 3 轮
4. 3 轮仍 FAIL → 上报人类
```

## Maker 技能（生成）

```markdown
输入：选题方向 + 调研数据
输出：完整文章初稿
约束：
  - 不要用 AI 套话（首先/其次/综上所述）
  - 每段不超过 5 行
  - 表格代替文字比较
  - 结尾必须互动
```

## Checker 技能（验证）

```markdown
输入：文章初稿
输出：五维评分 + PASS/FAIL
评分维度：
  - 🎣 钩子强度 (1-10)
  - 📊 数据支撑 (1-10)
  - 🧹 AI味检测 (1-10)
  - 📱 手机适配 (1-10)
  - 🎯 互动钩子 (1-10)
通过线：≥ 40/50
```

## 集成到 Hermes

使用 Hermes 的 `delegate_task` 实现 Maker/Checker 隔离：

```yaml
# 在技能中调用
1. Maker: delegate_task(goal="写初稿", context=选题+数据)
2. Checker: delegate_task(goal="验证质量", context=初稿)
3. Gate: 判断 PASS/FAIL → 决定输出或迭代
```
