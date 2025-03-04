import sys
import socket
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel
)
from PyQt5.QtCore import pyqtSignal, QObject, Qt

# Raspberry Pi'nin IP adresi ve main_server.py'yi dinleyen port
RPI_HOST = "10.5.64.121"  # Buraya Pi'nin gerçek IP'sini yazın
RPI_PORT = 5000

class WorkerSignals(QObject):
    finished = pyqtSignal(str)  # Sunucudan gelen son mesaj

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC PyQt Client - Remote main()")
        self.setGeometry(200, 200, 300, 150)

        # Ana widget + Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Buton
        self.btn_run = QPushButton("Raspberry'de main() Çalıştır")
        self.btn_run.clicked.connect(self.run_main_on_pi)
        layout.addWidget(self.btn_run)

        # Durum Label
        self.lbl_status = QLabel("Durum: Beklemede")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Worker sinyalleri
        self.signals = WorkerSignals()
        self.signals.finished.connect(self.on_main_finished)

    def run_main_on_pi(self):
        """Butona basılınca separate bir thread'de Raspberry Pi'ye bağlanıp START_MAIN komutu gönderir."""
        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Durum: main() başlatıldı, bekleniyor...")

        thread = threading.Thread(target=self.socket_task, daemon=True)
        thread.start()

    def socket_task(self):
        """Bu fonksiyon ayrı bir thread'de çalışır. Pi'ye bağlanıp START_MAIN yollayıp DONE veya hata bekler."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((RPI_HOST, RPI_PORT))
                # START_MAIN komutu gönder
                s.sendall(b"START_MAIN")

                # Yanıt olarak DONE veya ERROR gelebilir
                data = s.recv(1024)
                if not data:
                    # Sunucu kapattıysa
                    msg = "Sunucu yanıt vermedi (boş veri)."
                else:
                    msg = data.decode("utf-8").strip()
        except Exception as e:
            msg = f"HATA: {e}"

        # En son sinyalle ana thread'e bildiriyoruz
        self.signals.finished.emit(msg)

    def on_main_finished(self, message):
        """Sunucudan gelen son mesaj (DONE, ERROR vs.) burada işlenir."""
        if message == "DONE":
            self.lbl_status.setText("Durum: Çalışma bitti!")
        elif message.startswith("ERROR"):
            self.lbl_status.setText(f"Durum: Hata alındı -> {message}")
        elif message == "INVALID_COMMAND":
            self.lbl_status.setText("Durum: Geçersiz Komut Gönderildi!")
        else:
            self.lbl_status.setText(f"Sunucu mesajı: {message}")

        self.btn_run.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
