import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QComboBox, QProgressBar, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient

# Gradient background widget
class GradientWidget(QWidget):
    def __init__(self):
        super().__init__()
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(227, 235, 252))  # #E3EBFC
        gradient.setColorAt(1.0, QColor(224, 248, 249))  # #E0F8F9
        painter.fillRect(self.rect(), gradient)

# Card frame with drop shadow
class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(13)
        shadow.setColor(QColor("#c1d8fa"))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

# Button with accurate style
class CustomButton(QPushButton):
    def __init__(self, text, color, txt_color="#fff", font_weight="bold", parent=None):
        super().__init__(text, parent)
        style = f"""
        QPushButton {{
            background-color: {color};
            color: {txt_color};
            border-radius: 10px;
            font-size: 16px;
            font-weight: {font_weight};
            padding: 9px 30px;
        }}
        QPushButton:pressed {{
            background-color: #3B4B69;
        }}
        """
        self.setStyleSheet(style)
        self.setFont(QFont("Inter", 15, QFont.Weight.Bold))

# Clean productivity donut
class ProductivityCircle(QWidget):
    def __init__(self, percent):
        super().__init__()
        self.percent = percent
        self.setMinimumSize(130, 130)
        self.setMaximumSize(130, 130)
    def paintEvent(self, event):
        rect = QRectF(10, 10, 110, 110)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Background circle
        pen = QPen(QColor("#E0E9F1"), 14)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        # Blue Arc 26%
        pen.setColor(QColor("#5C7CF9"))
        painter.setPen(pen)
        painter.drawArc(rect, 90*16, int(-94*16))  # ~26% of 360
        # Teal Arc 5%
        pen.setColor(QColor("#41CDD0"))
        painter.setPen(pen)
        painter.drawArc(rect, -4*16, int(-18*16))  # ~5%
        # Purple Arc 2%
        pen.setColor(QColor("#9295FF"))
        painter.setPen(pen)
        painter.drawArc(rect, -22*16, int(-7*16)) # ~2%
        # Centered percent
        painter.setPen(QColor("#24292f"))
        font = QFont("Inter", 25, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.percent}%")

# To-Do styled row
class ToDoRow(QWidget):
    def __init__(self, label, value, color):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 13, 2)
        box = QCheckBox()
        box.setFixedSize(22, 22)
        layout.addWidget(box)
        lab = QLabel(label)
        lab.setFont(QFont("Inter", 15))
        layout.addWidget(lab)
        layout.addStretch()
        num = QLabel(str(value))
        num.setStyleSheet(f"color: {color}; font-weight:bold; font-size:17px")
        layout.addWidget(num)

# Bar chart for screen time
class BarChart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setMinimumHeight(70)
        self.setMaximumHeight(75)
    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        margin = 24
        bars = len(self.data)
        max_val = max(self.data)
        bar_space = (w - 2 * margin)
        bar_width = bar_space / (2 * bars - 1)
        for i, val in enumerate(self.data):
            x = margin + i * 2 * bar_width
            bh = int((val / max_val) * (h - 20))
            color = QColor("#5C7CF9") if i % 2 == 0 else QColor("#65DED2")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, h - bh - 14, bar_width, bh, 6, 6)

# Dashboard main widget
class Dashboard(GradientWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TASKSNAP JOURNAL")
        self.resize(1150, 720)
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 14, 32, 14)
        main.setSpacing(16)
        # Header Row
        header_row = QHBoxLayout()
        logo_icon = QLabel()
        logo_icon.setStyleSheet("margin-top:6px; margin-right:13px;")
        logo_icon.setFixedSize(54, 54)
        logo_icon.setPixmap(QLabel().style().standardIcon(getattr(QLabel().style(), 'SP_FileDialogContentsView')).pixmap(49, 49))
        title_lbl = QLabel("TASKSNAP\nJOURNAL")
        title_lbl.setFont(QFont("Inter", 29, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color:#343B51; line-height:0.9; letter-spacing:2px; margin-top:9px;")
        header_left = QVBoxLayout()
        header_left.setSpacing(0)
        header_left.addWidget(logo_icon)
        header_left.addWidget(title_lbl)
        header_left.setAlignment(Qt.AlignmentFlag.AlignTop)
        header_row.addLayout(header_left)
        header_row.addStretch(1)
        # Light Mode toggle mock, right
        toggle_layout = QVBoxLayout()
        light_row = QHBoxLayout()
        pill = QLabel()
        pill.setFixedSize(48, 24)
        pill.setStyleSheet("background: #ECECEC; border-radius: 12px;")
        sun = QLabel("☀️")
        sun.setStyleSheet("font-size:16px; margin-left:5px;")
        sun.setFixedWidth(21)
        light_row.addWidget(sun)
        light_row.addWidget(pill)
        toggle_layout.addLayout(light_row)
        toggle_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        toggle_layout.addSpacing(2)
        toggle_layout.addWidget(QLabel("Light Mode"), alignment=Qt.AlignmentFlag.AlignHCenter)
        header_row.addLayout(toggle_layout)
        main.addLayout(header_row)
        main.addSpacing(6)
        # Sub-Header
        main.addWidget(QLabel("Hey, Username!"), alignment=Qt.AlignmentFlag.AlignLeft)
        main.addSpacing(9)
        # Central grid for cards
        grid = QHBoxLayout()
        grid.setSpacing(13)
        col1 = QVBoxLayout()
        col1.setSpacing(14)
        ## Update Info Card
        card1 = CardFrame(); lay1 = QVBoxLayout(card1)
        lay1.setContentsMargins(18,14,18,14)
        up_lbl = QLabel("Update Info")
        up_lbl.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        up_lbl.setStyleSheet("color:#24292f")
        lay1.addWidget(up_lbl)
        profile_row = QHBoxLayout()
        profile_pic = QLabel()
        profile_pic.setFixedSize(36,36)
        profile_pic.setStyleSheet("background:#dadbde; border-radius:18px;")
        profile_row.addWidget(profile_pic)
        pr_comb = QComboBox()
        pr_comb.addItems(["Name"])
        pr_comb.setFixedWidth(90)
        profile_row.addWidget(pr_comb)
        profile_row.addStretch(1)
        lay1.addLayout(profile_row)
        lay1.addSpacing(2)
        prf = QLabel("Putriom")
        prf.setStyleSheet("background:#F0F3F7;color:#424750;border-radius:9px; padding:7px 15px 7px 11px; font-size:15px; margin-bottom:5px;")
        lay1.addWidget(prf)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(11)
        btn_row.addWidget(CustomButton("Profile", "#5C7CF9", "#fff"))
        btn_row.addWidget(CustomButton("Bodim", "#E1E7F5", "#7587A6", font_weight="normal"))
        lay1.addLayout(btn_row)
        card1.setFixedHeight(163)
        col1.addWidget(card1)
        ## To-Do Card
        card2 = CardFrame(); lay2 = QVBoxLayout(card2)
        lay2.setContentsMargins(18,14,18,14)
        todo_lbl = QLabel("To-Do")
        todo_lbl.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        todo_lbl.setStyleSheet("color:#24292f")
        lay2.addWidget(todo_lbl)
        lay2.addWidget(ToDoRow("Complets", 121, "#5C7CF9"))
        lay2.addWidget(ToDoRow("Aud Dost", 221, "#38D297"))
        lay2.addWidget(ToDoRow("Complete", 310, "#FB4545"))
        card2.setFixedHeight(144)
        col1.addWidget(card2)
        grid.addLayout(col1)
        col2 = QVBoxLayout()
        col2.setSpacing(14)
        ## Productivity Card
        card3 = CardFrame(); lay3 = QVBoxLayout(card3)
        lay3.setContentsMargins(18,14,18,14)
        prod_lbl = QLabel("Productivity")
        prod_lbl.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        prod_lbl.setStyleSheet("color:#24292f")
        lay3.addWidget(prod_lbl, alignment=Qt.AlignmentFlag.AlignLeft)
        circ_row = QHBoxLayout()
        circ_row.addStretch(1)
        circ_row.addWidget(ProductivityCircle(8))
        circ_row.addStretch(1)
        lay3.addLayout(circ_row)
        goals_row = QHBoxLayout()
        daily = QProgressBar()
        daily.setFixedHeight(8)
        daily.setValue(26)
        daily.setTextVisible(False)
        daily.setStyleSheet("""
            QProgressBar {background:#E4EDF2; border-radius:6px;}
            QProgressBar::chunk { background:#41CDD0; border-radius:6px;}
        """)
        weekly = QProgressBar()
        weekly.setFixedHeight(8)
        weekly.setValue(2)
        weekly.setTextVisible(False)
        weekly.setStyleSheet("""
            QProgressBar {background:#E4EDF2; border-radius:6px;}
            QProgressBar::chunk { background:#5C7CF9; border-radius:6px;}
        """)
        ltxt = QLabel("Daily Goals       Weekly Goals")
        ltxt.setFont(QFont("Inter", 13))
        lay3.addWidget(ltxt)
        goals_row.addWidget(daily)
        goals_row.addSpacing(13)
        goals_row.addWidget(weekly)
        lay3.addLayout(goals_row)
        card3.setFixedHeight(236)
        col2.addWidget(card3)
        ## Screen Time Card
        card4 = CardFrame(); lay4 = QVBoxLayout(card4)
        lay4.setContentsMargins(18,14,18,14)
        sc_lbl = QLabel("Screen Time")
        sc_lbl.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        sc_lbl.setStyleSheet("color:#24292f")
        lay4.addWidget(sc_lbl)
        lay4.addWidget(QLabel("Total Screen Time"))
        lay4.addWidget(BarChart([60, 25, 10, 70, 55, 65, 50]))
        card4.setFixedHeight(144)
        col2.addWidget(card4)
        grid.addLayout(col2)
        main.addLayout(grid)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Dashboard()
    win.show()
    sys.exit(app.exec())
