---
name: skill-factory
description: 任务→skill 的沉淀流水线（元 skill）——**任务执行时先启动对应的主 skill（如知夏出图）；本 skill 在任务收尾沉淀/建新 skill 时才启动，不抢主 skill 的位置**。当用户说"沉淀/复盘这个任务/建个 skill/这活以后还干要固化/skill 该怎么组织"时使用。触发词：沉淀、复盘、建 skill、skill 结构、固化、以后还干、经验分流。
metadata:
  version: "1.0"  # 2026-10-18 建
compatibility: Requires Python 3.9+; user-level skill (~/.workbuddy/skills/)
---

# skill-factory · 任务→skill 沉淀流水线

> **第 0 事：每个任务开始，先过「任务定位三问」；任务收尾，过「经验分流」。**

## 死线（不遵守 = 白干）

1. 🔴 **收尾沉淀三问**（任务完成时过一遍）：① **这任务以后还干吗**（干→按本 skill 结构沉淀；一次性→不建）② **经验是什么类型**（忘过的动作→开工卡／翻车→错题集／数据→references）③ **落点**（跨项目→元层或 user memory；本项目→工作区 memory）
2. 🔴 **结构分层铁律**：同一信息只在一层——**动作进开工卡、知识进 references、血泪进错题集**；别处只放指针，禁复制（防"内部打架"）
3. 🔴 **一屏原则**：SKILL.md <50 行、开工卡一屏、references 单文件按需查——超了就是没分层
4. 🔴 **忘过/错过的东西，最终形态是脚本不是文字**（eval/scripts 机械拦截层——文字会被忘，脚本不会）
5. 🔴 **沉淀判据**：跨项目通用→提炼到本 skill 或 user memory｜只对本项目→工作区 memory｜一次性→不记

## 路由

| 场景 | 去哪 |
|---|---|
| 新任务启动/结构疑问 | `开工卡.md`（L0，读这一页） |
| skill 标准结构长什么样 | `references/结构规范.md` |
| 完整实例参考 | 本目录自身（四层齐备：SKILL.md / 开工卡 / references / eval） |
| 新 skill 建完自检 | `eval/preflight-skill.py` |

## 任务定位三问（SKILL.md 内联兜底）

1. **还干吗**：一次性任务→直接干；重复任务→建/更新 skill
2. **前科**：同类坑查 `错题集.md`/历史 memory——**不重复踩**
3. **落点**：产出物位置＋验收标准，动手前定
