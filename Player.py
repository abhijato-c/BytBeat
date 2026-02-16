import random
import Backend as bk

from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QPixmap, QIcon, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QScrollArea, QPushButton, QHBoxLayout, QLabel, QSlider, QMessageBox
)

'''
todo:
Time label
Keyboard shortcuts (space for play/pause, left/right for prev/next)
'''


class Player(QWidget):
    SelectionUpdate = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.setStyleSheet(bk.LoadStylesheet('Player'))
        self.MainLayout = QHBoxLayout(self)

        self.SongButtons = {}
        self.ModeBtns = {}
        self.CurrentSong = None
        self.PlayMode = 'Play Once'

        self.SetupSidebar()
        self.MainLayout.addStretch(1)
        self.SetupPlayWin()

        self.MainLayout.setStretch(0, 24)
        self.MainLayout.setStretch(1, 1)
        self.MainLayout.setStretch(2, 75)

        self.SetPlayMode('Play Once')

    def SetupSidebar(self):
        self.Sidebar = QScrollArea()
        self.Sidebar.setObjectName("Sidebar")
        self.Sidebar.setWidgetResizable(True)
        self.Sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.Sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.SidebarContent = QWidget()
        self.SidebarContent.setObjectName("SidebarContent")
        self.SidebarLayout = QVBoxLayout(self.SidebarContent)
        self.SidebarLayout.setContentsMargins(5, 10, 5, 10)
        self.SidebarLayout.addStretch(1)

        self.Sidebar.setWidget(self.SidebarContent)
        self.MainLayout.addWidget(self.Sidebar)
    
    def SetupPlayWin(self):
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

                if self.PlayMode == 'Sequential':
                    PlayNext()
                elif self.PlayMode == 'Shuffle':
                    titles = bk.SongDF[bk.SongDF['Status'] == "Downloaded"]['Title'].tolist()
                    if len(titles) == 0: return
                    title = random.choice(titles)
                    self.PlaySong(title)
                elif self.PlayMode == 'Repeat':
                    self.PlaySong(self.CurrentSong)
        
        def FormatTime(ms):
            seconds = (ms // 1000) % 60
            minutes = (ms // 60000)
            return f"{minutes}:{seconds:02}"
        
        def PositionChanged(pos):
            self.SeekSlider.setValue(pos)
            #TimeLbl.setText(f"{FormatTime(pos)} / {FormatTime(self.AudioPlayer.duration())}")
        
        def PlayNext():
            if self.CurrentSong is None: return
            
            Current = bk.SongDF.index[bk.SongDF['Title'] == self.CurrentSong].tolist()
            if len(Current) == 0: return
            idx = Current[0]

            idx = (idx + 1) % len(bk.SongDF)
            song = bk.SongDF.iloc[idx]
            while song['Status'] != "Downloaded":
                idx = (idx + 1) % len(bk.SongDF)
                song = bk.SongDF.iloc[idx]
            
            self.PlaySong(song['Title'])
        
        def PlayPrev():
            if self.CurrentSong is None: return
            
            Current = bk.SongDF.index[bk.SongDF['Title'] == self.CurrentSong].tolist()
            if len(Current) == 0: return
            idx = Current[0]

            idx = (idx - 1) % len(bk.SongDF)
            song = bk.SongDF.iloc[idx]
            while song['Status'] != "Downloaded":
                idx = (idx - 1) % len(bk.SongDF)
                song = bk.SongDF.iloc[idx]
            
            self.PlaySong(song['Title'])
        
        def CreateModeBtn(text):
            btn = QPushButton()
            btn.setObjectName("ModeBtn")
            icon = QIcon(bk.ResourcePath(f'Static/{text}.png'))
            btn.setIcon(icon)
            btn.clicked.connect(lambda: self.SetPlayMode(text))
            self.PlayModeLayout.addWidget(btn, alignment = Qt.AlignmentFlag.AlignRight)
            self.ModeBtns[text] = btn

        self.AudioPlayer = QMediaPlayer()
        self.AudioOut = QAudioOutput()
        self.AudioOut.setVolume(1.0)
        self.AudioPlayer.setAudioOutput(self.AudioOut)

        self.AudioPlayer.positionChanged.connect(PositionChanged)
        self.AudioPlayer.durationChanged.connect(lambda duration: self.SeekSlider.setRange(0, duration))
        self.AudioPlayer.mediaStatusChanged.connect(MediaStatusChanged)
        self.AudioPlayer.playbackStateChanged.connect(SetPlaybuttonText)

        self.PlayWin = QFrame()
        self.PlayWin.setObjectName("PlayWin")
        self.PlayLayout = QVBoxLayout(self.PlayWin)
        self.PlayLayout.addStretch(10)

        TopLayout = QHBoxLayout()

        self.PlayModeLayout = QVBoxLayout()
        CreateModeBtn('Play Once')
        CreateModeBtn('Sequential')
        CreateModeBtn('Shuffle')
        CreateModeBtn('Repeat')
        TopLayout.addLayout(self.PlayModeLayout)

        self.SongImage = QLabel()
        self.SongImage.setObjectName("Image")
        pixmap = QPixmap(bk.ResourcePath('Static/Note.png'))
        self.SongImage.pix = pixmap
        self.SongImage.setPixmap(pixmap.scaled(10, 10, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.SongImage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        TopLayout.addWidget(self.SongImage, alignment = Qt.AlignmentFlag.AlignCenter)

        VolLayout = QVBoxLayout()
        self.VolSlider = QSlider(Qt.Orientation.Vertical)
        self.VolSlider.setRange(0, 100)
        self.VolSlider.setValue(100)
        self.VolSlider.valueChanged.connect(lambda v: self.AudioOut.setVolume(v / 100))
        VolLayout.addWidget(self.VolSlider, alignment = Qt.AlignmentFlag.AlignLeft) 
        TopLayout.addLayout(VolLayout)
        
        self.PlayLayout.addLayout(TopLayout)

        self.PlayLayout.addStretch(1)
        self.SongTitle = QLabel("Song Title")
        self.SongTitle.setObjectName("Title")
        self.SongTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.PlayLayout.addWidget(self.SongTitle, alignment = Qt.AlignmentFlag.AlignCenter)

        self.PlayLayout.addStretch(1)
        self.SongArtist = QLabel("Artist Name")
        self.SongArtist.setObjectName("Artist")
        self.SongArtist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.PlayLayout.addWidget(self.SongArtist, alignment = Qt.AlignmentFlag.AlignCenter)

        self.NavLayout = QHBoxLayout()
        self.NavLayout.addStretch()

        self.PrevBtn = QPushButton()
        self.PrevBtn.setIcon(QIcon(bk.ResourcePath('Static/Prev.png')))
        self.PrevBtn.setObjectName("NavBtn")
        self.PrevBtn.clicked.connect(PlayPrev)
        self.NavLayout.addWidget(self.PrevBtn)

        self.PlayBtn = QPushButton()
        self.PlayBtn.setIcon(QIcon(bk.ResourcePath('Static/Play.png')))
        self.PlayBtn.setObjectName("PlayBtn")
        self.PlayBtn.clicked.connect(TogglePlay)
        self.NavLayout.addWidget(self.PlayBtn)

        self.NextBtn = QPushButton()
        self.NextBtn.setIcon(QIcon(bk.ResourcePath('Static/Next.png')))
        self.NextBtn.setObjectName("NavBtn")
        self.NextBtn.clicked.connect(PlayNext)
        self.NavLayout.addWidget(self.NextBtn)

        self.NavLayout.addStretch()
        self.PlayLayout.addLayout(self.NavLayout)

        self.SeekSlider = QSlider(Qt.Orientation.Horizontal)
        self.SeekSlider.setRange(0, 0)
        self.SeekSlider.sliderMoved.connect(lambda position: self.AudioPlayer.setPosition(position))
        self.SeekSlider.sliderPressed.connect(lambda: self.AudioPlayer.pause())
        self.SeekSlider.sliderReleased.connect(lambda: self.AudioPlayer.play())
        self.PlayLayout.addWidget(self.SeekSlider, alignment = Qt.AlignmentFlag.AlignCenter)

        self.PlayLayout.addStretch(10)
        self.MainLayout.addWidget(self.PlayWin)
    
    def SetPlayMode(self, mode):
        CloseBtn = self.ModeBtns[self.PlayMode]
        OpenBtn = self.ModeBtns[mode]
        self.PlayMode = mode

        CloseBtn.setProperty("active", False)
        CloseBtn.setText("")
        CloseBtn.style().unpolish(CloseBtn)
        CloseBtn.style().polish(CloseBtn)

        OpenBtn.setProperty("active", True)
        OpenBtn.setText("    " + mode)
        OpenBtn.style().unpolish(OpenBtn)
        OpenBtn.style().polish(OpenBtn)

        self.AnimateModeBtn(CloseBtn, OpenBtn)

    
    def AnimateModeBtn(self, ClosingBtn, OpeningBtn, duration=150):
        self.AnimGroup = QParallelAnimationGroup()

        OpenMin = QPropertyAnimation(OpeningBtn, b"minimumWidth")
        OpenMax = QPropertyAnimation(OpeningBtn, b"maximumWidth")
        CloseMin = QPropertyAnimation(ClosingBtn, b"minimumWidth")
        CloseMax = QPropertyAnimation(ClosingBtn, b"maximumWidth")

        for anim in [OpenMin, OpenMax, CloseMin, CloseMax]:
            anim.setDuration(duration)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        for anim in [OpenMin, OpenMax]:
            anim.setStartValue(OpeningBtn.height())
            anim.setEndValue(OpeningBtn.sizeHint().width())
        
        for anim in [CloseMin, CloseMax]:
            anim.setStartValue(ClosingBtn.width())
            anim.setEndValue(ClosingBtn.height())

        self.AnimGroup.addAnimation(OpenMin)
        self.AnimGroup.addAnimation(OpenMax)
        self.AnimGroup.addAnimation(CloseMin)
        self.AnimGroup.addAnimation(CloseMax)

        self.AnimGroup.start()
    
    def AddSongBtn(self, title, ind):
        artist = bk.GetSongDetail(title, 'Artist')
        if not artist: artist = "Unknown Artist"
        genre = bk.GetSongDetail(title, 'Genre')
        status = bk.GetSongDetail(title, 'Status')

        btn = QPushButton()
        btn.setObjectName("SongBtn")
        btn.clicked.connect(lambda: self.PlaySong(title))
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(10, 0, 0, 0)
        
        img = QLabel()
        img.setObjectName("Image")
        pixmap = QPixmap(str(bk.ImageDir / (title+'.jpg')) if (bk.ImageDir / (title+'.jpg')).is_file() else bk.ResourcePath('Static/Note.png'))
        img.pix = pixmap
        img.setPixmap(pixmap)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img, alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        DetailsCard = QFrame()
        DetailsCard.setObjectName("DetailsCard")
        DetailsLayout = QVBoxLayout(DetailsCard)
        DetailsLayout.setContentsMargins(10, 10, 10, 10)
        DetailsLayout.addStretch(1)

        TitleLabel = QLabel(title)
        TitleLabel.setObjectName("Title")
        TitleLabel.FullText = title
        TitleLabel.installEventFilter(self)
        DetailsLayout.addWidget(TitleLabel)
        DetailsLayout.addStretch(1)

        ArtistLabel = QLabel(artist)
        ArtistLabel.setObjectName("Artist")
        ArtistLabel.FullText = artist
        ArtistLabel.installEventFilter(self)
        DetailsLayout.addWidget(ArtistLabel)
        DetailsLayout.addStretch(1)
        
        layout.addWidget(DetailsCard)
        layout.addStretch()

        # Download status
        indicator = QFrame()
        indicator.setObjectName("Status")
        if status == "Downloaded":
            color = "hsl(120, 50%, 40%)"
        else:
            color = "hsl(0, 50%, 40%)"
        indicator.setStyleSheet(f"background-color: {color};")

        layout.addWidget(indicator)

        if title in self.SongButtons.keys():
            self.SongButtons[title].setParent(None)
        self.SongButtons[title] = btn
        self.SidebarLayout.insertWidget(ind, btn, alignment = Qt.AlignmentFlag.AlignTop)
    
    def RefreshList(self):
        titles = [row['Title'] for index, row in bk.SongDF.iterrows()]
        for i, title in enumerate(titles):
            self.AddSongBtn(title, i)

        extras = [title for title, btn in self.SongButtons.items() if title not in titles]
        for title in extras:
            self.SongButtons[title].setParent(None)
            del self.SongButtons[title]
        
        if self.CurrentSong not in self.SongButtons.keys():
            self.CurrentSong = None
            self.RefreshSelection()
        elif self.AudioPlayer.source().isEmpty() and bk.GetSongDetail(self.CurrentSong, 'Status') == "Downloaded":
            self.PlaySong(self.CurrentSong)
            self.AudioPlayer.pause()
        
        self.resizeEvent(None)
    
    def PlaySong(self, title):
        self.AudioPlayer.stop()

        Path = None
        for ext in ['.mp3', '.flac', '.m4a']:
            path = bk.MusicDir / f"{title}{ext}"
            if path.exists():
                Path = path
                break

        if self.CurrentSong:
            OldBtn = self.SongButtons[self.CurrentSong]
            OldBtn.setProperty("active", False)
            OldBtn.style().unpolish(OldBtn)
            OldBtn.style().polish(OldBtn)
        NewBtn = self.SongButtons[title]
        NewBtn.setProperty("active", True)
        NewBtn.style().unpolish(NewBtn)
        NewBtn.style().polish(NewBtn)

        self.CurrentSong = title
        self.RefreshSelection()

        self.SongTitle.setText(title)
        artist = bk.GetSongDetail(title, 'Artist')
        if not artist: artist = "Unknown Artist"
        self.SongArtist.setText(artist)

        pixmap = QPixmap(str(bk.ImageDir / (title+'.jpg')) if (bk.ImageDir / (title+'.jpg')).is_file() else bk.ResourcePath('Static/Note.png'))
        self.SongImage.pix = pixmap
        scaled = pixmap.scaled(
            self.SongImage.width(), self.SongImage.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.SongImage.setPixmap(scaled)
        
        if Path:
            self.AudioPlayer.setSource(QUrl.fromLocalFile(str(Path)))
            self.AudioPlayer.play()
        else:
            self.AudioPlayer.setSource(QUrl())
            QMessageBox.warning(self, "Song not downloaded", f"Please download '{title}' first before playing!")
    
    def RefreshSelection(self):
        self.SelectionUpdate.emit([self.CurrentSong] if self.CurrentSong else [])
    
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.Resize and isinstance(source, QLabel):
            text = source.FullText
            metrics = QFontMetrics(source.font())
            elided = metrics.elidedText(text, Qt.TextElideMode.ElideRight, source.width())
            source.setText(elided)
                
        return super().eventFilter(source, event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)

        ButtonWidth = int((self.Sidebar.width() - 10) * 0.97)
        ButtonHeight = int(ButtonWidth * 0.3)
        SidebarSpacing = int(ButtonHeight * 0.1)
        self.SidebarLayout.setSpacing(SidebarSpacing)

        for btn in self.SongButtons.values():
            btn.setFixedSize(ButtonWidth, ButtonHeight)
        
        ImgSiz = int(ButtonHeight * 0.8)
        IndicatorWidth = int(ButtonWidth * 0.07)
        for title, btn in self.SongButtons.items():
            label = btn.findChild(QLabel)
            scaled = label.pix.scaled(
                ImgSiz, ImgSiz, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled)
            label.setFixedSize(ImgSiz, ImgSiz)

            indicator = btn.findChild(QFrame, "Status")
            indicator.setFixedSize(IndicatorWidth, ButtonHeight)
        
        CoverWidth = int(self.PlayWin.width() * 0.5)
        CoverHeight = int(self.PlayWin.height() * 0.5)
        CoverSize = min(CoverWidth, CoverHeight)

        scaled = self.SongImage.pix.scaled(
            CoverSize, CoverSize, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.SongImage.setPixmap(scaled)
        self.SongImage.setFixedSize(CoverSize, CoverSize)

        ModeBtnSize = int(CoverSize * 0.17)
        IconSiz = int(ModeBtnSize * 0.5)
        for btn in self.ModeBtns.values():
            btn.setStyleSheet(f"border-radius: {int(ModeBtnSize/2)}px; font-size: {int(ModeBtnSize*0.4)}px; ")
            btn.setIconSize(QSize(IconSiz, IconSiz))
            if btn.property("active"):
                btn.setFixedSize(btn.sizeHint().width(), ModeBtnSize)
            else:
                btn.setFixedSize(ModeBtnSize, ModeBtnSize)

        NavSiz = int(self.PlayWin.width() * 0.05)
        PlaySiz = int(NavSiz * 1.5)
        self.PlayBtn.setStyleSheet(f"border-radius: {int(PlaySiz/2)}px;")
        self.PrevBtn.setStyleSheet(f"border-radius: {int(NavSiz/2)}px;")
        self.NextBtn.setStyleSheet(f"border-radius: {int(NavSiz/2)}px;")
        self.PlayBtn.setIconSize(QSize(int(PlaySiz*0.4), int(PlaySiz*0.4)))
        self.PrevBtn.setIconSize(QSize(int(NavSiz*0.4), int(NavSiz*0.4)))
        self.NextBtn.setIconSize(QSize(int(NavSiz*0.4), int(NavSiz*0.4)))
        self.PlayBtn.setFixedSize(PlaySiz, PlaySiz)
        self.PrevBtn.setFixedSize(NavSiz, NavSiz)
        self.NextBtn.setFixedSize(NavSiz, NavSiz)

        # Scrub Slider
        GrooveHeight = int(self.PlayWin.height() * 0.02)
        GrooveWidth = int(self.PlayWin.width() * 0.5)
        HandleSize = int(GrooveHeight * 1.7)
        margin = -(HandleSize - GrooveHeight) // 2 # Magic formula to vertically center handle, idk how it works

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
        self.SeekSlider.setFixedSize(GrooveWidth, HandleSize+1)

        # Volume slider
        HandleSize = int(CoverSize * 0.05)
        GrooveWidth = int(CoverSize * 0.02)
        GrooveHeight = int(CoverSize * 0.9)
        margin = -(HandleSize - GrooveWidth) // 2

        self.VolSlider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                height: {GrooveHeight}px;
                width: {GrooveWidth}px;
                border-radius: {GrooveWidth // 2}px;
            }}
            QSlider::add-page:vertical {{
                border-radius: {GrooveWidth // 2}px;
            }}
            QSlider::handle:vertical {{
                width: {HandleSize}px;
                height: {HandleSize}px;
                margin: 0 {margin}px;
                border-radius: {HandleSize // 2}px;
            }}
        """)
        self.VolSlider.setFixedSize(HandleSize + 1, GrooveHeight + 1)