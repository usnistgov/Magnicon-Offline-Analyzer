set PYTHONHASHSEED=1
pyinstaller --clean --noconfirm --log-level=INFO --upx-dir=".\\upx-4.2.3-win64" Magnicon-Offline-Analyzer.spec
pause