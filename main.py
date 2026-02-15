import sys
import Backend as bk
from time import sleep

from PopupDialogs import AddSongDialog, EditSongDialog
from TaskThreads import DownloadWorker, ImageWorker, InitWorker
from Downloader import Downloader
from Player import Player

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QCheckBox, QSplashScreen,
    QPushButton, QMessageBox, QStatusBar, QFileDialog, QMenu, QWidgetAction, QHBoxLayout, QStackedWidget
)

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon(bk.ResourcePath('Static/logo.ico')))
        self.setWindowTitle("BytBeat")
        self.setGeometry(100, 100, 1100, 600)
        self.setStyleSheet(bk.LoadStylesheet('Main'))
        
        MainWidget = QWidget()
        self.setCentralWidget(MainWidget)
        self.MainLayout = QVBoxLayout(MainWidget)

        self.worker = None
        self.Mode = "Downloader"
        self.Selection = []

        bk.UpdateSongStatuses()

        self.FfmpegCheck()
        self.SetupTabs()
        self.SetupMenu()
        self.SetupStatusbar()
        self.SetupWin()

        self.ModeChanged("Downloader")
        self.UpdateSelection([])
        self.RefreshList()
    
    def FfmpegCheck(self):
        if not bk.IsFfmpegInstalled(): 
            print("local install")
            try: bk.LocalFFMPEG()
            except: print("local install failed")
        
        # Install failed
        if not bk.IsFfmpegInstalled(): 
            instruct = bk.InstallInstructions()
            QMessageBox.critical(None, "FFmpeg not found", 
                            f"FFmpeg is required to run BytBeat. Please follow the instructions to install: \n {instruct}")
            sys.exit(1)
    
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
        self.DownloadSongBtn = CreateMenuWidget(self.SongMenu, "Download Song(s)", "success", lambda: self.StartDownload(True))
        self.DelBtn = CreateMenuWidget(self.SongMenu, "Delete", "danger", self.DeleteSong)
        self.UpdateImgBtn = CreateMenuWidget(self.SongMenu, "Update Image(s)", "standard", lambda: self.StartImageUpdate(True, False))
        self.RedownloadImgBtn = CreateMenuWidget(self.SongMenu, "Redownload Image(s)", "success", lambda: self.StartImageUpdate(True, True))

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
    
    def SetupTabs(self):
        self.TabContainer = QWidget()
        self.TabContainer.setObjectName("TabContainer")
        self.TabLayout = QHBoxLayout(self.TabContainer)
        self.TabLayout.setContentsMargins(5, 5, 5, 5)
        self.TabLayout.setSpacing(5)
        self.TabLayout.addStretch()

        self.DownloaderTab = QPushButton("Downloader")
        self.DownloaderTab.setObjectName("TabBtn")
        self.DownloaderTab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.DownloaderTab.clicked.connect(lambda: self.ModeChanged("Downloader"))
        self.TabLayout.addWidget(self.DownloaderTab)

        self.PlayerTab = QPushButton("Player")
        self.PlayerTab.setObjectName("TabBtn")
        self.PlayerTab.setCursor(Qt.CursorShape.PointingHandCursor)
        self.PlayerTab.clicked.connect(lambda: self.ModeChanged("Player"))
        self.TabLayout.addWidget(self.PlayerTab)

        self.TabLayout.addStretch()
        self.MainLayout.addWidget(self.TabContainer)
    
    def SetupWin(self):
        self.Win = QStackedWidget()

        self.Downloader = Downloader()
        self.Downloader.SelectionUpdate.connect(self.UpdateSelection)
        self.Downloader.ContextUpdate.connect(self.ShowContextMenu)
        self.Win.addWidget(self.Downloader)

        self.Player = Player()
        self.Player.SelectionUpdate.connect(self.UpdateSelection)
        self.Win.addWidget(self.Player)

        self.MainLayout.addWidget(self.Win)

    def ModeChanged(self, name):
        self.Mode = name
        if name == "Downloader":
            self.DownloaderTab.setProperty("active", True)
            self.PlayerTab.setProperty("active", False)
            self.Win.setCurrentIndex(0)
        elif name == "Player":
            self.DownloaderTab.setProperty("active", False)
            self.PlayerTab.setProperty("active", True)
            self.Win.setCurrentIndex(1)
        
        self.DownloaderTab.style().unpolish(self.DownloaderTab)
        self.DownloaderTab.style().polish(self.DownloaderTab)
        self.PlayerTab.style().unpolish(self.PlayerTab)
        self.PlayerTab.style().polish(self.PlayerTab)
    
    def ShowContextMenu(self, pos):
        self.SongMenu.exec(pos)

    def UpdateSelection(self, titles):
        self.Selection = titles
        count = len(titles)
        
        self.EditSongBtn.setEnabled(count == 1)
        self.DownloadSongBtn.setEnabled(count > 0)
        self.DelBtn.setEnabled(count > 0)
        self.UpdateImgBtn.setEnabled(count > 0)
        self.RedownloadImgBtn.setEnabled(count > 0)

    def StartDownload(self, selected = False):
        def DownloadDone(successes, fails):
            QMessageBox.information(self, "Download Complete", f"{successes} songs downloaded successfully. \n {fails} songs failed to download.")
            self.DownloadBtn.setEnabled(True)
            self.Downloader.RefreshList()
            self.status.showMessage("Ready")
        
        if selected:
            titles = self.Selection
        else:
            titles = bk.SongDF[bk.SongDF['Status'] != 'Downloaded']['Title'].tolist()
        
        self.status.showMessage("Starting download...")
        self.DownloadBtn.setEnabled(False) # Disable menu action
        self.worker = DownloadWorker(titles)
        self.worker.ProgressUpdate.connect(lambda s: self.status.showMessage(s))
        self.worker.RefreshList.connect(self.RefreshList)
        self.worker.Finished.connect(DownloadDone)
        self.worker.start()

    def SetupStatusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def OpenAddSongDialog(self):
        dlg = AddSongDialog(self)
        dlg.song_added.connect(self.RefreshList) 
        dlg.exec()

    def EditSong(self):
        title = self.Selection[0]
        dlg = EditSongDialog(title, self)
        if dlg.exec():
            self.RefreshList()

    def DeleteSong(self):
        # Confirmation dialog
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Confirm Deletion")
        msg.setText(f"Are you sure you want to delete {len(self.Selection)} selected song(s)?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        DiskDelCB = QCheckBox("Also delete file(s) from disk")
        msg.setCheckBox(DiskDelCB)

        if msg.exec() == QMessageBox.StandardButton.No: return
        DiskDelete = DiskDelCB.isChecked()

        for title in self.Selection:
            if DiskDelete: bk.DeleteSongFromDisk(title)
            bk.SongDF = bk.SongDF[bk.SongDF['Title'] != title]
        bk.SaveSongfile()
        self.RefreshList()
        self.status.showMessage(f"Deleted {len(self.Selection)} songs.")
    
    def StartImageUpdate(self, selected=False, redownload=False):
        def UpdateDone():
            QMessageBox.information(self, "Done", "Images Updated")
            self.status.showMessage("Ready")

        if selected:
            titles = self.Selection
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
    
    def RefreshList(self):
        self.Downloader.RefreshList()
        self.Player.RefreshList()
    
    def closeEvent(self, event):
        bk.SaveSongfile()
        event.accept()

if __name__ == "__main__":
    def StartMainWindow(success):
        if success:
            #sleep(1)
            window = MainWindow()
            window.show()
            splash.finish(window)
        else:
            splash.close()
            instruct = bk.InstallInstructions()
            QMessageBox.critical(None, "FFmpeg Error", f"Failed to install FFmpeg.\n{instruct}")
            sys.exit(1)
    
    app = QApplication(sys.argv)
    app.setDesktopFileName("BytBeat")
    app.setWindowIcon(QIcon(bk.ResourcePath('Static/logo.ico')))
    app.setStyle("Fusion")

    pixmap = QPixmap()
    pixmap.load(bk.ResourcePath('Static/BytBeat.png'))
    pixmap = pixmap.scaledToHeight(500)
    splash = QSplashScreen(pixmap)
    splash.showMessage("Loading app", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
    splash.show()

    worker = InitWorker()
    worker.status.connect(lambda msg: splash.showMessage(msg, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white))
    worker.finished.connect(StartMainWindow)
    
    app.worker = worker 
    worker.start()

    sys.exit(app.exec())