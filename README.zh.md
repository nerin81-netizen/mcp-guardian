# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md)

---

AI 驱动开发的隐私防火墙。在 AI 代理提交代码时，阻止密钥、个人信息和
内部关键字到达 GitHub。

## 功能

`mcp-guardian` 可接入任何兼容 MCP 的代理(Claude Code、Cursor、Codex 等),
提供五个扫描工具和一个规则资源。

| 工具 | 调用时机 |
| --- | --- |
| `check_files` | 在保存可能包含敏感数据的文件之前 |
| `check_commit` | `git commit` 之前 — 扫描已暂存文件 |
| `sanitize_history` | 怀疑发生泄漏后 — 定位有问题的提交 |
| `check_remote_url` | `git push` 之前 — 检查远程 URL 中的 PAT |
| `install_hook` | 一次性设置 — 安装 pre-commit 钩子,由操作系统强制执行 |

此外 `config://rules` 资源可返回当前激活的完整规则集,便于审计人员
和其他代理查看拦截标准。

## 为什么需要它

AI 代理编写代码的速度远超人类审查的速度。README 中一行多余的凭据或
真实姓名,一旦提交到 GitHub 就会变成永久的公开记录。`mcp-guardian`
在四个检查点上拦截这些失误:

1. **编辑时** — `check_files` 在保存前标记敏感内容。
2. **提交时** — `check_commit` 或 pre-commit 钩子直接阻止提交。
3. **推送时** — `check_remote_url` 清除泄漏到远程 URL 的 PAT。
4. **审计时** — `sanitize_history` 追溯过去的泄漏到原始提交。

## 递归安全性

服务器在 `src/mcp_guardian/patterns.py` 中携带自己的模式规则。该文件
(连同 `server.py` 和测试 fixture) 被列入白名单,因此当 guardian 扫描
自身仓库时不会拦截自己。

## 安装

```bash
pip install mcp-guardian
```

或从源码安装:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## 接入配置

在 MCP 客户端配置文件中添加(例如 Claude Code 的 `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "guardian": {
      "command": "python",
      "args": ["-m", "mcp_guardian.server"]
    }
  }
}
```

然后让代理执行:

> "提交之前,在这个仓库上运行 `check_commit`。"

或一次性启用 OS 级强制执行:

```bash
mcp-guardian install-hook
```

之后即使代理忘记调用工具,每次 `git commit` 都会被守护。

## 规则类别

| 类别 | 拦截示例 |
| --- | --- |
| 个人标识符 | 公司 / 项目 / 个人姓名关键字 |
| GitHub 令牌 | `ghp_…`、`gho_…`、`github_pat_…` |
| 提供商密钥 | OpenAI、Anthropic、Slack、Google、AWS |
| 通用密钥 | `api_key = "…"` 形式的赋值 |
| 电子邮件 | 不在白名单中的地址 |

可通过 MCP 资源查询当前规则:

```
resource: config://rules
```

## 许可证

MIT — 详见 [LICENSE](./LICENSE)。
