"""theme.py - dark UI stylesheet shared across the app."""

DARK_STYLESHEET = """
QWidget {
    background-color: #121212;
    color: #E0E0E0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #121212;
}

QLineEdit {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 8px;
    color: #FFFFFF;
}

QLineEdit:focus {
    border: 1px solid #6C5CE7;
}

QPushButton {
    background-color: #6C5CE7;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #8377EA;
}

QPushButton:disabled {
    background-color: #3A3A3A;
    color: #888888;
}

QPushButton#secondary {
    background-color: #2A2A2A;
    color: #E0E0E0;
    border: 1px solid #3A3A3A;
}

QPushButton#secondary:hover {
    background-color: #333333;
}

QTabWidget::pane {
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1A1A1A;
    color: #AAAAAA;
    padding: 10px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #6C5CE7;
    color: #FFFFFF;
}

QTableWidget {
    background-color: #1A1A1A;
    gridline-color: #2A2A2A;
    border: 1px solid #2A2A2A;
    border-radius: 6px;
}

QHeaderView::section {
    background-color: #1E1E1E;
    color: #E0E0E0;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #333333;
}

QLabel#card {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 10px;
    padding: 14px;
}

QLabel#cardValue {
    font-size: 22px;
    font-weight: 700;
    color: #A29BFE;
}

QLabel#cardLabel {
    font-size: 11px;
    color: #999999;
}

QLabel#headline {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel#subheadline {
    font-size: 12px;
    color: #999999;
}

QScrollArea {
    border: none;
}
"""
