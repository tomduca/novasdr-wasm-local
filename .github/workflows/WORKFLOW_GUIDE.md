# GitHub Actions Workflow Guide

## 📋 Qué Hace Este Workflow

Este workflow automáticamente compila las aplicaciones para **macOS** y **Windows** cuando:
- Haces push a la rama `main`
- Creas un Pull Request hacia `main`
- Lo ejecutas manualmente desde GitHub

## 🚀 Configuración Inicial

### 1. Subir el Workflow a GitHub

```bash
cd /Users/tomasduca/CascadeProjects/nr_filter

# Agregar los archivos del workflow
git add .github/workflows/build-apps.yml
git add .github/workflows/WORKFLOW_GUIDE.md

# Commit
git commit -m "Add GitHub Actions workflow for macOS and Windows builds"

# Push a main
git push origin main
```

### 2. Verificar Permisos en GitHub

1. Ve a tu repositorio en GitHub
2. Click en **Settings** → **Actions** → **General**
3. En **Workflow permissions**, selecciona:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### 3. Ejecutar el Workflow

#### Automático (Push a main)
```bash
git push origin main
```

#### Manual
1. Ve a tu repositorio en GitHub
2. Click en **Actions**
3. Selecciona **Build macOS and Windows Apps**
4. Click **Run workflow** → **Run workflow**

## 📦 Descargar las Aplicaciones Compiladas

### Desde Actions (Artifacts)
1. Ve a **Actions** en GitHub
2. Click en el workflow run más reciente
3. Baja hasta **Artifacts**
4. Descarga:
   - `LU2MET_NR-macos.zip` (macOS app)
   - `LU2MET_NR-windows.zip` (Windows exe)

### Desde Releases (Automático en main)
1. Ve a **Releases** en GitHub
2. Descarga la versión más reciente
3. Los archivos estarán disponibles como assets

## 🔍 Monitorear el Build

1. Ve a **Actions** en tu repositorio
2. Verás los workflows corriendo en tiempo real
3. Click en un workflow para ver los logs detallados
4. Si falla, revisa los logs para ver el error

## ⚙️ Estructura del Workflow

```yaml
build-macos:          # Compila la app de macOS
  - Setup Python 3.9
  - Install Rust
  - Build NovaSDR module
  - Build .app bundle
  - Upload artifact

build-windows:        # Compila la app de Windows
  - Setup Python 3.9
  - Install Rust
  - Build NovaSDR module
  - Build .exe
  - Upload artifact

create-release:       # Crea release automático (solo en main)
  - Download artifacts
  - Create GitHub release
  - Attach files
```

## 🐛 Troubleshooting

### Build falla en macOS
- Revisa que `build_macos.sh` tenga permisos de ejecución
- Verifica que todas las dependencias estén en `requirements.txt`

### Build falla en Windows
- Revisa que `build_windows.bat` esté correcto
- Verifica rutas de archivos (Windows usa `\` en vez de `/`)

### NovaSDR module no se encuentra
- El workflow compila el módulo Rust automáticamente
- Si falla, revisa los logs de "Build NovaSDR Rust module"

### Release no se crea
- Solo se crea en push a `main`, no en PRs
- Verifica permisos de GitHub Actions (paso 2)

## 📝 Personalización

### Cambiar cuando se ejecuta
Edita la sección `on:` en `build-apps.yml`:

```yaml
on:
  push:
    branches: [ main, develop ]  # Agregar más ramas
  release:
    types: [created]              # En releases
```

### Cambiar versión de Python
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.10'  # Cambiar versión
```

### Agregar notificaciones
Puedes agregar steps para notificar por email, Slack, etc.

## ✅ Verificación

Después de configurar, verifica:
- [ ] Workflow aparece en GitHub Actions
- [ ] Build de macOS completa exitosamente
- [ ] Build de Windows completa exitosamente
- [ ] Artifacts se pueden descargar
- [ ] Release se crea automáticamente en main

## 🎯 Próximos Pasos

1. **Testing automático**: Agregar tests antes del build
2. **Code signing**: Firmar las aplicaciones para distribución
3. **Notarización**: Notarizar la app de macOS con Apple
4. **Versioning**: Usar tags de git para versiones semánticas

---

**73 de LU2MET** 📻
