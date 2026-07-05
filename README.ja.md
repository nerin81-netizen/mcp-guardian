# mcp-guardian

[English](./README.md) | [한국어](./README.ko.md) | [中文](./README.zh.md) | [日本語](./README.ja.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [हिन्दी](./README.hi.md) | [العربية](./README.ar.md)

---

AI 駆動開発のためのプライバシー防火壁。AI エージェントがコードをコミット
する際に、機密情報・個人情報・内部キーワードが GitHub に到達するのを
防ぎます。

## 機能

`mcp-guardian` は MCP 互換エージェント(Claude Code、Cursor、Codex など)
に接続でき、5 つのスキャンツールと 1 つのルールリソースを公開します。

| ツール | 呼び出すタイミング |
| --- | --- |
| `check_files` | 機密データを含む可能性のあるファイルを保存する前 |
| `check_commit` | `git commit` の前 — ステージ済みファイルをスキャン |
| `sanitize_history` | 漏洩が疑われるとき — 問題のあるコミットを追跡 |
| `check_remote_url` | `git push` の前 — リモート URL の PAT をチェック |
| `install_hook` | 1 回限りのセットアップ — pre-commit フックをインストールし、OS に強制させる |

さらに `config://rules` リソースで現在有効なルールセット全体を取得
できるため、監査人や他のエージェントがブロック基準を確認できます。

## なぜ必要か

AI エージェントは人間がレビューするよりも遥かに高速にコードを書きます。
README に紛れ込んだ 1 行の資格情報や実名は、コミットが GitHub に
プッシュされた瞬間に恒久的な公開記録になります。`mcp-guardian` は
4 つのチェックポイントでこれらのミスを防ぎます。

1. **編集時** — `check_files` が保存前に機密内容を警告。
2. **コミット時** — `check_commit` または pre-commit フックがコミット
   自体をブロック。
3. **プッシュ時** — `check_remote_url` がリモート URL に漏れた PAT を除去。
4. **監査時** — `sanitize_history` が過去の漏洩を発生元コミットまで追跡。

## 再帰的安全性

サーバーは自身のルールを `src/mcp_guardian/patterns.py` に同梱します。
このファイル(`server.py` およびテストフィクスチャと共に)はホワイト
リスト化されているため、ガーディアンが自分のリポジトリをスキャンして
も自分自身をブロックしません。

## インストール

```bash
pip install mcp-guardian
```

ソースから:

```bash
git clone https://github.com/nerin81-netizen/mcp-guardian
cd mcp-guardian
pip install -e .
```

## 接続設定

MCP クライアント設定ファイル(例: Claude Code の `claude_desktop_config.json`)
に追加:

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

その後、エージェントに指示:

> 「コミットする前に、このリポジトリで `check_commit` を実行して」

または OS レベルの強制を 1 回で有効化:

```bash
mcp-guardian install-hook
```

これで、エージェントがツール呼び出しを忘れて도、すべての `git commit`
が保護されます。

## ルールカテゴリ

| カテゴリ | ブロック例 |
| --- | --- |
| 個人識別子 | 会社 / プロジェクト / 個人名のキーワード |
| GitHub トークン | `ghp_…`、`gho_…`、`github_pat_…` |
| プロバイダーキー | OpenAI、Anthropic、Slack、Google、AWS |
| 汎用シークレット | `api_key = "…"` 形式の代入 |
| メールアドレス | ホワイトリストにないアドレス |

有効なルールは MCP リソースで確認:

```
resource: config://rules
```

## ライセンス

MIT — [LICENSE](./LICENSE) 参照。
