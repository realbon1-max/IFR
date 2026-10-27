# IFRブリーフィング

日本国内のIFR飛行計画を、ルート・気象・出発（SID）・航空路・到着（STAR）・進入・代替・燃料・飛行計画・FMS入力・管制交信まで一か所で確認するためのウェブアプリ（PWA）。

- 開く：https://realbon1-max.github.io/IFR/
- iPhone/iPad：Safari で開き「共有」→「ホーム画面に追加」
- Android：Chrome で開き「アプリをインストール」
- 一度開けば、電波がなくても起動します（気象の取得を除く）。

## 気象
`.github/workflows/wx.yml` が10分ごとに全127飛行場の METAR/TAF（気象庁発表の報を NOAA Aviation Weather Center が中継したもの）を取得し、`wx` ブランチの `wx.json` に置きます。アプリはこれを読み、MetAir から貼り付けた報があればそちらを優先します。自動取得の報は参考です。

運航の判断は必ず MetAir・最新の AIP / NOTAM・公式チャートで行ってください。航空路誌データは AIRAC 2026-10-01 版。
