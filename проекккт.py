import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import time
import threading
import os
import pygetwindow as gw
from pynput import mouse
import logging

# Set up logging
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_folder, 'work_tracker.log'),
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FocusedWorkTracker:
    def __init__(self):
        self.active_window = None
        self.start_time = None
        self.total_time = 0
        self.is_tracking = False
        self.is_paused = False
        self.cursor_positions = []
        self.window_changes = []

    def start_tracking(self):
        self.is_tracking = True
        self.start_time = datetime.now()
        self.cursor_positions.clear()
        self.window_changes.clear()
        self.register_window_change()
        logging.info("Started tracking work time.")

    def pause_tracking(self):
        if self.is_tracking and not self.is_paused:
            self.is_paused = True
            logging.info("Paused work tracking.")

    def resume_tracking(self):
        if self.is_tracking and self.is_paused:
            self.is_paused = False
            self.start_time = datetime.now()  # Reset start time for the resume
            logging.info("Resumed work tracking.")

    def stop_tracking(self):
        if self.is_tracking:
            elapsed_time = (datetime.now() - self.start_time).total_seconds() if not self.is_paused else 0
            self.total_time += elapsed_time
            self.is_tracking = False
            self.start_time = None
            logging.info("Stopped tracking work time. Total time: {:.2f} seconds".format(self.total_time))

    def get_total_time(self):
        return self.total_time

    def get_active_window(self):
        try:
            current_window = gw.getActiveWindow()
            if current_window:
                return current_window.title
            return "No active window"
        except Exception as e:
            logging.error("Error getting active window: {}".format(e))
            return str(e)

    def register_window_change(self):
        current_window = self.get_active_window()
        if current_window != self.active_window:
            change_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.active_window = current_window
            self.window_changes.append((change_time, current_window))
            logging.info(f"Window changed to '{current_window}' at {change_time}")

    def record_cursor_position(self, position):
        self.cursor_positions.append(position)
        logging.info("Recorded cursor position: {}".format(position))


class CursorTracker(threading.Thread):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.running = True

    def run(self):
        while self.running:
            if self.tracker.is_tracking and not self.tracker.is_paused:
                x, y = mouse.Controller().position
                self.tracker.record_cursor_position((x, y))
            time.sleep(1)

    def stop(self):
        self.running = False
        logging.info("Cursor tracking stopped.")


class TrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Focused Work Tracker")
        self.tracker = FocusedWorkTracker()
        self.cursor_tracker = None

        self.label = tk.Label(root, text="Focused Work Tracker", font=("Arial", 16))
        self.label.pack(pady=10)

        self.start_button = tk.Button(root, text="Start Tracking", command=self.start_tracking)
        self.start_button.pack(pady=5)

        self.pause_button = tk.Button(root, text="Pause Tracking", command=self.pause_tracking, state=tk.DISABLED)
        self.pause_button.pack(pady=5)

        self.resume_button = tk.Button(root, text="Resume Tracking", command=self.resume_tracking, state=tk.DISABLED)
        self.resume_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop Tracking", command=self.stop_tracking, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.stats_button = tk.Button(root, text="Show Statistics", command=self.show_statistics)
        self.stats_button.pack(pady=5)

        self.active_window_label = tk.Label(root, text="Active Window: None")
        self.active_window_label.pack(pady=10)

        self.update_active_window()

    def start_tracking(self):
        self.tracker.start_tracking()
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.cursor_tracker = CursorTracker(self.tracker)
        self.cursor_tracker.start()
        self.update_timer()

    def pause_tracking(self):
        self.tracker.pause_tracking()
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.NORMAL)

    def resume_tracking(self):
        self.tracker.resume_tracking()
        self.pause_button.config(state=tk.NORMAL)
        self.resume_button.config(state=tk.DISABLED)

    def stop_tracking(self):
        self.tracker.stop_tracking()
        if self.cursor_tracker is not None:
            self.cursor_tracker.stop()
            self.cursor_tracker = None
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.resume_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

    def on_closing(self):
        if self.tracker.is_tracking:
            self.tracker.stop_tracking()
        self.root.destroy()

    def show_statistics(self):
        total_time = self.tracker.get_total_time()
        active_window = self.tracker.get_active_window()
        cursor_positions = self.tracker.cursor_positions

        message = f"Total Focused Work Time: {total_time:.2f} seconds"
        message += f"Active Window: {active_window}\n"
        message += f"Cursor Positions Recorded: {len(cursor_positions)}\n"

        message += "Window Changes:\n"
        for change_time, window_title in self.tracker.window_changes:
            message += f"{change_time} - {window_title}\n"

        messagebox.showinfo("Statistics", message)

    def update_active_window(self):
        self.tracker.register_window_change()
        active_window = self.tracker.get_active_window()
        self.active_window_label.config(text=f"Active Window: {active_window}")
        self.root.after(1000, self.update_active_window)

    def update_timer(self):
        if self.tracker.is_tracking:
            self.root.after(1000, self.update_timer)


def main():
    root = tk.Tk()
    app = TrackerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
