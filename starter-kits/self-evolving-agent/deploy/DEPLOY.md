# 部署流程 Deploy

> 部署 = 换行为 + 留快照。没有快照的部署在裸奔。

## 步骤

1. **过闸确认**:evolution-gate/GATE.md 五闸门全过,判定记录归档
2. **打快照**:当前线上版本打 tag/复制到 `snapshots/<date>-<version>/`
3. **更新基线引用**:BASELINE.md 指向新版本
4. **部署**:按技能升级流程替换 prompt/schema/流程文件
5. **观察期**:跑完一个完整任务周期(至少 1 次 cron 周期),对比指标
6. **确认**:指标不劣化 → 部署完成;劣化 → 走 rollback/ROLLBACK.md

## 快照内容

- 全部行为文件(SKILL.md / prompt / schema / red-flags)
- 当时的 BASELINE.md
- 闸门判定记录
