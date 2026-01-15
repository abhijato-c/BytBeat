import sys
import Backend as bk
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, 
    QGroupBox, QMessageBox, QDialog, QLabel, QLineEdit, 
    QTextEdit, QAbstractItemView, QStatusBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor

# Download Thread
class DownloadWorker(QThread):
    ProgressUpdate = pyqtSignal(str) 
    RefreshList = pyqtSignal()       
    Finished = pyqtSignal()          

    def run(self):
        to_download = bk.SongDF[bk.SongDF['status'] != 'Downloaded'] #
        if to_download.empty:
            self.ProgressUpdate.emit("All songs are already downloaded.")
            self.Finished.emit()
            return

        for _, row in to_download.iterrows():
            title = row['title']
            self.ProgressUpdate.emit(f"Downloading: {title}...")
            bk.DownloadSong(row['VideoID'], title, artist=row['artist'], genre=row['genre']) #
            self.RefreshList.emit()

        self.ProgressUpdate.emit("Ready")
        self.Finished.emit()

# Update Images Thread
class ImageWorker(QThread):
    Finished = pyqtSignal()

    def run(self):
        for _, row in bk.SongDF.iterrows(): #
            img_path = bk.AppData / "Images" / f"{row['title']}.jpg" #
            for ext in ['mp3', 'flac', 'm4a']:
                song_path = bk.MusicDir / f"{row['title']}.{ext}" #
                if song_path.exists() and img_path.exists():
                    bk.AddCoverArt(song_path, img_path, ext) #
                    break
        self.Finished.emit()

# Add Song popup
class AddSongDialog(QDialog):
    song_added = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Song")
        self.setFixedSize(400, 300)
        self.layout = QVBoxLayout(self)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        FormLayout = QVBoxLayout()
        self.TitleInput = self.create_input("Title (Required):", FormLayout)
        self.URLInput = self.create_input("YouTube URL (Required):", FormLayout)
        self.ArtistInput = self.create_input("Artist (Optional):", FormLayout)
        self.GenreInput = self.create_input("Genre (Optional):", FormLayout)
        self.layout.addLayout(FormLayout)

        btn_box = QHBoxLayout()
        SaveBtn = QPushButton("Add Song")
        SaveBtn.clicked.connect(self.save_song)
        SaveBtn.setProperty("class", "success")

        CloseBtn = QPushButton("Close")
        CloseBtn.clicked.connect(self.reject) 
        
        btn_box.addWidget(SaveBtn)
        btn_box.addWidget(CloseBtn)
        self.layout.addLayout(btn_box)

    def create_input(self, label_text, layout):
        lbl = QLabel(label_text)
        inp = QLineEdit()
        layout.addWidget(lbl)
        layout.addWidget(inp)
        return inp

    def save_song(self):
        title = self.TitleInput.text().strip()
        url = self.URLInput.text().strip()
        artist = self.ArtistInput.text().strip()
        genre = self.GenreInput.text().strip()

        if not title or not url:
            self.status_label.setStyleSheet("color: #f44336;")
            self.status_label.setText("Error: Title and URL are required!")
            return

        bk.AddSongToSongfile(title, url, artist, genre)
        
        self.status_label.setStyleSheet("color: #4CAF50;")
        self.status_label.setText(f"Song '{title}' has been added.")
        self.TitleInput.clear()
        self.URLInput.clear()
        self.ArtistInput.clear()
        self.GenreInput.clear()
        self.TitleInput.setFocus()
        
        self.song_added.emit()

# Edit Song Popup
class EditSongDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit: {title}")
        self.setFixedSize(400, 350)
        self.original_title = title
        self.layout = QVBoxLayout(self)

        row = bk.SongDF.loc[bk.SongDF['title'] == title].iloc[0]
        
        self.title_input = self.create_field("Title:", row['title'])
        current_url = f"https://www.youtube.com/watch?v={row['VideoID']}"
        self.url_input = self.create_field("YouTube URL:", current_url)
        self.artist_input = self.create_field("Artist:", row['artist'])
        self.genre_input = self.create_field("Genre:", row['genre'])

        save_btn = QPushButton("Save Changes")
        save_btn.setProperty("class", "success")
        save_btn.clicked.connect(self.save)
        self.layout.addWidget(save_btn)

    def create_field(self, label, value):
        self.layout.addWidget(QLabel(label))
        txt = QTextEdit()
        txt.setPlainText(str(value))
        txt.setFixedHeight(30)
        self.layout.addWidget(txt)
        return txt

    def save(self):
        new_title = self.title_input.toPlainText().strip()
        new_url = self.url_input.toPlainText().strip()
        new_artist = self.artist_input.toPlainText().strip()
        new_genre = self.genre_input.toPlainText().strip()

        if not new_title:
            QMessageBox.critical(self, "Error", "Title cannot be empty")
            return

        bk.UpdateSongDetails(self.original_title, new_title, new_artist, new_genre, URL=new_url) #
        self.accept()

# Main Window
class MusicManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Manager")
        self.setGeometry(100, 100, 1100, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        self.setup_table()
        self.setup_controls()
        self.setup_statusbar()
        self.apply_styles()
        self.refresh_list()

    def setup_table(self):
        gb = QGroupBox("Library Status")
        gb_layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["S.No", "Title", "Artist", "Genre", "Status"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        self.table.itemSelectionChanged.connect(self.on_selection_change)

        gb_layout.addWidget(self.table)
        gb.setLayout(gb_layout)
        self.main_layout.addWidget(gb)

    def setup_controls(self):
        controls_layout = QHBoxLayout()

        global_gb = QGroupBox("Global Actions")
        global_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add New Song")
        self.btn_add.clicked.connect(self.open_add_song)
        
        self.btn_download = QPushButton("Download Pending")
        self.btn_download.setProperty("class", "success")
        self.btn_download.clicked.connect(self.start_download)

        self.btn_update_img = QPushButton("Update Images")
        self.btn_update_img.clicked.connect(self.start_image_update)

        global_layout.addWidget(self.btn_add)
        global_layout.addWidget(self.btn_download)
        global_layout.addWidget(self.btn_update_img)
        global_gb.setLayout(global_layout)

        selected_gb = QGroupBox("Selected Song Options")
        selected_layout = QHBoxLayout()

        self.btn_edit = QPushButton("Edit Details")
        self.btn_edit.clicked.connect(self.edit_song)
        
        self.btn_del_list = QPushButton("Delete from List")
        self.btn_del_list.setProperty("class", "danger")
        self.btn_del_list.clicked.connect(lambda: self.delete_song("list"))

        self.btn_del_folder = QPushButton("Delete from Folder")
        self.btn_del_folder.setProperty("class", "danger")
        self.btn_del_folder.clicked.connect(lambda: self.delete_song("folder"))
        
        self.btn_del_both = QPushButton("Delete Both")
        self.btn_del_both.setProperty("class", "danger_dark")
        self.btn_del_both.clicked.connect(lambda: self.delete_song("both"))

        selected_layout.addWidget(self.btn_edit)
        selected_layout.addWidget(self.btn_del_list)
        selected_layout.addWidget(self.btn_del_folder)
        selected_layout.addWidget(self.btn_del_both)
        selected_gb.setLayout(selected_layout)

        for btn in [self.btn_edit, self.btn_del_list, self.btn_del_folder, self.btn_del_both]:
            btn.setEnabled(False)

        controls_layout.addWidget(global_gb, 1)
        controls_layout.addWidget(selected_gb, 1)
        self.main_layout.addLayout(controls_layout)

    def setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

    def refresh_list(self):
        self.table.setRowCount(0)
        for index, row in bk.SongDF.iterrows():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            def make_item(text, center=False):
                item = QTableWidgetItem(str(text))
                if center: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item

            self.table.setItem(row_idx, 0, make_item(index + 1, True))
            self.table.setItem(row_idx, 1, make_item(row['title']))
            self.table.setItem(row_idx, 2, make_item(row['artist']))
            self.table.setItem(row_idx, 3, make_item(row['genre']))
            self.table.setItem(row_idx, 4, make_item(row['status'], True))
        
        self.on_selection_change()

    def on_selection_change(self):
        selected = self.table.selectionModel().selectedRows()
        count = len(selected)
        self.btn_edit.setEnabled(count == 1)
        self.btn_del_list.setEnabled(count > 0)
        self.btn_del_folder.setEnabled(count > 0)
        self.btn_del_both.setEnabled(count > 0)

    def open_add_song(self):
        dlg = AddSongDialog(self)
        dlg.song_added.connect(self.refresh_list) 
        dlg.exec()
        self.refresh_list() 

    def edit_song(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        title = self.table.item(rows[0].row(), 1).text()
        dlg = EditSongDialog(title, self)
        if dlg.exec():
            self.refresh_list()

    def delete_song(self, mode):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                   f"Are you sure you want to delete {len(rows)} item(s)?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        titles = [self.table.item(row.row(), 1).text() for row in rows]
        for title in titles:
            if mode in ["folder", "both"]: bk.DeleteSongFromDisk(title)
            if mode in ["list", "both"]: bk.SongDF = bk.SongDF[bk.SongDF.title != title]
        if mode in ["list", "both"]: bk.SaveSongfile()
        self.refresh_list()
        self.status.showMessage(f"Deleted {len(titles)} songs ({mode}).")

    def start_download(self):
        self.btn_download.setEnabled(False)
        self.worker = DownloadWorker()
        self.worker.ProgressUpdate.connect(lambda s: self.status.showMessage(s))
        self.worker.RefreshList.connect(self.refresh_list)
        self.worker.Finished.connect(self.on_download_finished)
        self.worker.start()

    def on_download_finished(self):
        self.btn_download.setEnabled(True)
        QMessageBox.information(self, "Success", "Downloads Complete!")
        self.refresh_list()

    def start_image_update(self):
        self.status.showMessage("Updating images")
        self.img_worker = ImageWorker()
        self.img_worker.Finished.connect(lambda: QMessageBox.information(self, "Done", "Images Updated"))
        self.img_worker.start()

    def closeEvent(self, event):
        bk.SaveSongfile()
        event.accept()

    def apply_styles(self):
        with open('style.qcss', "r") as f:
            stylesheet = f.read()
        self.setStyleSheet(stylesheet)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MusicManagerWindow()
    window.show()
    sys.exit(app.exec())