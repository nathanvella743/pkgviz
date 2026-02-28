import sys
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import QSize, QTimer, Qt, QProcess
from thefuzz import fuzz

class PackageWidget(QFrame):
    def __init__(self, package_name, status, parent=None):
        super().__init__(parent)
        self.package_name = package_name
        self.setFixedHeight(60)
        self.setStyleSheet("QFrame { border: 1px solid #ccc; background: white; }")
        
        layout = QHBoxLayout(self)
        self.name_label = QLabel(package_name)
        self.status_btn = QPushButton(status)
        self.status_btn.setFixedWidth(100)
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.status_btn)
        
        if status == "Update":
            self.status_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            self.status_btn.clicked.connect(self.handle_update)
        else:
            self.status_btn.setEnabled(False)

    def handle_update(self):
        self.status_btn.setText("Updating...")
        self.status_btn.setEnabled(False)
        
        # Use QProcess to keep the UI alive
        self.process = QProcess()
        self.process.finished.connect(lambda: self.status_btn.setText("Done"))
        self.process.start("pkexec", ["pacman", "-S", "--noconfirm", self.package_name])

class PackageUpdateManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arch Package Manager")
        self.resize(500, 600)

        # Data initialization
        self.package_data = self.get_packages()
        
        # UI Setup
        main_layout = QVBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.textChanged.connect(self.trigger_search)
        
        self.list_widget = QListWidget()
        
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.list_widget)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Search debouncing
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.populate_list()

    def get_packages(self):
        try:

            all_pkgs = subprocess.check_output(["pacman", "-Q"], text=True).splitlines()

            outdated = subprocess.run(["pacman", "-Qu"], capture_output=True, text=True).stdout.splitlines()
            outdated_names = {line.split()[0] for line in outdated}

            data = []
            for line in all_pkgs:
                name = line.split()[0]
                status = "Update" if name in outdated_names else "Up to date"
                data.append({'name': name, 'status': status})
            return data
        except Exception as e:
            print(f"Error fetching packages: {e}")
            return []

    def populate_list(self, items=None):

        self.list_widget.clear()
        display_items = items if items is not None else self.package_data
        
        for item in display_items[:100]: 
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(QSize(0, 65))
            
            widget = PackageWidget(item['name'], item['status'])
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, widget)

    def trigger_search(self):
        self.search_timer.start(200)

    def perform_search(self):
        query = self.search_input.text().lower()
        if not query:
            self.populate_list(self.package_data)
            return

        scored = []
        for p in self.package_data:
            score = fuzz.partial_ratio(query, p['name'].lower())
            if score > 50: # Threshold to keep list clean
                scored.append({**p, 'score': score})
        
        scored.sort(key=lambda x: x['score'], reverse=True)
        self.populate_list(scored)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PackageUpdateManager()
    window.show()
    sys.exit(app.exec())