import tkinter as tk
from tkinter import ttk
import serial
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import platform

# ========== Serial Port Setup ==========
SERIAL_PORT = 'COM6'  # Change this to your Arduino port (e.g., /dev/ttyUSB0)
BAUD_RATE = 9600

# ========== Globals ==========
distance_data = 0
angle_data = 0
warning = False
point_history = []  # Stores all previous points as (theta, r, color)
pause_until = 0     # Timestamp to pause updates

# ========== Sound Function ==========
def beep():
    if platform.system() == "Windows":
        import winsound
        winsound.Beep(1000, 200)  # freq (Hz), duration (ms)
    elif platform.system() == "Darwin":  # macOS
        import os
        os.system('say "beep"')
    else:  # Linux
        print("\a", end="")  # Terminal beep

# ========== Serial Reading Thread ==========
def read_serial():
    global distance_data, angle_data, warning, pause_until
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            while True:
                line = ser.readline().decode().strip()
                if ',' in line:
                    try:
                        angle_str, distance_str = line.split(',')
                        angle_data = float(angle_str)
                        distance_data = float(distance_str)

                        prev_warning = warning
                        warning = distance_data < 10

                        if warning and not prev_warning:
                            beep()
                            pause_until = time.time() + 1.5  # <-- Updated delay here

                    except ValueError:
                        continue
    except serial.SerialException:
        print("Error: Could not open serial port.")

# ========== GUI Setup ==========
class RadarGUI:
    def __init__(self, root):
        self.root = root
        root.title("Ultrasonic Radar Display")

        self.distance_label = ttk.Label(root, text="Distance: -- cm", font=("Helvetica", 24, "bold"))
        self.distance_label.pack(pady=10)

        self.warning_label = ttk.Label(root, text="", font=("Helvetica", 16), foreground="red")
        self.warning_label.pack()

        self.fig, self.ax = plt.subplots(subplot_kw={'projection': 'polar'})
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

        self.clear_button = ttk.Button(root, text="Clear Radar", command=self.clear_radar)
        self.clear_button.pack(pady=10)

        self.ax.set_ylim(0, 10)
        self.ax.set_title("Radar View", fontsize=14)

        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=100)

        self.update_labels()

    def clear_radar(self):
        global point_history
        point_history.clear()
        self.ax.clear()
        self.ax.set_ylim(0, 10)
        self.ax.set_title("Radar View", fontsize=14)
        self.canvas.draw()

    def update_plot(self, frame):
        global point_history, pause_until

        if time.time() < pause_until:
            # During pause, freeze radar plot updates
            return

        # Use actual angle_data for theta in radians
        theta = math.radians(angle_data)
        r = distance_data

        if r > 10:
            return

        if r < 5:
            color = 'red'
        elif r < 8:
            color = 'orange'
        else:
            color = 'green'

        # Add new point with angle and distance
        point_history.append((theta, r, color))

        self.ax.clear()
        self.ax.set_ylim(0, 10)
        self.ax.set_title("Radar View", fontsize=14)

        for pt_theta, pt_r, pt_color in point_history:
            self.ax.plot(pt_theta, pt_r, 'o', color=pt_color, markersize=6)

    def update_labels(self):
        global pause_until
        if time.time() < pause_until:
            # Freeze distance label update during pause
            pass
        else:
            if distance_data < 10:
                self.distance_label.config(text=f"Distance: {distance_data:.1f} cm")
            else:
                self.distance_label.config(text="Distance: -- cm")

        self.warning_label.config(text="Object detected!" if warning else "")
        self.root.after(100, self.update_labels)

# ========== Start ==========
if __name__ == "__main__":
    thread = threading.Thread(target=read_serial, daemon=True)
    thread.start()

    root = tk.Tk()
    gui = RadarGUI(root)
    root.mainloop()