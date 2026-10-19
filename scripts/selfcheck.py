#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selfcheck.py — skill 包门禁自检（交付 / 打包 / 发布前必跑）

用法
----
    python scripts/selfcheck.py              # 检查本包（脚本所在目录的上一级）
    python scripts/selfcheck.py <skill目录>  # 检查任意 skill 包
    python scripts/selfcheck.py --json       # 机器可读输出

退出码
------
    0  全部通过（可能带 INFO）
    2  用法错误：参数不对 / 目录不存在
    3  门禁未通过：存在 FAIL，不许交付
    4  环境问题：Python 版本不足 / 目录不可读
    8  部分通过：无 FAIL，但有 WARN，建议先修再交付

判定分三档
----------
    FAIL  硬伤，交付即事故（缺 SKILL.md、name 非法、打包垃圾、语法错）
    WARN  不致命，但会掉质量分（超一屏、缺开工卡、引用断链、绝对路径）
    INFO  可选项提示，不影响退出码（license、未填占位符之外的软提醒）
"""
import argparse
import json
import os
import re
import sys

MIN_PY = (3, 8)

# 硬垃圾：混进包就是事故
JUNK_DIRS = {"__pycache__", "__MACOSX", ".pytest_cache"}
# 软目录：开发时天然存在，打包时排除即可
DEV_DIRS = {".git", ".idea", ".vscode"}
JUNK_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_SUFFIX = (".pyc", ".pyo", ".bak", ".orig", ".swp", ".tmp", ".log")
JUNK_EXTS = {".zip", ".tar", ".gz", ".tgz", ".exe", ".dll", ".so", ".dylib"}
BIN_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico",
            ".mp4", ".mov", ".avi", ".mp3", ".wav", ".pdf", ".psd"}

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.S)
VER_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?$")
REF_RE = re.compile(r"`([A-Za-z0-9_\-./\u4e00-\u9fa5]+\.(?:md|py|sh|js|json|ya?ml|txt|csv))`")
ROOT_DOCS = {"SKILL.md", "README.md", "开工卡.md"}  # 根目录文档按裸文件名引用也算数
CODE_BLOCK_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|FIXME)\b|\{\{[a-z_]+\}\}|<PLACEHOLDER>")
ABS_PATH_RE = re.compile(r"(?<![\w.])/(?:Users|home)/[A-Za-z0-9_.-]+|C:\\Users\\")
TRIGGER_HINTS = ("当", "时使用", "适用", "Use when", "触发词", "何时用")


class Result(object):
    def __init__(self):
        self.fails = []
        self.warns = []
        self.infos = []

    def fail(self, item, detail="", fix=""):
        self.fails.append({"项": item, "实测": detail, "修法": fix})

    def warn(self, item, detail="", fix=""):
        self.warns.append({"项": item, "实测": detail, "修法": fix})

    def info(self, item, detail="", fix=""):
        self.infos.append({"项": item, "实测": detail, "修法": fix})


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fm_get(head, key):
    """取 frontmatter 字段，兼容单行值与 | / > 块标量。"""
    m = re.search(r"^%s:[ \t]*(.*)$" % re.escape(key), head, re.M)
    if not m:
        return None
    val = m.group(1).strip()
    if val.startswith("|") or val.startswith(">"):
        lines = []
        for line in head[m.end():].split("\n"):
            if not line.strip():
                lines.append("")
            elif line.startswith((" ", "\t")):
                lines.append(line.strip())
            else:
                break
        val = " ".join(x for x in lines if x)
    val = re.sub(r"\s+#.*$", "", val)  # YAML 行内注释：'#' 前须有空格
    return val.strip().strip('"').strip("'")


def walk_files(root):
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in JUNK_DIRS and d not in DEV_DIRS)
        for f in sorted(files):
            out.append(os.path.join(base, f))
    return out


def check(root):
    r = Result()
    root = os.path.abspath(root)
    base = os.path.basename(root.rstrip(os.sep))

    # ---------- 1. 入口文件 ----------
    # 注意：macOS 默认大小写不敏感，os.path.exists("SKILL.md") 对 skill.md 也返回真，
    # 必须拿真实文件名列表逐字比对，否则大小写违规漏拦。
    names = os.listdir(root) if os.path.isdir(root) else []
    skill = os.path.join(root, "SKILL.md")
    if "SKILL.md" not in names:
        alt = [f for f in names if f.lower() == "skill.md"]
        detail = ("发现 %s，大小写不对" % alt[0]) if alt else "包根目录没有 SKILL.md"
        r.fail("SKILL.md 存在且大小写精确", detail, "根目录放 SKILL.md（不能是 skill.md）")
        return r  # 没有入口，后面全部无从谈起

    try:
        text = read_text(skill)
    except UnicodeDecodeError as e:
        r.fail("SKILL.md 可读（UTF-8）", str(e), "另存为 UTF-8 编码")
        return r

    # ---------- 2. frontmatter ----------
    fm = FM_RE.match(text)
    if not fm:
        r.fail("frontmatter 由 --- 包裹", "开头没有成对的 ---", "文件第一行写 ---，元数据，再一行 ---")
        head = ""
    else:
        head = fm.group(1)

    name = fm_get(head, "name") if head else None
    if not name:
        r.fail("name 必填", "缺 name 字段", "frontmatter 写 name: my-skill")
    else:
        if not (3 <= len(name) <= 64):
            r.fail("name 长度 3-64", "当前 %d 字符" % len(name), "缩短或加长 name")
        elif not NAME_RE.match(name):
            r.fail("name 只含小写字母/数字/连字符", "当前 %s" % name,
                   "改小写，下划线换连字符，首尾不加连字符")
        if name != base:
            r.warn("name 与目录名一致", "%s vs %s" % (name, base),
                   "打包根目录名应与 name 相同（平铺解压可忽略）")

    desc = fm_get(head, "description") if head else None
    if not desc:
        r.fail("description 必填", "缺 description 或为空", "写清做什么 + 何时用 + 触发词")
    else:
        if len(desc) > 1024:
            r.fail("description ≤ 1024 字符", "当前 %d 字符" % len(desc), "精简，超长会被平台截断")
        if not any(h in desc for h in TRIGGER_HINTS):
            r.warn("description 含触发场景", "未见『当…时使用 / 适用 / 触发词』",
                   "补一句何时该用这个 skill")

    ver = fm_get(head, "version") if head else None
    if not ver:
        meta = re.search(r"^\s+version:[ \t]*(.+)$", head or "", re.M)
        if meta:
            ver = re.sub(r"\s+#.*$", "", meta.group(1)).strip().strip('"').strip("'")
    if not ver:
        r.warn("版本号 metadata.version", "未找到", "加 metadata.version: 1.0.0（SemVer）")
    elif not VER_RE.match(ver):
        r.warn("版本号为 SemVer", "当前 %s" % ver, "改成 1.0 / 1.0.0，不用 v1.0 或 latest")

    has_license = bool((fm_get(head, "license") if head else None)
                       or os.path.exists(os.path.join(root, "ATTRIBUTION.md"))
                       or os.path.exists(os.path.join(root, "LICENSE"))
                       or os.path.exists(os.path.join(root, "LICENSE.txt")))
    if not has_license:
        r.info("合规声明（license / ATTRIBUTION.md）", "两者都没有",
               "对外发布时补一个；内部自用可缓")

    # ---------- 3. 正文规模与结构 ----------
    lines = text.count("\n") + 1
    if lines > 50:
        r.warn("SKILL.md ≤ 50 行（一屏原则）", "当前 %d 行" % lines,
               "细则拆到 references/，SKILL.md 只留路由与死线")
    h2 = len(re.findall(r"^##\s+\S", text, re.M))
    if h2 < 3:
        r.warn("正文至少 3 个 ## 章节", "当前 %d 个" % h2, "按『何时用 / 怎么做 / 边界』分节")

    card = os.path.join(root, "开工卡.md")
    if not os.path.exists(card):
        r.info("开工卡.md 存在", "根目录没有", "一屏执行卡：动作 + 卡住怎么退（最小包可缓）")
    else:
        cn = read_text(card).count("\n") + 1
        if cn > 110:
            r.warn("开工卡 ≤ 110 行（一屏）", "当前 %d 行" % cn, "砍到能一屏读完")

    if not os.path.exists(os.path.join(root, "README.md")):
        r.info("README.md 存在", "根目录没有", "给人看的说明（最小包可缓）")

    # ---------- 4. 打包卫生 ----------
    files = walk_files(root)
    junk = []
    for p in files:
        n = os.path.basename(p)
        rel = os.path.relpath(p, root)
        ext = os.path.splitext(n)[1].lower()
        if n in JUNK_FILES or n.startswith("._") or ext in JUNK_SUFFIX or ext in JUNK_EXTS:
            junk.append(rel)
    for d in JUNK_DIRS:
        if os.path.isdir(os.path.join(root, d)):
            junk.append(d + "/")
    if junk:
        r.fail("无打包垃圾", "、".join(junk[:6]) + ("…共 %d 项" % len(junk) if len(junk) > 6 else ""),
               "删掉后再打包（缓存/备份/压缩包不进包）")

    dev = [d + "/" for d in sorted(DEV_DIRS) if os.path.isdir(os.path.join(root, d))]
    if dev:
        r.info("开发目录排除在包外", "、".join(dev),
               "打包时加排除规则，别把 .git/ 等带进 zip")

    bin_files = [os.path.relpath(p, root) for p in files
                 if os.path.splitext(p)[1].lower() in BIN_EXTS]
    if bin_files:
        r.warn("无二进制媒体文件", "、".join(bin_files[:5]),
               "Skills 广场类平台会直接拒收；仅本地用可忽略")

    # ---------- 5. 脚本可编译 ----------
    py_files = [p for p in files if p.endswith(".py")]
    broken = []
    for p in py_files:
        try:
            src = read_text(p)
            compile(src, p, "exec")
        except UnicodeDecodeError:
            broken.append(os.path.relpath(p, root) + "（非 UTF-8）")
        except SyntaxError as e:
            broken.append("%s:%s %s" % (os.path.relpath(p, root), e.lineno, e.msg))
    if broken:
        r.fail("所有 .py 语法可编译", "；".join(broken[:4]), "修语法再交付")

    # ---------- 6. 文档引用完整性 ----------
    docs = [skill] + [p for p in files if p.endswith(".md") and p != skill]
    missing, abs_hits, ph_hits = [], [], []
    for p in docs:
        try:
            t = read_text(p)
        except UnicodeDecodeError:
            continue
        rel = os.path.relpath(p, root)
        for ref in set(REF_RE.findall(t)):
            # 只认「带目录前缀」的引用；裸文件名仅当它是根目录文档时才算，
            # 否则「文档里举的例子」（如 `错题集.md` 作示例）会被误判成断链。
            if ref.startswith(".") or ref.endswith("/"):
                continue
            if "/" not in ref and ref not in ROOT_DOCS:
                continue
            if not os.path.exists(os.path.join(root, ref)):
                missing.append("%s → %s" % (rel, ref))
        # 绝对路径 / 占位符只在「正文」里找，先剥掉代码块与行内代码，
        # 否则脚本里举的反例（`TODO`、`/Users/xxx`）会把自己扫成违规。
        scan = INLINE_CODE_RE.sub("", CODE_BLOCK_RE.sub("", t))
        if ABS_PATH_RE.search(scan):
            abs_hits.append(rel)
        if PLACEHOLDER_RE.search(scan):
            ph_hits.append(rel)
    if missing:
        r.fail("文档引用路径存在", "；".join(missing[:5]), "补文件或改引用")
    if abs_hits:
        r.warn("无写死的绝对路径", "、".join(sorted(set(abs_hits))[:4]),
               "换相对路径；换台机器就失效")
    if ph_hits:
        r.warn("无未填占位符", "、".join(sorted(set(ph_hits))[:4]), "TODO/FIXME 清掉再交付")

    return r


def emit(r, root, as_json):
    code = 3 if r.fails else (8 if r.warns else 0)
    if as_json:
        print(json.dumps({
            "root": root,
            "pass": not r.fails,
            "fail": r.fails,
            "warn": r.warns,
            "info": r.infos,
            "exitCode": code,
        }, ensure_ascii=False, indent=2))
        return code

    print("skill 包自检：%s" % root)
    print("=" * 58)
    for label, bucket, mark in (("FAIL", r.fails, "✗"), ("WARN", r.warns, "!"), ("INFO", r.infos, "·")):
        if not bucket:
            continue
        print("%s  %d 项" % (label, len(bucket)))
        for c in bucket:
            print("  %s %s" % (mark, c["项"]))
            if c["实测"]:
                print("      实测：%s" % c["实测"])
            if c["修法"]:
                print("      修法：%s" % c["修法"])
    print("-" * 58)
    if r.fails:
        print("结论：门禁未通过（%d FAIL / %d WARN）→ 退出码 3 · 不许交付" % (len(r.fails), len(r.warns)))
    elif r.warns:
        print("结论：部分通过（0 FAIL / %d WARN）→ 退出码 8 · 建议先修再交付" % len(r.warns))
    else:
        print("结论：全部通过 → 退出码 0 · 可以交付")
    return code


def main():
    if sys.version_info < MIN_PY:
        sys.stderr.write("需要 Python %d.%d+，当前 %s\n" % (MIN_PY[0], MIN_PY[1], sys.version.split()[0]))
        return 4

    ap = argparse.ArgumentParser(description="skill 包门禁自检")
    ap.add_argument("path", nargs="?", default=None, help="skill 包目录；缺省为本脚本上一级")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    root = args.path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        sys.stderr.write("目录不存在：%s\n" % root)
        return 2
    if not os.access(root, os.R_OK | os.X_OK):
        sys.stderr.write("目录不可读：%s\n" % root)
        return 4

    return emit(check(root), root, args.json)


if __name__ == "__main__":
    sys.exit(main())
