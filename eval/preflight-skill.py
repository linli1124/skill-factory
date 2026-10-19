#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight-skill.py — 新 skill 结构自检（skill-factory/eval/）
建完 skill 跑一遍，结构不合格不许收工。
用法：python3 eval/preflight-skill.py <skill目录>
退出码：0=过；1=有 ❌
"""
import sys, os, re

def main():
    if len(sys.argv) < 2:
        print("用法：preflight-skill.py <skill目录>"); return 1
    root = os.path.abspath(sys.argv[1])
    if not os.path.isdir(root):
        print(f"❌ 目录不存在：{root}"); return 1

    checks = []
    # 1. SKILL.md 存在
    sk = os.path.join(root, "SKILL.md")
    checks.append(("SKILL.md 存在", os.path.exists(sk), ""))
    if os.path.exists(sk):
        txt = open(sk, encoding="utf-8").read()
        # 2. frontmatter
        fm = re.match(r"^---\n(.*?)\n---", txt, re.S)
        checks.append(("frontmatter 完整（--- 包裹）", bool(fm), ""))
        if fm:
            head = fm.group(1)
            mname = re.search(r"^name:\s*([a-z0-9-]+)\s*$", head, re.M)
            checks.append(("name 合规（小写+连字符）", bool(mname), f"got: {mname.group(1) if mname else '?'}"))
            if mname:
                checks.append(("name 匹配目录名", mname.group(1) == os.path.basename(root), f"{mname.group(1)} vs {os.path.basename(root)}"))
            checks.append(("description 有触发词", ("触发词" in head or "Use when" in head or "时使用" in head), "description 要写'做什么+何时用+触发词'"))
            checks.append(("version 元数据", ("version" in head), "metadata.version 便于追踪"))
        # 3. SKILL.md 行数 < 50
        n = txt.count("\n") + 1
        checks.append(("SKILL.md <50 行", n <= 50, f"当前 {n} 行"))
    # 4. 开工卡一屏
    for card in ["开工卡.md", "开工卡.md"]:
        cp = os.path.join(root, card)
        if os.path.exists(cp):
            cn = open(cp, encoding="utf-8").read().count("\n") + 1
            checks.append((f"{card} <110 行", cn <= 110, f"当前 {cn} 行"))
            break
    else:
        checks.append(("开工卡存在（L0 执行卡）", False, "标准结构需要开工卡"))
    # 5. README（人的入口）
    checks.append(("README.md 存在", os.path.exists(os.path.join(root, "README.md")), "大 skill 需要；最小版可缓"))
    # 6. eval 目录
    checks.append(("eval/ 存在（拦截层）", os.path.isdir(os.path.join(root, "eval")), "防退化层；最小版可缓"))

    bad = [c for c in checks if not c[1]]
    for name, ok, note in checks:
        mark = "✅" if ok else "❌"
        extra = f"（{note}）" if (note and not ok) else ""
        print(f"  {mark} {name}{extra}")
    if bad:
        print(f"❌ preflight-skill 不过：{len(bad)} 项——修好再收工")
        return 1
    print("✅ preflight-skill 过——结构合格")
    return 0

if __name__ == "__main__":
    sys.exit(main())
