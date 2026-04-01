#!/usr/bin/env python3
"""
NovaSDR Audio Processor - GUI Version
Simple graphical interface for device selection, preset control, and bypass toggle
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
import numpy as np
import sounddevice as sd
from scipy import signal
import queue
import time

try:
    import novasdr_nr_py
    NOVASDR_AVAILABLE = True
except ImportError:
    NOVASDR_AVAILABLE = False
    print("Warning: NovaSDR Rust module not available. Install with: cd ../novasdr_nr_py && maturin develop --release")

class AudioProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NovaSDR Audio Processor")
        self.root.geometry("600x700")
        
        # Processing state
        self.is_running = False
        self.bypass = False
        self.stream = None
        self.novasdr_nr = None
        
        # Audio parameters
        self.sample_rate = 48000
        self.block_size = 2048
        
        # Presets
        self.presets = {
            'moderate': {'gain': 1.0/1024.0, 'alpha': 0.98, 'asnr': 20.0, 'post_gain': 1.5},
            'aggressive': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 10.0, 'post_gain': 2.5},
            'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 2.0, 'post_gain': 10.0},
            'extreme': {'gain': 1.0/16384.0, 'alpha': 0.99, 'asnr': 1.0, 'post_gain': 14.0},
        }
        
        self.setup_ui()
        self.load_devices()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="NovaSDR Audio Processor", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Status indicator
        self.status_label = ttk.Label(main_frame, text="● Stopped", foreground="red", font=('Arial', 12))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Device selection
        device_frame = ttk.LabelFrame(main_frame, text="Audio Devices", padding="10")
        device_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(device_frame, text="Input Device:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_combo = ttk.Combobox(device_frame, width=40, state="readonly")
        self.input_combo.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(device_frame, text="Output Device:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_combo = ttk.Combobox(device_frame, width=40, state="readonly")
        self.output_combo.grid(row=1, column=1, pady=5, padx=5)
        
        # Preset selection
        preset_frame = ttk.LabelFrame(main_frame, text="Noise Reduction Preset", padding="10")
        preset_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.preset_var = tk.StringVar(value="ultra")
        for idx, (name, params) in enumerate(self.presets.items()):
            rb = ttk.Radiobutton(preset_frame, text=name.capitalize(), 
                                variable=self.preset_var, value=name,
                                command=self.on_preset_change)
            rb.grid(row=0, column=idx, padx=10, pady=5)
        
        # Preset info
        self.preset_info = ttk.Label(preset_frame, text="", font=('Arial', 9))
        self.preset_info.grid(row=1, column=0, columnspan=4, pady=5)
        self.update_preset_info()
        
        # Bypass toggle
        bypass_frame = ttk.LabelFrame(main_frame, text="Processing Control", padding="10")
        bypass_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.bypass_var = tk.BooleanVar(value=False)
        self.bypass_check = ttk.Checkbutton(bypass_frame, text="Bypass (Pass-through audio without processing)",
                                           variable=self.bypass_var, command=self.on_bypass_toggle)
        self.bypass_check.grid(row=0, column=0, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start", command=self.start_processing, width=15)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="■ Stop", command=self.stop_processing, 
                                     width=15, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def load_devices(self):
        """Load available audio devices"""
        devices = sd.query_devices()
        
        input_devices = []
        output_devices = []
        
        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append(f"{idx}: {device['name']}")
            if device['max_output_channels'] > 0:
                output_devices.append(f"{idx}: {device['name']}")
        
        self.input_combo['values'] = input_devices
        self.output_combo['values'] = output_devices
        
        # Try to select defaults (BlackHole for input, first output device)
        for device in input_devices:
            if 'BlackHole' in device or 'Loopback' in device:
                self.input_combo.set(device)
                break
        else:
            if input_devices:
                self.input_combo.current(0)
        
        if output_devices:
            self.output_combo.current(0)
        
        self.log(f"Loaded {len(input_devices)} input devices and {len(output_devices)} output devices")
        
    def update_preset_info(self):
        """Update preset information display"""
        preset = self.presets[self.preset_var.get()]
        info = f"Gain: 1/{int(1/preset['gain'])}, Alpha: {preset['alpha']}, ASNR: {preset['asnr']} dB, Post-Gain: {preset['post_gain']}x"
        self.preset_info.config(text=info)
        
    def on_preset_change(self):
        """Handle preset change"""
        self.update_preset_info()
        if self.is_running and self.novasdr_nr:
            # Reinitialize filter with new preset
            preset = self.presets[self.preset_var.get()]
            self.novasdr_nr = novasdr_nr_py.SpectralNoiseReduction(
                self.sample_rate,
                preset['gain'],
                preset['alpha'],
                preset['asnr']
            )
            self.current_post_gain = preset['post_gain']
            self.log(f"Preset changed to: {self.preset_var.get()}")
        
    def on_bypass_toggle(self):
        """Handle bypass toggle"""
        self.bypass = self.bypass_var.get()
        status = "BYPASSED" if self.bypass else "ACTIVE"
        self.log(f"Processing {status}")
        
    def log(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def get_device_index(self, combo_value):
        """Extract device index from combo box value"""
        if not combo_value:
            return None
        return int(combo_value.split(':')[0])
        
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Real-time audio processing callback"""
        if status:
            self.log(f"Audio status: {status}")
        
        # Extract mono from input
        audio_data = indata[:, 0].copy()
        
        if self.bypass or not NOVASDR_AVAILABLE:
            # Bypass mode - pass through unchanged
            filtered_audio = audio_data
        else:
            # Apply NovaSDR filter
            filtered_audio = self.novasdr_nr.process(audio_data.astype(np.float32))
            
            # Apply post-gain compensation
            filtered_audio = filtered_audio * self.current_post_gain
        
        # Clip to prevent distortion
        filtered_audio = np.clip(filtered_audio, -0.95, 0.95)
        
        # Output stereo
        outdata[:, 0] = filtered_audio
        if outdata.shape[1] > 1:
            outdata[:, 1] = filtered_audio
            
    def start_processing(self):
        """Start audio processing"""
        input_idx = self.get_device_index(self.input_combo.get())
        output_idx = self.get_device_index(self.output_combo.get())
        
        if input_idx is None or output_idx is None:
            self.log("ERROR: Please select both input and output devices")
            return
        
        if not NOVASDR_AVAILABLE:
            self.log("WARNING: NovaSDR module not available. Running in bypass mode.")
        
        try:
            # Initialize NovaSDR filter
            if NOVASDR_AVAILABLE:
                preset = self.presets[self.preset_var.get()]
                self.novasdr_nr = novasdr_nr_py.SpectralNoiseReduction(
                    self.sample_rate,
                    preset['gain'],
                    preset['alpha'],
                    preset['asnr']
                )
                self.current_post_gain = preset['post_gain']
                self.log(f"✓ NovaSDR initialized: {self.preset_var.get()} preset")
            
            # Start audio stream
            self.stream = sd.Stream(
                device=(input_idx, output_idx),
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=2,
                callback=self.audio_callback,
                latency='low'
            )
            
            self.stream.start()
            self.is_running = True
            
            # Update UI
            self.status_label.config(text="● Running", foreground="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.input_combo.config(state=tk.DISABLED)
            self.output_combo.config(state=tk.DISABLED)
            
            self.log(f"✓ Audio processing started")
            self.log(f"  Input: {self.input_combo.get()}")
            self.log(f"  Output: {self.output_combo.get()}")
            self.log(f"  Preset: {self.preset_var.get()}")
            self.log(f"  Latency: ~{(self.block_size / self.sample_rate) * 1000:.1f}ms")
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.is_running = False
            
    def stop_processing(self):
        """Stop audio processing"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.is_running = False
        
        # Update UI
        self.status_label.config(text="● Stopped", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.input_combo.config(state="readonly")
        self.output_combo.config(state="readonly")
        
        self.log("✓ Audio processing stopped")
        
    def on_closing(self):
        """Handle window close"""
        if self.is_running:
            self.stop_processing()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = AudioProcessorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
