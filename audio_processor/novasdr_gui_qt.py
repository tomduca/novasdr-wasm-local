#!/usr/bin/env python3
"""
NovaSDR Audio Processor - Native PyQt5 GUI
True standalone desktop application
"""

import sys
import numpy as np
import sounddevice as sd
from scipy import signal
import time
from datetime import datetime
from pathlib import Path
import wave
import logging

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QRadioButton, QButtonGroup, QCheckBox,
                             QGroupBox, QMessageBox, QSlider)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# Setup logging to file for debugging when run from Finder
log_file = Path.home() / 'novasdr_debug.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.info(f"NovaSDR Audio Processor starting... Log file: {log_file}")

try:
    import novasdr_nr as novasdr_nr_py
    NOVASDR_AVAILABLE = True
    logging.info(f"✓ NovaSDR module loaded from: {novasdr_nr_py.__file__}")
    print(f"✓ NovaSDR module loaded from: {novasdr_nr_py.__file__}")
except ImportError as e:
    NOVASDR_AVAILABLE = False
    logging.error(f"✗ NovaSDR module not available: {e}")
    print(f"✗ NovaSDR module not available: {e}")
except Exception as e:
    NOVASDR_AVAILABLE = False
    logging.error(f"✗ Error loading NovaSDR module: {e}", exc_info=True)
    print(f"✗ Error loading NovaSDR module: {e}")
    import traceback
    traceback.print_exc()

try:
    from pydub import AudioSegment
    MP3_AVAILABLE = True
except ImportError:
    MP3_AVAILABLE = False

# Audio parameters
SAMPLE_RATE = 48000
BLOCK_SIZE = 2048

# Presets
PRESETS_SSB = {
    'moderate': {'gain': 1.0/1024.0, 'alpha': 0.98, 'asnr': 20.0, 'post_gain': 1.5},
    'aggressive': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 10.0, 'post_gain': 2.5},
    'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 2.0, 'post_gain': 10.0},
    'extreme': {'gain': 1.0/16384.0, 'alpha': 0.99, 'asnr': 1.0, 'post_gain': 14.0}
}

PRESETS_CW = {
    'moderate': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 15.0, 'post_gain': 3.0},
    'aggressive': {'gain': 1.0/4096.0, 'alpha': 0.99, 'asnr': 8.0, 'post_gain': 5.0},
    'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 3.0, 'post_gain': 12.0},
    'extreme': {'gain': 1.0/16384.0, 'alpha': 0.995, 'asnr': 1.0, 'post_gain': 18.0}
}

BANDPASS_CONFIG = {
    'SSB': {'low': 300, 'high': 2700},
    'CW': {'low': 600, 'high': 900}
}


class AudioProcessor(QThread):
    """Audio processing thread"""
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
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
        self.input_gain = 0.05  # Default input gain (5% - very low for hot inputs)
        self.output_volume = 1.0  # Default output volume (100%)
        self.bandpass_filter = None
        self.zi_bandpass = None
        self.recording_data = []
        self.callback_count = 0
        
    def create_bandpass_filter(self, mode):
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
        self.callback_count += 1
        
        # Log every 100 callbacks to verify it's running
        if self.callback_count % 100 == 0:
            logging.debug(f"Audio callback running: {self.callback_count} calls")
        
        if status:
            logging.warning(f"Audio status: {status}")
            print(f"Audio status: {status}", file=sys.stderr)
        
        # Handle any number of input channels - extract mono
        if indata.ndim == 1:
            # Already mono
            audio_data = indata.copy()
        elif indata.shape[1] == 1:
            # Single channel in 2D array
            audio_data = indata[:, 0].copy()
        else:
            # Multiple channels - mix to mono
            audio_data = np.mean(indata, axis=1)
        
        # Apply input gain to prevent saturation
        audio_data = audio_data * self.input_gain
        
        if self.bypass or not NOVASDR_AVAILABLE or self.novasdr_nr is None:
            filtered_audio = audio_data
            if self.callback_count == 1:
                logging.info("Audio callback: BYPASS mode")
        else:
            try:
                if self.bandpass_filter is not None:
                    filtered_audio, self.zi_bandpass = signal.sosfilt(
                        self.bandpass_filter, audio_data, zi=self.zi_bandpass
                    )
                else:
                    filtered_audio = audio_data
                
                filtered_audio = self.novasdr_nr.process(filtered_audio.astype(np.float32))
                filtered_audio = filtered_audio * self.post_gain
                
                if self.callback_count == 1:
                    logging.info(f"Audio callback: PROCESSING mode (input level: {np.abs(audio_data).max():.4f}, output level: {np.abs(filtered_audio).max():.4f})")
            except Exception as e:
                logging.error(f"✗ Audio processing error: {e}", exc_info=True)
                print(f"✗ Audio processing error: {e}")
                filtered_audio = audio_data
        
        # Apply output volume control
        filtered_audio = filtered_audio * self.output_volume
        
        filtered_audio = np.clip(filtered_audio, -0.95, 0.95)
        
        if self.recording:
            self.recording_data.append(filtered_audio.copy())
        
        # Handle any number of output channels
        if outdata.ndim == 1:
            # Mono output
            outdata[:] = filtered_audio
        else:
            # Multi-channel output - duplicate to all channels
            for ch in range(outdata.shape[1]):
                outdata[:, ch] = filtered_audio
    
    def start_processing(self, input_dev, output_dev, preset, mode):
        self.input_device = input_dev
        self.output_device = output_dev
        self.preset = preset
        self.mode = mode
        
        self.bandpass_filter, self.zi_bandpass = self.create_bandpass_filter(mode)
        
        if NOVASDR_AVAILABLE:
            try:
                presets = PRESETS_CW if mode == 'CW' else PRESETS_SSB
                preset_config = presets[preset]
                self.novasdr_nr = novasdr_nr_py.SpectralNoiseReduction(
                    SAMPLE_RATE,
                    preset_config['gain'],
                    preset_config['alpha'],
                    preset_config['asnr']
                )
                self.post_gain = preset_config['post_gain']
                logging.info(f"✓ NovaSDR filter initialized: {preset} mode {mode}")
                print(f"✓ NovaSDR filter initialized: {preset} mode {mode}")
            except Exception as e:
                logging.error(f"✗ Failed to initialize NovaSDR: {e}", exc_info=True)
                print(f"✗ Failed to initialize NovaSDR: {e}")
                import traceback
                traceback.print_exc()
                self.log_signal.emit(f"ERROR: Failed to initialize NovaSDR: {e}")
        else:
            self.log_signal.emit("WARNING: NovaSDR module not available - running in bypass mode")
        
        # Query device info to get correct number of channels
        try:
            input_info = sd.query_devices(input_dev)
            output_info = sd.query_devices(output_dev)
            
            input_channels = min(input_info['max_input_channels'], 2)  # Use up to 2 channels
            output_channels = min(output_info['max_output_channels'], 2)  # Use up to 2 channels
            
            logging.info(f"Input device: {input_channels} channels, Output device: {output_channels} channels")
            print(f"Input device: {input_channels} channels, Output device: {output_channels} channels")
            
            self.stream = sd.Stream(
                device=(input_dev, output_dev),
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                channels=(input_channels, output_channels),
                callback=self.audio_callback,
                latency='low'
            )
        except Exception as e:
            logging.error(f"ERROR: Failed to open audio stream: {e}", exc_info=True)
            self.log_signal.emit(f"ERROR: Failed to open audio stream: {e}")
            raise
        
        try:
            self.stream.start()
            self.running = True
            logging.info("✓ Audio stream started successfully")
        except Exception as e:
            logging.error(f"ERROR: Failed to start audio stream: {e}", exc_info=True)
            self.log_signal.emit(f"ERROR: Failed to start audio stream: {e}")
            raise
        
        config = BANDPASS_CONFIG[mode]
        self.log_signal.emit(f"✓ Audio processing started")
        self.log_signal.emit(f"  Mode: {mode} ({config['low']}-{config['high']} Hz)")
        self.log_signal.emit(f"  Preset: {preset}")
        self.log_signal.emit(f"  Latency: ~{(BLOCK_SIZE / SAMPLE_RATE) * 1000:.1f}ms")
    
    def stop_processing(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False
        self.log_signal.emit("✓ Audio processing stopped")
    
    def set_mode(self, mode):
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
            
        config = BANDPASS_CONFIG[mode]
        self.log_signal.emit(f"Mode changed to {mode} (BW: {config['low']}-{config['high']} Hz)")
    
    def set_preset(self, preset):
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
            self.log_signal.emit(f"Preset changed to {preset} ({self.mode} mode)")
    
    def start_recording(self):
        self.recording = True
        self.recording_data = []
        self.log_signal.emit("🔴 Recording started")
    
    def stop_recording(self):
        self.recording = False
        
        if not self.recording_data:
            self.log_signal.emit("⏹️ Recording stopped - No data recorded")
            return None
        
        try:
            recordings_dir = Path(__file__).parent / 'recordings'
            recordings_dir.mkdir(exist_ok=True)
            
            now = datetime.now()
            audio_data = np.concatenate(self.recording_data)
            duration = len(audio_data) / SAMPLE_RATE
            
            self.log_signal.emit(f"Processing {len(self.recording_data)} chunks, {duration:.1f}s total...")
            
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            if MP3_AVAILABLE:
                filename = f"recording_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
                filepath = recordings_dir / filename
                
                temp_wav = recordings_dir / f"temp_{now.strftime('%Y%m%d_%H%M%S')}.wav"
                with wave.open(str(temp_wav), 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio_int16.tobytes())
                
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
            self.log_signal.emit(f"⏹️ Saved: {filepath}")
            self.log_signal.emit(f"   Duration: {duration:.1f}s, Format: {'MP3' if MP3_AVAILABLE else 'WAV'}")
            return filename, duration
            
        except Exception as e:
            self.log_signal.emit(f"ERROR saving recording: {e}")
            import traceback
            traceback.print_exc()
            return None


class NovaSDRGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = AudioProcessor()
        self.processor.log_signal.connect(self.add_log)
        self.init_ui()
        self.load_devices()
        
    def init_ui(self):
        self.setWindowTitle('LU2MET NR Filter v1.0.0-beta')
        self.setGeometry(100, 100, 600, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel('📻 LU2MET NR Filter')
        header.setFont(QFont('Arial', 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet('background: #667eea; color: white; padding: 15px; border-radius: 8px;')
        layout.addWidget(header)
        
        # Status
        self.status_label = QLabel('● Stopped')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('color: #ef4444; font-size: 14px; padding: 5px;')
        layout.addWidget(self.status_label)
        
        # Devices
        devices_group = QGroupBox('🎧 Audio Devices')
        devices_layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel('Input:'))
        self.input_combo = QComboBox()
        input_layout.addWidget(self.input_combo)
        devices_layout.addLayout(input_layout)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel('Output:'))
        self.output_combo = QComboBox()
        output_layout.addWidget(self.output_combo)
        devices_layout.addLayout(output_layout)
        
        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)
        
        # Mode
        mode_group = QGroupBox('📡 Mode')
        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup()
        
        self.ssb_radio = QRadioButton('SSB (300-2700 Hz)')
        self.ssb_radio.setChecked(True)
        self.ssb_radio.toggled.connect(self.on_mode_change)
        self.mode_group.addButton(self.ssb_radio)
        mode_layout.addWidget(self.ssb_radio)
        
        self.cw_radio = QRadioButton('CW (600-900 Hz)')
        self.cw_radio.toggled.connect(self.on_mode_change)
        self.mode_group.addButton(self.cw_radio)
        mode_layout.addWidget(self.cw_radio)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Presets
        preset_group = QGroupBox('🎛️ Noise Reduction Preset')
        preset_layout = QVBoxLayout()
        
        preset_buttons_layout = QHBoxLayout()
        self.preset_group = QButtonGroup()
        
        for preset_name in ['moderate', 'aggressive', 'ultra', 'extreme']:
            radio = QRadioButton(preset_name.capitalize())
            if preset_name == 'extreme':
                radio.setChecked(True)
                radio.setText('Extreme ⭐')
            radio.toggled.connect(lambda checked, p=preset_name: self.on_preset_change(p) if checked else None)
            self.preset_group.addButton(radio)
            preset_buttons_layout.addWidget(radio)
        
        preset_layout.addLayout(preset_buttons_layout)
        
        self.preset_info = QLabel()
        self.preset_info.setStyleSheet('color: #6b7280; font-size: 11px;')
        preset_layout.addWidget(self.preset_info)
        self.update_preset_info()
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # Control
        control_group = QGroupBox('⚙️ Control')
        control_layout = QVBoxLayout()
        
        # Input Gain Control
        gain_layout = QHBoxLayout()
        gain_label = QLabel('Input Gain:')
        gain_layout.addWidget(gain_label)
        
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setMinimum(1)  # 1% minimum
        self.gain_slider.setMaximum(100)  # 100% maximum
        self.gain_slider.setValue(5)  # 5% default (very low for hot inputs)
        self.gain_slider.setTickPosition(QSlider.TicksBelow)
        self.gain_slider.setTickInterval(10)
        self.gain_slider.valueChanged.connect(self.on_gain_change)
        gain_layout.addWidget(self.gain_slider)
        
        self.gain_value_label = QLabel('5%')
        self.gain_value_label.setStyleSheet('font-weight: bold; min-width: 40px;')
        gain_layout.addWidget(self.gain_value_label)
        
        control_layout.addLayout(gain_layout)
        
        gain_info = QLabel('⚠️ Start low (1-10%) and increase until audio is clear without saturation')
        gain_info.setStyleSheet('color: #f59e0b; font-size: 10px; padding: 2px;')
        control_layout.addWidget(gain_info)
        
        # Output Volume Control
        volume_layout = QHBoxLayout()
        volume_label = QLabel('Output Volume:')
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(10)  # 10% minimum
        self.volume_slider.setMaximum(400)  # 400% maximum (4x boost)
        self.volume_slider.setValue(100)  # 100% default
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.setTickInterval(50)
        self.volume_slider.valueChanged.connect(self.on_volume_change)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_value_label = QLabel('100%')
        self.volume_value_label.setStyleSheet('font-weight: bold; min-width: 40px;')
        volume_layout.addWidget(self.volume_value_label)
        
        control_layout.addLayout(volume_layout)
        
        volume_info = QLabel('💡 Adjust final output volume (can boost up to 400%)')
        volume_info.setStyleSheet('color: #3b82f6; font-size: 10px; padding: 2px;')
        control_layout.addWidget(volume_info)
        
        self.bypass_check = QCheckBox('Bypass (pass-through)')
        self.bypass_check.stateChanged.connect(self.on_bypass_change)
        control_layout.addWidget(self.bypass_check)
        
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton('▶ Start')
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setStyleSheet('background: #10b981; color: white; padding: 8px; font-weight: bold;')
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('■ Stop')
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet('background: #ef4444; color: white; padding: 8px; font-weight: bold;')
        buttons_layout.addWidget(self.stop_btn)
        
        control_layout.addLayout(buttons_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Recording
        rec_group = QGroupBox('🔴 Recording')
        rec_layout = QVBoxLayout()
        
        rec_info = QLabel('Recordings saved as: recording_YYYYMMDD_HHMMSS.mp3')
        rec_info.setStyleSheet('color: #6b7280; font-size: 11px;')
        rec_layout.addWidget(rec_info)
        
        rec_buttons_layout = QHBoxLayout()
        self.rec_start_btn = QPushButton('🔴 Start Recording')
        self.rec_start_btn.clicked.connect(self.start_recording)
        self.rec_start_btn.setEnabled(False)
        self.rec_start_btn.setStyleSheet('background: #dc2626; color: white; padding: 6px; font-weight: bold;')
        rec_buttons_layout.addWidget(self.rec_start_btn)
        
        self.rec_stop_btn = QPushButton('⏹️ Stop Recording')
        self.rec_stop_btn.clicked.connect(self.stop_recording)
        self.rec_stop_btn.setEnabled(False)
        self.rec_stop_btn.setStyleSheet('background: #6b7280; color: white; padding: 6px; font-weight: bold;')
        rec_buttons_layout.addWidget(self.rec_stop_btn)
        
        rec_layout.addLayout(rec_buttons_layout)
        
        # Open folder button
        self.open_folder_btn = QPushButton('📁 Open Recordings Folder')
        self.open_folder_btn.clicked.connect(self.open_recordings_folder)
        self.open_folder_btn.setStyleSheet('background: #3b82f6; color: white; padding: 6px; margin-top: 3px;')
        rec_layout.addWidget(self.open_folder_btn)
        
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        # Log
        log_group = QGroupBox('📋 Log')
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('background: #1f2937; color: #10b981; font-family: Courier; font-size: 11px;')
        self.log_text.setMaximumHeight(120)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Cafecito donation link
        cafecito = QLabel('If you found this useful, <a href="https://cafecito.app/lu2met" style="color: #f59e0b; text-decoration: none; font-weight: bold;">☕ buy me a coffee</a>')
        cafecito.setOpenExternalLinks(True)
        cafecito.setAlignment(Qt.AlignCenter)
        cafecito.setStyleSheet('color: #6b7280; font-size: 13px; padding: 6px;')
        cafecito.setTextFormat(Qt.RichText)
        cafecito.setToolTip('Si te resultó útil, invitame un cafecito')
        layout.addWidget(cafecito)
        
        # Footer with repository link (smaller)
        footer = QLabel('Based on NovaSDR NR filter | '
                       '<a href="https://github.com/tomduca/novasdr-audio-processor" style="color: #3b82f6; text-decoration: none;">GitHub</a>')
        footer.setOpenExternalLinks(True)
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet('color: #6b7280; font-size: 9px; padding: 2px;')
        footer.setTextFormat(Qt.RichText)
        layout.addWidget(footer)
        
        # Initial log
        self.add_log(f"NovaSDR module: {'✓ Available' if NOVASDR_AVAILABLE else '✗ Not available'}")
        self.add_log(f"MP3 recording: {'✓ Available' if MP3_AVAILABLE else '✗ Not available (will use WAV)'}")
    
    def load_devices(self):
        devices = sd.query_devices()
        
        for idx, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                self.input_combo.addItem(f"{idx}: {device['name']}", idx)
                if 'BlackHole' in device['name'] or 'Loopback' in device['name']:
                    self.input_combo.setCurrentIndex(self.input_combo.count() - 1)
            
            if device['max_output_channels'] > 0:
                self.output_combo.addItem(f"{idx}: {device['name']}", idx)
        
        self.add_log(f"Loaded {self.input_combo.count()} input and {self.output_combo.count()} output devices")
    
    def update_preset_info(self):
        mode = 'CW' if self.cw_radio.isChecked() else 'SSB'
        presets = PRESETS_CW if mode == 'CW' else PRESETS_SSB
        
        for button in self.preset_group.buttons():
            if button.isChecked():
                preset_name = button.text().lower().replace(' ⭐', '')
                preset = presets[preset_name]
                gain = int(1 / preset['gain'])
                info = f"Gain: 1/{gain}, Alpha: {preset['alpha']}, ASNR: {preset['asnr']} dB, Post-Gain: {preset['post_gain']}x"
                self.preset_info.setText(info)
                break
    
    def on_mode_change(self):
        mode = 'CW' if self.cw_radio.isChecked() else 'SSB'
        if self.processor.running:
            self.processor.set_mode(mode)
        self.update_preset_info()
    
    def on_preset_change(self, preset):
        if self.processor.running:
            self.processor.set_preset(preset)
        self.update_preset_info()
    
    def on_gain_change(self, value):
        gain = value / 100.0
        self.processor.input_gain = gain
        self.gain_value_label.setText(f'{value}%')
        if self.processor.running:
            self.add_log(f"Input gain: {value}%")
    
    def on_volume_change(self, value):
        # Logarithmic volume scaling for better control
        # Maps slider range (10-400) to logarithmic volume curve
        # Formula: volume = 10^((value/100 - 1) * 2)
        # This gives smooth control at low volumes and proper boost at high volumes
        linear_percent = value / 100.0
        
        if value <= 100:
            # Below 100%: logarithmic attenuation (10% to 100%)
            # Maps 10-100 slider to 0.1-1.0 volume logarithmically
            log_volume = 10 ** ((linear_percent - 1) * 2)
        else:
            # Above 100%: logarithmic boost (100% to 400%)
            # Maps 100-400 slider to 1.0-4.0 volume logarithmically
            log_volume = 10 ** ((linear_percent - 1) * 0.6)
        
        self.processor.output_volume = log_volume
        self.volume_value_label.setText(f'{value}%')
        if self.processor.running:
            self.add_log(f"Output volume: {value}% (actual: {log_volume:.2f}x)")
    
    def on_bypass_change(self, state):
        self.processor.bypass = (state == Qt.Checked)
        status = "BYPASSED" if self.processor.bypass else "ACTIVE"
        self.add_log(f"Processing {status}")
    
    def start_processing(self):
        input_idx = self.input_combo.currentData()
        output_idx = self.output_combo.currentData()
        
        mode = 'CW' if self.cw_radio.isChecked() else 'SSB'
        
        for button in self.preset_group.buttons():
            if button.isChecked():
                preset = button.text().lower().replace(' ⭐', '')
                break
        
        try:
            self.processor.start_processing(input_idx, output_idx, preset, mode)
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.rec_start_btn.setEnabled(True)
            self.status_label.setText('● Running')
            self.status_label.setStyleSheet('color: #10b981; font-size: 14px; padding: 5px;')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to start: {str(e)}')
            self.add_log(f"ERROR: {str(e)}")
    
    def stop_processing(self):
        self.processor.stop_processing()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.rec_start_btn.setEnabled(False)
        self.rec_stop_btn.setEnabled(False)
        self.status_label.setText('● Stopped')
        self.status_label.setStyleSheet('color: #ef4444; font-size: 14px; padding: 5px;')
    
    def start_recording(self):
        self.processor.start_recording()
        self.rec_start_btn.setEnabled(False)
        self.rec_stop_btn.setEnabled(True)
        self.rec_stop_btn.setStyleSheet('background: #dc2626; color: white; padding: 6px; font-weight: bold;')  # Red when active
    
    def stop_recording(self):
        self.processor.stop_recording()
        self.rec_start_btn.setEnabled(True)
        self.rec_stop_btn.setEnabled(False)
        self.rec_stop_btn.setStyleSheet('background: #6b7280; color: white; padding: 6px; font-weight: bold;')  # Gray when disabled
    
    def open_recordings_folder(self):
        """Open the recordings folder in file explorer"""
        import subprocess
        import platform
        
        recordings_dir = Path(__file__).parent / 'recordings'
        recordings_dir.mkdir(exist_ok=True)
        
        try:
            system = platform.system()
            if system == 'Windows':
                subprocess.run(['explorer', str(recordings_dir)])
            elif system == 'Darwin':  # macOS
                subprocess.run(['open', str(recordings_dir)])
            else:  # Linux
                subprocess.run(['xdg-open', str(recordings_dir)])
            self.add_log(f"📁 Opened: {recordings_dir}")
        except Exception as e:
            self.add_log(f"❌ Error opening folder: {e}")
    
    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        if self.processor.running:
            self.processor.stop_processing()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    gui = NovaSDRGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
