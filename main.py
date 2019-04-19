from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QMainWindow, QGroupBox, QLineEdit, QFileDialog, QListWidget, QSizePolicy, QAbstractItemView, QProgressBar
from PyQt5.QtCore import Qt
import tothebeat
import sys

# TODO: Allow user to either select a bunch of video files (store this in a list) or just select a directory and add all the video files
#       User can also reorganize the video files to their liking

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.title = 'To The Beat'
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()
        
        # Video chooser
        self.vid_chooser_list = QListWidget()
        self.vid_chooser_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.vid_chooser_model = self.vid_chooser_list.model()
        self.vid_chooser_model.rowsInserted.connect(self.changeVidChooserBtnState)
        self.vid_chooser_model.rowsRemoved.connect(self.changeVidChooserBtnState)

        self.vid_add_btn = QPushButton('Add')
        self.vid_add_btn.clicked.connect(self.addVideos)
        self.vid_rm_btn = QPushButton('Remove')
        self.vid_rm_btn.clicked.connect(self.removeVideos)
        self.vid_up_btn = QPushButton('Up')
        self.vid_up_btn.clicked.connect(self.moveVideosUp)
        self.vid_down_btn = QPushButton('Down')
        self.vid_down_btn.clicked.connect(self.moveVideosDown)

        self.vid_chooser_btn_layout = QVBoxLayout()
        self.vid_chooser_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.vid_chooser_btn_layout.setSpacing(0)
        self.vid_chooser_btn_layout.addWidget(self.vid_add_btn)
        self.vid_chooser_btn_layout.addWidget(self.vid_rm_btn)
        self.vid_chooser_btn_layout.addWidget(self.vid_up_btn)
        self.vid_chooser_btn_layout.addWidget(self.vid_down_btn)
        self.vid_chooser_btn_layout.addStretch(0)

        self.vid_chooser_layout = QHBoxLayout()
        self.vid_chooser_layout.addWidget(self.vid_chooser_list)
        self.vid_chooser_layout.addLayout(self.vid_chooser_btn_layout)

        self.vid_chooser_group_box = QGroupBox('Video files')
        self.vid_chooser_group_box.setLayout(self.vid_chooser_layout)

        # Music chooser
        self.music_file_textbox = QLineEdit()
        self.music_file_textbox.textChanged.connect(self.musicFileTextboxChanged)
        self.music_file_browse_btn = QPushButton('Browse')
        self.music_file_browse_btn.clicked.connect(self.browseMusicFile)

        self.music_chooser_layout = QHBoxLayout()
        self.music_chooser_layout.addWidget(self.music_file_textbox)
        self.music_chooser_layout.addWidget(self.music_file_browse_btn)

        self.music_chooser_group_box = QGroupBox('Music')
        self.music_chooser_group_box.setLayout(self.music_chooser_layout)

        # Start button (create video?)
        # Maybe make button bigger vertically so it's more obvious?
        self.start_btn = QPushButton('Start')
        self.start_btn.clicked.connect(self.start)
        self.can_start = {'vid_chooser_list': False, 'music_file_textbox': False}
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        self.changeVidChooserBtnState()

        # Add everything to the main layout
        self.layout.addWidget(self.vid_chooser_group_box)
        self.layout.addWidget(self.music_chooser_group_box)
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.progress_bar)

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.show()

    def checkCanStart(self):
        if self.can_start['vid_chooser_list'] and self.can_start['music_file_textbox']:
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(False)
    
    def changeVidChooserBtnState(self):
        if len(self.vid_chooser_list) > 0:
            self.vid_rm_btn.setEnabled(True)
            self.vid_up_btn.setEnabled(True)
            self.vid_down_btn.setEnabled(True)

            self.can_start['vid_chooser_list'] = True
        else:
            self.vid_rm_btn.setEnabled(False)
            self.vid_up_btn.setEnabled(False)
            self.vid_down_btn.setEnabled(False)

            self.can_start['vid_chooser_list'] = False
        
        self.checkCanStart()

    def musicFileTextboxChanged(self):
        if len(self.music_file_textbox.text()) > 0:
            self.can_start['music_file_textbox'] = True
        else:
            self.can_start['music_file_textbox'] = False
        
        self.checkCanStart()

    def addVideos(self):
        file_names = QFileDialog.getOpenFileNames(self, 'Select video files', '', 'Video files (*.mp4 *.avi *.mov *.flv *.wmv)')[0]
        self.vid_chooser_list.addItems(file_names)

    def removeVideos(self):
        for selected_widget in self.vid_chooser_list.selectedItems():
            self.vid_chooser_list.takeItem(self.vid_chooser_list.row(selected_widget))

    def moveVideosUp(self):
        selected_rows = [self.vid_chooser_list.row(selected_widget) for selected_widget in self.vid_chooser_list.selectedItems()]
        selected_rows.sort()

        if 0 not in selected_rows:
            for row in selected_rows:
                widget = self.vid_chooser_list.takeItem(row)
                self.vid_chooser_list.insertItem(row-1, widget)
                widget.setSelected(True)

    def moveVideosDown(self):
        selected_rows = [self.vid_chooser_list.row(selected_widget) for selected_widget in self.vid_chooser_list.selectedItems()]
        selected_rows.sort(reverse=True)
        
        if len(self.vid_chooser_list)-1 not in selected_rows:
            for row in selected_rows:
                widget = self.vid_chooser_list.takeItem(row)
                self.vid_chooser_list.insertItem(row+1, widget)
                widget.setSelected(True)

    def browseMusicFile(self):
        file_name = QFileDialog.getOpenFileName(self, 'Select a music file', '', 'Audio files (*.3gp *.aa *.aac *.aax *.act *.aiff *.amr *.ape *.au *.awb *.dct *.dss *.dvf *.flac *.gsm *.iklax *.ivs *.m4a *.m4b *.m4p *.mmf *.mp3 *.mpc *.msv *.nmf *.nsf *.ogg *.oga *.mogg *.opus *.ra *.rm *.raw *.sln *.tt *.vox *.wav *.webm *.wma *.wv)')[0]
        self.music_file_textbox.setText(file_name)

    def start(self):
        output_file_name = QFileDialog.getSaveFileName(self, 'Save video as...', '', 'Video files (*.mp4 *.avi *.mov *.flv *.wmv)')[0]
        vids = []
        for i in range(len(self.vid_chooser_list)):
            vids.append(self.vid_chooser_list.item(i).text())
 
        tothebeat.createVideo(
            self.music_file_textbox.text(),
            output_file_name,
            1920,
            1080,
            vids=vids
        )

if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()

    if (app):
        app.exec_()