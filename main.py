import sys
import Backend as bk
from PopupDialogs import AddSongDialog, EditSongDialog
from TaskThreads import DownloadWorker, ImageWorker

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QFrame, QSlider,
    QPushButton, QGroupBox, QMessageBox, QAbstractItemView, QStatusBar, QFileDialog, QMenu, QWidgetAction, QHBoxLayout, QLabel, 
)

# Main Window
class MusicManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Manager")
        self.setGeometry(100, 100, 1100, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.MainLayout = QVBoxLayout(central_widget)
        self.Columns = ['Title', 'Artist', 'Genre', 'Status']

        self.SortBy = 'Title'
        self.SortOrder = True  

        bk.UpdateSongStatuses()

        self.SetupMenu()
        self.SetupTable()
        self.SetupStatusbar()
        self.SetupPlayer()
        self.ApplyStyles()
        self.RefreshList()

    def SetupTable(self):
        gb = QGroupBox("Library Status")
        gb_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(4) 
        self.table.setHorizontalHeaderLabels(self.Columns)
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        self.table.horizontalHeader().sectionClicked.connect(self.HeaderClicked)
        self.table.horizontalHeader().setSortIndicatorShown(True)

        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setFixedWidth(40)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        self.table.itemSelectionChanged.connect(self.SelectionChanged)
        self.table.doubleClicked.connect(self.PlaySong)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.ShowContextMenu)

        gb_layout.addWidget(self.table)
        gb.setLayout(gb_layout)
        self.MainLayout.addWidget(gb)

    def SetupMenu(self):
        def CreateMenuWidget(menu, text, color_class, callback, Close=True):
            action = QWidgetAction(menu)
            
            # Container widget to handle padding/margins inside the menu
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(4, 2, 4, 2) # Button spacing inside dropdown
            
            btn = QPushButton(text)
            btn.setProperty("class", color_class)

            if Close: btn.clicked.connect(menu.close)
            btn.clicked.connect(callback)
            
            layout.addWidget(btn)
            action.setDefaultWidget(container)
            menu.addAction(action)
            return btn
        
        def ShowFormatMenu():
            Position = ChangeFormatBtn.mapToGlobal(ChangeFormatBtn.rect().topRight())
            SelectedAction = FormatMenu.exec(Position)
            if SelectedAction:
                ConfigMenu.close()
                self.ChangeFormat(SelectedAction.text())

        # Action Menu
        ActionMenu = self.menuBar().addMenu("Actions")

        CreateMenuWidget(ActionMenu, "Add New Song", "standard", self.OpenAddSongDialog)
        self.DownloadBtn = CreateMenuWidget(ActionMenu, "Download Pending", "success", self.StartDownload)
        CreateMenuWidget(ActionMenu, "Update ALL Images", "standard", lambda: self.StartImageUpdate(False, False))
        CreateMenuWidget(ActionMenu, "Redownload ALL Images", "success", lambda: self.StartImageUpdate(False, True))

        # Song Menu
        self.SongMenu = self.menuBar().addMenu("Song")

        self.EditSongBtn = CreateMenuWidget(self.SongMenu, "Edit Details", "standard", self.EditSong)
        self.DelBtn = CreateMenuWidget(self.SongMenu, "Delete from List", "danger", lambda: self.DeleteSong())
        self.UpdateImgBtn = CreateMenuWidget(self.SongMenu, "Update Image(s)", "standard", lambda: self.StartImageUpdate(True, False))
        self.RedownloadImgBtn = CreateMenuWidget(self.SongMenu, "Redownload Image(s)", "success", lambda: self.StartImageUpdate(True, True))
        
        for b in [self.EditSongBtn, self.DelBtn, self.UpdateImgBtn]: b.setEnabled(False) # Disable buttons initially

        # Config Menu
        ConfigMenu = self.menuBar().addMenu("Config")

        CreateMenuWidget(ConfigMenu, "Change Music Folder", "standard", self.ChangeDownloadDir)
        CreateMenuWidget(ConfigMenu, "Open Images Folder", "standard", lambda: bk.OpenImageDir())
        ChangeFormatBtn = CreateMenuWidget(ConfigMenu, "Change Music Format ->", "standard", ShowFormatMenu, False)

        FormatMenu = QMenu(ConfigMenu)
        FormatGroup = QActionGroup(self)
        FormatGroup.setExclusive(True)

        CurrentFormat = bk.Config.get("Encoding")

        for fmt in ["mp3", "flac", "m4a"]:
            action = QAction(fmt, self)
            action.setCheckable(True)
            if fmt == CurrentFormat: action.setChecked(True)
            FormatGroup.addAction(action)
            FormatMenu.addAction(action)
    
    def SetupPlayer(self):
        def SetPlaybuttonText():
            if self.Player.playbackState() == QMediaPlayer.PlaybackState.PlayingState: self.PlayBtn.setText("⏸")
            elif self.Player.playbackState() == QMediaPlayer.PlaybackState.PausedState: self.PlayBtn.setText("▶")

        def TogglePlay():
            if self.Player.playbackState() == QMediaPlayer.PlaybackState.PlayingState: self.Player.pause()
            elif self.Player.playbackState() == QMediaPlayer.PlaybackState.PausedState: self.Player.play()

        def MediaStatusChanged(status):
            if status == QMediaPlayer.MediaStatus.EndOfMedia:
                self.PlayBtn.setText("▶")
                self.SeekSlider.setValue(0)

        self.Player = QMediaPlayer()
        self.AudioOutput = QAudioOutput()
        self.AudioOutput.setVolume(1.0)
        self.Player.setAudioOutput(self.AudioOutput)

        self.Player.positionChanged.connect(lambda position: self.SeekSlider.setValue(position))
        self.Player.durationChanged.connect(lambda duration: self.SeekSlider.setRange(0, duration))
        self.Player.mediaStatusChanged.connect(MediaStatusChanged)
        self.Player.playbackStateChanged.connect(SetPlaybuttonText)

        self.PlayerFrame = QFrame()
        self.PlayerFrame.setObjectName("PlayerFrame")
        PlayerLayout = QHBoxLayout(self.PlayerFrame)

        # Play Button
        self.PlayBtn = QPushButton("▶")
        self.PlayBtn.setObjectName("PlayBtn")
        self.PlayBtn.clicked.connect(TogglePlay)
        PlayerLayout.addWidget(self.PlayBtn)

        # Scrubber and Title
        ScrubberLayout = QVBoxLayout()
        self.NowPlayingLbl = QLabel("Select a song to play")
        self.NowPlayingLbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.NowPlayingLbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #ddd;")
        ScrubberLayout.addWidget(self.NowPlayingLbl)

        # Slider
        self.SeekSlider = QSlider(Qt.Orientation.Horizontal)
        self.SeekSlider.setRange(0, 0)
        self.SeekSlider.sliderMoved.connect(lambda position: self.Player.setPosition(position))
        self.SeekSlider.sliderPressed.connect(lambda: self.Player.pause()) # Pause while dragging
        self.SeekSlider.sliderReleased.connect(lambda: self.Player.play()) # Resume after drag
        ScrubberLayout.addWidget(self.SeekSlider)

        PlayerLayout.addLayout(ScrubberLayout)
        self.MainLayout.addWidget(self.PlayerFrame, alignment=Qt.AlignmentFlag.AlignHCenter)
    
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
        
        self.Player.setSource(QUrl.fromLocalFile(str(Path)))
        self.Player.play()
        self.NowPlayingLbl.setText(title)
        self.status.showMessage(f"Playing: {title}")
    
    def ShowContextMenu(self, pos):
        if not self.table.selectionModel().hasSelection(): return
        self.SongMenu.exec(self.table.viewport().mapToGlobal(pos))

    def SelectionChanged(self):
        selected = self.table.selectionModel().selectedRows()
        count = len(selected)
        
        self.EditSongBtn.setEnabled(count == 1)
        self.DelBtn.setEnabled(count > 0)
        self.UpdateImgBtn.setEnabled(count > 0)
        self.RedownloadImgBtn.setEnabled(count > 0)

    def StartDownload(self):
        def DownloadDone():
            QMessageBox.information(self, "Download Complete", "All pending songs have been downloaded.")
            self.DownloadBtn.setEnabled(True) # Re-enable menu action
            self.RefreshList()
            self.status.showMessage("Ready")
        
        self.status.showMessage("Starting download...")
        self.DownloadBtn.setEnabled(False) # Disable menu action
        self.worker = DownloadWorker()
        self.worker.ProgressUpdate.connect(lambda s: self.status.showMessage(s))
        self.worker.RefreshList.connect(self.RefreshList)
        self.worker.Finished.connect(DownloadDone)
        self.worker.start()

    def SetupStatusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def RefreshList(self):
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
        
        self.SelectionChanged()
    
    def HeaderClicked(self, index):
        ClickedCol = self.Columns[index]

        if self.SortBy == ClickedCol:
            self.SortOrder = not self.SortOrder  
        else:
            self.SortBy = ClickedCol
            self.SortOrder = True  

        self.RefreshList()

    def OpenAddSongDialog(self):
        dlg = AddSongDialog(self)
        dlg.song_added.connect(self.RefreshList) 
        dlg.exec()
        self.RefreshList() 

    def EditSong(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        title = self.table.item(rows[0].row(), 0).text()
        dlg = EditSongDialog(title, self)
        if dlg.exec():
            self.RefreshList()

    def DeleteSong(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return

        # Confirmation dialog
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Confirm Deletion")
        msg.setText(f"Are you sure you want to delete {len(rows)} selected song(s)?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        DiskDelCB = QCheckBox("Also delete file(s) from disk")
        msg.setCheckBox(DiskDelCB)

        if msg.exec() == QMessageBox.StandardButton.No: return
        DiskDelete = DiskDelCB.isChecked()

        titles = [self.table.item(row.row(), 0).text() for row in rows]
        for title in titles:
            if DiskDelete: bk.DeleteSongFromDisk(title)
            bk.SongDF = bk.SongDF[bk.SongDF['Title'] != title]
        bk.SaveSongfile()
        self.RefreshList()
        self.status.showMessage(f"Deleted {len(titles)} songs.")
    
    def StartImageUpdate(self, selected=False, redownload=False):
        def UpdateDone():
            QMessageBox.information(self, "Done", "Images Updated")
            self.status.showMessage("Ready")

        if selected:
            rows = self.table.selectionModel().selectedRows()
            titles = [self.table.item(row.row(), 0).text() for row in rows]
        else:
            titles = bk.SongDF['Title'].tolist()

        self.status.showMessage(f"Updating images for {len(titles)} songs...")
        QApplication.processEvents()
        
        self.img_worker = ImageWorker(titles, redownload)
        self.img_worker.Finished.connect(UpdateDone)
        self.img_worker.start()
    
    def ChangeFormat(self, fmt):
        bk.UpdateDefaultFormat(fmt)
        self.status.showMessage(f"Default format set to: {fmt}")

    def ChangeDownloadDir(self):
        NewDir = QFileDialog.getExistingDirectory(self, "Select Music Download Folder", str(bk.MusicDir))
        if NewDir:
            bk.ChangeMusicDir(NewDir)
            self.status.showMessage(f"Download folder changed to: {NewDir}")
        self.RefreshList()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        height = self.height()

        PlayerFrameWidth = int(width * 0.75)
        PlayerFrameHeight = int(height * 0.10)
        
        self.PlayerFrame.setFixedSize(PlayerFrameWidth, PlayerFrameHeight)
        PlayBtnSize = int(PlayerFrameHeight * 0.6)
        self.PlayBtn.setStyleSheet(f"border-radius: {PlayBtnSize // 2}px; font-size: {int(PlayBtnSize * 0.4)}px;")
        self.PlayBtn.setFixedSize(PlayBtnSize, PlayBtnSize)

        # Slider
        HandleSize = int(PlayerFrameHeight / 4)
        
        # formula to vertically center dragger: Margin = -(Handle_Height - Groove_Height) / 2
        GrooveHeight = int(PlayerFrameHeight / 7)
        margin = -(HandleSize - GrooveHeight) // 2

        self.SeekSlider.setStyleSheet(f"""
            QSlider {{
                height: {HandleSize+1}px; /* Prevent the handle from clipping */
            }}
            QSlider::groove:horizontal {{
                height: {GrooveHeight}px;
                border-radius: {GrooveHeight // 2}px;
            }}
            QSlider::handle:horizontal {{
                width: {HandleSize}px;
                height: {HandleSize}px;
                margin: {margin}px 0;
                border-radius: {HandleSize // 2}px;
            }}
            QSlider::sub-page:horizontal {{
                border-radius: {GrooveHeight // 2}px;
            }}
        """)
    
    def closeEvent(self, event):
        bk.SaveSongfile()
        event.accept()

    def ApplyStyles(self):
        with open('style.css', "r") as f:
            stylesheet = f.read()
        self.setStyleSheet(stylesheet)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MusicManagerWindow()
    window.show()
    sys.exit(app.exec())