import mainprogress
from PyQt5.QtWidgets import QApplication, QMainWindow


class SecondWindowActions(mainprogress.Ui_MainWindow, QMainWindow):

    def __init__(self):
        super(SecondWindowActions, self).__init__()
        self.setupUi(self)
