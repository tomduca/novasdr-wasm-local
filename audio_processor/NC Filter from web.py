"""
NC Noise Filter - Equivalente Python al de NovaSDR/PhantomSDR-Plus
==================================================================
Implementa sustracción espectral con estimación de mínimos estadísticos,
replicando el comportamiento del "Noise Cancellation" del frontend jsdsp.

Uso básico:
    from nc_noise_filter import NCNoiseFilter
    import numpy as np

    filt = NCNoiseFilter(sample_rate=12000, fft_size=512)
    clean = filt.process(noisy_audio_block)   # Float32 array

Pipeline con archivo WAV:
    python nc_noise_filter.py input.wav output.wav
"""

import numpy as np
from typing import Optional
import sys


class NCNoiseFilter:
    """
    Filtro de cancelación de ruido por sustracción espectral.

    Parámetros
    ----------
    sample_rate : int
        Frecuencia de muestreo del audio (Hz). Default: 12000 (NovaSDR default).
    fft_size : int
        Tamaño de la FFT. Debe ser potencia de 2. Default: 512.
    hop_size : int | None
        Salto entre frames (overlap). None = fft_size // 2.
    alpha : float
        Factor de sobreestimación del ruido (oversubtraction). Típico: 2.0–4.0.
        Más alto = más agresivo; puede causar "musical noise" si es excesivo.
    beta : float
        Floor espectral (0.0–1.0). Evita que el gain baje de este valor.
        Valor bajo = más supresión pero más artefactos. Típico: 0.001–0.02.
    noise_lookback : int
        Cuántos frames se usan para estimar el piso de ruido mínimo.
        Más alto = estimación más estable pero reacción más lenta. Default: 30.
    noise_update_rate : float
        Qué tan rápido se actualiza la estimación de ruido. Default: 0.98.
    """

    def __init__(
        self,
        sample_rate: int = 12000,
        fft_size: int = 512,
        hop_size: Optional[int] = None,
        alpha: float = 2.5,
        beta: float = 0.01,
        noise_lookback: int = 30,
        noise_update_rate: float = 0.98,
    ):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.hop_size = hop_size if hop_size is not None else fft_size // 2
        self.alpha = alpha
        self.beta = beta
        self.noise_lookback = noise_lookback
        self.noise_update_rate = noise_update_rate

        n_bins = fft_size // 2 + 1

        # Ventana de análisis/síntesis (Hann)
        self.window = np.hanning(fft_size).astype(np.float32)

        # Buffer circular para estimación del mínimo de ruido
        self._noise_hist = np.ones((noise_lookback, n_bins), dtype=np.float32) * 1e-10
        self._hist_idx = 0

        # Estimación suavizada del piso de ruido
        self._noise_floor = np.ones(n_bins, dtype=np.float32) * 1e-10

        # Buffer de overlap-add
        self._ola_buffer = np.zeros(fft_size, dtype=np.float32)
        self._input_buffer = np.zeros(fft_size, dtype=np.float32)

        # Normalización OLA
        win2 = self.window ** 2
        ola_norm = np.zeros(fft_size, dtype=np.float32)
        for i in range(0, fft_size, self.hop_size):
            ola_norm[i:i + fft_size] += win2[:fft_size - i] if i == 0 else win2
        ola_norm = np.maximum(ola_norm[:fft_size], 1e-8)
        self._ola_norm = ola_norm

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def process_block(self, frame: np.ndarray) -> np.ndarray:
        """
        Procesa un bloque de audio de exactamente fft_size muestras.

        Parameters
        ----------
        frame : np.ndarray
            Array float32 de longitud fft_size.

        Returns
        -------
        np.ndarray
            Bloque procesado, misma longitud.
        """
        frame = np.asarray(frame, dtype=np.float32)
        assert len(frame) == self.fft_size, (
            f"frame debe tener {self.fft_size} muestras, recibido {len(frame)}"
        )

        # 1) Aplicar ventana y FFT
        windowed = frame * self.window
        spectrum = np.fft.rfft(windowed)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        # 2) Potencia espectral
        power = magnitude ** 2

        # 3) Actualizar historial de mínimos (minimum statistics)
        self._noise_hist[self._hist_idx] = power
        self._hist_idx = (self._hist_idx + 1) % self.noise_lookback

        # Estimación del ruido = mínimo suavizado
        min_power = np.min(self._noise_hist, axis=0)
        self._noise_floor = (
            self.noise_update_rate * self._noise_floor
            + (1.0 - self.noise_update_rate) * min_power
        )

        # 4) Calcular gain de sustracción espectral
        #    G[k] = max( (P[k] - alpha * N[k]) / P[k], beta ) ^ 0.5
        #    Equivalente a: max(1 - alpha * N[k]/P[k], beta)^0.5 en amplitud
        gain_power = np.maximum(
            (power - self.alpha * self._noise_floor) / np.maximum(power, 1e-20),
            self.beta,
        )
        gain = np.sqrt(gain_power)

        # 5) Aplicar gain al espectro
        clean_spectrum = gain * magnitude * np.exp(1j * phase)

        # 6) IFFT y síntesis
        clean_frame = np.fft.irfft(clean_spectrum, n=self.fft_size)
        clean_frame = (clean_frame * self.window).astype(np.float32)

        return clean_frame

    def process(self, audio: np.ndarray) -> np.ndarray:
        """
        Procesa un array de audio de longitud arbitraria usando overlap-add.

        Parameters
        ----------
        audio : np.ndarray
            Audio mono float32 de cualquier longitud.

        Returns
        -------
        np.ndarray
            Audio procesado, misma longitud que la entrada.
        """
        audio = np.asarray(audio, dtype=np.float32)
        n_samples = len(audio)

        # Pad para completar el último frame
        pad = self.fft_size - (n_samples % self.hop_size or self.hop_size)
        padded = np.concatenate([audio, np.zeros(pad, dtype=np.float32)])

        output = np.zeros(len(padded) + self.fft_size, dtype=np.float32)

        for start in range(0, len(padded) - self.fft_size + 1, self.hop_size):
            frame = padded[start:start + self.fft_size]
            processed = self.process_block(frame)
            output[start:start + self.fft_size] += processed

        # Normalización OLA
        # (simplificada — asume señal estacionaria en bordes)
        output /= (np.sum(self.window ** 2) / self.hop_size)

        return output[:n_samples]

    def reset(self):
        """Reinicia el estado interno del filtro."""
        n_bins = self.fft_size // 2 + 1
        self._noise_hist[:] = 1e-10
        self._noise_floor[:] = 1e-10
        self._hist_idx = 0


# ------------------------------------------------------------------
# Variante streaming (frame a frame, como el AudioWorklet)
# ------------------------------------------------------------------

class NCNoiseFilterStreaming:
    """
    Versión streaming del NC Noise Filter, pensada para procesar
    chunks de 128 muestras (como el AudioWorkletProcessor del browser).

    Uso:
        filt = NCNoiseFilterStreaming(sample_rate=12000)
        # En loop de audio:
        out_chunk = filt.process_chunk(in_chunk)  # len=128
    """

    def __init__(
        self,
        sample_rate: int = 12000,
        chunk_size: int = 128,       # tamaño del AudioWorklet block
        fft_size: int = 512,
        alpha: float = 2.5,
        beta: float = 0.01,
        noise_lookback: int = 30,
    ):
        self.chunk_size = chunk_size
        self.fft_size = fft_size
        self._filt = NCNoiseFilter(
            sample_rate=sample_rate,
            fft_size=fft_size,
            hop_size=chunk_size,
            alpha=alpha,
            beta=beta,
            noise_lookback=noise_lookback,
        )
        # Buffer de entrada acumulado
        self._in_buf = np.zeros(fft_size, dtype=np.float32)
        # Buffer de salida OLA
        self._out_buf = np.zeros(fft_size + chunk_size, dtype=np.float32)

    def process_chunk(self, chunk: np.ndarray) -> np.ndarray:
        """
        Procesa un chunk de chunk_size muestras.

        Returns un chunk de chunk_size muestras con latencia = fft_size.
        """
        chunk = np.asarray(chunk, dtype=np.float32)
        assert len(chunk) == self.chunk_size

        # Desplazar buffer de entrada
        self._in_buf = np.roll(self._in_buf, -self.chunk_size)
        self._in_buf[-self.chunk_size:] = chunk

        # Procesar frame completo
        processed = self._filt.process_block(self._in_buf.copy())

        # OLA output
        self._out_buf = np.roll(self._out_buf, -self.chunk_size)
        self._out_buf[-self.fft_size:] += processed
        self._out_buf[-self.fft_size:-self.fft_size + self.chunk_size] /= (
            np.sum(self._filt.window ** 2) / self.chunk_size
        )

        out = self._out_buf[:self.chunk_size].copy()
        self._out_buf[:self.chunk_size] = 0.0
        return out


# ------------------------------------------------------------------
# CLI: procesar archivo WAV
# ------------------------------------------------------------------

def process_wav(input_path: str, output_path: str, **kwargs):
    """Aplica el NC Noise Filter a un archivo WAV."""
    import wave
    import struct

    with wave.open(input_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    # Decodificar a float32
    if sampwidth == 2:
        audio_int = np.frombuffer(raw, dtype=np.int16)
        audio = audio_int.astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio_int = np.frombuffer(raw, dtype=np.int32)
        audio = audio_int.astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"sampwidth={sampwidth} no soportado")

    # Mezclar a mono si es stereo
    if n_channels == 2:
        audio = audio.reshape(-1, 2).mean(axis=1)

    print(f"Procesando {n_frames} frames @ {sample_rate} Hz...")
    filt = NCNoiseFilter(sample_rate=sample_rate, **kwargs)
    clean = filt.process(audio)

    # Guardar
    clean_int = np.clip(clean * 32768.0, -32768, 32767).astype(np.int16)
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(clean_int.tobytes())

    print(f"Guardado en {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python nc_noise_filter.py <input.wav> <output.wav>")
        print("Opciones extra: alpha=2.5 beta=0.01 fft_size=512 noise_lookback=30")
        sys.exit(1)

    kwargs = {}
    for arg in sys.argv[3:]:
        k, v = arg.split("=")
        kwargs[k] = float(v) if "." in v else int(v)

    process_wav(sys.argv[1], sys.argv[2], **kwargs)