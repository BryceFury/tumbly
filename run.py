import os
import sys
import queue

from tumbly.confighandler import put_config
from tumbly.database import create_check_database
from tumbly.scrape import scrape_tumblr
from tumbly.download import download_images

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QThread
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGridLayout, QInputDialog, QLabel
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QPushButton
from PyQt5.QtWidgets import QSizePolicy, QSpinBox, QTextEdit, QWidget

# Globals
user_username = None
user_number = None
user_offset = None


class WriteStream(object):

    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    # Everyone loves a no-op
    def flush(self):
        pass


class MyReceiver(QObject):
    mysignal = pyqtSignal(str)

    def __init__(self, queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = queue

    @pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)


class RunMain(QObject):

    @pyqtSlot()
    def run(self):

        # Get globals
        global user_username
        global user_number
        global user_offset

        # Init variables
        username = user_username
        url_to_scrape = ''
        database_name = ''
        number = user_number
        offset = user_offset

        # Get user input
        # Create URL
        url_to_scrape = 'http://{0}.tumblr.com'.format(username)
        # Create database name
        database_name = '{0}.db'.format(username)
        # Check if directory exists, create if not
        script_directory = os.path.dirname(os.path.abspath(__file__))
        downloaded_image_directory = os.path.join(script_directory,
                                                  'images',
                                                  '{0}_saved_images'
                                                  .format(username))

        if not os.path.exists(downloaded_image_directory):
            os.makedirs(downloaded_image_directory)

        create_check_database(database_name)

        scrape_tumblr(username,
                      url_to_scrape,
                      database_name,
                      number,
                      offset,
                      limit=20,
                      url_type='blog')

        download_images(username,
                        database_name,
                        downloaded_image_directory,
                        number)


class Tumbly(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        # Create titles
        self.title_tagline = QLabel('Welcome to')
        self.title_tagline.setSizePolicy(QSizePolicy.Preferred,
                                         QSizePolicy.Expanding)
        self.title_tagline.setStyleSheet('font: 12px;'
                                         ' color:#000000;'
                                         )

        self.title_text = QLabel('tumbly.')
        self.title_text.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Expanding)
        self.title_text.setStyleSheet('font: 24px;'
                                      ' color:#000000;'
                                      )

        # Create Labels
        self.number_label = QLabel('Number of images to scrape:')
        self.offset_label = QLabel('Post offest (start point):')

        # Create output box
        self.status_out = QTextEdit()
        self.status_out.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Expanding)

        # Create input boxes
        self.username_box = QLineEdit(self)
        self.username_box.setText('Enter username to scrape')
        self.username_box.setSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding)
        self.username_box.textChanged[str].connect(self.text_changed)

        # Create number boxes
        self.number_of_images = QSpinBox()
        self.number_of_images.setMinimum(1)
        self.number_of_images.setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Expanding)
        self.number_of_images.valueChanged[int].connect(self.number_changed)

        self.post_offset = QSpinBox()
        self.post_offset.setMinimum(20)
        self.post_offset.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Expanding)
        self.post_offset.valueChanged[int].connect(self.offset_changed)

        # Create get images button
        self.get_button = QPushButton('Get images')
        self.get_button.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Expanding)
        self.get_button.setStyleSheet('font: 12px;'
                                      ' color:#000000;'
                                      ' border: 1px solid #000000')

        # Create get images button
        self.get_settings = QPushButton('Set Auth')
        self.get_settings.setSizePolicy(QSizePolicy.Preferred,
                                        QSizePolicy.Expanding)
        self.get_settings.setStyleSheet('font: 12px;'
                                        ' color:#000000;'
                                        ' border: 1px solid #000000')

        # Create layout, add widgets
        self.grid = QGridLayout()
        self.grid.addWidget(self.title_tagline, 1, 0, 1, 2)
        self.grid.addWidget(self.title_text, 2, 0, 2, 2)
        self.grid.addWidget(self.username_box, 5, 0, 3, 1)
        self.grid.addWidget(self.get_button, 8, 0, 4, 2)
        self.grid.addWidget(self.number_label, 12, 0)
        self.grid.addWidget(self.offset_label, 12, 1)
        self.grid.addWidget(self.number_of_images, 13, 0, 2, 1)
        self.grid.addWidget(self.post_offset, 13, 1, 2, 1)
        self.grid.addWidget(self.status_out, 15, 0, 2, 2)
        self.grid.addWidget(self.get_settings, 17, 0, 4, 2)

        # Set layout
        self.setLayout(self.grid)

        # Get values
        self.number = self.number_of_images.value()
        self.offset = self.post_offset.value()

        # Connect get images button to get_images function
        self.get_button.clicked.connect(self.start_thread)
        # Connect get settings button to add_auth function
        self.get_settings.clicked.connect(self.add_auth)

        # Set window
        self.setFixedSize(500, 250)
        self.setWindowTitle('tumbly')
        self.setWindowIcon(QIcon(''))
        self.setStyleSheet('background: #FFFFFF')

    def text_changed(self, text):
        # Get text changes
        self.username = str(text)
        global user_username
        user_username = self.username

    def number_changed(self, number):
        self.number = int(number)
        global user_number
        user_number = self.number

    def offset_changed(self, number):
        self.offset = int(number)
        global user_offset
        user_offset = self.offset

    def add_auth(self):

        key, ok = QInputDialog.getText(self, 'No config file',
                                             'Enter your app key:')

        if ok:
            app_key = key

        else:
            app_key = ''

        secret, ok = QInputDialog.getText(self, 'No config file',
                                                'Enter your app secret:')
        if ok:
            app_secret = secret

        else:
            app_secret = ''

        if app_key == '' or app_secret == '':
            input_check = QMessageBox.question(self,
                                               'Error',
                                               'You must enter an app key'
                                               ' and an app secret to use'
                                               ' tumbly.',
                                               QMessageBox.Retry | QMessageBox.Cancel)

            if input_check == QMessageBox.Retry:
                self.add_auth()

        put_config('config/tumblyconfig.ini',
                   app_key, app_secret)

    @pyqtSlot(str)
    def append_text(self, text):
        self.status_out.moveCursor(QTextCursor.End)
        self.status_out.insertPlainText(text)

    @pyqtSlot()
    def start_thread(self):
        # Check config file exists, make one if not
        if not os.path.isfile('config/tumblyconfig.ini'):
            self.add_auth()
        else:
            self.thread = QThread()
            self.main_thread = RunMain()
            self.main_thread.moveToThread(self.thread)
            self.thread.started.connect(self.main_thread.run)
            self.thread.start()


queue = queue.Queue()
sys.stdout = WriteStream(queue)


qapp = QApplication(sys.argv)
app = Tumbly()
app.show()


thread = QThread()
my_receiver = MyReceiver(queue)
my_receiver.mysignal.connect(app.append_text)
my_receiver.moveToThread(thread)
thread.started.connect(my_receiver.run)
thread.start()

qapp.exec_()
