#!/usr/bin/env bash
# 一键同步:把 claude 私有仓的 hy7_* 脚本「清洗」后发布到公开仓 huaye7-digital-core。
#   清洗 = 抹掉 吉林大学/欧勒姆能源/精确井深 + 把外盘路径参数化为 HY7_DATA_ROOT。
#   安全闸门:清洗后若仍检出敏感字样 → 立即中止,绝不提交/推送。
#
# 用法:
#   bash scripts/sync_huaye7_public.sh         # check(默认):临时目录验证,不动公开仓
#   bash scripts/sync_huaye7_public.sh push    # 真正:清洗→闸门→提交→推送
set -euo pipefail

SRC=/Users/hxl/Documents/claude/src
PUB=/Users/hxl/Documents/huaye7-digital-core
FILES=(hy7_etl.py hy7_figures.py hy7_make_excel.py hy7_make_ppt.py hy7_make_word.py verify_hy7.py)
MODE="${1:-check}"

sanitize() {   # $1 = 目标目录(就地改写其中的 .py)
  local d="$1" f
  for f in "${FILES[@]}"; do
    perl -i -pe '
      s{B = os\.path\.join\(ROOT, "data", "hy7_raw"\)}{B = os.environ.get("HY7_DATA_ROOT", "data/raw")  # 指向你的多尺度数据目录};
      s{SUMMARY = f"\{B\}/花页7井_4199\.21m_多尺度数据汇总\.xlsx"}{SUMMARY = next(iter(glob.glob(f"{B}/*多尺度数据汇总.xlsx")), None)};
      s{^import os, json, warnings$}{import os, json, glob, warnings};
      s{^import os, warnings$}{import os, glob, warnings};
      s{"depth_m": 4199\.21}{"depth_m": 4200};
      s{服务商（欧勒姆能源测试）}{服务商};
      s{吉林大学样品 / 欧勒姆能源测试}{多尺度数字岩心样品 / 服务商测试};
      s{外置盘「吉林大学数据报告归总」}{本地多尺度数据目录};
      s{吉林大学花页7井}{花页7井};
      s{4199\.21 ?m}{约 4200 m}g;
      s{4199\.21}{约 4200}g;
      s{吉林大学}{}g;
      s{欧勒姆能源}{服务商}g;
    ' "$d/$f"
  done
}

gate() {       # $1 = 目录;检出敏感字样即中止
  if grep -rnE '吉林大学|吉大|欧勒姆|4199|Volumes|Untitled|数据报告归总' "$1"/*.py; then
    echo "✗ 安全闸门:仍有敏感残留 → 已中止,未提交/推送。把新写法交给 agent 清洗后再同步。"
    exit 1
  fi
  echo "✓ 安全闸门通过(无敏感残留)"
  local f; for f in "$1"/*.py; do python3 -m py_compile "$f"; done
  echo "✓ Python 编译通过"
}

case "$MODE" in
  check)
    T=$(mktemp -d); for f in "${FILES[@]}"; do cp "$SRC/$f" "$T/$f"; done
    sanitize "$T"; gate "$T"; rm -rf "$T"
    echo "（check:已在临时目录验证清洗规则,未改动公开仓。真正发布用: $0 push）"
    ;;
  push)
    for f in "${FILES[@]}"; do cp "$SRC/$f" "$PUB/src/$f"; done
    sanitize "$PUB/src"; gate "$PUB/src"
    git -C "$PUB" add -A
    if git -C "$PUB" diff --cached --quiet; then echo "（公开仓无变化,跳过）"; exit 0; fi
    git -C "$PUB" commit -q -m "sync: 从源仓更新清洗版脚本"
    if git -C "$PUB" push origin main; then
      echo "✓ 已推送到 github.com/xingleihuang850-lang/huaye7-digital-core"
    else
      echo "⚠ 推送失败(多半缺凭证)。提交已在本地;让 agent 用 token 从其侧推,或配好凭证后再 git -C \"$PUB\" push origin main。"
    fi
    ;;
  *) echo "用法: $0 [check|push]"; exit 2 ;;
esac
