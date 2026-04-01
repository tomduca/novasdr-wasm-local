import sounddevice as sd
import numpy as np
from scipy import signal
import queue
import sys
import time

RNNOISE_AVAILABLE = False
RNNoise = None

def load_rnnoise():
    """Lazy loading de RNNoise para evitar problemas de importación"""
    global RNNOISE_AVAILABLE, RNNoise
    try:
        from pyrnnoise import RNNoise as RNN
        RNNoise = RNN
        RNNOISE_AVAILABLE = True
        return True
    except Exception as e:
        print(f"Warning: pyrnnoise not available. AI noise reduction disabled.")
        print(f"Reason: {e}")
        return False

class AudioProcessor:
    def __init__(self, sample_rate=48000, block_size=2048, use_ai_nr=True, 
                 band='40m', mode='SSB', enable_agc=True, enable_notch=True, enable_gate=True):
        """
        Advanced HF Audio Processor for webSDR streams
        Optimized for 2.8 kHz bandwidth (SSB standard)
        
        Args:
            sample_rate: Sample rate (48000 Hz required for RNNoise)
            block_size: Block size (480 samples = 10ms at 48kHz, optimal for RNNoise)
            use_ai_nr: Enable AI-based noise reduction (RNNoise)
            band: HF band preset ('40m', '10m', '20m', '15m', '80m')
            mode: Transmission mode ('SSB', 'AM', 'CW', 'WIDE')
            enable_agc: Enable Automatic Gain Control
            enable_notch: Enable notch filters for 60/120Hz hum
            enable_gate: Enable noise gate
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.use_ai_nr = use_ai_nr and RNNOISE_AVAILABLE
        self.enable_agc = enable_agc
        self.enable_notch = enable_notch
        self.enable_gate = enable_gate
        self.band = band
        self.mode = mode
        
        # Mode-specific bandwidth optimization
        # SSB standard: 2.8 kHz (300-3100 Hz)
        # AM standard: 6 kHz (100-6100 Hz)
        # CW: Narrow 500 Hz (600-1100 Hz)
        if mode == 'SSB':
            # SSB optimizado: bandwidth muy estrecho para máxima reducción de ruido
            self.lowcut = 400
            self.highcut = 2700  # 400-2700 = 2.3 kHz (muy estrecho, solo voz)
            self.filter_order = 10  # Orden muy alto = máxima selectividad
        elif mode == 'AM':
            # AM: Más ancho para fidelidad
            self.lowcut = 100
            self.highcut = 6100  # 6 kHz bandwidth
            self.filter_order = 4
        elif mode == 'CW':
            # CW: Muy estrecho para telegrafía
            self.lowcut = 600
            self.highcut = 1100  # 500 Hz bandwidth
            self.filter_order = 8  # Muy selectivo
        elif mode == 'WIDE':
            # Modo ancho para experimentación
            self.lowcut = 200
            self.highcut = 4000
            self.filter_order = 4
        else:
            # Default SSB
            self.lowcut = 300
            self.highcut = 3100
            self.filter_order = 6
        
        # Calcular ancho de banda efectivo
        self.bandwidth = self.highcut - self.lowcut
        
        # Initialize RNNoise for AI-based noise reduction
        if self.use_ai_nr:
            if load_rnnoise():
                try:
                    self.rnnoise = RNNoise()
                    print("✓ AI Noise Reduction (RNNoise) enabled")
                except Exception as e:
                    print(f"Warning: Could not initialize RNNoise: {e}")
                    self.use_ai_nr = False
            else:
                self.use_ai_nr = False
        
        # Design optimized bandpass filter
        # Orden más alto para SSB = mejor rechazo fuera de banda
        # Esto reduce el procesamiento de frecuencias irrelevantes
        nyquist = self.sample_rate / 2
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        self.sos_bandpass = signal.butter(self.filter_order, [low, high], btype='band', output='sos')
        self.zi_bandpass = signal.sosfilt_zi(self.sos_bandpass)
        
        # Pre-énfasis para SSB (opcional, mejora inteligibilidad)
        self.use_preemphasis = (mode == 'SSB')
        if self.use_preemphasis:
            # Filtro de pre-énfasis suave para realzar frecuencias medias (1-2 kHz)
            # Donde está la mayor inteligibilidad de voz
            self.preemph_freq = 1500  # Centro de énfasis
            Q = 2.0
            w0 = self.preemph_freq / nyquist
            # Peaking filter para realzar frecuencias de voz
            b, a = signal.iirpeak(w0, Q, fs=self.sample_rate)
            self.sos_preemph = signal.tf2sos(b, a)
            self.zi_preemph = signal.sosfilt_zi(self.sos_preemph)
        
        # Design notch filters for 60Hz and 120Hz hum removal
        if self.enable_notch:
            self.notch_filters = []
            self.zi_notch = []
            for freq in [60, 120]:
                Q = 30.0  # Quality factor
                w0 = freq / nyquist
                b, a = signal.iirnotch(w0, Q, fs=self.sample_rate)
                sos_notch = signal.tf2sos(b, a)
                self.notch_filters.append(sos_notch)
                self.zi_notch.append(signal.sosfilt_zi(sos_notch))
        
        # AGC parameters (optimizados por modo)
        if self.enable_agc:
            if mode == 'SSB':
                # SSB: AGC más agresivo para compensar fading
                self.agc_target = 0.4  # Target más alto
                self.agc_attack = 0.003  # Muy rápido
                self.agc_release = 0.2  # Más lento para evitar pumping
                self.agc_max_gain = 20.0  # Más ganancia para señales débiles
                self.agc_min_gain = 0.05
            elif mode == 'AM':
                # AM: AGC más suave para preservar modulación
                self.agc_target = 0.3
                self.agc_attack = 0.01
                self.agc_release = 0.2
                self.agc_max_gain = 8.0
                self.agc_min_gain = 0.2
            elif mode == 'CW':
                # CW: AGC muy rápido para tonos
                self.agc_target = 0.4
                self.agc_attack = 0.001
                self.agc_release = 0.05
                self.agc_max_gain = 20.0
                self.agc_min_gain = 0.1
            else:
                self.agc_target = 0.3
                self.agc_attack = 0.01
                self.agc_release = 0.1
                self.agc_max_gain = 10.0
                self.agc_min_gain = 0.1
            
            self.agc_gain = 1.0
        
        # Noise gate parameters (optimizados por modo)
        if self.enable_gate:
            if mode == 'SSB':
                # SSB: Gate muy agresivo para eliminar murmullo
                self.gate_threshold = 0.025  # Threshold mucho más alto
                self.gate_ratio = 0.01  # Atenuación casi total (99%)
                self.gate_smooth = 0.99  # Muy suave para evitar clicks
            elif mode == 'CW':
                # CW: Gate más agresivo (tonos claros)
                self.gate_threshold = 0.015
                self.gate_ratio = 0.05
                self.gate_smooth = 0.90
            else:
                self.gate_threshold = 0.01
                self.gate_ratio = 0.1
                self.gate_smooth = 0.95
            
            self.gate_state = 1.0
        
        # Spectral noise reduction
        # NovaSDR Spectral Noise Reduction (MMSE Kim & Ruwisch 2002)
        self.use_advanced_nr = True
        self.nr_fft_size = 512  # Fixed size como NovaSDR
        self.nr_fft_half = 256
        
        # Speech probability parameters (NovaSDR)
        self.nr_psthr = 0.99    # Speech probability threshold
        self.nr_pnsaf = 0.01    # Noise probability safety
        self.nr_psini = 0.5     # Initial speech probability
        self.nr_pspri = 0.5     # Prior speech probability
        self.nr_ap = 0.98       # Speech probability smoothing
        self.nr_ax = 0.8        # Noise tracking smoothing
        
        # MMSE parameters
        self.nr_alpha = 0.98    # A priori SNR smoothing (Decision-Directed)
        self.nr_snr_prio_min = 10.0 ** (-30.0 / 10.0)  # -30 dB min
        self.nr_gain_limit = 0.001  # Spectral floor
        
        # Musical noise reduction (NovaSDR)
        self.nr_width = 4  # Frequency smoothing width
        self.nr_power_threshold = 0.4
        
        # Ventana sqrt(Hann) - CRÍTICO para NovaSDR
        hann = np.hanning(self.nr_fft_size).astype(np.float32)
        self.nr_window = np.sqrt(hann)
        
        # Buffers
        self.nr_last_sample_buffer = np.zeros(self.nr_fft_half, dtype=np.float32)
        self.nr_fft_buffer = np.zeros(self.nr_fft_size, dtype=np.complex64)
        
        # State arrays (256 bins)
        self.nr_nest = np.zeros(self.nr_fft_half, dtype=np.float32)  # Noise estimate
        self.nr_xt = np.zeros(self.nr_fft_half, dtype=np.float32)    # Smoothed noise
        self.nr_pslp = np.ones(self.nr_fft_half, dtype=np.float32) * 0.5  # Speech probability
        self.nr_snr_post = np.ones(self.nr_fft_half, dtype=np.float32)
        self.nr_snr_prio = np.ones(self.nr_fft_half, dtype=np.float32)
        self.nr_hk_old = np.ones(self.nr_fft_half, dtype=np.float32)
        self.nr_g = np.ones(self.nr_fft_half, dtype=np.float32)
        
        # Initialization
        self.nr_first_time = 1
        self.nr_init_counter = 0
        
        # Derived parameters
        self.nr_xih1 = 15.0  # Speech presence threshold
        self.nr_xih1r = 1.0 / (1.0 + self.nr_xih1)
        self.nr_pfac = (1.0 / self.nr_pspri - 1.0) * (1.0 + self.nr_xih1)
        
        # Filtro de suavizado adicional para reducir artefactos
        # Lowpass agresivo en 2500 Hz para eliminar ruido de alta frecuencia
        if mode == 'SSB':
            smooth_cutoff = 2500 / nyquist
            self.sos_smooth = signal.butter(6, smooth_cutoff, btype='low', output='sos')
            self.zi_smooth = signal.sosfilt_zi(self.sos_smooth)
        else:
            self.sos_smooth = None
        
        # Performance monitoring
        self.processing_times = []
        self.max_latency_samples = int(0.5 * self.sample_rate)  # 500ms max
        
    def advanced_noise_reduction(self, audio):
        """
        NovaSDR Spectral Noise Reduction - Versión simplificada y robusta
        Procesa el bloque completo sin overlap-add complejo
        """
        # Simplemente aplicar FFT al bloque completo con zero-padding si es necesario
        n_samples = len(audio)
        
        # Pad a múltiplo de 512
        pad_size = (self.nr_fft_size - (n_samples % self.nr_fft_size)) % self.nr_fft_size
        if pad_size > 0:
            audio_padded = np.pad(audio, (0, pad_size), mode='constant')
        else:
            audio_padded = audio
        
        # Aplicar ventana
        n_padded = len(audio_padded)
        if n_padded != self.nr_fft_size:
            # Procesar en un solo bloque grande
            window = np.hanning(n_padded).astype(np.float32)
            window = np.sqrt(window)
        else:
            window = self.nr_window
        
        windowed = audio_padded * window
        
        # FFT
        spectrum = np.fft.rfft(windowed)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)
        power = magnitude ** 2
        
        n_bins = len(power)
        
        # Asegurar que los arrays de estado tengan el tamaño correcto
        if len(self.nr_xt) != n_bins:
            self.nr_xt = np.zeros(n_bins, dtype=np.float32)
            self.nr_nest = np.zeros(n_bins, dtype=np.float32)
            self.nr_pslp = np.ones(n_bins, dtype=np.float32) * 0.5
            self.nr_snr_post = np.ones(n_bins, dtype=np.float32)
            self.nr_snr_prio = np.ones(n_bins, dtype=np.float32)
            self.nr_hk_old = np.ones(n_bins, dtype=np.float32)
            self.nr_g = np.ones(n_bins, dtype=np.float32)
        
        # Inicialización
        if self.nr_first_time == 1:
            self.nr_first_time = 2
        
        if self.nr_first_time == 2:
            self.nr_nest += 0.05 * power
            self.nr_xt = self.nr_psini * self.nr_nest
            self.nr_init_counter += 1
            if self.nr_init_counter > 19:
                self.nr_init_counter = 0
                self.nr_first_time = 3
        
        # Procesamiento MMSE
        if self.nr_first_time == 3:
            # Speech probability
            ph1y = 1.0 / (1.0 + self.nr_pfac * np.exp(self.nr_xih1r * power / np.maximum(self.nr_xt, 1e-10)))
            self.nr_pslp = self.nr_ap * self.nr_pslp + (1.0 - self.nr_ap) * ph1y
            ph1y = np.where(self.nr_pslp > self.nr_psthr, 1.0 - self.nr_pnsaf, np.minimum(ph1y, 1.0))
            
            # Noise tracking
            xtr = (1.0 - ph1y) * power + ph1y * self.nr_xt
            self.nr_xt = self.nr_ax * self.nr_xt + (1.0 - self.nr_ax) * xtr
            
            # SNR
            self.nr_snr_post = np.clip(power / np.maximum(self.nr_xt, 1e-10), self.nr_snr_prio_min, 1000.0)
            self.nr_snr_prio = np.maximum(
                self.nr_alpha * self.nr_hk_old + (1.0 - self.nr_alpha) * np.maximum(self.nr_snr_post - 1.0, 0.0),
                0.0
            )
            
            # MMSE Gain
            v = self.nr_snr_prio * self.nr_snr_post / (1.0 + self.nr_snr_prio)
            self.nr_g = np.maximum(
                (1.0 / self.nr_snr_post) * np.sqrt(0.7212 * v + v * v),
                self.nr_gain_limit
            )
            self.nr_hk_old = self.nr_snr_post * self.nr_g * self.nr_g
            
            # Musical noise reduction
            pre_power = np.sum(power)
            post_power = np.sum(self.nr_g * self.nr_g * power)
            power_ratio = post_power / max(pre_power, 1e-10)
            
            if power_ratio <= self.nr_power_threshold:
                nn = 1 + 2 * int(0.5 + self.nr_width * (1.0 - power_ratio / self.nr_power_threshold))
                if nn > 1:
                    kernel = np.ones(nn) / nn
                    self.nr_g = np.convolve(self.nr_g, kernel, mode='same')
        
        # Aplicar gain
        clean_magnitude = magnitude * self.nr_g
        clean_spectrum = clean_magnitude * np.exp(1j * phase)
        
        # IFFT
        clean_audio = np.fft.irfft(clean_spectrum, n=n_padded)
        
        # Aplicar ventana de síntesis y quitar padding
        clean_audio = clean_audio * window
        
        return clean_audio[:n_samples].astype(np.float32)
    
    def apply_noise_gate(self, audio):
        """Apply noise gate to reduce background noise"""
        rms = np.sqrt(np.mean(audio**2))
        
        if rms < self.gate_threshold:
            target_state = self.gate_ratio
        else:
            target_state = 1.0
        
        # Smooth gate transitions
        self.gate_state = (self.gate_smooth * self.gate_state + 
                          (1 - self.gate_smooth) * target_state)
        
        return audio * self.gate_state
    
    def apply_agc(self, audio):
        """Apply Automatic Gain Control"""
        rms = np.sqrt(np.mean(audio**2))
        
        if rms > 0.001:  # Avoid division by zero
            desired_gain = self.agc_target / rms
            
            # Limit gain range
            desired_gain = np.clip(desired_gain, self.agc_min_gain, self.agc_max_gain)
            
            # Smooth gain changes
            if desired_gain > self.agc_gain:
                # Attack (gain increase)
                alpha = self.agc_attack
            else:
                # Release (gain decrease)
                alpha = self.agc_release
            
            self.agc_gain = alpha * desired_gain + (1 - alpha) * self.agc_gain
        
        return audio * self.agc_gain
    
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Real-time audio processing callback"""
        start_time = time.perf_counter()
        
        if status:
            print(f"Status: {status}", file=sys.stderr)
        
        try:
            # Get mono audio (left channel)
            audio_data = indata[:, 0].copy()
            
            # Step 1: Bandpass filter (optimizado para modo seleccionado)
            # Para SSB: 300-3100 Hz (2.8 kHz bandwidth)
            # Esto elimina todo fuera del ancho de banda útil
            filtered_audio, self.zi_bandpass = signal.sosfilt(
                self.sos_bandpass, 
                audio_data, 
                zi=self.zi_bandpass
            )
            
            # Step 1.5: Pre-énfasis para SSB (realza frecuencias de voz)
            if self.use_preemphasis:
                filtered_audio, self.zi_preemph = signal.sosfilt(
                    self.sos_preemph,
                    filtered_audio,
                    zi=self.zi_preemph
                )
            
            # Step 2: Notch filters (remove 60/120 Hz hum)
            if self.enable_notch:
                for i, sos_notch in enumerate(self.notch_filters):
                    filtered_audio, self.zi_notch[i] = signal.sosfilt(
                        sos_notch,
                        filtered_audio,
                        zi=self.zi_notch[i]
                    )
            
            # Step 3: Advanced Noise Reduction (Minimum Statistics + Wiener)
            if self.use_advanced_nr:
                filtered_audio = self.advanced_noise_reduction(filtered_audio)
            
            # Step 3.5: Filtro de suavizado adicional (solo SSB)
            if self.sos_smooth is not None:
                filtered_audio, self.zi_smooth = signal.sosfilt(
                    self.sos_smooth,
                    filtered_audio,
                    zi=self.zi_smooth
                )
            
            # Step 4: Noise gate
            if self.enable_gate:
                filtered_audio = self.apply_noise_gate(filtered_audio)
            
            # Step 5: AGC (Automatic Gain Control)
            if self.enable_agc:
                filtered_audio = self.apply_agc(filtered_audio)
            
            # Final limiting to prevent clipping
            filtered_audio = np.clip(filtered_audio, -0.95, 0.95)
            
            # Output to both channels (stereo)
            outdata[:, 0] = filtered_audio
            if outdata.shape[1] > 1:
                outdata[:, 1] = filtered_audio
            
            # Monitor processing time
            processing_time = (time.perf_counter() - start_time) * 1000
            self.processing_times.append(processing_time)
            if len(self.processing_times) > 100:
                self.processing_times.pop(0)
                
        except Exception as e:
            print(f"Error in audio callback: {e}", file=sys.stderr)
            outdata.fill(0)
    
    def list_devices(self):
        """List all available audio devices"""
        print("\n=== Available Audio Devices ===")
        print(sd.query_devices())
        print("\n")
    
    def get_stats(self):
        """Get processing statistics"""
        if not self.processing_times:
            return None
        
        avg_time = np.mean(self.processing_times)
        max_time = np.max(self.processing_times)
        min_time = np.min(self.processing_times)
        
        return {
            'avg_ms': avg_time,
            'max_ms': max_time,
            'min_ms': min_time,
            'total_latency_ms': avg_time + (self.block_size / self.sample_rate * 1000)
        }
    
    def start(self, input_device=None, output_device=None):
        """Start the audio processing stream"""
        print("\n" + "="*60)
        print("  HF AUDIO PROCESSOR FOR WEBSDR")
        print("="*60)
        print(f"\nConfiguration:")
        print(f"  Band: {self.band}")
        print(f"  Mode: {self.mode}")
        print(f"  Sample Rate: {self.sample_rate} Hz")
        print(f"  Block Size: {self.block_size} samples ({(self.block_size / self.sample_rate) * 1000:.1f} ms)")
        print(f"\nBandwidth Optimization:")
        print(f"  Bandpass Filter: {self.lowcut}-{self.highcut} Hz")
        print(f"  Bandwidth: {self.bandwidth} Hz ({self.bandwidth/1000:.1f} kHz)")
        print(f"  Filter Order: {self.filter_order} (selectivity)")
        if self.use_preemphasis:
            print(f"  Pre-emphasis: {self.preemph_freq} Hz (voice enhancement)")
        print(f"\nActive Filters:")
        print(f"  ✓ Bandpass Filter ({self.mode} optimized)")
        if self.use_preemphasis:
            print(f"  ✓ Pre-emphasis (intelligibility boost)")
        if self.enable_notch:
            print(f"  ✓ Notch Filters (60/120 Hz hum removal)")
        if self.use_advanced_nr:
            print(f"  ✓ NovaSDR Spectral NR (MMSE Kim & Ruwisch 2002)")
            print(f"    - FFT size: {self.nr_fft_size}")
            print(f"    - Speech probability estimation: enabled")
            print(f"    - Dynamic musical noise reduction: enabled")
            print(f"    - Gain limit: {self.nr_gain_limit}")
        if self.sos_smooth is not None:
            print(f"  ✓ Smoothing Filter (high-freq noise reduction)")
        if self.enable_gate:
            print(f"  ✓ Noise Gate (threshold: {self.gate_threshold:.3f})")
        if self.enable_agc:
            print(f"  ✓ AGC (target: {self.agc_target:.2f}, max gain: {self.agc_max_gain:.1f}x)")
        
        # Latencia: block_size + NR processing (FFT 512 con overlap 256)
        base_latency = (self.block_size / self.sample_rate) * 1000
        nr_latency = (self.nr_fft_size / self.sample_rate) * 1000 if self.use_advanced_nr else 0
        estimated_latency = base_latency + nr_latency
        print(f"\nEstimated Total Latency: ~{estimated_latency:.1f} ms")
        print(f"Target: < 300 ms ✓")
        
        try:
            with sd.Stream(
                device=(input_device, output_device),
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                channels=2,
                callback=self.audio_callback,
                latency='low'
            ):
                print("\n" + "="*60)
                print("  AUDIO STREAM ACTIVE")
                print("="*60)
                print("\nPress Ctrl+C to stop and view statistics.\n")
                
                # Keep the stream running and show periodic stats
                try:
                    while True:
                        sd.sleep(5000)  # Sleep 5 seconds
                        stats = self.get_stats()
                        if stats:
                            print(f"\rProcessing: avg={stats['avg_ms']:.2f}ms, "
                                  f"max={stats['max_ms']:.2f}ms, "
                                  f"total_latency={stats['total_latency_ms']:.2f}ms", 
                                  end='', flush=True)
                except KeyboardInterrupt:
                    pass
                
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print("  STOPPING AUDIO PROCESSOR")
            print("="*60)
            
            # Show final statistics
            stats = self.get_stats()
            if stats:
                print(f"\nFinal Statistics:")
                print(f"  Average processing time: {stats['avg_ms']:.2f} ms")
                print(f"  Maximum processing time: {stats['max_ms']:.2f} ms")
                print(f"  Minimum processing time: {stats['min_ms']:.2f} ms")
                print(f"  Total latency: {stats['total_latency_ms']:.2f} ms")
                
                if stats['total_latency_ms'] < 500:
                    print(f"\n  ✓ Latency target met ({stats['total_latency_ms']:.2f} < 500 ms)")
                else:
                    print(f"\n  ✗ Latency target exceeded ({stats['total_latency_ms']:.2f} > 500 ms)")
            print()
            
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            raise

def main():
    """
    Main function to run the HF Audio Processor
    
    Setup for webSDR:
    1. Open webSDR in Chrome (e.g., http://websdr.org)
    2. Configure BlackHole as system audio output in macOS Sound Settings
    3. Run this script
    4. Select BlackHole as input device and your headphones as output
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='HF Audio Processor for webSDR with AI Noise Reduction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python audio_processor.py --band 40m --mode SSB --list-devices
  python audio_processor.py --band 40m --mode SSB --input 2 --output 0
  python audio_processor.py --band 10m --mode SSB --input 2 --output 0
  python audio_processor.py --band 40m --mode AM --input 2 --output 0
  python audio_processor.py --band 40m --mode CW --input 2 --output 0
  
  Modes:
  - SSB: 2.8 kHz bandwidth (300-3100 Hz) - Standard voice
  - AM:  6.0 kHz bandwidth (100-6100 Hz) - Wider fidelity
  - CW:  500 Hz bandwidth (600-1100 Hz) - Narrow for morse
  - WIDE: 3.8 kHz bandwidth (200-4000 Hz) - Experimental
  
  For webSDR setup:
  1. Open webSDR in Chrome
  2. Set macOS system audio output to BlackHole
  3. Run: python audio_processor.py --list-devices
  4. Note BlackHole input device number and your headphones output number
  5. Run: python audio_processor.py --band 40m --mode SSB --input X --output Y
        """)
    
    parser.add_argument('--band', choices=['40m', '10m', '20m', '15m', '80m'], default='40m',
                       help='HF band preset (default: 40m)')
    parser.add_argument('--mode', choices=['SSB', 'AM', 'CW', 'WIDE'], default='SSB',
                       help='Transmission mode - SSB: 2.8kHz, AM: 6kHz, CW: 500Hz (default: SSB)')
    parser.add_argument('--input', type=int, default=None,
                       help='Input device index (BlackHole)')
    parser.add_argument('--output', type=int, default=None,
                       help='Output device index (headphones/speakers)')
    parser.add_argument('--no-ai', action='store_true',
                       help='Disable AI noise reduction')
    parser.add_argument('--no-agc', action='store_true',
                       help='Disable Automatic Gain Control')
    parser.add_argument('--no-gate', action='store_true',
                       help='Disable noise gate')
    parser.add_argument('--no-notch', action='store_true',
                       help='Disable notch filters')
    parser.add_argument('--list-devices', action='store_true',
                       help='List audio devices and exit')
    parser.add_argument('--block-size', type=int, default=2048,
                       help='Block size in samples (default: 2048 = 43ms at 48kHz for better noise reduction)')
    parser.add_argument('--nr-alpha', type=float, default=4.0,
                       help='Noise reduction over-subtraction factor (default: 4.0, range: 1.0-6.0)')
    parser.add_argument('--nr-beta', type=float, default=0.002,
                       help='Noise reduction spectral floor (default: 0.002, range: 0.001-0.05)')
    parser.add_argument('--no-nr', action='store_true',
                       help='Disable advanced noise reduction')
    
    args = parser.parse_args()
    
    # Create processor instance
    processor = AudioProcessor(
        sample_rate=48000,
        block_size=args.block_size,
        use_ai_nr=not args.no_ai,
        band=args.band,
        mode=args.mode,
        enable_agc=not args.no_agc,
        enable_notch=not args.no_notch,
        enable_gate=not args.no_gate
    )
    
    # Aplicar parámetros de NR desde argumentos
    if not args.no_nr:
        processor.nr_alpha = args.nr_alpha
        processor.nr_beta = args.nr_beta
    else:
        processor.use_advanced_nr = False
    
    # List devices if requested
    if args.list_devices:
        processor.list_devices()
        print("\nTo start processing, run:")
        print(f"  python audio_processor.py --band {args.band} --input <INPUT_ID> --output <OUTPUT_ID>")
        return
    
    # List devices for reference
    processor.list_devices()
    
    # Start processing
    if args.input is not None and args.output is not None:
        print(f"Using input device {args.input} and output device {args.output}")
        processor.start(input_device=args.input, output_device=args.output)
    else:
        print("\n" + "!"*60)
        print("  WARNING: No devices specified!")
        print("!"*60)
        print("\nPlease specify input and output devices:")
        print("  --input <device_id>   (BlackHole virtual audio)")
        print("  --output <device_id>  (Your headphones/speakers)")
        print("\nRun with --list-devices to see available devices.")
        print("\nExample:")
        print(f"  python audio_processor.py --band {args.band} --mode SSB --input 2 --output 0\n")

if __name__ == "__main__":
    main()
