# AIP 更新パイプライン

`run.sh` が AIP Japan の AD 2（飛行場ごとのPDF、`ICAO__YYYYMMDD` フォルダ）から次を作り直し、`index.html` に書き込みます。

- 手順の経路・高度（コーディング表）`PLD`、fix座標 `PCD`
- SIDの滑走路の補完（`DB` のSID）
- チャート画像 `charts/`（AD 2 の日付が変わった飛行場だけ）と索引 `CHX`
- AIRAC の有効日

自動で更新しないもの：飛行場の基本データ（滑走路・周波数・手順一覧・ミニマ）、航空路・fix・管制区、従来型進入の形（`CVD`, `ARCP`）。

GitHub Actions の「AIP update」から実行すると、変更点のレポート付きでプルリクエストを作ります。
