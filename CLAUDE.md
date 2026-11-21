# モーションテトリス(旧称 Hand Tetris)

カメラで全身を認識し、足のステップ・スクワット・万歳でブロックを操作するテトリス。
作者: 石田(Dr. Ishida)。授業・オープンキャンパスでの体験用。学生のPC(Python未導入のWindows)にexeで配布する。

## 進め方のルール(ユーザーの希望)
- 呼称は「Dr. Ishida」、日本語で応答する。
- Pythonアプリは **1ファイル(hand_tetris.py)** にまとめる。モジュール分割しない。
- 事実に基づかない推測を足さない。簡潔に。
- 変更後は必ず `python -m py_compile hand_tetris.py` で構文確認し、実機で確認すべき点は「未確認」と明記する。
- 通常の仕様変更の成果物は、Python導入済みのPC(Dr. Ishidaの開発PC)で `python hand_tetris.py` として動くコードでよい。exeは作らない。
- 「実行形式にして」と指示されたときだけ、Python環境のないPC向けのexeも合わせて用意する(ビルドはWindows上で行う。「exe配布」の節を参照)。

## リポジトリ
GitHub: orangewhale105/Motion_Tetris(Private)。`.task` モデルとビルド成果物(build/・dist/・*.spec)は .gitignore で除外。

### 開発の流れ(GitHubで開発)
- 作業開始前に `git pull`、作業終了時に必ずコミットして `git push`(自宅・職場の複数PCで作業するため)。
- ブランチは当面 `main` のみ。
- コミット前に `python -m py_compile hand_tetris.py` で構文確認。
- 初回セットアップ: clone → `pip install opencv-python mediapipe numpy pygame pillow` → モデル2つを同じフォルダに置く(`build_exe_v3.bat` を実行すると自動ダウンロード)→ `python hand_tetris.py`。

## ファイル
| ファイル | 役割 |
|---|---|
| hand_tetris.py | 本体(約1180行、単一ファイル) |
| hand_landmarker.task | 手検出モデル(ワイヤーフレーム表示用) |
| pose_landmarker_lite.task | 姿勢検出モデル(操作・肩角度用) |
| build_exe_v3.bat | exeビルド用(モデルは自動ダウンロード) |

プロジェクト名は「モーションテトリス」。ファイル名・exe名(HandTetris)・ウィンドウタイトルは旧称のまま。改名するなら hand_tetris.py、bat、HandTetris.spec をまとめて直す。

## 実行
```
pip install opencv-python mediapipe numpy pygame pillow
python hand_tetris.py
```
モデル2つを同じフォルダに置く。URLは hand_tetris.py 冒頭のdocstringにある。
開発PCはWindows、Python 3.13(`C:\Users\user\AppData\Local\Programs\Python\Python313\`、PATH未登録)。作業フォルダは現在 `C:\Users\user\Downloads`。

## 操作仕様(現行)
カメラに全身(股関節〜足首、万歳しても収まる高さ)が映る距離に立つ。

| 動作 | ブロック |
|---|---|
| 右足を右へ踏み出す→足を揃える→また踏み出す | 1マス右 |
| 左足を左へ踏み出す→足を揃える→また踏み出す | 1マス左 |
| ハーフスクワット | 90度回転 |
| 両手を肩より高く上げて、肩付近まで下ろした瞬間 | ハードドロップ |

キー: Q / Esc / ウィンドウの「×」=終了、R=ゲームオーバー後に再開、P=一時停止、C=基準姿勢の再キャリブレーション。
手のワイヤーフレームは視覚効果のみで、**操作には使わない**。

## 構成(hand_tetris.py)
- サウンド: numpyで波形生成(外部音源なし)。`make_tone/make_chord/make_sequence/make_sweep`。pygameミキサーはステレオ(2ch)初期化。BGMは別スレッドでループ。
- `TetrisGame`: 盤面10x20、7種バッグ、ゴースト、ロックディレイ0.4秒、ウォールキック。落下間隔は 1.3秒−レベル×0.07秒(最速0.35秒)。
- `HandController`: MediaPipe HandLandmarker(Tasks API、VIDEOモード)。表示専用。
- `PoseController`: PoseLandmarker(Tasks API、VIDEOモード)。画像座標とworld座標を返す。
- `shoulder_flexion_abduction`: 肩の屈曲・外転角を体幹基準の座標系で算出し、HUDと肩の位置に表示。
- `BodyGestureController`: ステップ・スクワット・万歳の検出(状態機械)。
- `draw_board_overlay`: 盤面をカメラ映像に半透明合成。セルサイズは縦幅いっぱいに毎フレーム再計算(上余白140px、下余白85px)。カメラは1920x1080を要求。
- `resolve_model_path` / `show_error`: exe(PyInstaller)対応。モデルは `sys._MEIPASS` を優先して探す。

## ジェスチャー検出の設計判断(変えるときは理由を確認すること)
しきい値は `BodyGestureController` 直前の定数(`STEP_OUT_THRESH=0.035`、`STEP_RESET_THRESH=0.018`、`SQUAT_DOWN_THRESH=0.030`、`SQUAT_UP_THRESH=0.012`、`BANZAI_RAISE_MARGIN=0.12`、`BANZAI_LOWER_MARGIN=0.04`)。

- **キャリブレーション**: 起動後と C キー後の30フレームで、直立・足を揃えた姿勢の平均を基準にする。その間は判定しない。1フレーム目をそのまま基準にすると、ステップ/スクワットが反応しなかったため。基準は `BASELINE_EMA_ALPHA=0.01` で緩やかに追従。
- **左右の足の対応はキャリブレーション時に1回だけ固定**: 毎フレームx座標の大小で左右を決めると、足を揃える付近で入れ替わり、左ステップから戻る動きが右ステップと誤認識された。
- **足の移動量は各足の基準位置からの絶対移動量**: 股関節中心からの相対距離だと、体幹の重心移動が反対側の足の値に混ざった。
- **ステップは1回ごとに足を揃えるまで再発火しない**(踏み出したままでは連続移動しない)。
- **万歳はトリガーを「上げた」ではなく「下ろした瞬間」**。肩の高さ基準で、カメラ距離の影響を受けにくくしている。
- 画面左上に灰色の `[debug]` 行(右足Δ・左足Δ・腰の下がりΔと閾値)を出している。

## 実機確認の状況
- 確認済み(Dr. Ishida): exeのビルドと起動。
- **未確認**: 左右ステップ誤認識の修正後の動作、キャリブレーション導入後のスクワット反応、Esc/「×」終了、万歳のハードドロップ。これまでのテストは、合成した姿勢データでの論理検証のみ。
- ウィンドウタイトルが旧称「Hand Tetris - 手でつかんでテトリス」のまま(未修正)。

## 一度入れて取りやめたもの(再追加しない)
- 重心(COG)と支持基底面(BOS)の表示 → ユーザーの指示で削除。
- 手のピンチ・回内回外・ジャンプによる操作 → 全身操作への仕様変更で廃止(ジャンプはハードドロップを万歳に変更)。

## exe配布
ビルドは Python のあるPC(石田先生のPC)で行い、`dist\HandTetris.exe` だけを生徒に配る(Teams等)。生徒側はPythonもモデルも不要。
```
build_exe_v3.bat   # hand_tetris.py と同じフォルダに置いてダブルクリック
```
手動の場合:
```
python -m PyInstaller --noconfirm --clean --onefile --windowed --name HandTetris --collect-all mediapipe --add-data "hand_landmarker.task;." --add-data "pose_landmarker_lite.task;." hand_tetris.py
```
- exe約118MB。初回起動は数秒〜十数秒の見込み。起動を速くするなら `--onedir`。
- 学校PCのセキュリティで未署名exeが止まる可能性がある。
- 配布前に、コード変更のたびに再ビルドが必要。
- Linux環境(クラウド)ではWindows用exeを作れない。ビルドはWindows上で行う。

## 次の候補(Dr. Ishidaの指示待ち。決定事項ではない)
- 実機で上記の未確認項目を確認し、しきい値を調整する。
- ウィンドウタイトル・docstringの旧称を「モーションテトリス」に更新する。
- ファイル名・exe名の改名。
