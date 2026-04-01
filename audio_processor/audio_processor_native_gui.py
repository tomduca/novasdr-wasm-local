#!/usr/bin/env python3
"""
NovaSDR Audio Processor - Native GUI Application
Cross-platform desktop application using tkinter
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
import numpy as np
import sounddevice as sd
from scipy import signal
import time
from datetime import datetime
from pathlib import Path
import wave

try:
    import novasdr_nr as novasdr_nr_py
    NOVASDR_AVAILABLE = True
except ImportError:
    NOVASDR_AVAILABLE = False

try:
    from pydub import AudioSegment
    MP3_AVAILABLE = True
except ImportError:
    MP3_AVAILABLE = False

# Audio parameters
SAMPLE_RATE = 48000
BLOCK_SIZE = 2048

# Presets for SSB mode
PRESETS_SSB = {
    'moderate': {'gain': 1.0/1024.0, 'alpha': 0.98, 'asnr': 20.0, 'post_gain': 1.5},
    'aggressive': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 10.0, 'post_gain': 2.5},
    'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 2.0, 'post_gain': 10.0},
    'extreme': {'gain': 1.0/16384.0, 'alpha': 0.99, 'asnr': 1.0, 'post_gain': 14.0}
}

# Presets for CW mode
PRESETS_CW = {
    'moderate': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 15.0, 'post_gain': 3.0},
    'aggressive': {'gain': 1.0/4096.0, 'alpha': 0.99, 'asnr': 8.0, 'post_gain': 5.0},
    'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 3.0, 'post_gain': 12.0},
    'extreme': {'gain': 1.0/16384.0, 'alpha': 0.995, 'asnr': 1.0, 'post_gain': 18.0}
}

# Bandpass filter configurations
BANDPASS_CONFIG = {
    'SSB': {'low': 300, 'high': 2700},
    'CW': {'low': 600, 'high': 900}
}

class AudioProcessor:
    def __init__(self):
        self.running = False
        self.bypass = False
        self.recording = False
        self.mode = 'SSB'
        self.preset = 'extreme'
        self.input_device = None
        self.output_device = None
        self.stream = None
        self.novasdr_nr = None
        self.post_gain = 14.0
        self.bandpass_filter = None
        self.zi_bandpass = None
        self.recording_data = []
        
    def create_bandpass_filter(self, mode):
        """Create bandpass filter based on mode"""
        config = BANDPASS_CONFIG[mode]
        low_freq = config['low']
        high_freq = config['high']
        
        nyquist = SAMPLE_RATE / 2
        low_normalized = low_freq / nyquist
        high_normalized = high_freq / nyquist
        
        sos = signal.butter(4, [low_normalized, high_normalized], btype='band', output='sos')
        zi = signal.sosfilt_zi(sos)
        
        return sos, zi
    
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Real-time audio processing callback"""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        
        audio_data = indata[:, 0].copy()
        
        if self.bypass or not NOVASDR_AVAILABLE:
            filtered_audio = audio_data
        else:
            # Apply bandpass filter
            if self.bandpass_filter is not None:
                filtered_audio, self.zi_bandpass = signal.sosfilt(
                    self.bandpass_filter, 
                    audio_data, 
                    zi=self.zi_bandpass
                )
            else:
                filtered_audio = audio_data
            
            # Apply NovaSDR noise reduction
            filtered_audio = self.novasdr_nr.process(filtered_audio.astype(np.float32))
            filtered_audio = filtered_audio * self.post_gain
        
        filtered_audio = np.clip(filtered_audio, -0.95, 0.95)
        
        # Record if active
        if self.recording:
            self.recording_data.append(filtered_audio.copy())
        
        outdata[:, 0] = filtered_audio
        if outdata.shape[1] > 1:
            outdata[:, 1] = filtered_audio
    
    def start(self, input_dev, output_dev, preset, mode):
        """Start audio processing"""
        self.input_device = input_dev
        self.output_device = output_dev
        self.preset = preset
        self.mode = mode
        
        # Create bandpass filter
        self.bandpass_filter, self.zi_bandpass = self.create_bandpass_filter(mode)
        
        # Initialize NovaSDR
        if NOVASDR_AVAILABLE:
            presets = PRESETS_CW if mode == 'CW' else PRESETS_SSB
            preset_config = presets[preset]
            self.novasdr_nr = novasdr_nr_py.SpectralNoiseReduction(
                SAMPLE_RATE,
                preset_config['gain'],
                preset_config['alpha'],
                preset_config['asnr']
            )
            self.post_gain = preset_config['post_gain']
        
        # Start audio stream
        self.stream = sd.Stream(
            device=(input_dev, output_dev),
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=2,
            callback=self.audio_callback,
            latency='low'
        )
        self.stream.start()
        self.running = True
    
    def stop(self):
        """Stop audio processing"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False
    
    def set_mode(self, mode):
        """Change mode (SSB/CW)"""
        self.mode = mode
        self.bandpass_filter, self.zi_bandpass = self.create_bandpass_filter(mode)
        
        if self.novasdr_nr and NOVASDR_AVAILABLE:
            presets = PRESETS_CW if mode == 'CW' else PRESETS_SSB
            preset_config = presets[self.preset]
            self.novasdr_nr = novasdr_nr_py.SpectralNoiseReduction(
                SAMPLE_RATE,
                preset_config['gain'],
                preset_config['alpha'],
                preset_config['asnr']
            )
            self.post_gain = preset_config['post_gain']
    
    def set_preset(self, preset):
        """Change preset"""
        self.preset = preset
        
        if self.novasdr_nr and NOVASDR_AVAILABLE:
            presets = PRESETS_CW if self.mode == 'CW' else PRESETS_SSB
            preset_config = presets[preset]
            self.novasdr_nr = novasdr_nr_py.SpectralNoiseReduction(
                SAMPLE_RATE,
                preset_config['gain'],
                preset_config['alpha'],
                preset_config['asnr']
            )
            self.post_gain = preset_config['post_gain']
    
    def start_recording(self):
        """Start recording"""
        self.recording = True
        self.recording_data = []
    
    def stop_recording(self):
        """Stop recording and save file"""
        self.recording = False
        
        if not self.recording_data:
            return None
        
        # Create recordings directory
        recordings_dir = Path(__file__).parent / 'recordings'
        recordings_dir.mkdir(exist_ok=True)
        
        # Generate filename
        now = datetime.now()
        audio_data = np.concatenate(self.recording_data)
        duration = len(audio_data) / SAMPLE_RATE
        
        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        if MP3_AVAILABLE:
            filename = f"recording_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
            filepath = recordings_dir / filename
            
            # Create temp WAV
            temp_wav = recordings_dir / f"temp_{now.strftime('%Y%m%d_%H%M%S')}.wav"
            with wave.open(str(temp_wav), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
            
            # Convert to MP3
            audio = AudioSegment.from_wav(str(temp_wav))
            audio.export(str(filepath), format='mp3', bitrate='128k')
            temp_wav.unlink()
        else:
            filename = f"recording_{now.strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = recordings_dir / filename
            
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
        
        self.recording_data = []
        return filename, duration


class NovaSDRGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NovaSDR Audio Processor")
        self.root.geometry("700x800")
        
        self.processor = AudioProcessor()
        self.create_widgets()
        self.load_devices()
        
        # Set window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Header
        header = tk.Frame(self.root, bg='#667eea', pady=15)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="📻 NovaSDR Audio Processor", 
                        font=('Arial', 18, 'bold'), bg='#667eea', fg='white')
        title.pack()
        
        self.status_label = tk.Label(header, text="● Stopped", 
                                     font=('Arial', 12), bg='#667eea', fg='#fca5a5')
        self.status_label.pack()
        
        # Main container
        container = tk.Frame(self.root, padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Device Selection
        device_frame = tk.LabelFrame(container, text="🎧 Audio Devices", 
                                     font=('Arial', 12, 'bold'), padx=10, pady=10)
        device_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(device_frame, text="Input Device:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_combo = ttk.Combobox(device_frame, width=50, state='readonly')
        self.input_combo.grid(row=0, column=1, pady=5, padx=5)
        
        tk.Label(device_frame, text="Output Device:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_combo = ttk.Combobox(device_frame, width=50, state='readonly')
        self.output_combo.grid(row=1, column=1, pady=5, padx=5)
        
        # Mode Selection
        mode_frame = tk.LabelFrame(container, text="📡 Mode", 
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        mode_frame.pack(fill=tk.X, pady=10)
        
        self.mode_var = tk.StringVar(value='SSB')
        tk.Radiobutton(mode_frame, text="SSB (300-2700 Hz)", variable=self.mode_var, 
                      value='SSB', command=self.on_mode_change, font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="CW (600-900 Hz)", variable=self.mode_var, 
                      value='CW', command=self.on_mode_change, font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        
        # Preset Selection
        preset_frame = tk.LabelFrame(container, text="🎛️ Noise Reduction Preset", 
                                     font=('Arial', 12, 'bold'), padx=10, pady=10)
        preset_frame.pack(fill=tk.X, pady=10)
        
        self.preset_var = tk.StringVar(value='extreme')
        presets = [('Moderate', 'moderate'), ('Aggressive', 'aggressive'), 
                  ('Ultra', 'ultra'), ('Extreme ⭐', 'extreme')]
        
        for i, (label, value) in enumerate(presets):
            tk.Radiobutton(preset_frame, text=label, variable=self.preset_var, 
                          value=value, command=self.on_preset_change, 
                          font=('Arial', 10)).grid(row=0, column=i, padx=5)
        
        self.preset_info = tk.Label(preset_frame, text="", font=('Arial', 9), fg='#6b7280')
        self.preset_info.grid(row=1, column=0, columnspan=4, pady=5)
        self.update_preset_info()
        
        # Control Buttons
        control_frame = tk.LabelFrame(container, text="⚙️ Control", 
                                      font=('Arial', 12, 'bold'), padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.bypass_var = tk.BooleanVar()
        tk.Checkbutton(control_frame, text="Bypass (pass-through)", 
                      variable=self.bypass_var, command=self.on_bypass_change,
                      font=('Arial', 10)).pack(anchor=tk.W, pady=5)
        
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = tk.Button(button_frame, text="▶ Start", command=self.start_processing,
                                   bg='#10b981', fg='white', font=('Arial', 12, 'bold'),
                                   padx=20, pady=10)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.stop_btn = tk.Button(button_frame, text="■ Stop", command=self.stop_processing,
                                  bg='#ef4444', fg='white', font=('Arial', 12, 'bold'),
                                  padx=20, pady=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Recording
        rec_frame = tk.LabelFrame(container, text="🔴 Recording", 
                                  font=('Arial', 12, 'bold'), padx=10, pady=10)
        rec_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(rec_frame, text="Recordings saved as: recording_YYYYMMDD_HHMMSS.mp3",
                font=('Arial', 9), fg='#6b7280').pack(pady=5)
        
        rec_button_frame = tk.Frame(rec_frame)
        rec_button_frame.pack(fill=tk.X, pady=5)
        
        self.rec_start_btn = tk.Button(rec_button_frame, text="🔴 Start Recording",
                                       command=self.start_recording, bg='#dc2626', fg='white',
                                       font=('Arial', 10, 'bold'), state=tk.DISABLED)
        self.rec_start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.rec_stop_btn = tk.Button(rec_button_frame, text="⏹️ Stop Recording",
                                      command=self.stop_recording, bg='#6b7280', fg='white',
                                      font=('Arial', 10, 'bold'), state=tk.DISABLED)
        self.rec_stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.rec_status = tk.Label(rec_frame, text="", font=('Arial', 9))
        self.rec_status.pack(pady=5)
        
        # Log
        log_frame = tk.LabelFrame(container, text="📋 Log", 
                                  font=('Arial', 12, 'bold'), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  bg='#1f2937', fg='#10b981',
                                                  font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial log
        self.log(f"NovaSDR module: {'✓ Available' if NOVASDR_AVAILABLE else '✗ Not available'}")
        self.log(f"MP3 recording: {'✓ Available' if MP3_AVAILABLE else '✗ Not available (will use WAV)'}")
    
    def load_devices(self):
        """Load audio devices"""
        devices = sd.query_devices()
        
        input_devices = []
        output_devices = []
        
        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append((idx, f"{idx}: {device['name']}"))
            if device['max_output_channels'] > 0:
                output_devices.append((idx, f"{idx}: {device['name']}"))
        
        self.input_combo['values'] = [name for _, name in input_devices]
        self.output_combo['values'] = [name for _, name in output_devices]
        
        # Auto-select BlackHole for input
        for idx, name in input_devices:
            if 'BlackHole' in name or 'Loopback' in name:
                self.input_combo.current(input_devices.index((idx, name)))
                break
        else:
            if input_devices:
                self.input_combo.current(0)
        
        if output_devices:
            self.output_combo.current(0)
        
        self.log(f"Loaded {len(input_devices)} input and {len(output_devices)} output devices")
    
    def update_preset_info(self):
        """Update preset information display"""
        presets = PRESETS_CW if self.mode_var.get() == 'CW' else PRESETS_SSB
        preset = presets[self.preset_var.get()]
        gain = int(1 / preset['gain'])
        info = f"Gain: 1/{gain}, Alpha: {preset['alpha']}, ASNR: {preset['asnr']} dB, Post-Gain: {preset['post_gain']}x"
        self.preset_info.config(text=info)
    
    def on_mode_change(self):
        """Handle mode change"""
        mode = self.mode_var.get()
        if self.processor.running:
            self.processor.set_mode(mode)
            config = BANDPASS_CONFIG[mode]
            self.log(f"Mode changed to {mode} (BW: {config['low']}-{config['high']} Hz)")
        self.update_preset_info()
    
    def on_preset_change(self):
        """Handle preset change"""
        preset = self.preset_var.get()
        if self.processor.running:
            self.processor.set_preset(preset)
            self.log(f"Preset changed to {preset} ({self.mode_var.get()} mode)")
        self.update_preset_info()
    
    def on_bypass_change(self):
        """Handle bypass toggle"""
        self.processor.bypass = self.bypass_var.get()
        status = "BYPASSED" if self.bypass_var.get() else "ACTIVE"
        self.log(f"Processing {status}")
    
    def start_processing(self):
        """Start audio processing"""
        input_idx = int(self.input_combo.get().split(':')[0])
        output_idx = int(self.output_combo.get().split(':')[0])
        preset = self.preset_var.get()
        mode = self.mode_var.get()
        
        try:
            self.processor.start(input_idx, output_idx, preset, mode)
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.rec_start_btn.config(state=tk.NORMAL)
            self.status_label.config(text="● Running", fg='#86efac')
            
            config = BANDPASS_CONFIG[mode]
            self.log(f"✓ Audio processing started")
            self.log(f"  Mode: {mode} ({config['low']}-{config['high']} Hz)")
            self.log(f"  Preset: {preset}")
            self.log(f"  Latency: ~{(BLOCK_SIZE / SAMPLE_RATE) * 1000:.1f}ms")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
    
    def stop_processing(self):
        """Stop audio processing"""
        self.processor.stop()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.rec_start_btn.config(state=tk.DISABLED)
        self.rec_stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="● Stopped", fg='#fca5a5')
        
        self.log("✓ Audio processing stopped")
    
    def start_recording(self):
        """Start recording"""
        self.processor.start_recording()
        self.rec_start_btn.config(state=tk.DISABLED)
        self.rec_stop_btn.config(state=tk.NORMAL)
        self.rec_status.config(text="🔴 Recording...", fg='#dc2626')
        self.log("🔴 Recording started")
    
    def stop_recording(self):
        """Stop recording"""
        result = self.processor.stop_recording()
        
        self.rec_start_btn.config(state=tk.NORMAL)
        self.rec_stop_btn.config(state=tk.DISABLED)
        
        if result:
            filename, duration = result
            self.rec_status.config(text=f"✅ Saved: {filename} ({duration:.1f}s)", fg='#10b981')
            self.log(f"⏹️ Recording stopped - Saved: {filename} ({duration:.1f}s)")
        else:
            self.rec_status.config(text="No data recorded", fg='#ef4444')
            self.log("⏹️ Recording stopped - No data recorded")
    
    def log(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def on_closing(self):
        """Handle window close"""
        if self.processor.running:
            self.processor.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = NovaSDRGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
