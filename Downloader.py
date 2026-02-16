import Backend as bk

from PyQt6.QtCore import Qt, QUrl, QPoint, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QSlider,
    QPushButton, QMessageBox, QAbstractItemView, QMenu, QWidgetAction, QHBoxLayout, QLabel,
)

class Downloader(QWidget):
    SelectionUpdate = pyqtSignal(list)
    ContextUpdate = pyqtSignal(QPoint)

    def __init__(self):
        super().__init__()

        self.setStyleSheet(bk.LoadStylesheet('Downloader'))

        self.Columns = ['Title', 'Artist', 'Genre', 'Status']
        self.SortBy = 'Title'
        self.SortOrder = True

        self.MainLayout = QVBoxLayout(self)

        self.SetupTable()
        self.SetupPlayer()
    
    def SetupTable(self):
        self.table = QTableWidget()
        self.table.setColumnCount(4) 
        self.table.setHorizontalHeaderLabels(self.Columns)
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().sectionClicked.connect(self.HeaderClicked)

        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(45)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setAlternatingRowColors(True)
        
        self.table.doubleClicked.connect(self.PlaySong)
        self.table.itemSelectionChanged.connect(self.RefreshSelection)
        self.table.customContextMenuRequested.connect(self.ShowContextMenu)

        self.MainLayout.addWidget(self.table)
    
    def SetupPlayer(self):
        def SetPlaybuttonText():
            if self.AudioPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState: 
                self.PlayBtn.setIcon(QIcon(bk.ResourcePath('Static/Pause.png')))
            elif self.AudioPlayer.playbackState() == QMediaPlayer.PlaybackState.PausedState: 
                self.PlayBtn.setIcon(QIcon(bk.ResourcePath('Static/Play.png')))

        def TogglePlay():
            if self.AudioPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState: self.AudioPlayer.pause()
            elif self.AudioPlayer.playbackState() == QMediaPlayer.PlaybackState.PausedState: self.AudioPlayer.play()

        def MediaStatusChanged(status):
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                self.PlayBtn.setIcon(QIcon(bk.ResourcePath('Static/Play.png')))
                self.SeekSlider.setValue(0)
        
        def FormatTime(ms):
            seconds = (ms // 1000) % 60
            minutes = (ms // 60000)
            return f"{minutes}:{seconds:02}"
        
        def PositionChanged(pos):
            self.SeekSlider.setValue(pos)
            self.TimeLabel.setText(f"{FormatTime(pos)} / {FormatTime(self.AudioPlayer.duration())}")
        
        def ShowVolumeMenu():
            ButtonPos = self.VolBtn.mapToGlobal(self.VolBtn.rect().topLeft())

            MenuHeight = self.VolMenu.height()
            MenuWidth = self.VolMenu.width()
            ButtonWidth = self.VolBtn.width()
            
            CenteredX = ButtonPos.x() + (ButtonWidth // 2) - (MenuWidth // 2)
            TopY = ButtonPos.y() - MenuHeight

            PopupPos = ButtonPos
            PopupPos.setX(CenteredX)
            PopupPos.setY(TopY)

            self.VolMenu.exec(PopupPos)

        self.AudioPlayer = QMediaPlayer()
        self.AudioOut = QAudioOutput()
        self.AudioOut.setVolume(1.0)
        self.AudioPlayer.setAudioOutput(self.AudioOut)

        self.AudioPlayer.positionChanged.connect(PositionChanged)
        self.AudioPlayer.durationChanged.connect(lambda duration: self.SeekSlider.setRange(0, duration))
        self.AudioPlayer.mediaStatusChanged.connect(MediaStatusChanged)
        self.AudioPlayer.playbackStateChanged.connect(SetPlaybuttonText)

        self.PlayerFrame = QFrame()
        self.PlayerFrame.setObjectName("PlayerFrame")
        PlayerLayout = QHBoxLayout(self.PlayerFrame)

        # Play Button
        self.PlayBtn = QPushButton()
        self.PlayBtn.setObjectName("PlayBtn")
        self.PlayBtn.setIcon(QIcon(bk.ResourcePath('Static/Play.png')))
        self.PlayBtn.clicked.connect(TogglePlay)
        PlayerLayout.addWidget(self.PlayBtn)

        # Title and timer
        ScrubberLayout = QVBoxLayout()
        TopLayout = QHBoxLayout()

        # Song Title
        self.NowPlayingLbl = QLabel("Select a song to play")
        self.NowPlayingLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.NowPlayingLbl.setObjectName("NowPlaying")
        TopLayout.addWidget(self.NowPlayingLbl, Qt.AlignmentFlag.AlignHCenter)

        # Time indicator
        self.TimeLabel = QLabel("0:00 / 0:00")
        self.TimeLabel.setObjectName("TimeLabel")
        TopLayout.addWidget(self.TimeLabel, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        ScrubberLayout.addLayout(TopLayout)

        # Slider
        self.SeekSlider = QSlider(Qt.Orientation.Horizontal)
        self.SeekSlider.setRange(0, 0)
        self.SeekSlider.sliderMoved.connect(lambda position: self.AudioPlayer.setPosition(position))
        self.SeekSlider.sliderPressed.connect(lambda: self.AudioPlayer.pause()) # Pause while dragging
        self.SeekSlider.sliderReleased.connect(lambda: self.AudioPlayer.play()) # Resume after drag
        ScrubberLayout.addWidget(self.SeekSlider)

        # Volume
        self.VolMenu = QMenu(self)
        self.VolMenu.setObjectName("VolumeMenu")

        self.VolSlider = QSlider(Qt.Orientation.Vertical)
        self.VolSlider.setRange(0, 100)
        self.VolSlider.setValue(100)
        self.VolSlider.valueChanged.connect(lambda v: self.AudioOut.setVolume(v / 100))

        VolAction = QWidgetAction(self.VolMenu)
        VolAction.setDefaultWidget(self.VolSlider)
        self.VolMenu.addAction(VolAction)

        self.VolBtn = QPushButton()
        self.VolBtn.setObjectName("VolBtn")
        self.VolBtn.setIcon(QIcon(bk.ResourcePath('Static/Volume.png')))
        self.VolBtn.clicked.connect(ShowVolumeMenu)

        PlayerLayout.addLayout(ScrubberLayout)
        PlayerLayout.addWidget(self.VolBtn, alignment=Qt.AlignmentFlag.AlignRight)

        self.MainLayout.addWidget(self.PlayerFrame, alignment = Qt.AlignmentFlag.AlignHCenter)
    
    def PlaySong(self, index):
        title = self.table.item(index.row(), 0).text()
        
        # Find file extension
        Path = None
        for ext in ['.mp3', '.flac', '.m4a']:
            path = bk.MusicDir / f"{title}{ext}"
            if path.exists():
                Path = path
                break
        
        if not Path:
            QMessageBox.warning(self, "Song not downloaded", f"Please download '{title}' first before playing!")
            return
        
        self.AudioPlayer.setSource(QUrl.fromLocalFile(str(Path)))
        self.AudioPlayer.play()
        self.NowPlayingLbl.setText(title)
    
    def RefreshList(self):
        self.table.blockSignals(True)

        # Sort list
        bk.SongDF.sort_values(by=self.SortBy, ascending=self.SortOrder, inplace=True)
        bk.SongDF.reset_index(drop=True, inplace=True)
        self.table.horizontalHeader().setSortIndicator(self.Columns.index(self.SortBy), Qt.SortOrder.AscendingOrder if self.SortOrder else Qt.SortOrder.DescendingOrder)

        # Clear table and repopulate
        self.table.setRowCount(0)
        for index, row in bk.SongDF.iterrows():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(index + 1)))
            
            def make_item(text, center=False):
                item = QTableWidgetItem(str(text))
                if center: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item

            self.table.setItem(row_idx, 0, make_item(row['Title']))
            self.table.setItem(row_idx, 1, make_item(row['Artist']))
            self.table.setItem(row_idx, 2, make_item(row['Genre']))
            self.table.setItem(row_idx, 3, make_item(row['Status'], True))
        
        self.RefreshSelection()
        self.table.blockSignals(False)
    
    def RefreshSelection(self):
        rows = self.table.selectionModel().selectedRows()
        titles = [self.table.item(row.row(), 0).text() for row in rows]
        self.SelectionUpdate.emit(titles)

    def ShowContextMenu(self, pos: QPoint):
        if not self.table.selectionModel().hasSelection(): return
        self.ContextUpdate.emit(self.table.viewport().mapToGlobal(pos))
    
    def HeaderClicked(self, index):
        ClickedCol = self.Columns[index]

        if self.SortBy == ClickedCol:
            self.SortOrder = not self.SortOrder  
        else:
            self.SortBy = ClickedCol
            self.SortOrder = True  

        self.RefreshList()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        height = self.height()

        PlayerWidth = int(width * 0.7)
        PlayerHeight = int(height * 0.12)
        self.PlayerFrame.setFixedSize(PlayerWidth, PlayerHeight)

        PlayBtnSize = int(PlayerHeight * 0.7)
        self.PlayBtn.setStyleSheet(f"border-radius: {PlayBtnSize // 2}px;")
        self.PlayBtn.setFixedSize(PlayBtnSize, PlayBtnSize)
        self.PlayBtn.setIconSize(QSize(int(PlayBtnSize * 0.4), int(PlayBtnSize * 0.4)))

        self.NowPlayingLbl.setStyleSheet(f"font-size: {int(PlayerHeight * 0.23)}px;")
        self.TimeLabel.setStyleSheet(f"font-size: {int(PlayerHeight * 0.18)}px;")

        # Scrub Slider
        HandleSize = int(PlayerHeight * 0.2)
        GrooveHeight = int(PlayerHeight * 0.1)
        margin = -(HandleSize - GrooveHeight) // 2 # Magic formula to vertically center handle

        self.SeekSlider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: {GrooveHeight}px;
                border-radius: {GrooveHeight // 2}px;
            }}
            QSlider::sub-page:horizontal{{
                border-radius: {GrooveHeight // 2}px;
            }}
            QSlider::handle:horizontal {{
                width: {HandleSize}px;
                height: {HandleSize}px;
                margin: {margin}px 0;
                border-radius: {HandleSize // 2}px;
            }}
        """)
        self.SeekSlider.setFixedHeight(HandleSize+1)

        # Volume btn
        VolBtnSiz = int(PlayerHeight * 0.7)
        self.VolBtn.setFixedSize(VolBtnSiz, VolBtnSiz)
        self.VolBtn.setIconSize(QSize(int(VolBtnSiz * 0.4), int(VolBtnSiz * 0.4)))

        # Volume slider
        PopupHeight = int(PlayerHeight * 3)
        PopupWidth = int(VolBtnSiz * 0.6)

        HandleSize = int(PopupWidth * 0.4)
        GrooveWidth = int(PopupWidth * 0.2)
        GrooveHeight = int(PopupHeight * 0.9)
        margin = -(HandleSize - GrooveWidth) // 2

        self.VolMenu.setFixedSize(PopupWidth, PopupHeight)
        self.VolSlider.setFixedSize(PopupWidth, PopupHeight)

        self.VolSlider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                width: {GrooveWidth}px;
                height: {GrooveHeight}px;
                border-radius: {GrooveWidth // 2}px;
            }}
            QSlider::handle:vertical {{
                width: {HandleSize}px;
                height: {HandleSize}px;
                margin: 0 {margin}px;
                border-radius: {HandleSize // 2}px;
            }}
            QSlider::add-page:vertical {{
                border-radius: {GrooveWidth // 2}px;
            }}
        """)