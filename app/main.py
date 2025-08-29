import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QTabWidget,
    QMessageBox, QHBoxLayout, QComboBox, QDateEdit
)
from PyQt6.QtPrintSupport import QPrintDialog, QPrintPreviewDialog
from PyQt6.QtCore import Qt, QDate

from app.db import Database
from app.theme import apply_dark_blue_theme
from app.utils import (
    export_invoice_pdf, export_invoice_image,
    export_report_pdf, export_report_image
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نرم‌افزار حسابداری و فاکتور")
        self.resize(1100, 720)

        # DB
        self.db = Database()

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.add_dashboard_tab()
        self.add_company_tab()
        self.add_customers_tab()
        self.add_products_tab()
        self.add_invoice_tab()
        self.add_reports_tab()
        self.add_settings_tab()

    # Dashboard
    def add_dashboard_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        title = QLabel("نرم افزار حسابداری"); title.setProperty("title", True); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        self.tabs.addTab(w, "داشبورد")

    # Company
    def add_company_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        def add_row(lbl):
            lay.addWidget(QLabel(lbl))
            le = QLineEdit(); lay.addWidget(le); return le

        self.company_name_fa = add_row("نام شرکت (فارسی):")
        self.company_name_en = add_row("نام شرکت (انگلیسی):")
        self.company_phone   = add_row("تلفن:")
        self.company_address_fa = add_row("آدرس (فارسی):")
        self.company_address_en = add_row("آدرس (انگلیسی):")

        lay.addWidget(QLabel("VAT %")); self.vat_rate = QLineEdit("0"); lay.addWidget(self.vat_rate)

        btn = QPushButton("ذخیره"); btn.clicked.connect(lambda: QMessageBox.information(self, "ذخیره", "اطلاعات شرکت ذخیره شد."))
        lay.addWidget(btn)
        self.tabs.addTab(w, "اطلاعات شرکت")

    # Customers
    def add_customers_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        top = QHBoxLayout()
        self.customer_name = QLineEdit(); self.customer_name.setPlaceholderText("نام مشتری")
        self.customer_phone = QLineEdit(); self.customer_phone.setPlaceholderText("تلفن")
        self.customer_address = QLineEdit(); self.customer_address.setPlaceholderText("آدرس")
        self.customer_search = QLineEdit(); self.customer_search.setPlaceholderText("جستجو...")
        btn_add = QPushButton("افزودن"); btn_add.clicked.connect(self.add_customer)
        btn_search = QPushButton("جستجو"); btn_search.clicked.connect(self.refresh_customers)
        top.addWidget(self.customer_name); top.addWidget(self.customer_phone); top.addWidget(self.customer_address)
        top.addWidget(btn_add); top.addWidget(self.customer_search); top.addWidget(btn_search)
        lay.addLayout(top)

        self.table_customers = QTableWidget(); self.table_customers.setColumnCount(4)
        self.table_customers.setHorizontalHeaderLabels(["شناسه","نام","تلفن","آدرس"])
        lay.addWidget(self.table_customers)
        self.tabs.addTab(w, "مشتریان")
        self.refresh_customers()

    def add_customer(self):
        name = self.customer_name.text().strip()
        phone = self.customer_phone.text().strip()
        addr = self.customer_address.text().strip()
        if not name:
            QMessageBox.warning(self, "خطا", "نام مشتری را وارد کنید."); return
        self.db.add_customer(name, phone, addr)
        self.customer_name.clear(); self.customer_phone.clear(); self.customer_address.clear()
        self.refresh_customers()

    def refresh_customers(self):
        q = self.customer_search.text().strip() if hasattr(self, 'customer_search') else None
        rows = self.db.list_customers(q)
        self.table_customers.setRowCount(0)
        for r, (id_, name, phone, addr) in enumerate(rows):
            self.table_customers.insertRow(r)
            for c, val in enumerate([id_, name, phone, addr]):
                self.table_customers.setItem(r, c, QTableWidgetItem(str(val)))

    # Products
    def add_products_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        top = QHBoxLayout()
        self.product_name = QLineEdit(); self.product_name.setPlaceholderText("نام کالا")
        self.product_price = QLineEdit("0"); self.product_price.setPlaceholderText("قیمت واحد")
        self.product_search = QLineEdit(); self.product_search.setPlaceholderText("جستجوی کالا...")
        btn_add = QPushButton("افزودن"); btn_add.clicked.connect(self.add_product)
        btn_search = QPushButton("جستجو"); btn_search.clicked.connect(self.refresh_products)
        top.addWidget(self.product_name); top.addWidget(self.product_price); top.addWidget(btn_add)
        top.addWidget(self.product_search); top.addWidget(btn_search)
        lay.addLayout(top)

        self.table_products = QTableWidget(); self.table_products.setColumnCount(3)
        self.table_products.setHorizontalHeaderLabels(["شناسه","نام","قیمت واحد"])
        lay.addWidget(self.table_products)
        self.tabs.addTab(w, "کالاها")
        self.refresh_products()

    def add_product(self):
        name = self.product_name.text().strip()
        try:
            price = float(self.product_price.text().replace(',', ''))
        except ValueError:
            price = 0.0
        if not name:
            QMessageBox.warning(self, "خطا", "نام کالا را وارد کنید."); return
        self.db.add_product(name, price)
        self.product_name.clear(); self.product_price.setText("0")
        self.refresh_products()

    def refresh_products(self):
        q = self.product_search.text().strip() if hasattr(self, 'product_search') else None
        rows = self.db.list_products(q)
        self.table_products.setRowCount(0)
        for r, (id_, name, price) in enumerate(rows):
            self.table_products.insertRow(r)
            for c, val in enumerate([id_, name, f"{price:,.0f}"]):
                self.table_products.setItem(r, c, QTableWidgetItem(str(val)))

    # Invoice
    def add_invoice_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        row = QHBoxLayout()
        row.addWidget(QLabel("مشتری:")); self.invoice_customer = QLineEdit(); row.addWidget(self.invoice_customer)
        row.addWidget(QLabel("تاریخ:")); self.invoice_date = QDateEdit(QDate.currentDate()); self.invoice_date.setDisplayFormat("yyyy/MM/dd"); row.addWidget(self.invoice_date)
        lay.addLayout(row)

        # actions
        actions = QHBoxLayout()
        btn_save = QPushButton("ثبت فاکتور"); btn_save.clicked.connect(self.save_invoice)
        btn_prev = QPushButton("پیش‌نمایش چاپ"); btn_prev.clicked.connect(self.print_preview)
        btn_pdf  = QPushButton("PDF"); btn_pdf.clicked.connect(lambda: export_invoice_pdf(self))
        btn_img  = QPushButton("عکس"); btn_img.clicked.connect(lambda: export_invoice_image(self))
        actions.addWidget(btn_save); actions.addWidget(btn_prev); actions.addWidget(btn_pdf); actions.addWidget(btn_img)
        lay.addLayout(actions)

        self.tabs.addTab(w, "صدور فاکتور")

    def print_preview(self):
        dlg = QPrintPreviewDialog(self)
        dlg.paintRequested.connect(lambda printer: self.render(printer))
        dlg.exec()

    def save_invoice(self):
        cust = self.invoice_customer.text().strip() or "بدون نام"
        date = self.invoice_date.date().toString("yyyy/MM/dd")
        subtotal = 0.0; tax = 0.0; total = 0.0
        inv_id = self.db.save_invoice_basic(cust, date, subtotal, tax, total)
        QMessageBox.information(self, "ثبت شد", f"فاکتور شماره {inv_id} ذخیره شد.")

    # Reports
    def add_reports_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        btn_pdf = QPushButton("خروجی PDF گزارش"); btn_pdf.clicked.connect(lambda: export_report_pdf(self))
        btn_img = QPushButton("خروجی عکس گزارش"); btn_img.clicked.connect(lambda: export_report_image(self))
        lay.addWidget(btn_pdf); lay.addWidget(btn_img)
        self.tabs.addTab(w, "گزارش‌ها")

    # Settings
    def add_settings_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        # فقط چند دکمه کمکی
        btn_wipe = QPushButton("پاکسازی کامل دیتابیس"); btn_wipe.clicked.connect(self.confirm_wipe)
        lay.addWidget(btn_wipe)
        self.tabs.addTab(w, "تنظیمات")

    def confirm_wipe(self):
        if QMessageBox.question(self, "تأیید", "همه داده‌ها حذف شوند؟") == QMessageBox.StandardButton.Yes:
            self.db.wipe_all()
            self.refresh_customers(); self.refresh_products()
            QMessageBox.information(self, "انجام شد", "دیتابیس پاکسازی شد.")

def main():
    app = QApplication(sys.argv)
    apply_dark_blue_theme(app)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
