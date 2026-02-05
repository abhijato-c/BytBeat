import Backend as bk

from PyQt6.QtCore import Qt, QUrl, QPoint, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QAction, QActionGroup, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSlider, QScrollArea, 
    QPushButton, QMessageBox, QAbstractItemView, QMenu, QWidgetAction, QHBoxLayout, QLabel
)

class Player(QWidget):
    SelectionUpdate = pyqtSignal(list)
    ContextUpdate = pyqtSignal(QPoint)

    def __init__(self):
        super().__init__()

        self.setStyleSheet(bk.LoadStylesheet('Player'))
        self.MainLayout = QHBoxLayout(self)

        self.SongButtons = {}

        self.SetupSidebar()
        self.MainLayout.addStretch(1)
        self.SetupPlayWin()

        self.MainLayout.setStretch(0, 24)
        self.MainLayout.setStretch(1, 1)
        self.MainLayout.setStretch(2, 75)

        self.AddSongBtn('Ado-Ussewa')

    def SetupSidebar(self):
        self.Sidebar = QScrollArea()
        self.Sidebar.setObjectName("Sidebar")
        self.SidebarLayout = QVBoxLayout(self.Sidebar)
        self.MainLayout.addWidget(self.Sidebar)
    
    def SetupPlayWin(self):
        self.PlayWin = QFrame()
        self.PlayWin.setObjectName("PlayWin")
        self.PlayLayout = QVBoxLayout(self.PlayWin)
        self.MainLayout.addWidget(self.PlayWin)
    
    def AddSongBtn(self, title):
        artist = bk.GetSongDetail(title, 'Artist')
        genre = bk.GetSongDetail(title, 'Genre')
        status = bk.GetSongDetail(title, 'Status') == "Downloaded"

        btn = QPushButton()
        btn.setObjectName("SongBtn")
        layout = QHBoxLayout(btn)
        
        img = QLabel()
        pixmap = QPixmap(str(bk.ImageDir / (title+'.jpg')))
        img.setPixmap(pixmap)
        img.setScaledContents(True)
        layout.addWidget(img)

        details = QVBoxLayout()
        header = QLabel(title)
        details.addWidget(header)
        
        layout.addLayout(details)

        self.SidebarLayout.addWidget(btn)
    
    def RefreshList(self):
        pass