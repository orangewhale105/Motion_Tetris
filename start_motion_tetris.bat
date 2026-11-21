@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

rem ============================================================
rem  モーションテトリス 起動用(どのPCでもこれをダブルクリック)
rem   1. GitHub から最新版を取得(初回はダウンロード、2回目以降は更新)
rem   2. 足りないライブラリとモデルファイルを自動で用意
rem   3. ゲームを起動
rem  このファイルだけを別のPCに置いて実行してもよい(そのときは
rem  %USERPROFILE%\Motion_Tetris にダウンロードする)。
rem ============================================================

rem --- 更新(git pull)でこのファイル自身が書き換わっても止まらないよう、一時コピーから実行する ---
if /i not "%~1"=="--from-temp" (
    copy /y "%~f0" "%TEMP%\motion_tetris_start.bat" > nul
    call "%TEMP%\motion_tetris_start.bat" --from-temp "%~dp0"
    exit /b
)

set "HERE=%~2"
set "REPO_URL=https://github.com/orangewhale105/Motion_Tetris.git"
if exist "%HERE%.git" if exist "%HERE%hand_tetris.py" (
    set "REPO=%HERE%"
) else (
    set "REPO=%USERPROFILE%\Motion_Tetris\"
)
if not defined REPO set "REPO=%USERPROFILE%\Motion_Tetris\"

echo ============================================
echo  モーションテトリス 起動
echo  フォルダ: %REPO%
echo ============================================
echo.

rem --- [1/5] Git ---
echo [1/5] Git を確認しています...
git --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Git が入っていません。
    echo   https://git-scm.com/download/win からインストールして、もう一度実行してください。
    pause
    exit /b 1
)

rem --- [2/5] 最新版の取得 ---
echo.
echo [2/5] GitHub から最新版を取得しています...
if not exist "%REPO%.git" (
    if exist "%REPO%hand_tetris.py" (
        echo [エラー] %REPO% に GitHub 管理でないファイルがあります。
        echo   フォルダ名を変えるか削除してから、もう一度実行してください。
        pause
        exit /b 1
    )
    echo   初回のためダウンロードします。GitHub へのログイン画面が出たらログインしてください。
    git clone "%REPO_URL%" "%REPO:~0,-1%"
    if errorlevel 1 (
        echo [エラー] ダウンロードに失敗しました。ネットワークと GitHub のログインを確認してください。
        pause
        exit /b 1
    )
)
cd /d "%REPO%"
git checkout -q main
git pull --ff-only
if errorlevel 1 (
    echo.
    echo [注意] 最新版を取得できませんでした(ネットワーク未接続、またはこのPCで変更したファイルがある)。
    echo   今このPCにある版で起動します。
    echo.
)

rem --- [3/5] Python ---
echo.
echo [3/5] Python とライブラリを確認しています...
set "PY="
py -3 --version > nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python --version > nul 2>&1
    if not errorlevel 1 set "PY=python"
)
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
    echo   https://www.python.org/downloads/ からインストールして、もう一度実行してください。
    pause
    exit /b 1
)
set "FAILED="
call :ensure cv2 opencv-python
call :ensure mediapipe mediapipe
call :ensure numpy numpy
call :ensure pygame pygame
call :ensure PIL pillow
if defined FAILED (
    echo [エラー] 次のライブラリのインストールに失敗しました:%FAILED%
    pause
    exit /b 1
)

rem --- [4/5] モデルファイル(GitHubには置いていないので、無ければダウンロード) ---
echo.
echo [4/5] モデルファイルを確認しています...
if not exist hand_landmarker.task (
    echo   hand_landmarker.task をダウンロードします...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task' -OutFile 'hand_landmarker.task'"
)
if not exist pose_landmarker_lite.task (
    echo   pose_landmarker_lite.task をダウンロードします...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task' -OutFile 'pose_landmarker_lite.task'"
)
if not exist hand_landmarker.task goto :model_error
if not exist pose_landmarker_lite.task goto :model_error

rem --- [5/5] 起動 ---
echo.
echo [5/5] 起動します...
%PY% hand_tetris.py
if errorlevel 1 (
    echo.
    echo [エラー] 異常終了しました。上のエラー文を確認してください。
    pause
)
exit /b 0

:model_error
echo [エラー] モデルファイルを用意できませんでした。ネットワークを確認してください。
pause
exit /b 1

:ensure
rem 引数1=import名, 引数2=pipパッケージ名
%PY% -c "import %1" > nul 2>&1
if not errorlevel 1 (
    echo   %2 : OK
    goto :eof
)
echo   %2 をインストールします...
%PY% -m pip install %2
if errorlevel 1 set "FAILED=!FAILED! %2"
goto :eof
