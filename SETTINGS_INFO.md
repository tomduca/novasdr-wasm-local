# 💾 Persistent Settings

La aplicación **LU2MET NovaSDR NR Filter** ahora guarda automáticamente todas tus preferencias.

## ✅ Qué se Guarda

Cuando cerrás la aplicación, se guardan automáticamente:

- **Dispositivos de audio** (Input/Output seleccionados)
- **Modo** (SSB o CW)
- **Preset** (Moderate, Aggressive, Ultra, Extreme)
- **Input Gain** (1-100%)
- **Output Volume** (10-400%)
- **Bypass** (activado/desactivado)

## 📍 Dónde se Guardan

### Windows
Los settings se guardan en el **Registro de Windows**:
```
HKEY_CURRENT_USER\Software\LU2MET\NovaSDR_NR_Filter
```

Podés ver/editar con `regedit` si es necesario.

### macOS
Los settings se guardan en:
```
~/Library/Preferences/com.LU2MET.NovaSDR_NR_Filter.plist
```

### Linux
Los settings se guardan en:
```
~/.config/LU2MET/NovaSDR_NR_Filter.conf
```

## 🔄 Cómo Funciona

1. **Al abrir la app:** Se cargan automáticamente los últimos settings usados
2. **Al cerrar la app:** Se guardan automáticamente todos los settings actuales
3. **Primera vez:** Usa valores por defecto (Extreme preset, 5% input gain, 100% output volume)

## 🗑️ Resetear Settings

Si querés volver a los valores por defecto:

### Windows
```powershell
reg delete "HKEY_CURRENT_USER\Software\LU2MET\NovaSDR_NR_Filter" /f
```

### macOS
```bash
rm ~/Library/Preferences/com.LU2MET.NovaSDR_NR_Filter.plist
```

### Linux
```bash
rm ~/.config/LU2MET/NovaSDR_NR_Filter.conf
```

## 📝 Notas

- Los settings son **por usuario** (cada usuario de Windows/macOS tiene sus propios settings)
- Los settings **persisten** entre reinstalaciones de la app
- Si cambiás de dispositivos de audio, la app intentará usar los últimos que tenías configurados (si existen)
- Si un dispositivo guardado no existe, la app usa el dispositivo por defecto del sistema

## 🔧 Valores por Defecto

Si no hay settings guardados o los reseteás:

```
Mode: SSB
Preset: Extreme
Input Gain: 5%
Output Volume: 100%
Bypass: Off
Input Device: Sistema por defecto
Output Device: Sistema por defecto
```

---

**Implementado con:** `QSettings` de PyQt5 (método estándar multiplataforma)
