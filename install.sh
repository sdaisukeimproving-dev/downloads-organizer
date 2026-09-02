#!/bin/zsh
# downloads-organizer インストーラ
#   usage: ./install.sh /path/to/rules.json
# 何をするか:
#   ① ランチャーを Intel + Apple Silicon 両対応でビルド
#   ② ~/Applications/DownloadsOrganizer.app として配置
#   ③ organize.py と rules.json を Application Support へ配置
#   ④ 毎月1日 9:00 の LaunchAgent を登録
# 削除も上書きも、この4つ以外は行わない。
set -e

HERE="${0:A:h}"
RULES="${1:-$HERE/rules.json}"
APP="$HOME/Applications/DownloadsOrganizer.app"
SUP="$HOME/Library/Application Support/DownloadsOrganizer"
LABEL="com.aidiv.downloads-organizer"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

[[ -f "$RULES" ]] || { echo "エラー: rules.json がありません: $RULES"; exit 1; }
python3 -c "import json,sys;json.load(open(sys.argv[1],encoding='utf-8'))" "$RULES" \
  || { echo "エラー: rules.json が壊れています"; exit 1; }

echo "① ランチャーをビルド"
mkdir -p "$APP/Contents/MacOS"
ARCHS=(-arch arm64)
if xcrun --show-sdk-path >/dev/null 2>&1; then ARCHS=(-arch arm64 -arch x86_64); fi
clang -O2 $ARCHS -o "$APP/Contents/MacOS/DownloadsOrganizer" "$HERE/launcher.c" 2>/dev/null \
  || clang -O2 -o "$APP/Contents/MacOS/DownloadsOrganizer" "$HERE/launcher.c"
echo "   対応CPU: $(lipo -archs "$APP/Contents/MacOS/DownloadsOrganizer")"

cat > "$APP/Contents/Info.plist" <<'PLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>DownloadsOrganizer</string>
  <key>CFBundleDisplayName</key><string>DownloadsOrganizer</string>
  <key>CFBundleIdentifier</key><string>com.aidiv.downloads-organizer</string>
  <key>CFBundleExecutable</key><string>DownloadsOrganizer</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>LSUIElement</key><true/>
</dict>
</plist>
PLEOF
codesign --force --deep -s - "$APP" >/dev/null 2>&1 && echo "   署名OK (ad-hoc)"

echo "② 本体と設定を配置"
mkdir -p "$SUP"
cp "$HERE/organize.py" "$SUP/organize.py"
if [[ -f "$SUP/rules.json" && "$RULES" != "$SUP/rules.json" ]]; then
  cp "$SUP/rules.json" "$SUP/rules.json.bak.$(date +%Y%m%d%H%M%S)"
  echo "   既存 rules.json を .bak に退避"
fi
[[ "$RULES" != "$SUP/rules.json" ]] && cp "$RULES" "$SUP/rules.json"
echo "   $SUP"

echo "③ 定期実行を登録（毎月1日 9:00）"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLEOF2
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$APP/Contents/MacOS/DownloadsOrganizer</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Day</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$SUP/launchd.out</string>
  <key>StandardErrorPath</key><string>$SUP/launchd.err</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
PLEOF2
plutil -lint "$PLIST" >/dev/null
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "   登録OK"

echo
echo "───────────────────────────────"
echo "インストール完了。残り1つ、人の手が必要です。"
echo
echo "フルディスクアクセスを許可してください（1回だけ）"
echo "  ① システム設定 → プライバシーとセキュリティ → フルディスクアクセス"
echo "  ② ＋ を押す"
echo "  ③ Finderで command+shift+G → ~/Applications と入力"
echo "  ④ DownloadsOrganizer を選んで「開く」"
echo "  ⑤ スイッチをONにする"
echo
echo "許可なしでも手動実行は動きます。自動実行だけが失敗します。"
echo "───────────────────────────────"
