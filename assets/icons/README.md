# Iconos de kps

Coloca aquí los archivos generados. Los scripts de build los leen automáticamente si existen.

## Archivos obligatorios (mínimo para cada plataforma)

| Archivo | Tamaño / formato | Uso |
|---------|------------------|-----|
| `kps.ico` | ICO multi-res (16, 32, 48, 256 px) | `dist/kps.exe` (Windows) |
| `kps.icns` | ICNS (macOS) | `dist/kps.app` (macOS) |
| `linux/kps.png` | **256×256** PNG RGBA | AppImage (raíz + `.DirIcon`) |
| `linux/hicolor/256x256/apps/kps.png` | **256×256** PNG | Menú de aplicaciones Linux |
| `kps-tray.png` | **64×64** PNG RGBA | Bandeja del sistema (`kps --tray`) |

## Suite Linux completa (recomendada)

Copia `kps.png` en cada carpeta bajo `linux/hicolor/<tamaño>/apps/`:

```
linux/hicolor/
  16x16/apps/kps.png
  22x22/apps/kps.png
  24x24/apps/kps.png
  32x32/apps/kps.png
  48x48/apps/kps.png
  64x64/apps/kps.png
  128x128/apps/kps.png
  256x256/apps/kps.png
  512x512/apps/kps.png
```

También deja `linux/kps.png` (256×256) en la raíz de `linux/`.

## Imagen base

| Archivo | Uso |
|---------|-----|
| `assets/image_base.png` | Fuente PNG (cualquier tamaño cuadrado; el script redimensiona) |
| `assets/image_base.icns` | ICNS listo para macOS (se copia a `kps.icns`; no hace falta redimensionar) |

Generar toda la suite:

```bash
./scripts/generate_icons.sh
```

Requiere **Pillow**. Si no hay `image_base.icns`, `kps.icns` se genera en **macOS** (`iconutil`) o con **ImageMagick**.

## Fuente de referencia (generada)

Tras ejecutar el script, se copia la base a `source/kps-base.png` dentro de este directorio.

## Verificar antes de empaquetar

```bash
./scripts/verify_icons.sh
```

## Builds que consumen estos iconos

| Script | Iconos usados |
|--------|----------------|
| `scripts/build_windows.bat` | `kps.ico` |
| `scripts/build_macos.sh` | `kps.icns` |
| `scripts/build_appimage.sh` | `linux/kps.png` + `linux/hicolor/**` |
| `kps --tray` | `kps-tray.png` (fallback: `linux/hicolor/64x64/apps/kps.png`) |

Si falta un archivo, el build continúa con aviso y sin icono en ese artefacto.
