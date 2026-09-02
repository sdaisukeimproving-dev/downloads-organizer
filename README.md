# downloads-organizer

ダウンロードフォルダを、毎月1日に自動で片付けるツール。

## 何が変わるか

| | 導入前 | 導入後 |
|---|---|---|
| ダウンロードフォルダ | 数百件が1階層に平積み | 案件別フォルダに自動整理 |
| 「あの資料どこ」 | 毎回スクロールして探す | 案件フォルダを開くだけ |
| 重複ファイル | 気づかず溜まり続ける | 自動で隔離される |
| 片付け | 思い出したときに手作業 | 毎月1日 9:00 に自動 |

**ファイルは絶対に削除しません。** 捨てる判断は必ず人に残します。

## 使い方（渡された人へ）

Claudeにこう言ってください。

> このフォルダの CLAUDE.md を読んで、セットアップして

あとはClaudeが全部やります。
現状のヒアリングから、ルール作成、予行演習、インストール、動作確認まで完走します。

**あなたがやることは2つだけです。**

① Claudeが出すカテゴリ案に「合ってる／これも足して」と答える
② 最後にシステム設定でフルディスクアクセスをONにする（1回だけ・30秒）

## 中身

| ファイル | 役割 |
|---|---|
| `CLAUDE.md` | **Claude向けの実行手順書。これが本体** |
| `install.sh` | 配置と定期実行の登録 |
| `uninstall.sh` | 完全撤去 |
| `rules.example.json` | 分類ルールの雛形 |
| `organize.py` | 仕分けの実体 |
| `launcher.c` | 権限を保ったままPythonを起動する小さなランチャー |

## 動作条件

- macOS（Intel / Apple Silicon 両対応）
- `python3` と `clang`
  ※どちらも `xcode-select --install` で入ります

## 手動で動かす

```bash
python3 ~/Library/Application\ Support/DownloadsOrganizer/organize.py --config ~/Library/Application\ Support/DownloadsOrganizer/rules.json
```

※これは予行演習（1件も動かさない）。実際に動かすときは末尾に ` --go` を付ける

## ログ

```bash
cat ~/Library/Application\ Support/DownloadsOrganizer/organize.log
```
