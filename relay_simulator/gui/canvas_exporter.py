"""Canvas export helpers (Tk canvas -> PIL image).

This module converts a tkinter Canvas region to a raster image via:
- Canvas.postscript()
- Ghostscript (ps -> PNG)
- Pillow (PNG -> PIL.Image)

It also supports export-time tweaks:
- Optional background rectangle (black/white)
- Optional grid visibility (hide/show items tagged 'grid')
- Optional inversion of "white" drawn content when background is white

Notes:
- Full-canvas export is typically done at zoom=1.0.
- This module does not depend on simulator engine code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import os
import re
import shutil
import subprocess
import tempfile


@dataclass(frozen=True)
class CanvasExportOptions:
    mode: str  # 'visible' | 'full'
    background: str  # 'black' | 'white'
    include_grid: bool
    invert_white_on_white_bg: bool = True
    padding: int = 40
    scale: float = 2.0


class CanvasExportError(RuntimeError):
    pass


def _normalize_color_string(color: str) -> str:
    return str(color or "").strip().lower()


def _is_near_white_rgb(r: int, g: int, b: int, threshold: int = 245) -> bool:
    return r >= threshold and g >= threshold and b >= threshold


def _is_grayish_rgb(r: int, g: int, b: int, *, max_channel_delta: int = 18, min_brightness: int = 120) -> bool:
    """Return True for neutral-ish grays that will be hard to read on white.

    We intentionally avoid changing colored text (e.g. red/green labels).
    """
    if abs(r - g) > max_channel_delta or abs(g - b) > max_channel_delta or abs(r - b) > max_channel_delta:
        return False
    # Perceived brightness (approx). If it's already dark, keep it.
    brightness = int(0.2126 * r + 0.7152 * g + 0.0722 * b)
    return brightness >= min_brightness


def _tk_color_to_rgb_8bit(canvas, color: str) -> Optional[Tuple[int, int, int]]:
    """Convert a Tk color string to 8-bit RGB using the given canvas."""
    c = _normalize_color_string(color)
    if not c:
        return None

    # Fast-path for hex colors.
    if c.startswith("#") and len(c) in (4, 7):
        try:
            if len(c) == 4:
                r = int(c[1] * 2, 16)
                g = int(c[2] * 2, 16)
                b = int(c[3] * 2, 16)
            else:
                r = int(c[1:3], 16)
                g = int(c[3:5], 16)
                b = int(c[5:7], 16)
            return r, g, b
        except Exception:
            return None

    try:
        # winfo_rgb returns 0..65535
        r16, g16, b16 = canvas.winfo_rgb(color)
        return r16 // 257, g16 // 257, b16 // 257
    except Exception:
        return None


def _is_whiteish(canvas, color: str) -> bool:
    rgb = _tk_color_to_rgb_8bit(canvas, color)
    if not rgb:
        return False
    return _is_near_white_rgb(*rgb)


def _is_grayish(canvas, color: str) -> bool:
    rgb = _tk_color_to_rgb_8bit(canvas, color)
    if not rgb:
        return False
    return _is_grayish_rgb(*rgb)


def _find_ghostscript_executable(user_hint: Optional[str] = None) -> str:
    """Locate Ghostscript executable on Windows/macOS/Linux."""

    candidates: List[Path] = []
    seen: set[str] = set()

    def add_candidate(path_like: Optional[str]) -> None:
        if not path_like:
            return
        try:
            p = Path(path_like)
        except Exception:
            return
        if p.is_file():
            key = str(p.resolve()).lower()
            if key not in seen:
                candidates.append(p)
                seen.add(key)

    def add_directory(directory: Optional[str]) -> None:
        if not directory:
            return
        try:
            d = Path(directory)
        except Exception:
            return
        if not d.is_dir():
            return
        for exe_name in ("gswin64c.exe", "gswin32c.exe", "gs.exe"):
            add_candidate(str(d / "bin" / exe_name))
            add_candidate(str(d / exe_name))

    # 1) User hint
    add_directory(user_hint)

    # 2) Environment variables
    add_directory(os.environ.get("GHOSTSCRIPT_PATH"))
    add_directory(os.environ.get("GHOSTSCRIPT_HOME"))

    # 3) PATH
    for exe in ("gswin64c", "gswin32c", "gs"):
        p = shutil.which(exe)
        if p:
            add_candidate(p)

    # 4) Common install dirs (Windows)
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pfx86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    for root in (Path(pf) / "gs", Path(pfx86) / "gs"):
        if root.exists() and root.is_dir():
            try:
                for version_dir in sorted(root.iterdir(), reverse=True):
                    add_directory(str(version_dir))
            except Exception:
                pass

    for c in candidates:
        if c.is_file():
            return str(c)

    raise FileNotFoundError(
        "Ghostscript executable not found.\n\n"
        "Install Ghostscript from:\n"
        "https://www.ghostscript.com/releases/gsdnld.html\n\n"
        "Then ensure gswin64c.exe is on PATH, or set GHOSTSCRIPT_PATH."
    )


def _postscript_to_png_bytes(
    ps_data: str,
    *,
    pixel_width: int,
    pixel_height: int,
    dpi: int,
    ghostscript_hint: Optional[str] = None,
) -> bytes:
    gs = _find_ghostscript_executable(ghostscript_hint)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ps", mode="w", encoding="utf-8") as tmp_ps:
        tmp_ps.write(ps_data)
        ps_path = tmp_ps.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_png:
        png_path = tmp_png.name

    try:
        cmd = [
            gs,
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=pngalpha",
            "-dGraphicsAlphaBits=4",
            "-dTextAlphaBits=4",
            f"-r{max(72, int(dpi))}",
            f"-g{max(1, int(pixel_width))}x{max(1, int(pixel_height))}",
            f"-sOutputFile={png_path}",
            ps_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        return Path(png_path).read_bytes()

    except subprocess.CalledProcessError as exc:
        stderr = ""
        try:
            stderr = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else ""
        except Exception:
            stderr = ""
        raise CanvasExportError(
            "Ghostscript conversion failed.\n\n"
            f"{stderr.strip()}"
        ) from exc
    finally:
        for p in (ps_path, png_path):
            try:
                os.unlink(p)
            except Exception:
                pass


def _compute_visible_region(canvas) -> Tuple[int, int, int, int]:
    """Return (x, y, width, height) in canvas coordinates for the visible viewport."""
    x0 = int(canvas.canvasx(0))
    y0 = int(canvas.canvasy(0))
    w = int(canvas.winfo_width())
    h = int(canvas.winfo_height())
    # Canvas.postscript expects x,y,width,height in canvas coordinates.
    return x0, y0, max(1, w), max(1, h)


def _compute_content_bounds(canvas, *, padding: int) -> Optional[Tuple[int, int, int, int]]:
    """Return (x, y, width, height) for the bbox of non-grid items."""
    # Exclude grid tag if present (grid covers entire scrollregion).
    all_items = canvas.find_all()
    if not all_items:
        return None

    def is_grid_item(item_id: int) -> bool:
        try:
            return "grid" in canvas.gettags(item_id)
        except Exception:
            return False

    min_x = min_y = None
    max_x = max_y = None

    for item_id in all_items:
        if is_grid_item(item_id):
            continue
        try:
            bbox = canvas.bbox(item_id)
        except Exception:
            bbox = None
        if not bbox:
            continue
        x1, y1, x2, y2 = bbox
        min_x = x1 if min_x is None else min(min_x, x1)
        min_y = y1 if min_y is None else min(min_y, y1)
        max_x = x2 if max_x is None else max(max_x, x2)
        max_y = y2 if max_y is None else max(max_y, y2)

    if min_x is None or min_y is None or max_x is None or max_y is None:
        return None

    min_x -= int(padding)
    min_y -= int(padding)
    max_x += int(padding)
    max_y += int(padding)

    # Clamp to the canvas scrollregion origin; Tk postscript behaves poorly
    # when asked to render negative regions.
    min_x = max(0, int(min_x))
    min_y = max(0, int(min_y))
    max_x = max(min_x + 1, int(max_x))
    max_y = max(min_y + 1, int(max_y))

    width = max(1, int(max_x - min_x))
    height = max(1, int(max_y - min_y))
    return int(min_x), int(min_y), width, height


def _extract_ps_bbox(ps_content: str) -> Optional[Tuple[int, int, int, int]]:
    m = re.search(r"%%BoundingBox:\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", ps_content)
    if not m:
        return None
    try:
        return tuple(int(p) for p in m.groups())  # type: ignore[return-value]
    except Exception:
        return None


def _normalize_postscript_bbox(ps_content: str, bbox: Tuple[int, int, int, int]) -> str:
    """Translate PostScript so the BoundingBox starts at (0,0)."""
    min_x, min_y, max_x, max_y = bbox
    shift_x = -min_x
    shift_y = -min_y
    if shift_x == 0 and shift_y == 0:
        return ps_content

    injection = f"{shift_x} {shift_y} translate\n"
    marker = "%%EndProlog\n"
    idx = ps_content.find(marker)
    if idx != -1:
        idx += len(marker)
        ps_content = ps_content[:idx] + injection + ps_content[idx:]
    else:
        ps_content = injection + ps_content

    new_bbox = (min_x + shift_x, min_y + shift_y, max_x + shift_x, max_y + shift_y)
    ps_content = re.sub(
        r"%%BoundingBox:\s*-?\d+\s+-?\d+\s+-?\d+\s+-?\d+",
        f"%%BoundingBox: {new_bbox[0]} {new_bbox[1]} {new_bbox[2]} {new_bbox[3]}",
        ps_content,
        count=1,
    )
    ps_content = re.sub(
        r"%%HiResBoundingBox:\s*-?[\d\.]+\s+-?[\d\.]+\s+-?[\d\.]+\s+-?[\d\.]+",
        f"%%HiResBoundingBox: {float(new_bbox[0]):.3f} {float(new_bbox[1]):.3f} {float(new_bbox[2]):.3f} {float(new_bbox[3]):.3f}",
        ps_content,
        count=1,
    )
    return ps_content


def _snapshot_item_configs(canvas, item_ids: Iterable[int], options: Iterable[str]) -> Dict[int, Dict[str, str]]:
    snap: Dict[int, Dict[str, str]] = {}
    for item_id in item_ids:
        item_snap: Dict[str, str] = {}
        for opt in options:
            try:
                item_snap[opt] = canvas.itemcget(item_id, opt)
            except Exception:
                continue
        if item_snap:
            snap[item_id] = item_snap
    return snap


def _restore_item_configs(canvas, snapshot: Dict[int, Dict[str, str]]) -> None:
    for item_id, opts in snapshot.items():
        for k, v in opts.items():
            try:
                canvas.itemconfig(item_id, **{k: v})
            except Exception:
                pass


def canvas_to_pil_image(
    *,
    canvas,
    options: CanvasExportOptions,
    ghostscript_hint: Optional[str] = None,
) -> "object":
    """Render a tkinter Canvas to a PIL Image (requires Pillow at runtime)."""

    try:
        from PIL import Image  # type: ignore
    except Exception as e:
        raise CanvasExportError("Export requires Pillow. Install it with: pip install Pillow") from e

    mode = (options.mode or "").strip().lower()
    if mode not in {"visible", "full"}:
        raise CanvasExportError(f"Invalid export mode: {options.mode}")

    bg = (options.background or "").strip().lower()
    if bg not in {"black", "white"}:
        raise CanvasExportError(f"Invalid background: {options.background}")

    invert_whites = bool(options.invert_white_on_white_bg) and bg == "white"
    # Always ensure neutral gray text is readable on white background.
    convert_gray_text = bg == "white"

    # Scale factor for raster output. Increasing scale increases output resolution
    # and makes lines/text appear sharper.
    try:
        export_scale = float(getattr(options, "scale", 1.0) or 1.0)
    except Exception:
        export_scale = 1.0
    if export_scale <= 0:
        export_scale = 1.0

    # Collect items for possible modification.
    all_items = list(canvas.find_all())

    # Track what we change so we can restore.
    grid_items = list(canvas.find_withtag("grid"))
    grid_state_snapshot = _snapshot_item_configs(canvas, grid_items, ["state"])

    # Inversion snapshot: fill/outline for shapes + fill for text.
    invert_snapshot = _snapshot_item_configs(canvas, all_items, ["fill", "outline"])

    export_bg_id: Optional[int] = None

    # For 'full' mode we export the content bounds in current canvas coords.
    # The calling UI should prepare zoom=1 if it wants a true 1:1 world export.

    try:
        # Optionally hide grid items.
        if not options.include_grid:
            for item_id in grid_items:
                try:
                    canvas.itemconfig(item_id, state="hidden")
                except Exception:
                    pass

        # Compute region.
        if mode == "visible":
            x, y, width, height = _compute_visible_region(canvas)
        else:
            bounds = _compute_content_bounds(canvas, padding=options.padding)
            if not bounds:
                raise CanvasExportError("No content found on canvas to export")
            x, y, width, height = bounds

        # Add background rectangle covering export region.
        fill = "#FFFFFF" if bg == "white" else "#000000"
        try:
            export_bg_id = canvas.create_rectangle(
                x,
                y,
                x + width,
                y + height,
                fill=fill,
                outline="",
                tags=("export_bg",),
            )
            canvas.tag_lower(export_bg_id)
        except Exception:
            export_bg_id = None

        # If exporting on white background:
        # - Invert near-white strokes/fills (so white wires/text are visible)
        # - Convert neutral gray text fills to black for readability
        if invert_whites or convert_gray_text:
            for item_id in all_items:
                if export_bg_id and item_id == export_bg_id:
                    continue

                item_type = None
                try:
                    item_type = canvas.type(item_id)
                except Exception:
                    item_type = None

                # Neutral gray text -> black
                if convert_gray_text and item_type == "text":
                    try:
                        current_fill = canvas.itemcget(item_id, "fill")
                    except Exception:
                        current_fill = ""
                    if current_fill and _is_grayish(canvas, current_fill):
                        try:
                            canvas.itemconfig(item_id, fill="#000000")
                        except Exception:
                            pass

                # Near-white shapes/text -> black
                if invert_whites:
                    for opt in ("fill", "outline"):
                        try:
                            current = canvas.itemcget(item_id, opt)
                        except Exception:
                            continue
                        if not current:
                            continue
                        if _is_whiteish(canvas, current):
                            try:
                                canvas.itemconfig(item_id, **{opt: "#000000"})
                            except Exception:
                                pass

        # Ensure Tk has drawn everything.
        try:
            # update() is important for ImageGrab accuracy
            canvas.update()
        except Exception:
            try:
                canvas.update_idletasks()
            except Exception:
                pass

        # Visible export: capture the actual onscreen canvas pixels so the preview
        # matches what the user sees (including zoom/pan).
        if mode == "visible":
            try:
                from PIL import ImageGrab  # type: ignore
            except Exception as e:
                raise CanvasExportError(
                    "Visible preview/export requires Pillow ImageGrab support."
                ) from e

            x0 = int(canvas.winfo_rootx())
            y0 = int(canvas.winfo_rooty())
            x1 = x0 + int(canvas.winfo_width())
            y1 = y0 + int(canvas.winfo_height())
            if x1 <= x0 or y1 <= y0:
                raise CanvasExportError("Canvas is not visible (invalid widget bounds)")
            return ImageGrab.grab(bbox=(x0, y0, x1, y1))

        # Full export: use PostScript so we can capture offscreen content.
        ps_data = canvas.postscript(
            colormode="color",
            x=x,
            y=y,
            width=width,
            height=height,
            pagewidth=f"{width}p",
            pageheight=f"{height}p",
        )

        # Normalize BoundingBox to (0,0) to avoid Ghostscript clipping.
        bbox = _extract_ps_bbox(ps_data)
        if bbox is not None:
            ps_data = _normalize_postscript_bbox(ps_data, bbox)

        # Rasterize at higher DPI for crisper output.
        dpi = int(round(72 * export_scale))
        pixel_w = int(round(width * export_scale))
        pixel_h = int(round(height * export_scale))

        png_bytes = _postscript_to_png_bytes(
            ps_data,
            pixel_width=pixel_w,
            pixel_height=pixel_h,
            dpi=dpi,
            ghostscript_hint=ghostscript_hint,
        )

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(png_bytes)
            tmp_path = tmp.name
        try:
            img = Image.open(tmp_path)
            out = img.copy()
            img.close()
            return out
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    finally:
        # Cleanup background
        if export_bg_id is not None:
            try:
                canvas.delete(export_bg_id)
            except Exception:
                pass

        # Restore grid visibility
        _restore_item_configs(canvas, grid_state_snapshot)

        # Restore colors
        _restore_item_configs(canvas, invert_snapshot)
