# HF Audio Processor for webSDR

Procesador de audio en tiempo real con **AI Noise Reduction** optimizado para transmisiones de HF desde webSDR. Utiliza RNNoise (AI) combinado con filtros DSP tradicionales para limpiar el audio con latencia ultra-baja (<500ms).

**✨ Optimizado para bandwidth estándar SSB de 2.8 kHz**

## 🎯 Características

### Optimización de Bandwidth
- **SSB Mode**: 2.8 kHz (300-3100 Hz) - Estándar internacional para voz
- **AM Mode**: 6.0 kHz (100-6100 Hz) - Mayor fidelidad
- **CW Mode**: 500 Hz (600-1100 Hz) - Ultra-estrecho para telegrafía
- **Pre-énfasis**: Realza frecuencias de voz (1-2 kHz) para mejor inteligibilidad

### Filtros DSP Tradicionales
- **Bandpass Filter** - Orden adaptativo según modo (6 para SSB)
- **Notch Filters** (60/120 Hz) - Elimina zumbido de línea eléctrica
- **Noise Gate** - Parámetros optimizados por modo
- **AGC (Automatic Gain Control)** - Configuración específica por modo

### AI Noise Reduction
- **RNNoise** - Red neuronal recurrente para reducción de ruido
- Latencia: ~10ms por frame
- Optimizado para voz humana
- Funciona en tiempo real

### Rendimiento
- **Latencia total**: ~15-20ms (muy por debajo del objetivo de 500ms)
- **Sample rate**: 48 kHz
- **Block size**: 480 samples (10ms)
- Monitoreo de latencia en tiempo real

## 📋 Requisitos

### Software
- Python 3.8+
- macOS (para usar BlackHole)
- [BlackHole](https://existential.audio/blackhole/) - Audio virtual driver

### Instalación de BlackHole
```bash
# Instalar con Homebrew
brew install blackhole-2ch

# O descargar desde: https://existential.audio/blackhole/
```

## 🚀 Instalación

1. **Clonar o descargar el proyecto**
```bash
cd /Users/tomasduca/CascadeProjects/audio_processor
```

2. **Crear entorno virtual (recomendado)**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

## 🔧 Configuración

### 1. Configurar BlackHole en macOS

**Opción A: Multi-Output Device (Recomendado)**
1. Abrir **Audio MIDI Setup** (Aplicaciones → Utilidades)
2. Click en "+" → "Create Multi-Output Device"
3. Seleccionar:
   - ✓ BlackHole 2ch
   - ✓ Tus auriculares/parlantes
4. Hacer click derecho → "Use This Device For Sound Output"

**Opción B: Solo BlackHole**
1. Ir a **System Preferences** → **Sound** → **Output**
2. Seleccionar "BlackHole 2ch"
3. El audio del sistema irá a BlackHole (no escucharás nada directamente)

### 2. Identificar dispositivos de audio

```bash
python audio_processor.py --list-devices
```

Salida ejemplo:
```
=== Available Audio Devices ===
  0 MacBook Pro Microphone, Core Audio (2 in, 0 out)
  1 MacBook Pro Speakers, Core Audio (0 in, 2 out)
> 2 BlackHole 2ch, Core Audio (2 in, 2 out)
  3 AirPods Pro, Core Audio (0 in, 2 out)
```

Anota:
- **Input device**: BlackHole (ejemplo: 2)
- **Output device**: Tus auriculares (ejemplo: 3)

## 🎮 Uso

### Flujo de trabajo completo

```
WebSDR (Chrome) → Audio del sistema → BlackHole → Python Script → Auriculares
```

### 1. Abrir webSDR
```
http://websdr.org
http://websdr.ewi.utwente.nl:8901/  (Ejemplo: Holanda)
http://kiwisdr.com/public/           (Lista de KiwiSDR)
```

### 2. Configurar banda en webSDR
- **40m**: 7.000 - 7.300 MHz (SSB: 7.100-7.300 MHz)
- **10m**: 28.000 - 29.700 MHz (SSB: 28.300-29.700 MHz)

### 3. Ejecutar el procesador

**SSB en 40 metros (modo por defecto - 2.8 kHz bandwidth):**
```bash
python audio_processor.py --band 40m --mode SSB --input 2 --output 3
```

**SSB en 10 metros:**
```bash
python audio_processor.py --band 10m --mode SSB --input 2 --output 3
```

**AM (6 kHz bandwidth para mayor fidelidad):**
```bash
python audio_processor.py --band 40m --mode AM --input 2 --output 3
```

**CW - Morse Code (500 Hz bandwidth ultra-estrecho):**
```bash
python audio_processor.py --band 40m --mode CW --input 2 --output 3
```

**Sin AI (solo filtros DSP):**
```bash
python audio_processor.py --band 40m --mode SSB --input 2 --output 3 --no-ai
```

**Personalizar filtros:**
```bash
# Deshabilitar AGC
python audio_processor.py --band 40m --input 2 --output 3 --no-agc

# Deshabilitar noise gate
python audio_processor.py --band 40m --input 2 --output 3 --no-gate

# Deshabilitar notch filters
python audio_processor.py --band 40m --input 2 --output 3 --no-notch

# Solo bandpass (sin AI, AGC, gate, ni notch)
python audio_processor.py --band 40m --input 2 --output 3 --no-ai --no-agc --no-gate --no-notch
```

**Ajustar latencia (block size):**
```bash
# Menor latencia (puede ser menos estable)
python audio_processor.py --band 40m --input 2 --output 3 --block-size 256

# Mayor estabilidad (más latencia)
python audio_processor.py --band 40m --input 2 --output 3 --block-size 1024
```

## 📊 Monitoreo en tiempo real

Durante la ejecución verás:
```
============================================================
  HF AUDIO PROCESSOR FOR WEBSDR
============================================================

Configuration:
  Band: 40m
  Sample Rate: 48000 Hz
  Block Size: 480 samples (10.0 ms)
  Bandpass Filter: 300-2800 Hz

Active Filters:
  ✓ Bandpass Filter (Voice optimization)
  ✓ Notch Filters (60/120 Hz hum removal)
  ✓ AI Noise Reduction (RNNoise)
  ✓ Noise Gate
  ✓ Automatic Gain Control (AGC)

Estimated Total Latency: ~15.0 ms
Target: < 500 ms ✓

============================================================
  AUDIO STREAM ACTIVE
============================================================

Press Ctrl+C to stop and view statistics.

Processing: avg=2.34ms, max=4.12ms, total_latency=12.34ms
```

## 🛑 Detener el procesador

Presiona `Ctrl+C` para detener. Verás estadísticas finales:

```
============================================================
  STOPPING AUDIO PROCESSOR
============================================================

Final Statistics:
  Average processing time: 2.34 ms
  Maximum processing time: 4.12 ms
  Minimum processing time: 1.89 ms
  Total latency: 12.34 ms

  ✓ Latency target met (12.34 < 500 ms)
```

## 🎛️ Parámetros de los filtros

### Modos de Transmisión

| Modo | Bandwidth | Frecuencias | Orden Filtro | Uso |
|------|-----------|-------------|--------------|-----|
| **SSB** | 2.8 kHz | 300-3100 Hz | 6 | Voz estándar (recomendado) |
| **AM** | 6.0 kHz | 100-6100 Hz | 4 | Mayor fidelidad, broadcast |
| **CW** | 500 Hz | 600-1100 Hz | 8 | Telegrafía morse |
| **WIDE** | 3.8 kHz | 200-4000 Hz | 4 | Experimental |

### Bandpass Filter
- **Orden adaptativo**: Mayor orden = mejor selectividad
- **SSB**: Orden 6 para rechazo óptimo fuera de 2.8 kHz
- **Butterworth**: Respuesta plana en banda de paso

### Notch Filters
- **60 Hz**: Elimina zumbido de línea eléctrica (USA)
- **120 Hz**: Elimina armónico
- Q factor: 30 (muy selectivo)

### Noise Gate
- **Threshold**: 0.01 RMS
- **Ratio**: 0.1 (90% atenuación)
- **Smoothing**: 0.95 (transiciones suaves)

### Pre-énfasis (solo SSB)
- **Frecuencia central**: 1500 Hz
- **Q factor**: 2.0
- **Efecto**: Realza frecuencias de voz (1-2 kHz) para mejor inteligibilidad
- **Tipo**: Peaking filter (IIR)

### AGC (optimizado por modo)

**SSB:**
- Target: 0.35 RMS
- Attack: 0.005 (muy rápido para compensar fading)
- Release: 0.15 (lento para evitar "pumping")
- Gain range: 0.1 - 15.0x (más ganancia para señales débiles)

**AM:**
- Target: 0.3 RMS
- Attack: 0.01 (moderado)
- Release: 0.2 (lento para preservar modulación)
- Gain range: 0.2 - 8.0x

**CW:**
- Target: 0.4 RMS
- Attack: 0.001 (ultra-rápido para tonos)
- Release: 0.05 (rápido)
- Gain range: 0.1 - 20.0x

### RNNoise (AI)
- **Frame size**: 480 samples (10ms @ 48kHz)
- **Model**: Pre-entrenado para voz
- **Latencia**: ~5-10ms

## 🔍 Troubleshooting

### No escucho audio
1. Verifica que BlackHole esté seleccionado como entrada
2. Verifica que tus auriculares estén seleccionados como salida
3. Verifica los índices de dispositivos con `--list-devices`

### Latencia alta
1. Reduce el block size: `--block-size 256`
2. Deshabilita AI: `--no-ai`
3. Cierra otras aplicaciones de audio

### Audio distorsionado
1. Aumenta el block size: `--block-size 1024`
2. Ajusta el AGC deshabilitándolo: `--no-agc`
3. Reduce el volumen en webSDR

### RNNoise no disponible
```bash
# Reinstalar pyrnnoise
pip uninstall pyrnnoise
pip install pyrnnoise

# Si falla, el script funcionará sin AI
# Solo mostrará un warning
```

### Audio con mucho ruido
1. Verifica que AI esté habilitado (sin `--no-ai`)
2. Ajusta el noise gate threshold en el código
3. Usa una mejor fuente webSDR (señal más limpia)

## 📁 Estructura del proyecto

```
audio_processor/
├── audio_processor.py    # Script principal
├── requirements.txt      # Dependencias Python
└── README.md            # Esta documentación
```

## � ¿Por qué 2.8 kHz para SSB?

El ancho de banda de **2.8 kHz** es el estándar internacional para transmisiones SSB (Single Side Band) en HF por varias razones:

1. **Inteligibilidad óptima**: Contiene todas las frecuencias necesarias para voz clara (300-3100 Hz)
2. **Eficiencia espectral**: Permite más canales en el espectro limitado de HF
3. **Regulación**: Cumple con regulaciones ITU (International Telecommunication Union)
4. **Compatibilidad**: Todos los equipos SSB están diseñados para este bandwidth

### Ventajas de la optimización

Al filtrar exactamente a 2.8 kHz:
- ✅ **Reduce ruido**: Elimina frecuencias fuera de la banda de voz
- ✅ **Mejora SNR**: Signal-to-Noise Ratio más alto
- ✅ **Menor procesamiento**: El AI solo procesa frecuencias útiles
- ✅ **Mejor inteligibilidad**: Pre-énfasis en frecuencias críticas (1-2 kHz)

## �🔬 Detalles técnicos

### Pipeline de procesamiento

```
Input (BlackHole)
    ↓
1. Bandpass Filter (modo-específico)
   SSB: 300-3100 Hz (2.8 kHz) - Orden 6
   AM:  100-6100 Hz (6.0 kHz) - Orden 4
   CW:  600-1100 Hz (500 Hz) - Orden 8
    ↓
1.5. Pre-énfasis (solo SSB)
     Realza 1500 Hz ±500 Hz
    ↓
2. Notch Filters (60/120 Hz)
   Elimina hum de línea eléctrica
    ↓
3. AI Noise Reduction (RNNoise)
   Red neuronal para voz
    ↓
4. Noise Gate (parámetros por modo)
   SSB: threshold 0.008
   CW:  threshold 0.015
    ↓
5. AGC (configuración por modo)
   SSB: max gain 15x, attack 5ms
   AM:  max gain 8x, attack 10ms
   CW:  max gain 20x, attack 1ms
    ↓
6. Limiter (-0.95 to 0.95)
   Previene clipping
    ↓
Output (Auriculares)
```

### Latencia estimada por componente

| Componente | Latencia |
|------------|----------|
| Block size (480 samples @ 48kHz) | 10.0 ms |
| Bandpass filter | <0.1 ms |
| Notch filters (2x) | <0.1 ms |
| RNNoise (AI) | ~5.0 ms |
| Noise gate | <0.1 ms |
| AGC | <0.1 ms |
| **Total** | **~15-20 ms** |

## 🌐 webSDR recomendados

### Europa
- **Holanda**: http://websdr.ewi.utwente.nl:8901/
- **Alemania**: http://websdr.tu-chemnitz.de:8901/
- **Reino Unido**: http://websdr.suws.org.uk/

### América
- **USA (California)**: http://k3fef.com:8901/
- **USA (Colorado)**: http://kd0rc.com:8073/
- **Brasil**: http://py2ems.ddns.net:8901/

### KiwiSDR (mejor calidad)
- Lista completa: http://kiwisdr.com/public/

## 📝 Notas

- **RNNoise** está optimizado para voz humana, perfecto para SSB/AM en HF
- El **AGC** ayuda a normalizar señales débiles y fuertes
- El **Noise gate** reduce el ruido cuando no hay transmisión
- Los **Notch filters** eliminan el zumbido de 60Hz común en grabaciones
- La latencia total es ~15-20ms, muy por debajo del objetivo de 500ms

## 🤝 Contribuciones

Mejoras sugeridas:
- [ ] Interfaz gráfica (GUI) con controles en tiempo real
- [ ] Más presets de bandas (20m, 15m, etc.)
- [ ] Grabación de audio procesado
- [ ] Espectrograma en tiempo real
- [ ] Filtros adaptativos

## 📄 Licencia

Este proyecto es de código abierto. Úsalo libremente para escuchar transmisiones de radioaficionados en HF.

## 🙏 Créditos

- **NovaSDR**: Algoritmo Spectral Noise Reduction (https://github.com/Steven9101/novasdr-wasm)
- **PyO3**: Bindings Rust-Python para integración
- **sounddevice**: Librería de audio I/O en Python
- **rustfft**: FFT implementation en Rust
- **Desarrollo**: Prompteado con Claude Sonnet 4.5

---

**73 de LU2MET** 📻
