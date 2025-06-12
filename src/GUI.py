import subprocess
import tkinter as tk 
from tkinter import ttk
import serial
import threading
import time 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
import math
import re

class RadarVisualization:
    def __init__(self):
        self.radar_center_x, self.radar_center_y = 200, 200
        self.radar_radius = 180
        self.upload_arduino_sketch()
        self.setup_serial_connection()
        self.initialize_gui()
        self.setup_visualizations()
        

    def upload_arduino_sketch(self):
        print("Uploading arduino sketch...")
        upload_result = subprocess.run(
            [r"C:\Users\Sahaj\.platformio\penv\Scripts\platformio.exe", "run", "--target", "upload"],
            capture_output=True,
            text=True,
            cwd=r"C:\Users\Sahaj\Documents\PlatformIO\Projects\ScienceCPT"  
        )

        if upload_result.returncode != 0:
            print("Upload failed...")
            print(upload_result.stdout)
            print(upload_result.stderr)
            exit(1)
        print("Upload successful!")
    
    def setup_serial_connection(self):
        time.sleep(2)
        self.arduino = serial.Serial('COM6', 9600, timeout=1)
        time.sleep(2)
        self.current_distance = 0
    
    def initialize_gui(self):
        self.root = tk.Tk()
        self.root.title("Ultrasonic Sensor Display")
        self.root.geometry("1200x800")

        self.plot_frame = tk.Frame(self.root)
        self.plot_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.right_panel = tk.Frame(self.root)
        self.right_panel.pack(side="right", fill="y", padx=10)

        self.distance_label = ttk.Label(self.root, text="Waiting for data...", font=("Arial",48))
        self.distance_label.pack(pady=10)

        self.threshold = 15
        self.alert_label = ttk.Label(self.root, text="", font=("Arial", 32), foreground="red")
        self.alert_label.pack()

        self.info = ttk.Label(self.root, text="Ultrasonic sensors measure distance", wraplength=1200, justify="center")
        self.info.pack(pady=10)
    
    def setup_visualizations(self):
        self.setup_radar_display()
        self.setup_wave_visualization()
        self.setup_1d_plot()
        self.setup_polar_plot()
    
    def setup_radar_display(self):
        self.radar_canvas = tk.Canvas(self.root, width=400, height=400, bg="black")
        self.radar_canvas.pack(pady=10)
        self.radar_radius = 180
        self.draw_radar_grid()
        self.detect_objects = collections.deque(maxlen=50)
    
    def draw_radar_grid(self):
        for r in range(50, self.radar_radius, 50):
            self.radar_canvas.create_oval(self.radar_center_x - r, self.radar_center_y - r, self.radar_center_x + r, self.radar_center_y + r, outline="darkgreen", width=1)
        
        for angle in range(0, 360, 30):
            radian_angle = math.radians(angle)
            x = self.radar_center_x + self.radar_radius * math.sin(radian_angle)
            y = self.radar_center_y - self.radar_radius * math.cos(radian_angle)
            self.radar_canvas.create_line(self.radar_center_x, self.radar_center_y, x, y, fill="darkgreen", width=1)
    
    def setup_wave_visualization(self):
        self.ripple_canvas = tk.Canvas(self.root, width=400, height=200, bg="black")
        self.ripple_canvas.pack(pady=5)
        self.sine_canvas = tk.Canvas(self.root, width=800, height=200, bg="navy")
        self.sine_canvas.pack(pady=5)
        self.ripples = []
    
    def setup_1d_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.data_buffer = collections.deque([0]*100,maxlen=100)
        self.line, = self.ax.plot(self.data_buffer, color="green")
        self.ax.set_title("1D Ultrasound Distance Plot")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Distance (cm)")
        self.ax.set_ylim(0, 100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def setup_polar_plot(self):
        self.fig2, self.ax2 = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(5, 5))
        self.radii = [0] * 360
        self.angles = list(range(360))
        self.angle_radians = [math.radians(a) for a in self.angles]
        self.line2, = self.ax2.plot(self.angles, self.radii, color='green')
        self.ax2.set_theta_zero_location("N")
        self.ax2.set_theta_direction(-1)
        self.ax2.set_title("2D Polar Radar View")
        self.ax2.set_ylim(0, 100)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.right_panel)
        self.canvas2.get_tk_widget().pack(side="left", padx=10)
    
    def start_application(self):
        self.serial_thread = threading.Thread(target=self.read_from_arduino, daemon=True)
        self.serial_thread.start()
        self.update_gui()
        self.root.mainloop()
    
    def read_from_arduino(self):
        while True:
            if self.arduino.in_waiting:
                line = self.arduino.readline().decode('utf-8').strip()
                if "," in line:
                    parts = line.split(",")
                    if len(parts) == 2:
                        angle_str, dist_str = parts[0].strip(), parts[1].strip()
                        if self.is_valid_number(angle_str) and self.is_valid_number(dist_str):
                            angle = int(float(angle_str))
                            dist = int(float(dist_str))
                            self.process_radar_data(angle, dist)

            time.sleep(0.05)
    
    def process_radar_data(self, angle, distance):
        self.current_distance = distance
        self.update_polar_plot(angle, distance)
        self.update_distance_label(distance)
        self.data_buffer.append(distance)
        if distance < 100:
            self.detect_objects.append((angle, distance))

    def update_polar_plot(self, angle_deg, distance_cm):
        angle_deg = angle_deg % 360
        self.radii[angle_deg] = distance_cm
        self.line2.set_data(self.angle_radians, self.radii)
        self.ax2.set_ylim(0, max(100, max(self.radii) + 20))
        self.canvas2.draw()

    def update_distance_label(self, distance):
        self.distance_label.config(text=f"Distance: {distance} cm")
        if distance < 15:
            self.alert_label.config(text="OBJECT DETECTED!", foreground="red")
        else:
            self.alert_label.config(text="")
    
    def update_gui(self):
        self.update_1d_plot()
        self.update_radar_display()
        self.update_wave_visualization()
        self.root.after(50, self.update_gui)
    
    def update_1d_plot(self):
        self.line.set_ydata(self.data_buffer)
        self.line.set_xdata(range(len(self.data_buffer)))
        self.ax.set_xlim(0, 100)
        self.canvas.draw()
    
    def update_radar_display(self):
        self.radar_canvas.delete("all")
        self.draw_radar_grid()
        sweep_time = time.time() % 2
        sweep_angle = sweep_time * 180
        radian_angle = math.radians(sweep_angle)
        x = self.radar_center_x + self.radar_radius * math.sin(radian_angle)
        y = self.radar_center_y - self.radar_radius * math.cos(radian_angle)
        self.radar_canvas.create_line(self.radar_center_x, self.radar_center_y, x, y, fill="red", width=2)
        for angle, distance in self.detect_objects:
            if distance > 0:
                scaled_dist = distance * (self.radar_radius / 100)
                radian_angle = math.radians(angle)
                obj_x = self.radar_center_x + scaled_dist * math.sin(radian_angle)
                obj_y = self.radar_center_y - scaled_dist * math.cos(radian_angle)
                self.radar_canvas.create_oval(obj_x - 5, obj_y - 5, obj_x + 5, obj_y + 5, fill="red", outline="blue")
    
    def update_wave_visualization(self):
        self.update_ripple_effect()
        self.update_sine_wave()

    def update_ripple_effect(self):
        self.ripple_canvas.delete("all")
        if self.current_distance > 0:
            self.ripples.append({'radius':5,'max_radius': (self.current_distance / 100)*180,'alpha':255})
        for ripple in self.ripples[:]:
            radius = ripple['radius']
            alpha = ripple['alpha']
            color = f'#{alpha:02x}ff{alpha:02x}'
            self.ripple_canvas.create_oval(200 - radius, 100 - radius, 200 + radius, 100 + radius, outline=color, width=2)
            ripple['radius'] += 3
            ripple['alpha'] -= 7
            if ripple['radius'] > ripple['max_radius'] or ripple['alpha'] <= 0:
                self.ripples.remove(ripple)

    def update_sine_wave(self):
        self.sine_canvas.delete("all")
        amplitude = 40
        frequency = max(1, 100 // (self.current_distance + 1))
        points = []
        for x in range(0, 800, 5):
            y = 100 + amplitude * math.sin((x / 800) * frequency * 2 * math.pi)
            points.append(x)
            points.append(y)
        self.sine_canvas.create_line(points, fill="cyan", smooth=True, width=3)
    
    @staticmethod
    def is_valid_number(s):
        return s.replace('.', '', 1).isdigit()
    
if __name__ == "__main__":
    app = RadarVisualization()
    app.start_application()