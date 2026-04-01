#!/usr/bin/env python3
"""
HF Audio Processor con NovaSDR - PARÁMETROS AJUSTABLES
Permite ajustar la agresividad del filtro en tiempo de ejecución
"""
import sounddevice as sd
import numpy as np
import sys
import time

try:
    import novasdr_nr
    NOVASDR_AVAILABLE = True
    print("✓ NovaSDR Rust module loaded successfully")
except ImportError as e:
    print(f"✗ NovaSDR Rust module not available: {e}")
    NOVASDR_AVAILABLE = False
    sys.exit(1)

class AudioProcessorNovaSDRTunable:
    def __init__(self, sample_rate=48000, block_size=2048, 
                 gain=1.0/1024.0, alpha=0.98, asnr=20.0, post_gain=1.0):
        """
        HF Audio Processor - Parámetros ajustables
        
        Args:
            sample_rate: Sample rate (48000 Hz)
            block_size: Block size (2048 samples)
            gain: Gain factor (más bajo = más agresivo)
                  - 1.0/512.0  = moderado (default novasdr)
                  - 1.0/1024.0 = agresivo
                  - 1.0/2048.0 = muy agresivo
            alpha: A priori SNR smoothing (0.0-1.0)
                  - 0.95 = menos suavizado (más rápido)
                  - 0.98 = más suavizado (más estable)
            asnr: SNR a priori en dB
                  - 30.0 = conservador (menos reducción)
                  - 20.0 = moderado
                  - 10.0 = agresivo (más reducción)
            post_gain: Ganancia después del filtro (compensar pérdida de volumen)
                  - 1.0 = sin cambio
                  - 2.0 = duplicar volumen
                  - 3.0 = triplicar volumen
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.gain = gain
        self.alpha = alpha
        self.asnr = asnr
        self.post_gain = post_gain
        
        if NOVASDR_AVAILABLE:
            self.novasdr_nr = novasdr_nr.SpectralNoiseReduction(
                sample_rate=sample_rate,
                gain=gain,
                alpha=alpha,
                asnr=asnr
            )
            print(f"✓ NovaSDR initialized: gain={gain:.6f}, alpha={alpha}, asnr={asnr}")
        
        self.processing_times = []
        
    def audio_callback(self, indata, outdata, frames, time_info, status):
        """Real-time audio processing callback"""
        start_time = time.perf_counter()
        
        if status:
            print(f"Status: {status}", file=sys.stderr)
        
        try:
            # Extract mono, process with NovaSDR, output stereo
            audio_data = indata[:, 0].copy().astype(np.float32)
            
            if NOVASDR_AVAILABLE:
                filtered_audio = self.novasdr_nr.process(audio_data)
                # Apply post-filter gain to compensate volume reduction
                if self.post_gain != 1.0:
                    filtered_audio = filtered_audio * self.post_gain
            else:
                filtered_audio = audio_data
            
            filtered_audio = np.clip(filtered_audio, -1.0, 1.0)
            
            outdata[:, 0] = filtered_audio
            if outdata.shape[1] > 1:
                outdata[:, 1] = filtered_audio
            
            processing_time = (time.perf_counter() - start_time) * 1000
            self.processing_times.append(processing_time)
            if len(self.processing_times) > 100:
                self.processing_times.pop(0)
                
        except Exception as e:
            print(f"Error in audio callback: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
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
        print("  HF AUDIO PROCESSOR - NovaSDR Tunable")
        print("="*60)
        print(f"\nConfiguration:")
        print(f"  Sample Rate: {self.sample_rate} Hz")
        print(f"  Block Size: {self.block_size} samples ({(self.block_size / self.sample_rate) * 1000:.1f} ms)")
        print(f"\nNovaSDR Parameters:")
        print(f"  Gain:  {self.gain:.6f} (1/{1.0/self.gain:.0f})")
        print(f"  Alpha: {self.alpha}")
        print(f"  ASNR:  {self.asnr} dB")
        print(f"  Post-Gain: {self.post_gain}x")
        
        # Interpretar parámetros
        if self.gain <= 1.0/2048.0:
            aggressiveness = "MUY AGRESIVO"
        elif self.gain <= 1.0/1024.0:
            aggressiveness = "AGRESIVO"
        elif self.gain <= 1.0/512.0:
            aggressiveness = "MODERADO"
        else:
            aggressiveness = "SUAVE"
        
        print(f"\n  → Agresividad: {aggressiveness}")
        if self.post_gain > 1.0:
            print(f"  → Compensación de volumen: +{20*np.log10(self.post_gain):.1f} dB")
        
        base_latency = (self.block_size / self.sample_rate) * 1000
        nr_latency = (512 / self.sample_rate) * 1000 if NOVASDR_AVAILABLE else 0
        estimated_latency = base_latency + nr_latency
        print(f"\nEstimated Total Latency: ~{estimated_latency:.1f} ms")
        print(f"Target: < 500 ms ✓")
        
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
                
                try:
                    while True:
                        sd.sleep(5000)
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
            
            stats = self.get_stats()
            if stats:
                print(f"\nFinal Statistics:")
                print(f"  Average processing time: {stats['avg_ms']:.2f} ms")
                print(f"  Total latency: {stats['total_latency_ms']:.2f} ms")
            print()
            
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='HF Audio Processor with NovaSDR - Tunable Parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Presets:
  --preset light      : Reducción suave (gain=1/512, alpha=0.95, asnr=30)
  --preset moderate   : Reducción moderada (gain=1/1024, alpha=0.98, asnr=20) [DEFAULT]
  --preset aggressive : Reducción agresiva (gain=1/2048, alpha=0.98, asnr=10)
  --preset maximum    : Reducción máxima (gain=1/4096, alpha=0.99, asnr=5)

Custom parameters:
  --gain <value>  : Gain factor (ej: 0.000488 = 1/2048)
  --alpha <value> : A priori SNR smoothing (0.0-1.0)
  --asnr <value>  : SNR a priori en dB

Example usage:
  python audio_processor_novasdr_tunable.py --preset moderate --input 5 --output 2
  python audio_processor_novasdr_tunable.py --gain 0.000244 --alpha 0.99 --asnr 5 --input 5 --output 2
        """)
    
    parser.add_argument('--input', type=int, default=None,
                       help='Input device index (BlackHole)')
    parser.add_argument('--output', type=int, default=None,
                       help='Output device index (headphones/speakers)')
    parser.add_argument('--list-devices', action='store_true',
                       help='List audio devices and exit')
    parser.add_argument('--block-size', type=int, default=2048,
                       help='Block size in samples (default: 2048)')
    
    # Presets
    parser.add_argument('--preset', choices=['light', 'moderate', 'aggressive', 'maximum', 'ultra', 'extreme'],
                       default='moderate',
                       help='Noise reduction preset (default: moderate)')
    
    # Custom parameters
    parser.add_argument('--gain', type=float, default=None,
                       help='Custom gain factor')
    parser.add_argument('--alpha', type=float, default=None,
                       help='Custom alpha value (0.0-1.0)')
    parser.add_argument('--asnr', type=float, default=None,
                       help='Custom ASNR value (dB)')
    parser.add_argument('--post-gain', type=float, default=None,
                       help='Post-filter gain multiplier (compensate volume)')
    
    args = parser.parse_args()
    
    # Determine parameters
    presets = {
        'light': {'gain': 1.0/512.0, 'alpha': 0.95, 'asnr': 30.0, 'post_gain': 1.0},
        'moderate': {'gain': 1.0/1024.0, 'alpha': 0.98, 'asnr': 20.0, 'post_gain': 1.5},
        'aggressive': {'gain': 1.0/2048.0, 'alpha': 0.98, 'asnr': 10.0, 'post_gain': 2.5},
        'maximum': {'gain': 1.0/4096.0, 'alpha': 0.99, 'asnr': 5.0, 'post_gain': 4.5},
        'ultra': {'gain': 1.0/8192.0, 'alpha': 0.99, 'asnr': 2.0, 'post_gain': 10.0},
        'extreme': {'gain': 1.0/16384.0, 'alpha': 0.99, 'asnr': 1.0, 'post_gain': 14.0},
    }
    
    params = presets[args.preset].copy()
    
    # Override with custom parameters if provided
    if args.gain is not None:
        params['gain'] = args.gain
    if args.alpha is not None:
        params['alpha'] = args.alpha
    if args.asnr is not None:
        params['asnr'] = args.asnr
    if args.post_gain is not None:
        params['post_gain'] = args.post_gain
    
    processor = AudioProcessorNovaSDRTunable(
        sample_rate=48000,
        block_size=args.block_size,
        **params
    )
    
    if args.list_devices:
        processor.list_devices()
        print("\nTo start processing, run:")
        print(f"  python audio_processor_novasdr_tunable.py --preset {args.preset} --input <INPUT_ID> --output <OUTPUT_ID>")
        return
    
    processor.list_devices()
    
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
        print(f"  python audio_processor_novasdr_tunable.py --preset {args.preset} --input 5 --output 2\n")

if __name__ == "__main__":
    main()
