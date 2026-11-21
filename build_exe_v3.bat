@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================
echo  Hand Tetris - exe ビルド (Windows用)
echo ============================================
echo.

rem --- Python の検出 (py ランチャー優先、なければ python) ---
set "PY="
py -3 --version > nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python --version > nul 2>&1
    if not errorlevel 1 set "PY=python"
)
rem --- PATH に無い場合: 標準のインストール先を探す ---
if not defined PY (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set PY="%%D\python.exe"
    )
)
if not defined PY (
    for /d %%D in ("C:\Program Files\Python3*") do (
        if exist "%%D\python.exe" set PY="%%D\python.exe"
    )
)
if not defined PY (
    echo [エラー] Python が見つかりません。
    echo   Pythonをインストールするか、PATHの設定を確認してください。
    pause
    exit /b 1
)
echo 使用するPython:
%PY% --version
%PY% -c "import sys; print(sys.executable)"
echo.

rem --- ライブラリ確認 (入っていないものだけインストール) ---
set "FAILED="
echo [1/4] ライブラリを確認しています...
call :ensure cv2 opencv-python
call :ensure mediapipe mediapipe
call :ensure numpy numpy
call :ensure pygame pygame
call :ensure PIL pillow
call :ensure PyInstaller pyinstaller

if defined FAILED (
    echo.
    echo [エラー] 次のライブラリのインストールに失敗しました:%FAILED%
    echo   上に表示された赤字/エラー文を確認してください。
    echo   原因の例: ネットワーク制限、プロキシ、Pythonのバージョン非対応
    pause
    exit /b 1
)

rem --- モデルファイル ---
echo.
echo [2/4] モデルファイルを確認しています...
if not exist hand_landmarker.task (
    echo   hand_landmarker.task をダウンロードします...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task' -OutFile 'hand_landmarker.task'"
)
if not exist pose_landmarker_lite.task (
    echo   pose_landmarker_lite.task をダウンロードします...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task' -OutFile 'pose_landmarker_lite.task'"
)
if not exist hand_landmarker.task (
    echo [エラー] hand_landmarker.task がありません。ブラウザで手動ダウンロードして同じフォルダに置いてください。
    pause
    exit /b 1
)
if not exist pose_landmarker_lite.task (
    echo [エラー] pose_landmarker_lite.task がありません。ブラウザで手動ダウンロードして同じフォルダに置いてください。
    pause
    exit /b 1
)

rem --- ビルド ---
echo.
echo [3/4] exe を作成しています(数分かかります)...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name HandTetris --collect-all mediapipe --add-data "hand_landmarker.task;." --add-data "pose_landmarker_lite.task;." hand_tetris.py
if errorlevel 1 (
    echo [エラー] exe の作成に失敗しました。上のエラー文を確認してください。
    pause
    exit /b 1
)

echo.
echo [4/4] 完了しました。
echo   dist\HandTetris.exe を配布してください(モデルは exe に同梱済みです)。
echo.
pause
exit /b 0

:ensure
rem 引数1=import名, 引数2=pipパッケージ名
%PY% -c "import %1" > nul 2>&1
if not errorlevel 1 (
    echo   %2 : OK (インストール済み)
    goto :eof
)
echo   %2 をインストールします...
%PY% -m pip install %2
if errorlevel 1 (
    echo   [失敗] %2
    set "FAILED=!FAILED! %2"
)
goto :eof
