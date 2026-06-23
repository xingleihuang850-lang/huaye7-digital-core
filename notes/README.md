# 笔记 vault（Obsidian）

本项目的笔记层。**在 Obsidian 里把这个 `notes/` 文件夹作为 vault 打开。**

## 约定
- 纯 Markdown，一条笔记一个 `.md` 文件。
- 附件（图片 / PDF）统一放 `attachments/`。
- 用 `[[双链]]` 互联；学习笔记、概念卡、公式、源码笔记都放这。

## agent 怎么用（见 CLAUDE.md §3）
- **直接读**：agent 可直接 grep / 读这些 md 做精确查找。
- **语义查**：笔记分块 embedding 进 LanceDB（`vectorstore/`）做语义检索；喂 embedding 前轻清 Obsidian 自家语法（`[[ ]]`、`%%注释%%`、callout、YAML frontmatter）。

## git
- `.md` 笔记入 git（版本化你的思考）。
- `.obsidian/`（Obsidian 本地配置 / UI 状态）已 gitignore。
- `attachments/` 暂入 git；若体积变大，改走 gitignore 或 git-lfs。
