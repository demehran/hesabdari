def apply_dark_blue_theme(app):
    """تم آبی تیره مینیمال برای PyQt6"""
    style = """
        QWidget {
            background-color: #121421;
            color: #f2f2f2;
            font-size: 14px;
        }
        QTabWidget::pane { border: 1px solid #2a2d3a; background: #1a1d2b; }
        QTabBar::tab {
            background: #1a1d2b; color: #f2f2f2; padding: 8px 18px; font-weight: bold;
        }
        QTabBar::tab:selected { background: #222742; border-bottom: 2px solid #3daee9; }
        QPushButton { background-color: #222742; border: none; padding: 7px 12px; border-radius: 8px; }
        QPushButton:hover { background-color: #2c3155; }
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
            background-color: #1a1d2b; border: 1px solid #343a52; padding: 6px; border-radius: 6px;
        }
        QTableWidget { background-color: #161927; gridline-color: #2f3550; selection-background-color: #2c3155; }
        QHeaderView::section { background-color: #222742; color: #ddd; padding: 6px; border: none; }
        QLabel[title="true"] { font-size: 26px; font-weight: 800; margin: 40px 0; }
    """
    app.setStyleSheet(style)
