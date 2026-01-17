import Backend as bk
from PyQt6.QtCore import QThread, pyqtSignal

# Download Thread
class DownloadWorker(QThread):
    ProgressUpdate = pyqtSignal(str) 
    RefreshList = pyqtSignal()       
    Finished = pyqtSignal()          

    def run(self):
        PendingDownload = bk.SongDF[bk.SongDF['Status'] != 'Downloaded']
        if PendingDownload.empty:
            self.ProgressUpdate.emit("All songs are already downloaded.")
            self.Finished.emit()
            return

        for _, row in PendingDownload.iterrows():
            title = row['Title']
            self.ProgressUpdate.emit(f"Downloading: {title}...")
            bk.DownloadSong(row['VideoID'], title, artist=row['Artist'], genre=row['Genre'], encoding=bk.Config.get("Encoding"))
            self.RefreshList.emit()

        self.ProgressUpdate.emit("Ready")
        self.Finished.emit()

# Update Images Thread
class ImageWorker(QThread):
    Finished = pyqtSignal()

    def __init__(self, titles, redownload):
        super().__init__()
        self.titles = titles
        self.redownload = redownload

    def run(self):
        for title in self.titles:
            ImagePath = bk.AppData / "Images" / f"{title}.jpg"
            # Download cover if not exists or redownload is True
            if self.redownload or not ImagePath.exists():
                id = bk.SongDF.loc[bk.SongDF['Title'] == title, 'VideoID'].item()
                bk.DownloadCover(id, title)
            
            # Add cover art
            for ext in ['mp3', 'flac', 'm4a']:
                SongPath = bk.MusicDir / f"{title}.{ext}"
                if SongPath.exists() and ImagePath.exists():
                    bk.AddCoverArt(SongPath, ImagePath, ext)
                    break
        self.Finished.emit()