# 🛠️ Instrucciones de Compilación Local

Este documento describe cómo compilar **LU2MET NovaSDR NR** localmente para macOS y Windows.

---

## 📋 Requisitos Previos

### Ambas Plataformas
- **Python 3.9.13** (importante: usar esta versión exacta)
- **Rust** (toolchain stable, versión 1.95.0 o superior)
- **Git**

### macOS Específico
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (recomendado)

### Windows Específico
- Visual Studio Build Tools 2019 o superior
- Windows SDK

---

## 🍎 Compilación en macOS

### 1. Preparar el Entorno

```bash
# Clonar el repositorio
git clone https://github.com/tomduca/novasdr-wasm-local.git
cd novasdr-wasm-local

# Verificar versiones
python3 --version  # Debe ser 3.9.13
rustc --version    # Debe ser 1.95.0 o superior
```

### 2. Crear Virtual Environment

```bash
cd audio_processor
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 3. Instalar Dependencias Python

```bash
pip install PyQt5 sounddevice scipy pydub numpy maturin pyinstaller
```

### 4. Compilar Módulo Rust (NovaSDR)

```bash
cd ../novasdr_nr_py
maturin develop --release
```

**Verificar que el módulo se instaló correctamente:**
```bash
cd ../audio_processor
python3 -c "import novasdr_nr; print('✓ NovaSDR loaded:', novasdr_nr.__file__)"
```

### 5. Compilar la Aplicación macOS

```bash
# Asegurarse de estar en audio_processor con venv activado
source venv/bin/activate
chmod +x build_macos.sh
./build_macos.sh
```

### 6. Resultado

La aplicación estará en: `audio_processor/dist/LU2MET_NR.app`

**Tamaño esperado:** ~280-300 MB

**Probar la app:**
```bash
open dist/LU2MET_NR.app
```

**Si macOS bloquea la app (quarantine):**
```bash
xattr -cr dist/LU2MET_NR.app
```

---

## 🪟 Compilación en Windows

### 1. Preparar el Entorno

```powershell
# Clonar el repositorio
git clone https://github.com/tomduca/novasdr-wasm-local.git
cd novasdr-wasm-local

# Verificar versiones
python --version  # Debe ser 3.9.13
rustc --version   # Debe ser 1.95.0 o superior
```

### 2. Crear Virtual Environment

```powershell
cd audio_processor
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 3. Instalar Dependencias Python

```powershell
pip install PyQt5 sounddevice scipy pydub numpy maturin pyinstaller
```

### 4. Compilar Módulo Rust (NovaSDR)

```powershell
cd ..\novasdr_nr_py
..\audio_processor\venv\Scripts\Activate.ps1
maturin develop --release
```

**Verificar que el módulo se instaló correctamente:**
```powershell
cd ..\audio_processor
python -c "import novasdr_nr; print('NovaSDR loaded:', novasdr_nr.__file__)"
```

### 5. Compilar la Aplicación Windows

```powershell
# Asegurarse de estar en audio_processor con venv activado
.\venv\Scripts\Activate.ps1
.\build_windows.bat
```

### 6. Resultado

El ejecutable estará en: `audio_processor\dist\LU2MET_NR.exe`

**Tamaño esperado:** ~95-100 MB

**Probar el exe:**
```powershell
.\dist\LU2MET_NR.exe
```

---

## 🐛 Troubleshooting

### Error: "No module named 'novasdr_nr'"

**Causa:** El módulo Rust no está compilado o no está en el virtual environment.

**Solución Windows:**
```powershell
cd novasdr_nr_py
..\audio_processor\venv\Scripts\Activate.ps1
maturin develop --release
```

**Solución macOS:**
```bash
cd novasdr_nr_py
source ../audio_processor/venv/bin/activate
maturin develop --release
```

**Verificar que se instaló:**
```powershell
# Windows
cd ..\audio_processor
python -c "import novasdr_nr; print('OK:', novasdr_nr.__file__)"

# macOS
cd ../audio_processor
python3 -c "import novasdr_nr; print('OK:', novasdr_nr.__file__)"
```

### Error: PyInstaller no encuentra el módulo .so/.pyd

**Solución:** El script `build_macos.sh` / `build_windows.bat` ya incluye el flag `--add-binary` correcto. Verificar que el módulo Rust se compiló exitosamente antes de ejecutar PyInstaller.

### macOS: "App is damaged and can't be opened"

**Solución:**
```bash
xattr -cr dist/LU2MET_NR.app
```

### Windows: Audio saturado o distorsionado

**Causa:** Compilación con RUSTFLAGS incorrectos.

**Solución:** Asegurarse de NO tener `RUSTFLAGS` configurado en variables de entorno:
```powershell
# Verificar
echo $env:RUSTFLAGS

# Si está configurado, eliminarlo temporalmente
$env:RUSTFLAGS = ""
```

### Build muy grande (>500 MB)

**Causa:** PyInstaller está incluyendo módulos de test.

**Solución:** Los scripts ya incluyen `--exclude-module` para scipy.tests, numpy.tests, etc. Verificar que estés usando los scripts `build_macos.sh` / `build_windows.bat` actualizados.

---

## 📦 Distribución

### Crear ZIP para Distribución

**macOS:**
```bash
cd audio_processor/dist
zip -r LU2MET_NR-macos.zip LU2MET_NR.app
```

**Windows:**
```powershell
cd audio_processor\dist
Compress-Archive -Path LU2MET_NR.exe -DestinationPath LU2MET_NR-windows.zip
```

### Subir a GitHub Releases

1. Ir a: `https://github.com/tomduca/novasdr-wasm-local/releases`
2. Click en "Draft a new release"
3. Crear tag (ej: `v1.0.0`)
4. Subir los archivos ZIP
5. Publicar release

---

## 🔄 Workflow de Desarrollo

### Hacer cambios en el código Python
```bash
# Editar archivos .py
# No requiere recompilar Rust
./build_macos.sh  # o build_windows.bat
```

### Hacer cambios en el código Rust
```bash
# Editar archivos en novasdr_nr_py/src/
cd novasdr_nr_py
maturin develop --release
cd ../audio_processor
./build_macos.sh  # o build_windows.bat
```

---

## ✅ Checklist Pre-Release

- [ ] Código compilado localmente en macOS sin errores
- [ ] Código compilado localmente en Windows sin errores
- [ ] App macOS probada y funciona correctamente
- [ ] Exe Windows probado y funciona correctamente
- [ ] Audio procesado sin saturación/distorsión
- [ ] Tamaño de builds razonable (~280 MB macOS, ~95 MB Windows)
- [ ] ZIPs creados para distribución
- [ ] Release creado en GitHub con archivos adjuntos

---

## 📝 Notas Importantes

1. **Siempre usar Python 3.9.13** - Versiones diferentes pueden causar incompatibilidades
2. **Compilar Rust en modo `--release`** - El modo debug es mucho más lento
3. **No usar GitHub Actions** - Los builds locales funcionan mejor y son más confiables
4. **Verificar el módulo Rust** - Siempre verificar que `import novasdr_nr` funciona antes de compilar con PyInstaller
5. **Tamaños de referencia:**
   - macOS: ~280-300 MB
   - Windows: ~95-100 MB
   - Si son mucho más grandes, algo está mal

---

## 🆘 Soporte

Si encontrás problemas no cubiertos aquí, revisar:
- Logs de compilación en `audio_processor/build/` y `audio_processor/dist/`
- Verificar que todas las dependencias estén instaladas
- Limpiar builds anteriores: `rm -rf build dist` antes de recompilar
