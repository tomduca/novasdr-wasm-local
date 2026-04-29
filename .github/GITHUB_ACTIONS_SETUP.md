# 🚀 Setup Rápido de GitHub Actions

## Paso 1: Subir el Workflow

```bash
cd /Users/tomasduca/CascadeProjects/nr_filter

# Agregar archivos
git add .github/

# Commit
git commit -m "Add automated build workflow for macOS and Windows"

# Push
git push origin main
```

## Paso 2: Configurar Permisos en GitHub

1. Abrí tu repositorio: `https://github.com/tomduca/novasdr-audio-processor`
2. **Settings** → **Actions** → **General**
3. En **Workflow permissions**:
   - ✅ Selecciona **Read and write permissions**
   - ✅ Marca **Allow GitHub Actions to create and approve pull requests**
4. **Save**

## Paso 3: Verificar que Funciona

1. Ve a **Actions** en GitHub
2. Deberías ver el workflow "Build macOS and Windows Apps" corriendo
3. Esperá ~15-20 minutos para que compile ambas apps
4. Una vez completo:
   - Click en el workflow
   - Bajá a **Artifacts**
   - Descargá `LU2MET_NR-macos.zip` y `LU2MET_NR-windows.zip`

## 🎉 ¡Listo!

Ahora cada vez que hagas push a `main`, se compilarán automáticamente ambas aplicaciones.

### Descargar Builds

**Opción 1: Desde Actions**
- GitHub → Actions → Click en el run → Artifacts

**Opción 2: Desde Releases** (automático)
- GitHub → Releases → Última versión

### Ejecutar Manualmente

1. GitHub → Actions
2. "Build macOS and Windows Apps"
3. **Run workflow** → **Run workflow**

---

## 📋 Checklist

- [ ] Workflow subido a GitHub
- [ ] Permisos configurados
- [ ] Primer build exitoso
- [ ] Artifacts descargables
- [ ] Apps funcionan correctamente

## ❓ Problemas?

Ver guía completa: `.github/workflows/WORKFLOW_GUIDE.md`

---

**73 de LU2MET** 📻
