import sys, os, csv
from pathlib import Path
from configparser import ConfigParser
from datetime import date

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFormLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QTabWidget, QComboBox, QDateEdit, QFileDialog, QDoubleSpinBox,
    QGroupBox
)
from PyQt6.QtCore import Qt, QLocale, QDate
from PyQt6.QtGui import QFont

from db import APP_DIR, USER_DB, USER_SETTINGS, get_sqlite_conn, get_access_conn, ensure_sqlite_schema
from lang import get_strings


def resource_path(rel: str) -> str:
    base = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
    return str(Path(base) / rel)


def load_settings() -> ConfigParser:
    cfg = ConfigParser()
    # Ensure user config exists
    if not USER_SETTINGS.exists():
        # copy defaults from assets if exists
        try:
            default_ini = Path(resource_path('assets')) / 'settings.ini'
            APP_DIR.mkdir(parents=True, exist_ok=True)
            if default_ini.exists():
                USER_SETTINGS.write_text(default_ini.read_text(encoding='utf-8'), encoding='utf-8')
            else:
                USER_SETTINGS.write_text('[app]\nlang=fa\n', encoding='utf-8')
        except Exception:
            USER_SETTINGS.write_text('[app]\nlang=fa\n', encoding='utf-8')
    cfg.read(USER_SETTINGS, encoding='utf-8')
    # Guarantee sections/keys
    if 'app' not in cfg:
        cfg['app'] = {}
    appsec = cfg['app']
    appsec.setdefault('lang', 'fa')
    appsec.setdefault('db_type', 'sqlite')
    appsec.setdefault('vat_percent', '9')
    appsec.setdefault('company_name_fa', 'شرکت نمونه')
    appsec.setdefault('company_name_en', 'Sample Co.')
    appsec.setdefault('company_phone', '021-12345678')
    appsec.setdefault('company_address_fa', 'تهران')
    appsec.setdefault('company_address_en', 'Tehran')
    appsec.setdefault('currency_symbol', 'ریال')
    if 'sqlite' not in cfg:
        cfg['sqlite'] = {'db_file': 'data.db'}
    if 'access' not in cfg:
        cfg['access'] = {'file_path': '', 'connection_string': ''}
    # Save back normalized settings
    with USER_SETTINGS.open('w', encoding='utf-8') as f:
        cfg.write(f)
    return cfg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_settings()
        self.lang = self.cfg['app'].get('lang', 'fa')
        self.s = get_strings(self.lang)
        self.setWindowTitle(self.s['app_title'])
        self.resize(1100, 720)

        # Language and RTL
        if self.lang == 'fa':
            QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            QLocale.setDefault(QLocale(QLocale.Language.Persian, QLocale.Country.Iran))
            self.setFont(QFont('Segoe UI', 10))  # Persian-friendly
        else:
            QApplication.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            QLocale.setDefault(QLocale(QLocale.Language.English))
            self.setFont(QFont('Segoe UI', 10))

        # DB init (SQLite default)
        if self.cfg['app'].get('db_type', 'sqlite').lower() == 'sqlite':
            ensure_sqlite_schema(USER_DB)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._build_dashboard_tab()
        self._build_company_tab()
        self._build_customers_tab()
        self._build_products_tab()
        self._build_invoice_tab()
        self._build_reports_tab()
        self._build_settings_tab()

        self.statusBar().showMessage(self.s['status_ready'])

    # ---------- Helpers ----------
    def conn(self):
        dbtype = self.cfg['app'].get('db_type', 'sqlite').lower()
        if dbtype == 'sqlite':
            return get_sqlite_conn(USER_DB)
        else:
            asec = self.cfg['access']
            connstr = asec.get('connection_string') or None
            fpath = asec.get('file_path') or None
            return get_access_conn(connstr, fpath)

    # ---------- Tabs ----------
    def _build_dashboard_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        title = QLabel(self.s['app_title']); title.setAlignment(Qt.AlignmentFlag.AlignCenter); title.setStyleSheet("font-size:18px;font-weight:600")
        lay.addWidget(title)
        info = QLabel("Windows 11 x64 • SQLite/Access • Persian/English")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info)
        self.tabs.addTab(w, self.s['tab_dashboard'])

    def _build_company_tab(self):
        w = QWidget(); lay = QFormLayout(w)
        self.inp_company_name_fa = QLineEdit(self.cfg['app'].get('company_name_fa', ''))
        self.inp_company_name_en = QLineEdit(self.cfg['app'].get('company_name_en', ''))
        self.inp_company_phone = QLineEdit(self.cfg['app'].get('company_phone', ''))
        self.inp_company_address_fa = QLineEdit(self.cfg['app'].get('company_address_fa', ''))
        self.inp_company_address_en = QLineEdit(self.cfg['app'].get('company_address_en', ''))
        self.inp_vat = QDoubleSpinBox(); self.inp_vat.setRange(0, 100); self.inp_vat.setValue(float(self.cfg['app'].get('vat_percent', '9')))
        self.inp_currency = QLineEdit(self.cfg['app'].get('currency_symbol', 'ریال'))
        save_btn = QPushButton(self.s['save']); save_btn.clicked.connect(self._save_company_settings)

        lay.addRow(QLabel(self.s['company_name_fa']), self.inp_company_name_fa)
        lay.addRow(QLabel(self.s['company_name_en']), self.inp_company_name_en)
        lay.addRow(QLabel(self.s['company_phone']), self.inp_company_phone)
        lay.addRow(QLabel(self.s['company_address_fa']), self.inp_company_address_fa)
        lay.addRow(QLabel(self.s['company_address_en']), self.inp_company_address_en)
        lay.addRow(QLabel("VAT %"), self.inp_vat)
        lay.addRow(QLabel("Currency"), self.inp_currency)
        lay.addRow(save_btn)

        self.tabs.addTab(w, self.s['tab_company'])

    def _build_customers_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        form = QFormLayout()
        self.cust_name = QLineEdit(); self.cust_phone = QLineEdit(); self.cust_addr = QLineEdit()
        form.addRow(QLabel(self.s['name']), self.cust_name)
        form.addRow(QLabel(self.s['phone']), self.cust_phone)
        form.addRow(QLabel(self.s['address']), self.cust_addr)
        btn_add = QPushButton(self.s['add']); btn_add.clicked.connect(self._add_customer)
        lay.addLayout(form); lay.addWidget(btn_add)

        self.customer_table = QTableWidget(0, 3)
        self.customer_table.setHorizontalHeaderLabels([self.s['name'], self.s['phone'], self.s['address']])
        lay.addWidget(self.customer_table)
        self.tabs.addTab(w, self.s['tab_customers'])
        self._refresh_customers()

    def _build_products_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        form = QFormLayout()
        self.prod_name = QLineEdit(); self.prod_price = QDoubleSpinBox(); self.prod_price.setMaximum(1e12); self.prod_price.setDecimals(2)
        form.addRow(QLabel(self.s['name']), self.prod_name)
        form.addRow(QLabel(self.s['price']), self.prod_price)
        btn_add = QPushButton(self.s['add']); btn_add.clicked.connect(self._add_product)
        lay.addLayout(form); lay.addWidget(btn_add)

        self.product_table = QTableWidget(0, 2)
        self.product_table.setHorizontalHeaderLabels([self.s['name'], self.s['price']])
        lay.addWidget(self.product_table)
        self.tabs.addTab(w, self.s['tab_products'])
        self._refresh_products()

    def _build_invoice_tab(self):
        w = QWidget(); main_l = QVBoxLayout(w)

        top = QHBoxLayout()
        self.invoice_customer = QComboBox()
        self.invoice_date = QDateEdit(); self.invoice_date.setDate(QDate.currentDate()); self.invoice_date.setCalendarPopup(True)
        top.addWidget(QLabel(self.s['customer'])); top.addWidget(self.invoice_customer, 2)
        top.addWidget(QLabel(self.s['date'])); top.addWidget(self.invoice_date, 1)
        main_l.addLayout(top)

        # Items table
        cols = [self.s['product'], self.s['price'], self.s['quantity'], self.s['discount'], self.s['tax'], self.s['total']]
        self.items = QTableWidget(0, len(cols))
        self.items.setHorizontalHeaderLabels(cols)
        main_l.addWidget(self.items)

        # Line buttons
        line_btns = QHBoxLayout()
        btn_add_row = QPushButton(self.s['add_row']); btn_add_row.clicked.connect(self._add_item_row)
        btn_del_row = QPushButton(self.s['remove_row']); btn_del_row.clicked.connect(self._remove_item_row)
        line_btns.addWidget(btn_add_row); line_btns.addWidget(btn_del_row); line_btns.addStretch()
        main_l.addLayout(line_btns)

        # Totals
        gb = QGroupBox("Totals")
        g = QFormLayout(gb)
        self.t_subtotal = QLineEdit("0"); self.t_subtotal.setReadOnly(True)
        self.t_discount = QLineEdit("0"); self.t_discount.setReadOnly(True)
        self.t_taxable = QLineEdit("0"); self.t_taxable.setReadOnly(True)
        self.t_vat = QLineEdit("0"); self.t_vat.setReadOnly(True)
        self.t_grand = QLineEdit("0"); self.t_grand.setReadOnly(True)
        g.addRow(QLabel(self.s['subtotal']), self.t_subtotal)
        g.addRow(QLabel(self.s['discount_sum']), self.t_discount)
        g.addRow(QLabel(self.s['taxable']), self.t_taxable)
        g.addRow(QLabel(self.s['vat']), self.t_vat)
        g.addRow(QLabel(self.s['grand_total']), self.t_grand)
        main_l.addWidget(gb)

        # Save
        btn_save = QPushButton(self.s['save_invoice']); btn_save.clicked.connect(self._save_invoice)
        main_l.addWidget(btn_save)

        self.tabs.addTab(w, self.s['tab_invoice'])
        self._refresh_customers_into_combo()
        self._refresh_products_cache()

    def _build_reports_tab(self):
        w = QWidget(); lay = QVBoxLayout(w)
        btn_refresh = QPushButton(self.s['report_refresh']); btn_refresh.clicked.connect(self._load_invoices_report)
        lay.addWidget(btn_refresh)
        self.report_table = QTableWidget(0, 5)
        self.report_table.setHorizontalHeaderLabels([self.s['invoice_no'], self.s['customer_name'], self.s['subtotal'], self.s['vat'], self.s['grand_total']])
        lay.addWidget(self.report_table)

        btn_export = QPushButton(self.s['export_csv']); btn_export.clicked.connect(self._export_report_csv)
        lay.addWidget(btn_export)

        self.tabs.addTab(w, self.s['tab_reports'])
        self._load_invoices_report()

    def _build_settings_tab(self):
        w = QWidget(); lay = QFormLayout(w)

        # language
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem(self.s['lang_fa'], 'fa')
        self.cmb_lang.addItem(self.s['lang_en'], 'en')
        self.cmb_lang.setCurrentIndex(0 if self.lang=='fa' else 1)

        # db type
        self.cmb_db = QComboBox()
        self.cmb_db.addItem(self.s['db_sqlite'], 'sqlite')
        self.cmb_db.addItem(self.s['db_access'], 'access')
        self.cmb_db.setCurrentIndex(0 if self.cfg['app'].get('db_type','sqlite')=='sqlite' else 1)

        # access file path
        self.access_path = QLineEdit(self.cfg['access'].get('file_path',''))
        btn_browse = QPushButton("...")
        def browse():
            fp, _ = QFileDialog.getOpenFileName(self, "Select Access DB", "", "Access DB (*.accdb *.mdb)")
            if fp: self.access_path.setText(fp)
        btn_browse.clicked.connect(browse)

        btn_save = QPushButton(self.s['save']); btn_save.clicked.connect(self._save_settings)

        lay.addRow(QLabel(self.s['lang_label']), self.cmb_lang)
        lay.addRow(QLabel(self.s['db_type']), self.cmb_db)
        lay.addRow(QLabel("Access file"), self.access_path)
        lay.addRow(btn_save)

        self.tabs.addTab(w, self.s['tab_settings'])

    # ---------- Actions ----------
    def _save_company_settings(self):
        self.cfg['app']['company_name_fa'] = self.inp_company_name_fa.text()
        self.cfg['app']['company_name_en'] = self.inp_company_name_en.text()
        self.cfg['app']['company_phone'] = self.inp_company_phone.text()
        self.cfg['app']['company_address_fa'] = self.inp_company_address_fa.text()
        self.cfg['app']['company_address_en'] = self.inp_company_address_en.text()
        self.cfg['app']['vat_percent'] = f"{self.inp_vat.value():.2f}"
        self.cfg['app']['currency_symbol'] = self.inp_currency.text()
        with USER_SETTINGS.open('w', encoding='utf-8') as f:
            self.cfg.write(f)
        QMessageBox.information(self, "", self.s['msg_saved'])

    def _add_customer(self):
        name = self.cust_name.text().strip()
        if not name:
            return
        conn = self.conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", (name, self.cust_phone.text(), self.cust_addr.text()))
        conn.commit(); conn.close()
        self.cust_name.clear(); self.cust_phone.clear(); self.cust_addr.clear()
        self._refresh_customers(); self._refresh_customers_into_combo()

    def _add_product(self):
        name = self.prod_name.text().strip()
        price = float(self.prod_price.value())
        if not name:
            return
        conn = self.conn(); cur = conn.cursor()
        cur.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
        conn.commit(); conn.close()
        self.prod_name.clear(); self.prod_price.setValue(0)
        self._refresh_products(); self._refresh_products_cache()

    def _refresh_customers(self):
        self.customer_table.setRowCount(0)
        conn = self.conn(); cur = conn.cursor()
        cur.execute("SELECT id, name, phone, address FROM customers ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            i = self.customer_table.rowCount(); self.customer_table.insertRow(i)
            self.customer_table.setItem(i, 0, QTableWidgetItem(str(r[1])))
            self.customer_table.setItem(i, 1, QTableWidgetItem(str(r[2] or '')))
            self.customer_table.setItem(i, 2, QTableWidgetItem(str(r[3] or '')))

    def _refresh_products(self):
        self.product_table.setRowCount(0)
        conn = self.conn(); cur = conn.cursor()
        cur.execute("SELECT id, name, price FROM products ORDER BY id DESC")
        rows = cur.fetchall(); conn.close()
        for r in rows:
            i = self.product_table.rowCount(); self.product_table.insertRow(i)
            self.product_table.setItem(i, 0, QTableWidgetItem(str(r[1])))
            self.product_table.setItem(i, 1, QTableWidgetItem(f"{float(r[2]):,.2f}"))

    def _refresh_customers_into_combo(self):
        self.invoice_customer.clear()
        conn = self.conn(); cur = conn.cursor()
        cur.execute("SELECT id, name FROM customers ORDER BY name ASC")
        rows = cur.fetchall(); conn.close()
        for cid, name in rows:
            self.invoice_customer.addItem(str(name), cid)

    def _refresh_products_cache(self):
        self.products_cache = []
        conn = self.conn(); cur = conn.cursor()
        cur.execute("SELECT id, name, price FROM products ORDER BY name ASC")
        self.products_cache = cur.fetchall()
        conn.close()

    def _add_item_row(self):
        r = self.items.rowCount(); self.items.insertRow(r)
        # Product combo
        cmb = QComboBox()
        for pid, name, price in self.products_cache:
            cmb.addItem(f"{name} ({price})", (pid, float(price)))
        cmb.currentIndexChanged.connect(lambda _=None, row=r: self._recalc_row(row))
        self.items.setCellWidget(r, 0, cmb)

        # Unit price
        sp_price = QDoubleSpinBox(); sp_price.setMaximum(1e12); sp_price.setDecimals(2); sp_price.setValue(0.0)
        sp_qty = QDoubleSpinBox(); sp_qty.setMaximum(1e9); sp_qty.setDecimals(3); sp_qty.setValue(1.0)
        sp_disc = QDoubleSpinBox(); sp_disc.setRange(0,100); sp_disc.setDecimals(2); sp_disc.setValue(0.0)
        sp_tax = QDoubleSpinBox(); sp_tax.setRange(0,100); sp_tax.setDecimals(2); sp_tax.setValue(float(self.cfg['app'].get('vat_percent','9')))

        for c, w in enumerate([sp_price, sp_qty, sp_disc, sp_tax], start=1):
            self.items.setCellWidget(r, c, w)
            w.valueChanged.connect(self._recalc_totals)

        # total (read-only)
        tot = QLineEdit("0"); tot.setReadOnly(True)
        self.items.setCellWidget(r, 5, tot)
        self._recalc_row(r); self._recalc_totals()

    def _remove_item_row(self):
        r = self.items.currentRow()
        if r >= 0:
            self.items.removeRow(r)
            self._recalc_totals()

    def _row_widgets(self, row):
        cmb = self.items.cellWidget(row, 0)  # product
        sp_price = self.items.cellWidget(row, 1)
        sp_qty = self.items.cellWidget(row, 2)
        sp_disc = self.items.cellWidget(row, 3)
        sp_tax = self.items.cellWidget(row, 4)
        tot = self.items.cellWidget(row, 5)
        return cmb, sp_price, sp_qty, sp_disc, sp_tax, tot

    def _recalc_row(self, row):
        cmb, sp_price, sp_qty, sp_disc, sp_tax, tot = self._row_widgets(row)
        if cmb.count() > 0 and cmb.currentIndex() >= 0:
            pid, price = cmb.currentData()
            sp_price.setValue(price)
        amount = sp_price.value() * sp_qty.value()
        disc_val = amount * (sp_disc.value()/100.0)
        taxable = amount - disc_val
        tax_val = taxable * (sp_tax.value()/100.0)
        line_total = taxable + tax_val
        tot.setText(f"{line_total:,.2f}")
        self._recalc_totals()

    def _recalc_totals(self):
        rows = self.items.rowCount()
        subtotal = 0.0; discount_sum = 0.0; taxable_sum = 0.0; vat_sum = 0.0; grand = 0.0
        for r in range(rows):
            cmb, sp_price, sp_qty, sp_disc, sp_tax, tot = self._row_widgets(r)
            amount = sp_price.value() * sp_qty.value()
            disc_val = amount * (sp_disc.value()/100.0)
            taxable = amount - disc_val
            tax_val = taxable * (sp_tax.value()/100.0)
            line_total = taxable + tax_val
            subtotal += amount
            discount_sum += disc_val
            taxable_sum += taxable
            vat_sum += tax_val
            grand += line_total
        self.t_subtotal.setText(f"{subtotal:,.2f}")
        self.t_discount.setText(f"{discount_sum:,.2f}")
        self.t_taxable.setText(f"{taxable_sum:,.2f}")
        self.t_vat.setText(f"{vat_sum:,.2f}")
        self.t_grand.setText(f"{grand:,.2f}")

    def _save_invoice(self):
        if self.invoice_customer.count() == 0 or len(self.products_cache) == 0:
            QMessageBox.warning(self, self.s['msg_error'], self.s['msg_need_customer_product']); return
        rows = self.items.rowCount()
        if rows == 0:
            return
        # Calculate totals again
        self._recalc_totals()
        subtotal = float(self.t_subtotal.text().replace(',',''))
        discount_sum = float(self.t_discount.text().replace(',',''))
        taxable = float(self.t_taxable.text().replace(',',''))
        vat = float(self.t_vat.text().replace(',',''))
        grand = float(self.t_grand.text().replace(',',''))
        cust_id = self.invoice_customer.currentData()
        d = self.invoice_date.date().toString("yyyy-MM-dd")

        conn = self.conn(); cur = conn.cursor()
        cur.execute("INSERT INTO invoices (customer_id, date, subtotal, discount_sum, taxable, vat, grand_total) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (cust_id, d, subtotal, discount_sum, taxable, vat, grand))
        # Last invoice id
        inv_id = None
        if hasattr(cur, "lastrowid"):
            inv_id = cur.lastrowid
        if inv_id in (None, 0):
            try:
                cur.execute("SELECT @@IDENTITY")
                inv_id = list(cur.fetchone())[0]
            except Exception:
                pass

        for r in range(rows):
            cmb, sp_price, sp_qty, sp_disc, sp_tax, tot = self._row_widgets(r)
            pid, _ = cmb.currentData()
            cur.execute("INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price, discount_percent, tax_percent, line_total) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (inv_id, pid, sp_qty.value(), sp_price.value(), sp_disc.value(), sp_tax.value(), float(tot.text().replace(',',''))))
        conn.commit(); conn.close()
        QMessageBox.information(self, "", self.s['msg_saved'])
        # Clear items
        self.items.setRowCount(0); self._recalc_totals()
        self._load_invoices_report()

    def _load_invoices_report(self):
        self.report_table.setRowCount(0)
        conn = self.conn(); cur = conn.cursor()
        cur.execute("""SELECT i.id, c.name, i.subtotal, i.vat, i.grand_total
                       FROM invoices i JOIN customers c ON c.id=i.customer_id
                       ORDER BY i.id DESC""")
        rows = cur.fetchall(); conn.close()
        for r in rows:
            i = self.report_table.rowCount(); self.report_table.insertRow(i)
            for c in range(5):
                self.report_table.setItem(i, c, QTableWidgetItem(str(r[c])))

    def _export_report_csv(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV (*.csv)")
        if not fp: return
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            # header
            w.writerow([self.s['invoice_no'], self.s['customer_name'], self.s['subtotal'], self.s['vat'], self.s['grand_total']])
            # rows
            for i in range(self.report_table.rowCount()):
                row = [self.report_table.item(i, j).text() if self.report_table.item(i, j) else "" for j in range(self.report_table.columnCount())]
                w.writerow(row)
        QMessageBox.information(self, "", self.s['msg_saved'])

    def _save_settings(self):
        self.cfg['app']['lang'] = self.cmb_lang.itemData(self.cmb_lang.currentIndex())
        self.cfg['app']['db_type'] = self.cmb_db.itemData(self.cmb_db.currentIndex())
        self.cfg['access']['file_path'] = self.access_path.text()
        with USER_SETTINGS.open('w', encoding='utf-8') as f:
            self.cfg.write(f)
        QMessageBox.information(self, "", self.s['msg_saved'])
        QMessageBox.information(self, "", "برای اعمال تغییر زبان، برنامه را دوباره اجرا کنید." if self.lang=='fa' else "Please restart the app to apply language change.")

def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
