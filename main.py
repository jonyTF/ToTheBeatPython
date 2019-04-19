from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QMainWindow, QGroupBox, QLineEdit, QFileDialog, QListWidget, QSizePolicy, QAbstractItemView, QProgressBar, QMessageBox, QListWidgetItem, QAbstractItemView, QTabWidget, QComboBox, QSpinBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
import tothebeat
import sys
import subprocess
import uuid

# TODO: Allow user to edit advanced options 
# TODO: Create a little console thing to show progress of rendering
# TODO: Catching errors --> file does not exist, ffmpeg error, etc.

class RenderVideoThread(QThread):
    setProgress = pyqtSignal(int)

    def __init__(self,
        audio_path,
        output_file_name,
        resolution_w,
        resolution_h,
        sep=5,
        fps=30,
        split_every_n_beat=4,
        preset='ultrafast',
        csv_path='',
        vids=[],
        vid_directory=''
    ):
        QThread.__init__(self)
        self.audio_path = audio_path
        self.output_file_name = output_file_name
        self.resolution_w = resolution_w
        self.resolution_h = resolution_h
        self.sep = sep
        self.fps = fps
        self.split_every_n_beat = split_every_n_beat
        self.preset = preset
        self.csv_path = csv_path
        self.vids = vids
        self.vid_directory = vid_directory

    def __del__(self):
        self.wait()

    def run(self):
        self.setProgress.emit(5)
        data = tothebeat.getRenderVideoCmd(
            self.audio_path,
            self.output_file_name,
            self.resolution_w,
            self.resolution_h,
            self.sep,
            self.fps,
            self.split_every_n_beat,
            self.preset,
            self.csv_path,
            self.vids,
            self.vid_directory
        )
        self.setProgress.emit(10)
        
        # Run cmd, track progress
        cmd = data[0]
        tot_frames = data[1]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        line = ''
        end_char = '\n'
        for c in iter(lambda: process.stdout.read(1), b''):
            c = c.decode('utf-8')
            if c != end_char:
                line += c
                if 'frame=' in line:
                    end_char = 'x'
            else:
                if '[fatal]' in line:
                    raise Exception('An error occurred: ' + line)
                elif 'frame=' in line:
                    cur_frame = int(line[line.index('frame=')+6:line.index('fps')].strip())
                    progress = cur_frame / tot_frames
                    self.setProgress.emit(10 + int(progress*90))
                line = ''
        
        print('Render complete.')


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.title = 'To The Beat'
        self.can_start = {'vid_chooser_list': False, 'music_file_textbox': False, 'output_file_textbox': False, 'isRendering': False}
        self.vids = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)

        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.inputTab = QWidget()
        self.inputLayout = QVBoxLayout()
        self.inputTab.setLayout(self.inputLayout)
        self.optionsTab = QWidget()
        self.optionsGrid = QGridLayout()
        self.optionsLayout = QVBoxLayout()
        self.optionsTab.setLayout(self.optionsLayout)

        self.tabs.addTab(self.inputTab, 'Input')
        self.tabs.addTab(self.optionsTab, 'Options')
        
        # Video chooser
        self.vid_chooser_list = QListWidget()
        self.vid_chooser_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.vid_chooser_list.setIconSize(QSize(320/3, 240/3))
        self.vid_chooser_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
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

        # Output vid chooser
        self.output_file_textbox = QLineEdit()
        self.output_file_textbox.textChanged.connect(self.outputFileTextboxChanged)
        self.output_file_browse_btn = QPushButton('Browse')
        self.output_file_browse_btn.clicked.connect(self.browseOutputFile)

        self.output_chooser_layout = QHBoxLayout()
        self.output_chooser_layout.addWidget(self.output_file_textbox)
        self.output_chooser_layout.addWidget(self.output_file_browse_btn)

        self.output_chooser_group_box = QGroupBox('Output')
        self.output_chooser_group_box.setLayout(self.output_chooser_layout)

        # OPTIONS
        # TODO: Add hint text (hover text?)
        self.preset_textbox = QComboBox()
        self.preset_textbox.addItems([
            'ultrafast', 
            'superfast',
            'veryfast',
            'faster',
            'fast',
            'medium',
            'slow',
            'slower',
            'veryslow'
        ])
        self.preset_textbox.setCurrentIndex(0) #ultrafast

        self.split_beat_spinbox = QSpinBox()
        self.split_beat_spinbox.setMinimum(1)
        self.split_beat_spinbox.setValue(4)
        self.split_beat_spinbox.setPrefix('Cut every ')
        self.split_beat_spinbox.setSuffix(' beats')


        self.optionsLayout.addWidget(QLabel('Hover over an option to learn more about it'))
        
        self.optionsGrid.addWidget(QLabel('Beat to cut at'), 0, 0)
        self.optionsGrid.addWidget(self.split_beat_spinbox, 0, 1)
        self.optionsGrid.addWidget(QLabel('FFmpeg render preset'), 1, 0)
        self.optionsGrid.addWidget(self.preset_textbox, 1, 1)
        
        self.optionsLayout.addLayout(self.optionsGrid)
        self.optionsLayout.addStretch()

        # Start button (create video?)
        # Maybe make button bigger vertically so it's more obvious?
        self.start_btn = QPushButton('Start')
        self.start_btn.clicked.connect(self.start)
        self.changeVidChooserBtnState()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        # Add everything to the main layout
        self.inputLayout.addWidget(self.vid_chooser_group_box)
        self.inputLayout.addWidget(self.music_chooser_group_box)

        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.output_chooser_group_box)
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.progress_bar)

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.show()

    def checkCanStart(self):
        if self.can_start['vid_chooser_list'] and self.can_start['music_file_textbox'] and self.can_start['output_file_textbox'] and not self.can_start['isRendering']:
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

    def outputFileTextboxChanged(self):
        if len(self.output_file_textbox.text()) > 0:
            self.can_start['output_file_textbox'] = True
        else:
            self.can_start['output_file_textbox'] = False
        
        self.checkCanStart()

    def addVideos(self):
        file_names = QFileDialog.getOpenFileNames(self, 'Select video files', '', 'Video files (*.mp4 *.avi *.mov *.flv *.wmv)')[0]

        for i, name in enumerate(file_names):
            thumbnail_name = f'./tmp/{str(uuid.uuid4())}.png'
            tothebeat.createThumbnail(name, thumbnail_name)

            short_name = name.split('/')[-1]
            self.vid_chooser_list.addItem(QListWidgetItem(QIcon(thumbnail_name), short_name))
            self.vids.append(name)

    def removeVideos(self):
        for selected_widget in self.vid_chooser_list.selectedItems():
            index = self.vid_chooser_list.row(selected_widget)
            self.vid_chooser_list.takeItem(index)
            self.vids.pop(index)

    def moveVideosUp(self):
        selected_rows = [self.vid_chooser_list.row(selected_widget) for selected_widget in self.vid_chooser_list.selectedItems()]
        selected_rows.sort()

        if 0 not in selected_rows:
            for row in selected_rows:
                widget = self.vid_chooser_list.takeItem(row)
                self.vid_chooser_list.insertItem(row-1, widget)
                widget.setSelected(True)
                
                self.vids.insert(row-1, self.vids.pop(row))

    def moveVideosDown(self):
        selected_rows = [self.vid_chooser_list.row(selected_widget) for selected_widget in self.vid_chooser_list.selectedItems()]
        selected_rows.sort(reverse=True)
        
        if len(self.vid_chooser_list)-1 not in selected_rows:
            for row in selected_rows:
                widget = self.vid_chooser_list.takeItem(row)
                self.vid_chooser_list.insertItem(row+1, widget)
                widget.setSelected(True)

                self.vids.insert(row+1, self.vids.pop(row))

    def browseMusicFile(self):
        file_name = QFileDialog.getOpenFileName(self, 'Select a music file', '', 'Audio files (*.3gp *.aa *.aac *.aax *.act *.aiff *.amr *.ape *.au *.awb *.dct *.dss *.dvf *.flac *.gsm *.iklax *.ivs *.m4a *.m4b *.m4p *.mmf *.mp3 *.mpc *.msv *.nmf *.nsf *.ogg *.oga *.mogg *.opus *.ra *.rm *.raw *.sln *.tt *.vox *.wav *.webm *.wma *.wv)')[0]
        self.music_file_textbox.setText(file_name)

    def browseOutputFile(self):
        file_name = QFileDialog.getSaveFileName(self, 'Save output video as...', '', 'Video files (*.mp4 *.avi *.mov *.flv *.wmv)')[0]
        self.output_file_textbox.setText(file_name)

    def start(self):
        self.output_file_name = self.output_file_textbox.text()
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        self.render_thread = RenderVideoThread(
            self.music_file_textbox.text(),
            self.output_file_name,
            1920,
            1080,
            vids=self.vids
        )
        self.render_thread.setProgress.connect(self.setProgress)
        self.render_thread.finished.connect(self.done)
        self.render_thread.start()

        # self.stop_btn.clicked.connect(self.render_thread.terminate) #IF WANT TO STOP THREAD
        self.can_start['isRendering'] = True
        self.checkCanStart()

    def setProgress(self, progress):
        self.progress_bar.setValue(progress)

    def done(self):
        self.progress_bar.setValue(100)
        QMessageBox.information(self, 'Render complete!', f'Video has been successfully rendered to {self.output_file_name}!')
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        self.can_start['isRendering'] = False
        self.checkCanStart()

if __name__ == '__main__':
    app = QApplication([])

    window = MainWindow()

    if (app):
        sys.exit(app.exec_())