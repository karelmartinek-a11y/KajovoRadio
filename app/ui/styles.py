from __future__ import annotations

# Near-black base, cyan/yellow accents, grey secondary.

APP_QSS = """
QMainWindow { background: #0B0D10; }

/* Header */
#HeaderBar { background: #0F1217; border-bottom: 1px solid #1A2230; }
#HeaderTitle { color: #E6E8EB; font-size: 16px; font-weight: 700; }
#PanoramaLine { background: #111824; }

/* Panels */
QFrame#LeftPanel { background: #0F1217; border-right: 1px solid #1A2230; }
QFrame#FooterBar { background: #0F1217; border-top: 1px solid #1A2230; }

QGroupBox { color: #C8CDD3; border: 1px solid #1A2230; border-radius: 10px; margin-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #E6E8EB; font-weight: 700; }

QLineEdit { background: #0B0D10; border: 1px solid #1A2230; border-radius: 8px; padding: 6px 8px; color: #E6E8EB; }
QLineEdit:focus { border: 1px solid #2EE6FF; }

QListWidget { background: #0B0D10; border: 1px solid #1A2230; border-radius: 8px; color: #E6E8EB; }
QListWidget::item { padding: 6px 8px; border-bottom: 1px solid #111824; }
QListWidget::item:selected { background: #132636; }

QPushButton { background: #111824; border: 1px solid #1A2230; border-radius: 10px; padding: 8px 10px; color: #E6E8EB; }
QPushButton:hover { border: 1px solid #2EE6FF; }
QPushButton:pressed { background: #0B0D10; }

QPushButton#Primary { background: #F4C61C; color: #101216; border: 0px; font-weight: 700; }
QPushButton#Primary:hover { background: #FFD64C; }

QToolButton { background: #111824; border: 1px solid #1A2230; border-radius: 10px; padding: 6px 10px; color: #E6E8EB; }
QToolButton:hover { border: 1px solid #2EE6FF; }

QSlider::groove:horizontal { height: 6px; background: #111824; border-radius: 3px; }
QSlider::handle:horizontal { width: 14px; margin: -6px 0; border-radius: 7px; background: #2EE6FF; }

QTabBar::tab { background: #111824; border: 1px solid #1A2230; padding: 8px 12px; border-radius: 10px; color: #C8CDD3; margin-right: 6px; }
QTabBar::tab:selected { background: #132636; border: 1px solid #2EE6FF; color: #E6E8EB; }

/* Warnings */
#WarningLabel { color: #F4C61C; font-weight: 700; }
"""
