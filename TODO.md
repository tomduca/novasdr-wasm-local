# TODO - NovaSDR Audio Processor

## ✅ Completado
- [x] Interfaz web con controles en tiempo real
- [x] Selección de dispositivos y presets
- [x] Toggle de bypass
- [x] Grabación de audio con timestamp
- [x] BlackHole auto-seleccionado por defecto
- [x] Preset Extreme por defecto

## 🔄 Pendiente para Mañana

### 1. Arreglar Grabación MP3
- [ ] Instalar ffmpeg: `brew install ffmpeg`
- [ ] Probar grabación en MP3 (128kbps)
- [ ] Verificar ahorro de espacio vs WAV

### 2. Interfaz Gráfica Nativa (Sin Navegador)
- [ ] Crear GUI con tkinter o PyQt5
- [ ] Incluir todos los controles actuales:
  - Selección de dispositivos
  - Presets (Moderate, Aggressive, Ultra, Extreme)
  - Bypass toggle
  - Botones Start/Stop
  - Grabación con Start/Stop
  - Log en tiempo real
- [ ] Diseño simple y funcional
- [ ] Mantener misma funcionalidad que web

### 3. Versión para Windows
- [ ] Investigar compatibilidad de dependencias en Windows
- [ ] Probar compilación de módulo Rust en Windows
- [ ] Adaptar rutas y configuraciones para Windows
- [ ] Crear instalador o ejecutable standalone
- [ ] Documentar proceso de instalación en Windows

## 📝 Notas

### Grabación Actual
- **Funciona:** Sí ✓
- **Formato actual:** WAV (fallback porque falta ffmpeg)
- **Archivo de prueba:** `recording_20260331_234140.wav` (42.9s)
- **Para MP3:** Instalar `brew install ffmpeg`

### Arquitectura Actual
- Python 3.14 + Rust (PyO3)
- sounddevice para audio I/O
- NovaSDR filter en Rust
- Flask para interfaz web
- Latencia: ~43ms

### Consideraciones Windows
- sounddevice funciona en Windows
- Rust/PyO3 compila en Windows
- Necesita MSVC o MinGW para compilar
- BlackHole no existe en Windows (usar VB-Cable o similar)

---

**73 de LU2MET** 📻
