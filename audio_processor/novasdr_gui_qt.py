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

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QPushButton, 
                             QTextEdit, QRadioButton, QButtonGroup, QCheckBox,
                             QGroupBox, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

try:
    import novasdr_nr as novasdr_nr_py
    NOVASDR_AVAILABLE = True
    print(f"✓ NovaSDR module loaded from: {novasdr_nr_py.__file__}")
except ImportError as e:
    NOVASDR_AVAILABLE = False
    print(f"✗ NovaSDR module not available: {e}")
except Exception as e:
    NOVASDR_AVAILABLE = False
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
        self.bandpass_filter = None
        self.zi_bandpass = None
        self.recording_data = []
        
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
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        
        audio_data = indata[:, 0].copy()
        
        if self.bypass or not NOVASDR_AVAILABLE or self.novasdr_nr is None:
            filtered_audio = audio_data
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
            except Exception as e:
                print(f"✗ Audio processing error: {e}")
                filtered_audio = audio_data
        
        filtered_audio = np.clip(filtered_audio, -0.95, 0.95)
        
        if self.recording:
            self.recording_data.append(filtered_audio.copy())
        
        outdata[:, 0] = filtered_audio
        if outdata.shape[1] > 1:
            outdata[:, 1] = filtered_audio
    
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
                print(f"✓ NovaSDR filter initialized: {preset} mode {mode}")
            except Exception as e:
                print(f"✗ Failed to initialize NovaSDR: {e}")
                import traceback
                traceback.print_exc()
                self.log_signal.emit(f"ERROR: Failed to initialize NovaSDR: {e}")
        else:
            self.log_signal.emit("WARNING: NovaSDR module not available - running in bypass mode")
        
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
        
        recordings_dir = Path(__file__).parent / 'recordings'
        recordings_dir.mkdir(exist_ok=True)
        
        now = datetime.now()
        audio_data = np.concatenate(self.recording_data)
        duration = len(audio_data) / SAMPLE_RATE
        
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
        self.log_signal.emit(f"⏹️ Recording stopped - Saved: {filename} ({duration:.1f}s)")
        return filename, duration


class NovaSDRGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = AudioProcessor()
        self.processor.log_signal.connect(self.add_log)
        self.init_ui()
        self.load_devices()
        
    def init_ui(self):
        self.setWindowTitle('NovaSDR Audio Processor')
        self.setGeometry(100, 100, 700, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel('📻 NovaSDR Audio Processor')
        header.setFont(QFont('Arial', 18, QFont.Bold))
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
        
        self.bypass_check = QCheckBox('Bypass (pass-through)')
        self.bypass_check.stateChanged.connect(self.on_bypass_change)
        control_layout.addWidget(self.bypass_check)
        
        buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton('▶ Start')
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setStyleSheet('background: #10b981; color: white; padding: 10px; font-weight: bold;')
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton('■ Stop')
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet('background: #ef4444; color: white; padding: 10px; font-weight: bold;')
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
        self.rec_start_btn.setStyleSheet('background: #dc2626; color: white; padding: 8px;')
        rec_buttons_layout.addWidget(self.rec_start_btn)
        
        self.rec_stop_btn = QPushButton('⏹️ Stop Recording')
        self.rec_stop_btn.clicked.connect(self.stop_recording)
        self.rec_stop_btn.setEnabled(False)
        self.rec_stop_btn.setStyleSheet('background: #6b7280; color: white; padding: 8px;')
        rec_buttons_layout.addWidget(self.rec_stop_btn)
        
        rec_layout.addLayout(rec_buttons_layout)
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        # Log
        log_group = QGroupBox('📋 Log')
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('background: #1f2937; color: #10b981; font-family: Courier;')
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Footer
        footer = QLabel('NovaSDR Audio Processor\nBased on NovaSDR-WASM')
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet('color: #6b7280; font-size: 10px; padding: 10px;')
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
    
    def stop_recording(self):
        self.processor.stop_recording()
        self.rec_start_btn.setEnabled(True)
        self.rec_stop_btn.setEnabled(False)
    
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
