#!/usr/bin/env python3
"""
NovaSDR Audio Processor - Web Interface
Simple web-based interface for device selection, preset control, and bypass toggle
"""

from flask import Flask, render_template_string, jsonify, request
import threading
import sys
import numpy as np
import sounddevice as sd
from scipy import signal
import time
import wave
import os
from datetime import datetime
from pathlib import Path
try:
    from pydub import AudioSegment
    MP3_AVAILABLE = True
except ImportError:
    MP3_AVAILABLE = False

try:
    import novasdr_nr as novasdr_nr_py
    NOVASDR_AVAILABLE = True
except ImportError:
    NOVASDR_AVAILABLE = False

app = Flask(__name__)

# Global state
processor_state = {
    'running': False,
    'bypass': False,
    'preset': 'extreme',
    'mode': 'SSB',  # SSB or CW
    'input_device': None,
    'output_device': None,
    'stream': None,
    'novasdr_nr': None,
    'post_gain': 14.0,
    'logs': [],
    'recording': False,
    'recording_file': None,
    'recording_data': [],
    'bandpass_filter': None,
    'zi_bandpass': None
}

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

# Presets for CW mode (more aggressive, optimized for narrow bandwidth)
PRESETS_CW = {
    'moderate': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 15.0, 'post_gain': 3.0},
    'aggressive': {'gain': 1.0/4096.0, 'alpha': 0.99, 'asnr': 8.0, 'post_gain': 5.0},
    'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 3.0, 'post_gain': 12.0},
    'extreme': {'gain': 1.0/16384.0, 'alpha': 0.995, 'asnr': 1.0, 'post_gain': 18.0}
}

# Bandpass filter configurations
BANDPASS_CONFIG = {
    'SSB': {'low': 300, 'high': 2700},   # Standard SSB bandwidth
    'CW': {'low': 600, 'high': 900}      # Narrow CW filter (300 Hz centered at 750 Hz)
}

def log(message):
    """Add log message with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    processor_state['logs'].append(log_entry)
    print(log_entry)

def create_bandpass_filter(mode):
    """Create bandpass filter based on mode (SSB or CW)"""
    config = BANDPASS_CONFIG[mode]
    low_freq = config['low']
    high_freq = config['high']
    
    # Design Butterworth bandpass filter
    nyquist = SAMPLE_RATE / 2
    low_normalized = low_freq / nyquist
    high_normalized = high_freq / nyquist
    
    sos = signal.butter(4, [low_normalized, high_normalized], btype='band', output='sos')
    zi = signal.sosfilt_zi(sos)
    
    return sos, zi

def audio_callback(indata, outdata, frames, time_info, status):
    """Real-time audio processing callback"""
    if status:
        log(f"Audio status: {status}")
    
    audio_data = indata[:, 0].copy()
    
    if processor_state['bypass'] or not NOVASDR_AVAILABLE:
        filtered_audio = audio_data
    else:
        # Apply bandpass filter first
        if processor_state['bandpass_filter'] is not None:
            filtered_audio, processor_state['zi_bandpass'] = signal.sosfilt(
                processor_state['bandpass_filter'], 
                audio_data, 
                zi=processor_state['zi_bandpass']
            )
        else:
            filtered_audio = audio_data
        
        # Apply NovaSDR noise reduction
        filtered_audio = processor_state['novasdr_nr'].process(filtered_audio.astype(np.float32))
        filtered_audio = filtered_audio * processor_state['post_gain']
    
    filtered_audio = np.clip(filtered_audio, -0.95, 0.95)
    
    # Record audio if recording is active
    if processor_state['recording']:
        processor_state['recording_data'].append(filtered_audio.copy())
    
    outdata[:, 0] = filtered_audio
    if outdata.shape[1] > 1:
        outdata[:, 1] = filtered_audio

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>NovaSDR Audio Processor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .status {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        .status.running { background: #10b981; }
        .status.stopped { background: #ef4444; }
        .content { padding: 30px; }
        .section {
            background: #f9fafb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h2 {
            font-size: 18px;
            margin-bottom: 15px;
            color: #374151;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #4b5563;
        }
        select, input[type="checkbox"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            font-size: 14px;
        }
        select:focus {
            outline: none;
            border-color: #667eea;
        }
        .presets {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .preset-btn {
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s;
        }
        .preset-btn:hover { border-color: #667eea; }
        .preset-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        .preset-info {
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 6px;
            font-size: 12px;
            color: #6b7280;
        }
        .mode-btn {
            flex: 1;
            padding: 12px;
            border: 2px solid #e5e7eb;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        .mode-btn:hover {
            border-color: #10b981;
            background: #f9fafb;
        }
        .mode-btn.active {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border-color: #10b981;
            transform: scale(1.05);
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .checkbox-group input[type="checkbox"] {
            width: auto;
        }
        .buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-start {
            background: #10b981;
            color: white;
        }
        .btn-start:hover { background: #059669; }
        .btn-start:disabled {
            background: #d1d5db;
            cursor: not-allowed;
        }
        .btn-stop {
            background: #ef4444;
            color: white;
        }
        .btn-stop:hover { background: #dc2626; }
        .btn-stop:disabled {
            background: #d1d5db;
            cursor: not-allowed;
        }
        .btn-rec {
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
            color: white;
        }
        .btn-rec:hover:not(:disabled) { opacity: 0.9; }
        .btn-rec:disabled {
            background: #d1d5db !important;
            cursor: not-allowed;
        }
        input[type="text"] {
            width: 100%;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .log {
            background: #1f2937;
            color: #10b981;
            padding: 15px;
            border-radius: 6px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }
        .log::-webkit-scrollbar { width: 8px; }
        .log::-webkit-scrollbar-track { background: #374151; }
        .log::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📻 NovaSDR Audio Processor</h1>
            <div class="status" id="status">● Stopped</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>🎧 Audio Devices</h2>
                <div class="form-group">
                    <label>Input Device</label>
                    <select id="input-device"></select>
                </div>
                <div class="form-group">
                    <label>Output Device</label>
                    <select id="output-device"></select>
                </div>
            </div>
            
            <div class="section">
                <h2>📡 Mode</h2>
                <div class="presets">
                    <button class="mode-btn active" data-mode="SSB">SSB (300-2700 Hz)</button>
                    <button class="mode-btn" data-mode="CW">CW (600-900 Hz)</button>
                </div>
            </div>
            
            <div class="section">
                <h2>🎛️ Noise Reduction Preset</h2>
                <div class="presets">
                    <button class="preset-btn" data-preset="moderate">Moderate</button>
                    <button class="preset-btn" data-preset="aggressive">Aggressive</button>
                    <button class="preset-btn" data-preset="ultra">Ultra</button>
                    <button class="preset-btn active" data-preset="extreme">Extreme ⭐</button>
                </div>
                <div class="preset-info" id="preset-info"></div>
            </div>
            
            <div class="section">
                <h2>⚙️ Processing Control</h2>
                <div class="checkbox-group">
                    <input type="checkbox" id="bypass">
                    <label for="bypass" style="margin: 0;">Bypass (Pass-through audio without processing)</label>
                </div>
            </div>
            
            <div class="buttons">
                <button class="btn-start" id="start-btn">▶ Start</button>
                <button class="btn-stop" id="stop-btn" disabled>■ Stop</button>
            </div>
            
            <div class="section">
                <h2>🔴 Recording</h2>
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 15px;">
                    Recordings will be saved as: recording_YYYYMMDD_HHMMSS.mp3 (128kbps)
                </p>
                <div class="buttons">
                    <button class="btn-rec" id="rec-start-btn" disabled style="background: #dc2626; flex: 1;">🔴 Start Recording</button>
                    <button class="btn-rec" id="rec-stop-btn" disabled style="background: #6b7280; flex: 1;">⏹️ Stop Recording</button>
                </div>
            <div class="section">
                <h2>📋 Log</h2>
                <div class="log" id="log"></div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: white; font-size: 12px; opacity: 0.8;">
                <p>NovaSDR Audio Processor</p>
                <p>Based on <a href="https://github.com/Steven9101/novasdr-wasm" target="_blank" style="color: #86efac; text-decoration: none;">NovaSDR-WASM</a></p>
                <p style="margin-top: 10px;">
                    <a href="https://github.com/tomduca/novasdr-audio-processor" target="_blank" style="color: #86efac; text-decoration: none;">
                        📻 View on GitHub
                    </a>
                </p>
            </div>
        </div>
    </div>
    
    <script>
        const presetsSSB = {{ presets_ssb|tojson }};
        const presetsCW = {{ presets_cw|tojson }};
        let currentPreset = 'extreme';
        let currentMode = 'SSB';
        
        // Load devices
        fetch('/api/devices')
            .then(r => r.json())
            .then(data => {
                const inputSelect = document.getElementById('input-device');
                const outputSelect = document.getElementById('output-device');
                
                data.input.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.index;
                    opt.textContent = d.name;
                    inputSelect.appendChild(opt);
                    
                    // Auto-select BlackHole or Loopback
                    if (d.name.includes('BlackHole') || d.name.includes('Loopback')) {
                        inputSelect.value = d.index;
                    }
                });
                
                data.output.forEach(d => {
                    const opt = document.createElement('option');
                    opt.value = d.index;
                    opt.textContent = d.name;
                    outputSelect.appendChild(opt);
                });
            });
        
        // Update preset info
        function updatePresetInfo() {
            const presets = currentMode === 'CW' ? presetsCW : presetsSSB;
            const preset = presets[currentPreset];
            const gain = Math.round(1 / preset.gain);
            document.getElementById('preset-info').textContent = 
                `Gain: 1/${gain}, Alpha: ${preset.alpha}, ASNR: ${preset.asnr} dB, Post-Gain: ${preset.post_gain}x`;
        }
        updatePresetInfo();
        
        // Mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentMode = btn.dataset.mode;
                updatePresetInfo();
                
                fetch('/api/mode', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({mode: currentMode})
                });
            });
        });
        
        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentPreset = btn.dataset.preset;
                updatePresetInfo();
                
                fetch('/api/preset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({preset: currentPreset})
                });
            });
        });
        
        // Bypass toggle
        document.getElementById('bypass').addEventListener('change', (e) => {
            fetch('/api/bypass', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({bypass: e.target.checked})
            });
        });
        
        // Start button
        document.getElementById('start-btn').addEventListener('click', () => {
            const input = document.getElementById('input-device').value;
            const output = document.getElementById('output-device').value;
            
            fetch('/api/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    input: parseInt(input),
                    output: parseInt(output),
                    preset: currentPreset
                })
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                    document.getElementById('status').textContent = '● Running';
                    document.getElementById('status').className = 'status running';
                }
            });
        });
        
        // Stop button
        document.getElementById('stop-btn').addEventListener('click', () => {
            fetch('/api/stop', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    document.getElementById('start-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    document.getElementById('rec-start-btn').disabled = true;
                    document.getElementById('status').textContent = '● Stopped';
                    document.getElementById('status').className = 'status stopped';
                });
        });
        
        // Recording start button
        document.getElementById('rec-start-btn').addEventListener('click', () => {
            fetch('/api/recording/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    document.getElementById('rec-start-btn').disabled = true;
                    document.getElementById('rec-stop-btn').disabled = false;
                    document.getElementById('rec-status').style.display = 'block';
                    document.getElementById('rec-status').innerHTML = '🔴 <strong>Recording...</strong>';
                }
            });
        });
        
        // Recording stop button
        document.getElementById('rec-stop-btn').addEventListener('click', () => {
            fetch('/api/recording/stop', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    document.getElementById('rec-start-btn').disabled = false;
                    document.getElementById('rec-stop-btn').disabled = true;
                    if (data.success) {
                        document.getElementById('rec-status').innerHTML = 
                            '✅ <strong>Saved:</strong> ' + data.filename + ' (' + data.duration.toFixed(1) + 's)';
                    }
                });
        });
        
        // Enable recording button when processing starts
        const originalStartHandler = document.getElementById('start-btn').onclick;
        document.getElementById('start-btn').addEventListener('click', () => {
            setTimeout(() => {
                document.getElementById('rec-start-btn').disabled = false;
            }, 500);
        });
        
        // Update logs
        setInterval(() => {
            fetch('/api/logs')
                .then(r => r.json())
                .then(data => {
                    const logDiv = document.getElementById('log');
                    logDiv.textContent = data.logs.join('\\n');
                    logDiv.scrollTop = logDiv.scrollHeight;
                });
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, presets_ssb=PRESETS_SSB, presets_cw=PRESETS_CW)

@app.route('/api/devices')
def get_devices():
    devices = sd.query_devices()
    input_devices = []
    output_devices = []
    
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append({'index': idx, 'name': f"{idx}: {device['name']}"})
        if device['max_output_channels'] > 0:
            output_devices.append({'index': idx, 'name': f"{idx}: {device['name']}"})
    
    log(f"Loaded {len(input_devices)} input and {len(output_devices)} output devices")
    return jsonify({'input': input_devices, 'output': output_devices})

@app.route('/api/preset', methods=['POST'])
def set_preset():
    data = request.json
    preset_name = data['preset']
    
    # Get presets based on current mode
    presets = PRESETS_CW if processor_state['mode'] == 'CW' else PRESETS_SSB
    
    if preset_name not in presets:
        return jsonify({'success': False, 'error': 'Invalid preset'})
    
    processor_state['preset'] = preset_name
    
    if processor_state['novasdr_nr'] and NOVASDR_AVAILABLE:
        preset = presets[preset_name]
        processor_state['novasdr_nr'] = novasdr_nr_py.SpectralNoiseReduction(
            SAMPLE_RATE,
            preset['gain'],
            preset['alpha'],
            preset['asnr']
        )
        processor_state['post_gain'] = preset['post_gain']
        log(f"Preset changed to {preset_name} ({processor_state['mode']} mode)")
    
    return jsonify({'success': True})

@app.route('/api/bypass', methods=['POST'])
def set_bypass():
    data = request.json
    processor_state['bypass'] = data['bypass']
    status = "BYPASSED" if data['bypass'] else "ACTIVE"
    log(f"Processing {status}")
    return jsonify({'success': True})

@app.route('/api/mode', methods=['POST'])
def set_mode():
    data = request.json
    mode = data['mode']
    
    if mode not in ['SSB', 'CW']:
        return jsonify({'success': False, 'error': 'Invalid mode'})
    
    processor_state['mode'] = mode
    
    # Update bandpass filter
    processor_state['bandpass_filter'], processor_state['zi_bandpass'] = create_bandpass_filter(mode)
    
    # Update NovaSDR parameters based on mode and current preset
    presets = PRESETS_CW if mode == 'CW' else PRESETS_SSB
    preset = presets[processor_state['preset']]
    
    if processor_state['novasdr_nr'] and NOVASDR_AVAILABLE:
        processor_state['novasdr_nr'] = novasdr_nr_py.SpectralNoiseReduction(
            SAMPLE_RATE,
            preset['gain'],
            preset['alpha'],
            preset['asnr']
        )
        processor_state['post_gain'] = preset['post_gain']
    
    config = BANDPASS_CONFIG[mode]
    log(f"Mode changed to {mode} (BW: {config['low']}-{config['high']} Hz)")
    return jsonify({'success': True})

@app.route('/api/start', methods=['POST'])
def start_processing():
    data = request.json
    
    try:
        processor_state['input_device'] = data['input']
        processor_state['output_device'] = data['output']
        processor_state['preset'] = data['preset']
        
        # Initialize bandpass filter based on current mode
        processor_state['bandpass_filter'], processor_state['zi_bandpass'] = create_bandpass_filter(processor_state['mode'])
        
        # Initialize NovaSDR filter with mode-specific presets
        if NOVASDR_AVAILABLE:
            presets = PRESETS_CW if processor_state['mode'] == 'CW' else PRESETS_SSB
            preset = presets[data['preset']]
            processor_state['novasdr_nr'] = novasdr_nr_py.SpectralNoiseReduction(
                SAMPLE_RATE,
                preset['gain'],
                preset['alpha'],
                preset['asnr']
            )
            processor_state['post_gain'] = preset['post_gain']
            log(f"✓ NovaSDR initialized: {data['preset']} preset")
        
        processor_state['stream'] = sd.Stream(
            device=(data['input'], data['output']),
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=2,
            callback=audio_callback,
            latency='low'
        )
        
        processor_state['stream'].start()
        processor_state['running'] = True
        processor_state['input_device'] = data['input']
        processor_state['output_device'] = data['output']
        
        log(f"✓ Audio processing started")
        log(f"  Preset: {data['preset']}")
        log(f"  Latency: ~{(BLOCK_SIZE / SAMPLE_RATE) * 1000:.1f}ms")
        
        return jsonify({'success': True})
    except Exception as e:
        log(f"ERROR: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_processing():
    if processor_state['stream']:
        processor_state['stream'].stop()
        processor_state['stream'].close()
        processor_state['stream'] = None
    
    processor_state['running'] = False
    log("✓ Audio processing stopped")
    
    return jsonify({'success': True})

@app.route('/api/logs')
def get_logs():
    return jsonify({'logs': processor_state['logs']})

@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    if not processor_state['running']:
        return jsonify({'success': False, 'error': 'Audio processing not running'})
    
    if processor_state['recording']:
        return jsonify({'success': False, 'error': 'Already recording'})
    
    # Start recording
    processor_state['recording'] = True
    processor_state['recording_data'] = []
    
    log(f"🔴 Recording started")
    return jsonify({'success': True})

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    if not processor_state['recording']:
        return jsonify({'success': False, 'error': 'Not recording'})
    
    processor_state['recording'] = False
    
    # Create recordings directory
    recordings_dir = Path(__file__).parent / 'recordings'
    recordings_dir.mkdir(exist_ok=True)
    
    # Generate filename with date/time
    now = datetime.now()
    
    # Concatenate all recorded chunks
    if processor_state['recording_data']:
        audio_data = np.concatenate(processor_state['recording_data'])
        duration = len(audio_data) / SAMPLE_RATE
        
        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        if MP3_AVAILABLE:
            # Save as MP3 (compressed)
            filename = f"recording_{now.strftime('%Y%m%d_%H%M%S')}.mp3"
            filepath = recordings_dir / filename
            
            # Create temporary WAV in memory
            temp_wav = recordings_dir / f"temp_{now.strftime('%Y%m%d_%H%M%S')}.wav"
            with wave.open(str(temp_wav), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
            
            # Convert to MP3
            audio = AudioSegment.from_wav(str(temp_wav))
            audio.export(str(filepath), format='mp3', bitrate='128k')
            
            # Remove temp WAV
            temp_wav.unlink()
            
            log(f"⏹️ Recording stopped - Saved: {filename} ({duration:.1f}s, MP3 128kbps)")
        else:
            # Fallback to WAV if pydub not available
            filename = f"recording_{now.strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = recordings_dir / filename
            
            with wave.open(str(filepath), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_int16.tobytes())
            
            log(f"⏹️ Recording stopped - Saved: {filename} ({duration:.1f}s, WAV)")
        
        # Clear recording data
        processor_state['recording_data'] = []
        
        return jsonify({'success': True, 'filename': filename, 'duration': duration})
    else:
        log("⏹️ Recording stopped - No data recorded")
        return jsonify({'success': False, 'error': 'No data recorded'})

@app.route('/api/recording/status')
def recording_status():
    return jsonify({
        'recording': processor_state['recording']
    })

if __name__ == '__main__':
    log("NovaSDR Audio Processor Web Interface")
    log(f"NovaSDR module: {'✓ Available' if NOVASDR_AVAILABLE else '✗ Not available'}")
    print("\n" + "="*50)
    print("Open your browser at: http://localhost:5001")
    print("="*50 + "\n")
    app.run(debug=False, host='0.0.0.0', port=5001)
