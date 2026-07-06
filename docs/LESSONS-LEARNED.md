# Lessons Learned：关联已有远程仓库并推送

> 场景：本地已有一份完整项目代码（非 git 仓库），需要关联到一个**已有提交历史**的 GitHub 远程仓库并推送本地增量改动。
>
> 本次操作日期：2026-07-06
> 仓库：[Frank-zhao-junjun/Purchase_collaboration](https://github.com/Frank-zhao-junjun/Purchase_collaboration)

---

## 1. ⚠️ `git init` + 直接 commit 会产生断裂历史（最严重）

**问题**

本地 `git init` 后直接 `git add -A && git commit`，产生的是一个**无父提交的孤儿 commit**，与远程历史没有任何共同祖先。此时：

- `git push` 会被拒绝（non-fast-forward）
- `git push --force` 会**永久覆盖远程全部历史**，远程已有提交全部丢失

**正确做法**

关联已有非空远程时，**先 fetch，再基于 `origin/main` 提交**：

```bash
git init -b main
git remote add origin <url>
git fetch origin main          # 先拉远程历史
git reset --soft origin/main   # 把工作区改动挂到远程历史之上
git commit -m "..."            # 此时提交基于远程，可 fast-forward push
git push origin main
```

**教训**

> 永远不要对非空远程 force push，除非确认要丢弃远程历史。关联已有远程的第一步永远是 `fetch`。

---

## 2. Windows 文件模式（100755↔100644）制造大量伪差异

**问题**

Windows 文件系统不保留可执行位，`git add` 会把所有文件记成 `100644`，而远程很多脚本是 `100755`。结果 96 个内容完全相同的文件显示为"已修改"，严重干扰对真实改动的判断。

**识别方法**

用 `git diff --raw` 看源 hash 和目标 hash 是否相同：

```
:100755 100644 4ba0ec8 4ba0ec8 M README.md   ← hash 相同 = 纯 mode 差异（伪改动）
:100644 100644 bf454bd 86b7275 M .gitignore  ← hash 不同 = 真实内容差异
```

**解决**

```bash
git config core.fileMode false                    # 忽略工作区 mode 检测
git update-index --chmod=+x <file>                # 把 index 里的 mode 改回 100755
```

**教训**

> Windows 上务必设置 `core.fileMode=false`；判断真实改动看 blob hash，不要只看 `git status`。

---

## 3. 缺少 `.gitattributes` 导致 CRLF/LF 噪音

**问题**

没有 `.gitattributes`，Windows 的 `core.autocrlf=true` 会让行尾符在不同操作间漂移，污染 diff——大量文件显示为"整文件改动"但实际只是 CRLF↔LF。

**解决**

新增 `.gitattributes` 强制 LF：

```
* text=auto eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.py text eol=lf
*.sh text eol=lf
*.md text eol=lf
*.json text eol=lf
# 含 UTF-8 中文且无需 EOL 转换的文件单独标记
assets/US.txt -text
# 二进制
*.png binary
*.db binary
```

**教训**

> 跨平台项目第一天就该提交 `.gitattributes`，不要依赖个人的 `autocrlf` 设置。

---

## 4. PowerShell 把 git 的 stderr 当错误（最大的干扰）

**问题**

git 把进度信息写到 stderr，PowerShell 把 stderr 当成 `RemoteException` 报红，导致**大量"假错误"**——实际操作已成功。例如 push 输出 `7ac75e8..7bea6d6 main -> main` 却标红，退出码也显示为 1。

**教训**

> 在 PowerShell 里看 git 输出，**不要被红色吓到**，重点看实际内容；判断成功与否看 `git log` / `git status` 的真实状态，而非退出码颜色。或改用 `cmd /c "git ..."` 执行。

---

## 5. PowerShell 管道会损坏二进制/UTF-8 内容显示

**问题**

`git cat-file -p <blob> | Format-Hex` 显示中文变成 `?`（0x3F），一度误以为 blob 被损坏。实际 blob 完好（7691 字节完整 UTF-8），是 PowerShell 把 stdout 当文本解码时损坏了显示。

**正确验证方法**

```bash
git cat-file -s <blob>      # 看字节大小（不经文本管道）
git rev-parse <blob>        # 看 hash
git rev-parse origin/main:<path>   # 对比远程与本地 hash 是否一致
```

**教训**

> 用 `git cat-file -s`（字节大小）和 `git rev-parse`（hash）判断内容完整性，**不要通过 PowerShell 文本管道检视二进制内容**。

---

## 6. `.gitattributes` 与 `git add -A` 同批操作会损坏 blob

**问题**

在同一轮 `git add -A` 里同时新增 `.gitattributes` 并添加所有文件，导致约 100 个文件 blob 被破坏（diff 显示 `0 N 删除`，即 0 行新增 N 行删除）。`.gitattributes` 稳定后再重新 `git add -A` 即恢复正常。

**正确顺序**

```bash
# 1. 先单独提交 .gitattributes
git add .gitattributes
git commit -m "chore: add .gitattributes"
# 2. 再 add 其余文件
git add -A
git commit -m "..."
```

**教训**

> 先单独提交 `.gitattributes`，再 add 其余文件，避免规范化规则与批量添加的竞态。

---

## 7. HTTPS 推 GitHub 不稳，SSH 更可靠

**问题**

`git push` over HTTPS 报 `Connection was reset`——能连上 443 端口，TLS 握手成功，但传输数据时连接被重置。这是国内访问 GitHub 的典型网络问题。`git ls-remote` / `git fetch` 也频繁超时。

**解决**

改用 SSH 协议，走 22 端口，一次成功：

```bash
# 确认 SSH key 已配置
ssh -T git@github.com
# 切换远程 URL 为 SSH
git remote set-url origin git@github.com:<user>/<repo>.git
git push origin main
```

**教训**

> HTTPS 推送失败时优先切换 SSH；提前确认 SSH key 已配置（`ssh -T git@github.com`）。gh CLI 走 HTTPS API 相对稳定，可用于查远程状态。

---

## 8. 本地产物被误提交到远程

**问题**

远程仓库里已存在 `tests/api/.coverage`（测试覆盖率 SQLite 文件）等本地产物。`.gitignore` 只忽略了 `coverage/` 目录，漏了 `.coverage` 文件本身。

**排查方法**

```bash
git ls-files | grep -E '\.(db|log|coverage|sqlite)$'   # 审查已跟踪的产物
git check-ignore -v <file>                              # 确认是否被忽略
```

**解决**

```bash
git rm --cached <产物文件>          # 从仓库移除但保留本地
# 在 .gitignore 补充：
#   coverage/
#   .coverage
```

**教训**

> 提交前用 `git ls-files` 审查已跟踪文件，识别 db/log/coverage 等产物；`.gitignore` 要同时覆盖目录和文件两种形式。

---

## 一句话总结

> 关联已有远程时：**先 fetch 再基于远程历史提交**；Windows 上设 `core.fileMode=false` + 提交 `.gitattributes`；用 blob hash 判断真实改动；HTTPS 不行就换 SSH；别被 PowerShell 的红色 stderr 误导。