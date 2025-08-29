from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QSize
from PyQt6.QtPrintSupport import QPrinter

def _choose_path(parent, title, filters, default_ext):
    path, sel = QFileDialog.getSaveFileName(parent, title, filter=filters)
    if not path:
        return None
    if '.' not in path.split('/')[-1]:
        path = f"{path}.{default_ext}"
    return path

def _render_widget_to_pdf(widget, out_path):
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(out_path)
    # A4 size in points ~ 2480x3508 at 300dpi, but QPrinter handles auto scaling
    painter = QPainter(printer)
    widget.render(painter)
    painter.end()

def _render_widget_to_image(widget, out_path):
    pm = widget.grab()  # QPixmap
    pm.save(out_path)

def export_invoice_pdf(parent):
    path = _choose_path(parent, "ذخیره PDF فاکتور", "PDF Files (*.pdf)", "pdf")
    if not path: return
    _render_widget_to_pdf(parent.centralWidget(), path)
    QMessageBox.information(parent, "فایل ذخیره شد", f"PDF در مسیر\n{path}\nذخیره شد.")

def export_invoice_image(parent):
    path = _choose_path(parent, "ذخیره تصویر فاکتور", "Images (*.png *.jpg)", "png")
    if not path: return
    _render_widget_to_image(parent.centralWidget(), path)
    QMessageBox.information(parent, "فایل ذخیره شد", f"عکس در مسیر\n{path}\nذخیره شد.")

def export_report_pdf(parent):
    path = _choose_path(parent, "ذخیره PDF گزارش", "PDF Files (*.pdf)", "pdf")
    if not path: return
    _render_widget_to_pdf(parent.centralWidget(), path)
    QMessageBox.information(parent, "فایل ذخیره شد", f"PDF در مسیر\n{path}\nذخیره شد.")

def export_report_image(parent):
    path = _choose_path(parent, "ذخیره تصویر گزارش", "Images (*.png *.jpg)", "png")
    if not path: return
    _render_widget_to_image(parent.centralWidget(), path)
    QMessageBox.information(parent, "فایل ذخیره شد", f"عکس در مسیر\n{path}\nذخیره شد.")
