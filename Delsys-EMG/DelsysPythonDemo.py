import sys
from PySide6.QtWidgets import QApplication
from UIControls.LandingScreenController import *

import sys

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet('.QLabel { font-size: 12pt;}'
                      '.QPushButton { font-size: 12pt;}'
                      '.QListWidget { font-size: 12pt;}'
                      '.QComboBox{ font-size: 12pt;}'
                      )
    controller = LandingScreenController()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()