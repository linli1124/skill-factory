# skill-factory · 任务→skill 沉淀流水线

> **每个任务开始自动启动的元 skill**。version 1.0 · 2026-10-18 · 知夏实证泛化

## 这是什么

把"任何一个重复任务"沉淀成结构合格的 skill 的标准流水线。它自己就是按这套结构长出来的（自举）。

## 结构

```
skill-factory/
├── SKILL.md            # 路由＋五条死线＋任务定位三问（必定加载）
├── 开工卡.md           # L0：任务开始三问/收尾经验分流/新 skill 自检
├── references/
│   └── 结构规范.md      # 什么时候值得沉淀/标准结构/分层铁律/触发词设计
├── eval/
│   └── preflight-skill.py  # 新 skill 结构自检（frontmatter/行数/README/eval）
└── README.md           # 本文件
```

## 核心口诀

- **任务开始**：还干吗 → 查前科 → 定落点（三问 30 秒）
- **任务收尾**：忘过的进开工卡、翻车进错题集、数据进 leaves、跨项目进元层、本项目进 memory、一次性不记
- **同一信息只在一层**（防内部打架）
- **忘过的东西最终形态是脚本不是文字**（eval 拦截层）

## 跟其他 skill 的关系

- `skill-creator`（官方）：管"怎么写 skill 的技术格式"（YAML/打包/验证）
- **本 skill**：管"任务怎么沉淀/怎么组织"（何时建/结构分层/经验分流/触发设计）——**内容层 vs 格式层**
- 实例参考：`~/.workbuddy/skills/zhixia-character/`（全结构实战版）

## 用法

```bash
# 任务收尾时自检新 skill
python3 eval/preflight-skill.py ~/.workbuddy/skills/<新skill名>
```
