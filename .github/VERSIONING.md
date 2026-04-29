# 📌 Sistema de Versionado

## Formato de Versión

Cada build automático genera una versión única:

```
v1.0.0-beta-YYYYMMDD-HHMMSS-commit
```

### Componentes

- **v1.0.0-beta**: Versión base del proyecto
- **YYYYMMDD**: Fecha del build (año-mes-día)
- **HHMMSS**: Hora del build (hora-minuto-segundo)
- **commit**: Hash corto del commit de git (7 caracteres)

### Ejemplos

```
v1.0.0-beta-20260429-091530-a3f2c1b
v1.0.0-beta-20260429-143022-7b9e4d2
v1.0.0-beta-20260430-080015-c5a1f8e
```

## Artifacts

### Nombres de Archivos

**macOS:**
```
LU2MET_NR-macos-v1.0.0-beta-20260429-091530-a3f2c1b.zip
```

**Windows:**
```
LU2MET_NR-windows-v1.0.0-beta-20260429-091530-a3f2c1b.zip
```

### Retención

- **Duración**: 90 días
- **Ubicación**: GitHub Actions → Artifacts
- **Acceso**: Cualquier build, incluso de PRs

## Releases

### Tags

Cada release en `main` crea un tag único:

```
v1.0.0-beta-20260429-091530-a3f2c1b
```

### Características

- ✅ **No se sobreescriben**: Cada release queda guardado permanentemente
- ✅ **Historial completo**: Podés volver a cualquier versión anterior
- ✅ **Prerelease**: Marcados como "Pre-release" (beta)
- ✅ **Changelog**: Incluye el mensaje del commit

### Estructura del Release

```
LU2MET NR Filter v1.0.0-beta-20260429-091530-a3f2c1b
├── LU2MET_NR-macos-v1.0.0-beta-20260429-091530-a3f2c1b.zip
└── LU2MET_NR-windows-v1.0.0-beta-20260429-091530-a3f2c1b.zip
```

## Encontrar Versiones Antiguas

### Desde Actions

1. GitHub → **Actions**
2. Selecciona el workflow run que querés
3. Bajá a **Artifacts**
4. Descargá el ZIP con la versión específica

### Desde Releases

1. GitHub → **Releases**
2. Todas las versiones están listadas
3. Click en la versión que necesitás
4. Descargá los assets (ZIPs)

## Comparar Versiones

### Por Fecha

```bash
# Ordenadas cronológicamente
v1.0.0-beta-20260429-091530-a3f2c1b  # Más antigua
v1.0.0-beta-20260429-143022-7b9e4d2
v1.0.0-beta-20260430-080015-c5a1f8e  # Más reciente
```

### Por Commit

```bash
# Ver cambios entre versiones
git log a3f2c1b..c5a1f8e --oneline
```

## Cambiar Versión Base

Para cambiar de `v1.0.0-beta` a `v1.0.0` o `v1.1.0`:

1. Edita `.github/workflows/build-apps.yml`
2. Busca `VERSION="v1.0.0-beta-..."`
3. Cambia `v1.0.0-beta` por la nueva versión
4. Commit y push

```yaml
# Ejemplo: cambiar a v1.0.0 (release estable)
VERSION="v1.0.0-$(date +'%Y%m%d-%H%M%S')-$(git rev-parse --short HEAD)"

# Ejemplo: cambiar a v1.1.0 (nueva feature)
VERSION="v1.1.0-beta-$(date +'%Y%m%d-%H%M%S')-$(git rev-parse --short HEAD)"
```

## Ventajas del Sistema

- ✅ **Trazabilidad**: Cada build vinculado a un commit específico
- ✅ **Rollback fácil**: Volver a cualquier versión anterior
- ✅ **Testing**: Probar diferentes versiones en paralelo
- ✅ **Backup automático**: Todas las versiones guardadas
- ✅ **Sin conflictos**: Nunca se sobreescriben builds
- ✅ **Timestamp preciso**: Saber exactamente cuándo se compiló

## Limpieza

### Artifacts (automático)

- Se eliminan automáticamente después de 90 días
- No requiere acción manual

### Releases (manual)

Para eliminar releases antiguos:

1. GitHub → **Releases**
2. Click en el release a eliminar
3. **Delete** → Confirmar
4. **También eliminar el tag** si querés

---

**73 de LU2MET** 📻
