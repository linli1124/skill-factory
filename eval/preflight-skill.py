#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight-skill.py — 旧入口（保留兼容）

真正的实现已迁到 scripts/selfcheck.py。这里只做转发，
因为 skill 包的社区约定是 scripts/selfcheck.py，且退出码要统一为 0/2/3/4/8。

新代码请直接用：
    python scripts/selfcheck.py <skill目录>
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(os.path.dirname(HERE), "scripts", "selfcheck.py")

if not os.path.exists(TARGET):
    sys.stderr.write("找不到实现文件：scripts/selfcheck.py\n")
    sys.exit(4)

sys.argv[0] = TARGET
runpy.run_path(TARGET, run_name="__main__")
