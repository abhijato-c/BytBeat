import sys
import Backend as bk
from PopupDialogs import AddSongDialog, EditSongDialog
from TaskThreads import DownloadWorker, ImageWorker, InitWorker

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QActionGroup, QPixmap, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QFrame, QSlider, QSplashScreen,
    QPushButton, QMessageBox, QAbstractItemView, QStatusBar, QFileDialog, QMenu, QWidgetAction, QHBoxLayout, QLabel,
)

class DateTimeUtil(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(bk.LoadStylesheet('Downloader'))