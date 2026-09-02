# downloads-organizer ／ Claude向け実行手順書

**このファイルを読んだClaudeへ。**
あなたはこれから、目の前のユーザーのMacにこのツールを導入します。
ユーザーはコマンドを1行も打ちません。**あなたが全部やります。**

以下を上から順に実行してください。飛ばさないこと。

---

## 0. このツールが解決する課題

ダウンロードフォルダは放置すると数百件・数GBになる。
そうなると「あの資料どこだっけ」の検索が毎回発生し、探す時間が積み上がる。

一度手で片付けても、1ヶ月後には同じ状態に戻る。
**だから片付けではなく、毎月自動で片付く状態を作る。**

このツールがやること。

- 対象フォルダ（既定は `~/Downloads`）の直下を、案件別フォルダに自動で仕分ける
- 中身が完全一致する重複ファイルを見つけて隔離する
- インストーラ（`.dmg` `.pkg`）を隔離する
- 毎月1日 9:00 に自動で回る

**このツールは絶対にファイルを削除しません。** 隔離までで止め、捨てる判断は人に返します。

---

## 1. 絶対にやらないこと

これを破ると、ユーザーのファイルを失わせます。

- ファイルを削除しない。`rm` を使わない。ゴミ箱にも入れない
- 予行演習の結果をユーザーに見せる前に、本実行しない
- ヒアリングを省略して、勝手にカテゴリを決めない
- ユーザーの承認なしに、既存の `rules.json` を上書きしない
- `~/Desktop` `~/Documents` を対象にしない（ユーザーが明示的に希望した場合のみ）

---

## 2. 前提の確認

まずこれを実行して、環境を確認してください。

```bash
sw_vers -productVersion; uname -m; which clang python3
```

- macOS 13以降が望ましい
- `clang` がない場合 → ユーザーに「ターミナルで `xcode-select --install` を実行してください」と伝える
  ※これはパスワード入力を伴うことがあるため、あなたは実行しない
- `python3` がない場合も上と同じ

---

## 3. ヒアリング（ここを飛ばすと使えないものが出来上がる）

分類ルールはユーザーごとに違います。**必ず現物を見てから提案してください。**

### ① 対象フォルダの現状を調べる

```bash
cd ~/Downloads && ls -1 | wc -l && du -sh . && ls -lt | head -40
```

### ② 拡張子と重複の分布を見る

```bash
cd ~/Downloads && for f in *; do e="${f##*.}"; [ "$f" = "$e" ] && e="(フォルダ)"; echo "$e"; done | sort | uniq -c | sort -rn | head -15
```

### ③ ファイル名から案件・プロジェクトの塊を読み取る

ファイル名に繰り返し出てくる固有名詞（会社名・案件名・イベント名・サービス名）を拾います。
拾ったら、**そのままカテゴリ案としてユーザーに見せて確認を取ってください。**

聞くことは3つだけです。

- このカテゴリ分けで合っているか
- 抜けている案件はあるか
- 対象は `~/Downloads` でいいか

推測でカテゴリを確定しないこと。ユーザーの言葉で確認を取ること。

---

## 4. rules.json を作る

`rules.example.json` を雛形に、ヒアリング結果を反映したファイルを作ります。

作業用に `/tmp` ではなくユーザーのスクラッチ領域か、このフォルダ直下に `rules.json` として置いてください。

### 書き方のコツ

- `categories` は**上から順に判定**する。具体的なものを先に置く
  ※「A社」より先に「A社_定例」を置く、など
- `keywords` は小文字化して部分一致で判定される。日本語・英語を混ぜてよい
- 拡張子もキーワードとして使える（`".mp4"` など）
- `image_fallback` を設定すると、どの案件にも当たらない画像類をそこへ集められる
  ※不要なら空文字にする
- `min_age_hours` は既定24。作業中のファイルを守る安全装置なので、0にしないこと

### 検証

```bash
python3 -c "import json;json.load(open('rules.json',encoding='utf-8'));print('JSON OK')"
```

---

## 5. 予行演習（本実行の前に必ず）

**1件も動かさずに、何が起きるかだけ出します。**

```bash
python3 organize.py --config rules.json
```

出力をユーザーに見せて、次を確認してください。

- 各カテゴリの件数が想定どおりか
- `99_未分類` が多すぎないか（目安：全体の2割を超えたらキーワードを足す）
- 重複・インストーラの件数

`99_未分類` が多い場合は、その中身を見てキーワードを追加し、**もう一度予行演習から**やり直します。

未分類が十分減るまで、ここを繰り返してください。ここが品質を決めます。

---

## 6. インストール

ユーザーの承認を得てから実行します。

```bash
./install.sh rules.json
```

これで次の4つが行われます。

① ランチャーをビルド（Intel + Apple Silicon 両対応）
② `~/Applications/DownloadsOrganizer.app` を配置
③ `~/Library/Application Support/DownloadsOrganizer/` に本体と設定を配置
④ 毎月1日 9:00 の定期実行を登録

---

## 7. 初回の本実行

```bash
python3 ~/Library/Application\ Support/DownloadsOrganizer/organize.py \
  --config ~/Library/Application\ Support/DownloadsOrganizer/rules.json --go
```

終わったら結果を確認して、ユーザーに報告してください。

```bash
cd ~/Downloads && for d in */; do printf "%-32s %4d件 %8s\n" "$d" "$(find "$d" -type f ! -name '.DS_Store' | wc -l | tr -d ' ')" "$(du -sh "$d" | cut -f1)"; done
echo "直下の残り: $(find . -maxdepth 1 -type f ! -name '.*' | wc -l | tr -d ' ')件"
```

### 隔離した重複が安全か検証する（必ずやる）

隔離した重複ファイルは、本体が別フォルダに必ず残っているはずです。確認してください。

```bash
python3 - <<'EOF'
import os,hashlib
D=os.path.expanduser('~/Downloads'); Q=os.path.join(D,'_整理待ち','重複')
def h(p):
    m=hashlib.md5()
    with open(p,'rb') as f:
        while c:=f.read(1<<20): m.update(c)
    return m.hexdigest()
kept=set()
for r,_,fs in os.walk(D):
    if r.startswith(Q): continue
    for n in fs:
        p=os.path.join(r,n)
        try:
            if os.path.getsize(p)>=1024: kept.add(h(p))
        except OSError: pass
miss=[n for n in os.listdir(Q) if os.path.isfile(os.path.join(Q,n)) and h(os.path.join(Q,n)) not in kept]
print(f"隔離{len(os.listdir(Q))}件 / 本体が残っていないもの: {len(miss)}件")
for m in miss: print("  !!", m)
EOF
```

`0件` でなければ**ユーザーに即報告**してください。0件なら安全です。

---

## 8. フルディスクアクセスの許可（人の手が必要な唯一の場所）

自動実行はmacOSのプライバシー保護に阻まれます。ユーザーに次を案内してください。

① システム設定 →「プライバシーとセキュリティ」→「フルディスクアクセス」
② 「＋」を押す
③ Finderで `command + shift + G` → `~/Applications` と入力
④ `DownloadsOrganizer` を選んで「開く」
⑤ スイッチをONにする

---

## 9. 自動実行のテスト（ここまでやって完了）

許可が終わったら、実際に定期実行の経路で動くか確認します。

```bash
SUP="$HOME/Library/Application Support/DownloadsOrganizer"
: > "$SUP/run.out"
launchctl kickstart -k gui/$(id -u)/com.aidiv.downloads-organizer
sleep 5
cat "$SUP/run.out"
launchctl list com.aidiv.downloads-organizer | grep LastExitStatus
```

**`LastExitStatus = 0` なら成功です。**

`run.out` に `PermissionError` が出ていたら、許可が効いていません。→ 11章へ。

---

## 10. ユーザーへの最終報告に必ず含めること

- 整理前後の件数と容量
- 作られたフォルダの一覧
- `_整理待ち` の中身は**削除していない**こと。捨てる判断はユーザーがすること
- 次回の自動実行日
- 手動実行のコマンド（予行演習と本実行の2つ）
- ログの場所：`~/Library/Application Support/DownloadsOrganizer/organize.log`

---

## 11. トラブルシューティング

### `PermissionError: Operation not permitted: '/Users/xxx/Downloads'`

フルディスクアクセスが効いていません。原因は次のどれかです。

① 許可を入れていない → 8章をやり直す
② アプリを再ビルドした後に、許可を入れ直していない
　※中身が変わると許可が無効になります。**古い項目を「−」で削除してから、＋で入れ直す**
③ アプリを移動・改名した → パスに紐づくため無効になる。元に戻すか入れ直す

### 許可を入れたのに通らない

ランチャーが `exec` でpython3に置き換わっていないか確認してください。
`launcher.c` は `fork` + `execv` で**子プロセス**として起動する実装になっています。
これはシェルスクリプトのランチャーでは許可が効かないためです。作り直さないこと。

### `99_未分類` が多すぎる

キーワード不足です。5章に戻ってキーワードを追加し、予行演習からやり直してください。
※すでに `99_未分類` に入ったファイルは自動では再分類されません。手動で直下に戻してから再実行します

### `install.sh` が `Operation not permitted` / `killed` で止まる

ダウンロードしたファイルに検疫属性（quarantine）が付いています。フォルダごと外してください。

```bash
xattr -dr com.apple.quarantine .
```

外した後、もう一度 `./install.sh rules.json` を実行します。

### 配布したアプリが「開発元を確認できません」と出る

このツールはインストール先でビルドするため、通常は出ません。
ビルド済みの `.app` を直接配った場合に出ます。その場合は配らず、`install.sh` から入れ直してください。

### 撤去したい

```bash
./uninstall.sh
```

仕分け済みのファイルには触りません。ツール本体だけが消えます。

---

## 12. 設計の背景（変更を検討する人へ）

なぜこの形かの理由です。触る前に読んでください。

| 決めごと | 理由 |
|---|---|
| 削除しない | 誤判定は必ず起きる。取り返しがつかない操作をツールに持たせない |
| 直近24時間は動かさない | 「いまダウンロードして作業中」のファイルが消えたように見えるのを防ぐ |
| 仕分け済みフォルダを触らない | 何度実行しても結果が変わらない（冪等）。事故と混乱を防ぐ |
| 重複判定は中身のハッシュ | ファイル名が違う同一ファイルを捕まえるため。名前だけでは漏れる |
| ランチャーがCバイナリ | シェルスクリプトだとフルディスクアクセスの許可が引き継がれないため |
| 月1回・9:00 | 週1だと通知疲れ、年1だと溜まりすぎる。月初の朝が区切りとして自然 |
