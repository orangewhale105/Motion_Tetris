# モーションテトリス

カメラで全身を認識し、足のステップ・スクワット・万歳でブロックを操作するテトリス(旧称 Hand Tetris)。
授業・オープンキャンパスでの体験用。ステップ数・スクワット数・上肢挙上数などの運動の記録も表示します。
詳しい仕様と経緯は `CLAUDE.md`、変更履歴は `CHANGELOG.md`。

## ダウンロードと起動
1. Releases の最新版から `hand_tetris.py` をダウンロードする。
   - 直接ダウンロード: https://github.com/orangewhale105/Motion_Tetris/releases/latest/download/hand_tetris.py
   - 版の一覧: https://github.com/orangewhale105/Motion_Tetris/releases
2. ダウンロードした `hand_tetris.py` をダブルクリックする。
   - 必要なのは Python(公式インストーラー)だけ。初回は足りないライブラリとモデルファイルを自動で用意する(インターネット接続が必要・数分)。
   - ダウンロードフォルダに古い `hand_tetris.py` があると `hand_tetris (1).py` になる。古いほうは削除する。
   - ダブルクリックでメモ帳などが開くときは、右クリック →「プログラムから開く」→「Python」。

## 遊び方
カメラに全身(足首〜万歳した手)が映る距離に立つ。

| 動作 | 操作 |
|---|---|
| 右足を右へ踏み出す → 足を揃える | 1マス右 |
| 左足を左へ踏み出す → 足を揃える | 1マス左 |
| ハーフスクワット | 回転 |
| 両手を万歳して下ろす | 一気に落下 |
| ジャンプ(タイトル・結果画面) | スタート |
| 両足を揃えて両手を横に伸ばす(1秒) | キャリブレーション |

キー: S=スタート、P=一時停止、C=キャリブレーション、Q / Esc / ×=終了。

## ファイル
- `hand_tetris.py` 本体(1ファイル)
- `tests/` 自動テスト(`python -m unittest discover tests`)
- `.github/workflows/release.yml` 配布ファイルを作る仕組み(main に取り込むと Releases に自動で置く)
- `build_exe_v3.bat` exe を作るとき用(Windows 上で実行)
