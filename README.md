# Hesabdari App (PyQt6)

نسخه‌ی مینیمال برای اجرای محلی و ساخت exe با PyInstaller.

## اجرای محلی
```bash
pip install -r requirements.txt
python run.py
```

## ساخت exe
```bash
pyinstaller --name Hesabdari --onefile --noconsole --hidden-import PyQt6.QtPrintSupport run.py
```
