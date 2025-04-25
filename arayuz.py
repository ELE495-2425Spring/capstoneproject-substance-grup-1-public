#!/usr/bin/env python3
import socket
import threading
import json
import tkinter as tk
from tkinter import scrolledtext
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

SERVER_IP = "10.5.64.137"
PORT      = 5000

class ClientUI:
    def __init__(self, master):
        self.master = master
        master.title("Robot Control UI")
        self.master.configure(bg="#f0f0f0")
        self.master.geometry("800x750")

        self.status_label    = tk.Label(master, text="Status: Idle", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
        self.direction_label = tk.Label(master, text="Direction: 0°", font=("Helvetica", 14), bg="#f0f0f0")
        self.spectrum_label  = tk.Label(master, text="Spectrum: 0 dBm", font=("Helvetica", 14), bg="#f0f0f0")
        self.status_label.pack(pady=10)
        self.direction_label.pack(pady=5)
        self.spectrum_label.pack(pady=5)

        self.fig = Figure(figsize=(7, 4), dpi=100)
        self.ax  = self.fig.add_subplot(111)
        self.ax.set_title("Real-Time Spectrum (433–435 MHz)")
        self.ax.set_xlabel("Frequency (MHz)")
        self.ax.set_ylabel("Magnitude (dBm)")
        self.ax.set_xlim(432, 434)
        self.ax.set_ylim(-100, 0)
        self.line, = self.ax.plot([], [], lw=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master)
        self.canvas.get_tk_widget().pack(pady=10)
        self.canvas.draw()

        self.start_button = tk.Button(master, text="Start Operation", command=self.send_start_command, width=25, height=2, bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(master, text="Stop Operation", command=self.send_stop_command, width=25, height=2, bg="#f44336", fg="white", font=("Helvetica", 12, "bold"))
        self.stop_button.pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(master, width=90, height=15, font=("Courier", 10))
        self.log_text.pack(padx=10, pady=10)
        self.log_text.config(state="disabled")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_IP, PORT))
            self.log("Connected to server")
        except Exception as e:
            self.log(f"Connection error: {e}")

        self.buffer = ""
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_start_command(self):
        self.sock.sendall(json.dumps({"command": "start"}).encode() + b"\n")
        self.status_label.config(text="Status: running")
        self.log("Start command sent")

    def send_stop_command(self):
        self.sock.sendall(json.dumps({"command": "stop"}).encode() + b"\n")
        self.log("Stop command sent")

    def receive_messages(self):
        while True:
            chunk = self.sock.recv(4096).decode()
            if not chunk:
                break
            self.buffer += chunk
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                try:
                    msg = json.loads(line.strip())
                    self.master.after(0, lambda m=msg: self.process_message(m))
                except json.JSONDecodeError:
                    self.log("JSON parse error")

    def process_message(self, m):
        t = m.get("type", "")
        if t == "status":
            st = m.get("status", "")
            display_status = "stopped" if st in ["Operation complete", "Manually stopped"] else st
            self.status_label.config(text=f"Status: {display_status}")
            self.log(f"Status: {display_status}")

        elif t == "live_update":
            st = m.get("status", "")
            d = m.get("direction", 0)
            sp = m.get("spectrum", 0)
            fft = m.get("fft", [])

            if st not in ["Operation complete", "Manually stopped"]:
                st = "running"
            self.status_label.config(text=f"Status: {st}")
            self.master.after(5000, lambda: self.direction_label.config(text=f"Direction: {d}°"))
            self.spectrum_label.config(text=f"Spectrum: {sp:.2f} dBm")

            if fft:
                volts = np.array(fft)
                power_mw = (volts ** 2) / 50 * 1000
                mags_dbm = 10 * np.log10(power_mw + 1e-12)
                freqs = np.linspace(432, 434, mags_dbm.size)

                #  Spektrum + Referans çizgisi (kırmızı)
                self.ax.clear()
                self.ax.set_title("Real-Time Spectrum (433–435 MHz)")
                self.ax.set_xlabel("Frequency (MHz)")
                self.ax.set_ylabel("Magnitude (dBm)")
                self.ax.set_xlim(432, 434)
                self.ax.set_ylim(mags_dbm.min(), mags_dbm.max())

                self.ax.plot(freqs, mags_dbm, lw=1, label="FFT")
                self.ax.axhline(y=sp, color="red", linestyle="--", linewidth=1, label=f"Robot: {sp:.1f} dBm")
                self.ax.legend()
                self.canvas.draw_idle()

        elif t == "operation":
            d = m.get("direction", 0)
            sp = m.get("spectrum", 0)
            self.direction_label.config(text=f"Direction: {d}°")
            self.spectrum_label.config(text=f"Spectrum: {sp:.2f} dBm")
            self.log(f"Operation update: Direction {d}°, Spectrum {sp:.2f} dBm")

    def log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")


def main():
    root = tk.Tk()
    app = ClientUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
