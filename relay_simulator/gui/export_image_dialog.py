"""Export Image dialog with live preview.

Provides a modal UI to export the visible viewport or full content extents
from the design canvas to a PNG file, with background + grid options.

This dialog is intentionally GUI-focused and delegates rendering to
`gui.canvas_exporter`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import time

from gui.theme import VSCodeTheme
from gui.canvas_exporter import CanvasExportOptions, CanvasExportError, canvas_to_pil_image


@dataclass
class ExportDialogResult:
    saved_path: Optional[str] = None


class ExportImageDialog:
    def __init__(
        self,
        parent: tk.Tk,
        *,
        canvas: tk.Canvas,
        default_mode: str = "visible",
        suggested_filename: str = "canvas.png",
    ) -> None:
        self._parent = parent
        self._canvas = canvas

        self._dialog = tk.Toplevel(parent)
        self._dialog.title("Export Image")
        self._dialog.geometry("920x640")
        self._dialog.transient(parent)
        self._dialog.grab_set()

        self.result = ExportDialogResult()

        # State vars
        self._mode_var = tk.StringVar(value=default_mode)
        self._bg_var = tk.StringVar(value="white")
        self._grid_var = tk.BooleanVar(value=False)
        self._scale_var = tk.StringVar(value="4x")
        self._filename_var = tk.StringVar(value=str(Path(suggested_filename)))

        self._preview_photo = None
        self._preview_image = None

        self._create_ui()
        self._center_dialog()

        # Initial render after layout so the preview widget has a real size.
        self._dialog.after(50, self._refresh_preview)

    def show(self) -> ExportDialogResult:
        self._dialog.wait_window()
        return self.result

    def _center_dialog(self) -> None:
        try:
            self._dialog.update_idletasks()
            px = self._parent.winfo_rootx()
            py = self._parent.winfo_rooty()
            pw = self._parent.winfo_width()
            ph = self._parent.winfo_height()
            dw = self._dialog.winfo_width()
            dh = self._dialog.winfo_height()
            x = px + (pw - dw) // 2
            y = py + (ph - dh) // 2
            self._dialog.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _create_ui(self) -> None:
        outer = ttk.Frame(self._dialog, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        outer.columnconfigure(0, weight=0)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        # Left controls
        controls = ttk.Frame(outer)
        controls.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        ttk.Label(controls, text="Export settings", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        ttk.Label(controls, text="Region:").pack(anchor="w", pady=(12, 2))
        mode_combo = ttk.Combobox(
            controls,
            textvariable=self._mode_var,
            values=["visible", "full"],
            state="readonly",
            width=16,
        )
        mode_combo.pack(anchor="w")
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_preview())

        ttk.Label(controls, text="Background:").pack(anchor="w", pady=(12, 2))
        bg_combo = ttk.Combobox(
            controls,
            textvariable=self._bg_var,
            values=["black", "white"],
            state="readonly",
            width=16,
        )
        bg_combo.pack(anchor="w")
        bg_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_preview())

        grid_check = ttk.Checkbutton(
            controls,
            text="Include grid",
            variable=self._grid_var,
            command=self._refresh_preview,
        )
        grid_check.pack(anchor="w", pady=(12, 0))

        ttk.Label(controls, text="Resolution:").pack(anchor="w", pady=(12, 2))
        scale_combo = ttk.Combobox(
            controls,
            textvariable=self._scale_var,
            values=["1x", "2x", "3x", "4x"],
            state="readonly",
            width=16,
        )
        scale_combo.pack(anchor="w")
        scale_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_preview())

        ttk.Separator(controls, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        ttk.Label(controls, text="Filename:").pack(anchor="w")
        filename_entry = ttk.Entry(controls, textvariable=self._filename_var, width=38)
        filename_entry.pack(anchor="w", pady=(2, 4))

        browse_btn = ttk.Button(controls, text="Browse...", command=self._browse)
        browse_btn.pack(anchor="w")

        ttk.Separator(controls, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        btn_row = ttk.Frame(controls)
        btn_row.pack(fill=tk.X)

        refresh_btn = ttk.Button(btn_row, text="Refresh preview", command=self._refresh_preview)
        refresh_btn.pack(side=tk.LEFT)

        export_btn = ttk.Button(btn_row, text="Export PNG", command=self._export)
        export_btn.pack(side=tk.RIGHT)

        cancel_btn = ttk.Button(controls, text="Close", command=self._dialog.destroy)
        cancel_btn.pack(anchor="e", pady=(12, 0))

        # Right preview panel
        preview_frame = ttk.Frame(outer)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)

        ttk.Label(preview_frame, text="Preview", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")

        self._preview_label = tk.Label(
            preview_frame,
            bg=VSCodeTheme.BG_PRIMARY,
            bd=1,
            relief=tk.SOLID,
        )
        self._preview_label.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        self._status_var = tk.StringVar(value="")
        status = ttk.Label(preview_frame, textvariable=self._status_var)
        status.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        self._dialog.bind("<Escape>", lambda e: self._dialog.destroy())

    def _browse(self) -> None:
        suggested = self._filename_var.get().strip() or "canvas.png"
        try:
            initialfile = Path(suggested).name
        except Exception:
            initialfile = "canvas.png"

        path = filedialog.asksaveasfilename(
            parent=self._dialog,
            title="Export PNG",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            initialfile=initialfile,
        )
        if path:
            self._filename_var.set(path)

    def _options(self) -> CanvasExportOptions:
        # Scale: higher = larger pixel output (sharper), but bigger files.
        scale_str = (self._scale_var.get() or "1x").strip().lower().replace("x", "")
        try:
            scale = float(scale_str)
        except Exception:
            scale = 1.0
        if scale <= 0:
            scale = 1.0

        return CanvasExportOptions(
            mode=self._mode_var.get(),
            background=self._bg_var.get(),
            include_grid=bool(self._grid_var.get()),
            invert_white_on_white_bg=True,
            padding=40,
            scale=scale,
        )

    def _capture_with_dialog_hidden(self):
        """Capture image while ensuring this dialog isn't on top of the canvas.

        This is required for visible-mode capture which uses screen grabbing.
        """
        # Hide this dialog so it can't appear in the screenshot.
        # (withdraw is more reliable than lower on Windows.)
        was_visible = True
        try:
            was_visible = bool(self._dialog.winfo_viewable())
        except Exception:
            was_visible = True

        try:
            if was_visible:
                self._dialog.withdraw()
                # Let the window manager repaint.
                try:
                    self._parent.update_idletasks()
                    self._parent.update()
                except Exception:
                    pass
                time.sleep(0.05)

            img = canvas_to_pil_image(canvas=self._canvas, options=self._options())
            return img
        finally:
            if was_visible:
                try:
                    self._dialog.deiconify()
                    self._dialog.lift()
                    self._dialog.grab_set()
                except Exception:
                    pass

    def _refresh_preview(self) -> None:
        self._status_var.set("Rendering preview...")
        self._dialog.update_idletasks()

        try:
            if (self._mode_var.get() or "").strip().lower() == "visible":
                img = self._capture_with_dialog_hidden()
            else:
                img = canvas_to_pil_image(canvas=self._canvas, options=self._options())
        except Exception as e:
            self._preview_photo = None
            self._preview_image = None
            self._preview_label.config(image="", text="")
            self._status_var.set(str(e))
            return

        # Fit into preview box
        try:
            from PIL import ImageTk  # type: ignore
        except Exception as e:
            self._status_var.set("Preview requires Pillow ImageTk")
            return

        self._preview_image = img

        # Determine available size
        try:
            self._preview_label.update_idletasks()
            max_w = int(self._preview_label.winfo_width())
            max_h = int(self._preview_label.winfo_height())
        except Exception:
            max_w, max_h = 0, 0

        # If the widget hasn't been sized yet, use a sensible fallback.
        if max_w < 50 or max_h < 50:
            max_w, max_h = 640, 480

        preview = img.copy()
        target_w = max(1, max_w - 12)
        target_h = max(1, max_h - 12)
        preview.thumbnail((target_w, target_h))

        self._preview_photo = ImageTk.PhotoImage(preview)
        self._preview_label.config(image=self._preview_photo)
        self._status_var.set(f"{img.width}x{img.height} px")

    def _export(self) -> None:
        path = self._filename_var.get().strip()
        if not path:
            messagebox.showinfo("Export", "Choose a filename to export to.", parent=self._dialog)
            return

        # Ensure extension
        out_path = Path(path)
        if out_path.suffix.lower() != ".png":
            out_path = out_path.with_suffix(".png")

        try:
            if (self._mode_var.get() or "").strip().lower() == "visible":
                img = self._capture_with_dialog_hidden()
            else:
                img = canvas_to_pil_image(canvas=self._canvas, options=self._options())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(out_path), format="PNG")
        except CanvasExportError as e:
            messagebox.showerror("Export Failed", str(e), parent=self._dialog)
            return
        except FileNotFoundError as e:
            messagebox.showerror("Export Failed", str(e), parent=self._dialog)
            return
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self._dialog)
            return

        self.result.saved_path = str(out_path)
        messagebox.showinfo("Export", f"Exported: {out_path.name}", parent=self._dialog)
        self._dialog.destroy()
