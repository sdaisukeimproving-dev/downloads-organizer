#!/bin/zsh
# downloads-organizer を完全に撤去する。
# 仕分け済みのファイルには一切触らない。ツール本体だけを消す。
LABEL="com.aidiv.downloads-organizer"
APP="$HOME/Applications/DownloadsOrganizer.app"
SUP="$HOME/Library/Application Support/DownloadsOrganizer"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null && echo "定期実行を解除"
[[ -f "$PLIST" ]] && rm -f "$PLIST" && echo "plist を削除"
[[ -d "$APP" ]] && rm -rf "$APP" && echo "アプリを削除"
echo
echo "設定とログは残しています: $SUP"
echo "不要なら手動で削除してください（rules.json の中身を先に確認すること）"
echo
echo "システム設定 → フルディスクアクセス に残った DownloadsOrganizer の項目は、"
echo "手動で「−」で削除してください。"
