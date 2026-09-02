#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
downloads-organizer : 対象フォルダを rules.json のルールで自動仕分けする。

設計上の約束（変更しないこと）:
  - 削除は一切しない。重複とインストーラは隔離フォルダへ移すだけ。
  - 仕分け済みフォルダの中身は触らない（何度実行しても荒れない＝冪等）。
  - 直近 N 時間に触ったファイルは動かさない（作業中のファイル保護）。

使い方:
  python3 organize.py            予行演習（1件も動かさず、結果だけ表示）
  python3 organize.py --go       実行
  python3 organize.py --config /path/to/rules.json
"""
import os, re, sys, json, time, shutil, hashlib, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.avif', '.heic', '.bmp', '.tiff')


def load_config(path):
    with open(path, encoding='utf-8') as f:
        cfg = json.load(f)
    cfg.setdefault('target_dir', '~/Downloads')
    cfg.setdefault('min_age_hours', 24)
    cfg.setdefault('quarantine_dir', '_整理待ち')
    cfg.setdefault('duplicates_dir', '重複')
    cfg.setdefault('installers_dir', 'インストーラ')
    cfg.setdefault('installer_ext', ['.dmg', '.pkg'])
    cfg.setdefault('image_fallback', '')
    cfg.setdefault('fallback', '99_未分類')
    cfg.setdefault('categories', [])
    cfg.setdefault('log_path', '~/Library/Application Support/DownloadsOrganizer/organize.log')
    return cfg


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def managed_names(cfg):
    """このツールが作ったフォルダ＝中身を触らない対象。"""
    names = {cfg['quarantine_dir'], cfg['fallback']}
    if cfg['image_fallback']:
        names.add(cfg['image_fallback'])
    names |= {c['folder'] for c in cfg['categories']}
    return names


def classify(name, cfg):
    low = name.lower()
    for c in cfg['categories']:
        if any(k.lower() in low for k in c.get('keywords', [])):
            return c['folder']
    if cfg['image_fallback'] and low.endswith(IMG_EXT):
        return cfg['image_fallback']
    return cfg['fallback']


def safe_move(src, dest_dir, dry):
    """同名があっても上書きしない。必ず別名で退避する。"""
    if dry:
        return
    os.makedirs(dest_dir, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(src))
    dst = os.path.join(dest_dir, os.path.basename(src))
    i = 1
    while os.path.exists(dst):
        dst = os.path.join(dest_dir, f"{base}_dup{i}{ext}")
        i += 1
    shutil.move(src, dst)


def run(cfg, dry):
    D = os.path.expanduser(cfg['target_dir'])
    if not os.path.isdir(D):
        return [f"対象フォルダが見つかりません: {D}"], False

    managed = managed_names(cfg)
    cutoff = time.time() - cfg['min_age_hours'] * 3600

    # --- 対象の切り出し（直下のみ・未仕分けのみ・新しすぎるものは除外） ---
    targets, held = [], 0
    for n in sorted(os.listdir(D)):
        if n.startswith('.') or n in managed:
            continue
        try:
            if os.path.getmtime(os.path.join(D, n)) > cutoff:
                held += 1
                continue
        except OSError:
            continue
        targets.append(n)

    if not targets:
        return [f"対象なし（直近{cfg['min_age_hours']}hのため保留: {held}件）"], True

    # --- 仕分け済みファイルのハッシュ（重複判定の参照用。これらは動かさない） ---
    filed = set()
    for n in managed:
        d = os.path.join(D, n)
        if not os.path.isdir(d):
            continue
        for root, _, fs in os.walk(d):
            for f in fs:
                p = os.path.join(root, f)
                try:
                    if os.path.getsize(p) >= 1024:
                        filed.add(md5(p))
                except OSError:
                    pass

    dups, insts, moves, seen = [], [], {}, set()
    inst_ext = tuple(e.lower() for e in cfg['installer_ext'])
    for n in targets:
        p = os.path.join(D, n)
        if os.path.isfile(p):
            if n.lower().endswith(inst_ext):
                insts.append(n)
                continue
            try:
                if os.path.getsize(p) >= 1024:
                    h = md5(p)
                    if h in filed or h in seen:
                        dups.append(n)
                        continue
                    seen.add(h)
            except OSError:
                pass
        moves.setdefault(classify(n, cfg), []).append(n)

    # --- 実行 ---
    qdir = os.path.join(D, cfg['quarantine_dir'])
    lines = []
    for names, dest, label in ((dups, os.path.join(qdir, cfg['duplicates_dir']), '重複'),
                               (insts, os.path.join(qdir, cfg['installers_dir']), 'インストーラ')):
        if names:
            lines.append(f"{label}: {len(names)}件 → {os.path.relpath(dest, D)}")
            for n in names:
                safe_move(os.path.join(D, n), dest, dry)
    for folder in sorted(moves):
        lines.append(f"{folder}: {len(moves[folder])}件")
        for n in moves[folder]:
            safe_move(os.path.join(D, n), os.path.join(D, folder), dry)
    if held:
        lines.append(f"（直近{cfg['min_age_hours']}hのため保留: {held}件）")
    return lines, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--go', action='store_true', help='実際に移動する（付けなければ予行演習）')
    ap.add_argument('--config', default=os.path.join(HERE, 'rules.json'))
    a = ap.parse_args()

    if not os.path.exists(a.config):
        print(f"設定ファイルがありません: {a.config}")
        sys.exit(2)

    cfg = load_config(a.config)
    lines, ok = run(cfg, dry=not a.go)
    head = f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {'実行' if a.go else '予行演習'}"
    print(head)
    for l in lines:
        print("  " + l)

    if a.go:
        log = os.path.expanduser(cfg['log_path'])
        try:
            os.makedirs(os.path.dirname(log), exist_ok=True)
            with open(log, 'a', encoding='utf-8') as f:
                f.write(head + "\n" + "\n".join("  " + l for l in lines) + "\n")
        except OSError:
            pass
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
