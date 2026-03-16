from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


@dataclass(frozen=True)
class CropBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def size(self) -> int:
        return self.right - self.left


class CropSelector:
    def __init__(self, image_path: Path, preview_max_size: int = 1000, parent: tk.Misc | None = None) -> None:
        self.image_path = image_path
        self.preview_max_size = preview_max_size
        self.parent = parent
        self.original = Image.open(image_path).convert("RGB")
        self.original_width, self.original_height = self.original.size
        self.square_size = min(self.original_width, self.original_height)
        self.scale = min(
            1.0,
            preview_max_size / self.original_width,
            preview_max_size / self.original_height,
        )
        self.preview_width = int(self.original_width * self.scale)
        self.preview_height = int(self.original_height * self.scale)
        self.preview_image = self.original.resize(
            (self.preview_width, self.preview_height),
            Image.Resampling.LANCZOS,
        )
        self.tk_image: ImageTk.PhotoImage | None = None
        self.root: tk.Tk | tk.Toplevel | None = None
        self.canvas: tk.Canvas | None = None
        self.overlay_id: int | None = None
        self.selection: CropBox | None = None

    def choose_crop(self) -> CropBox:
        if self.parent is None:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(self.parent)
            self.root.transient(self.parent)
            self.root.grab_set()
        self.root.title(f"Selection du carré - {self.image_path.name}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.cancel(None))

        title = tk.Label(
            self.root,
            text="Déplacez la souris pour voir le carré. Clic gauche pour valider. Entrée pour centrer. Échap pour annuler.",
            padx=12,
            pady=8,
        )
        title.pack()

        self.canvas = tk.Canvas(
            self.root,
            width=self.preview_width,
            height=self.preview_height,
            highlightthickness=0,
        )
        self.canvas.pack(padx=12, pady=(0, 12))

        self.tk_image = ImageTk.PhotoImage(self.preview_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.overlay_id = self.canvas.create_rectangle(0, 0, 0, 0, outline="#ff3b30", width=3)

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Return>", self.use_center_crop)
        self.root.bind("<Escape>", self.cancel)

        self.selection = self.center_crop()
        self.draw_overlay(self.selection)

        if self.parent is None:
            self.root.mainloop()
        else:
            self.parent.wait_window(self.root)

        if self.selection is None:
            raise RuntimeError("Selection annulée.")

        return self.selection

    def center_crop(self) -> CropBox:
        return self.compute_crop(self.original_width / 2, self.original_height / 2)

    def compute_crop(self, center_x: float, center_y: float) -> CropBox:
        half = self.square_size / 2
        left = max(0.0, min(center_x - half, self.original_width - self.square_size))
        top = max(0.0, min(center_y - half, self.original_height - self.square_size))
        return CropBox(
            left=int(round(left)),
            top=int(round(top)),
            right=int(round(left + self.square_size)),
            bottom=int(round(top + self.square_size)),
        )

    def draw_overlay(self, crop: CropBox) -> None:
        if self.canvas is None or self.overlay_id is None:
            return

        self.canvas.coords(
            self.overlay_id,
            crop.left * self.scale,
            crop.top * self.scale,
            crop.right * self.scale,
            crop.bottom * self.scale,
        )

    def on_mouse_move(self, event: tk.Event) -> None:
        x = event.x / self.scale
        y = event.y / self.scale
        self.selection = self.compute_crop(x, y)
        self.draw_overlay(self.selection)

    def on_left_click(self, event: tk.Event) -> None:
        self.on_mouse_move(event)
        if self.root is not None:
            self.close_window()

    def use_center_crop(self, _event: tk.Event) -> None:
        self.selection = self.center_crop()
        if self.root is not None:
            self.close_window()

    def cancel(self, _event: tk.Event) -> None:
        self.selection = None
        if self.root is not None:
            self.close_window()

    def close_window(self) -> None:
        if self.root is None:
            return
        if self.parent is not None:
            self.root.grab_release()
        self.root.destroy()


class CropApplication:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Rognage carré d'images")
        self.root.geometry("700x420")
        self.root.minsize(640, 380)

        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str((Path.cwd() / "sortie").resolve()))
        self.mode_var = tk.StringVar(value="image")
        self.status_var = tk.StringVar(value="Choisissez une image ou un dossier.")

        self.build_ui()

    def build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            container,
            text="Rogner des images en carré",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor=tk.W)

        subtitle = ttk.Label(
            container,
            text="Choisissez une image ou un dossier, puis cliquez sur Lancer. Une fenêtre de sélection s'ouvrira pour chaque image.",
            wraplength=640,
        )
        subtitle.pack(anchor=tk.W, pady=(6, 16))

        mode_frame = ttk.LabelFrame(container, text="Source", padding=12)
        mode_frame.pack(fill=tk.X)

        ttk.Radiobutton(mode_frame, text="Une image", value="image", variable=self.mode_var).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(mode_frame, text="Un dossier", value="folder", variable=self.mode_var).grid(row=0, column=1, sticky="w", padx=(16, 0))

        source_row = ttk.Frame(mode_frame)
        source_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        source_row.columnconfigure(0, weight=1)

        source_entry = ttk.Entry(source_row, textvariable=self.source_var)
        source_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(source_row, text="Parcourir", command=self.pick_source).grid(row=0, column=1, padx=(8, 0))

        output_frame = ttk.LabelFrame(container, text="Sortie", padding=12)
        output_frame.pack(fill=tk.X, pady=(16, 0))
        output_frame.columnconfigure(0, weight=1)

        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(output_frame, text="Choisir", command=self.pick_output).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(output_frame, text="Ouvrir", command=self.open_output_dir).grid(row=0, column=2, padx=(8, 0))

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(16, 0))
        ttk.Button(actions, text="Lancer le rognage", command=self.run).pack(side=tk.LEFT)
        ttk.Button(actions, text="Quitter", command=self.root.destroy).pack(side=tk.LEFT, padx=(8, 0))

        help_text = (
            "Dans la fenêtre de rognage : déplacez la souris pour déplacer le carré, "
            "cliquez pour valider, Entrée pour centrer, Échap pour ignorer l'image."
        )
        ttk.Label(container, text=help_text, wraplength=640, foreground="#444444").pack(anchor=tk.W, pady=(16, 8))
        ttk.Label(container, textvariable=self.status_var, foreground="#1f4e79").pack(anchor=tk.W, pady=(0, 8))

        self.log = tk.Text(container, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

    def pick_source(self) -> None:
        if self.mode_var.get() == "image":
            selected = filedialog.askopenfilename(
                title="Choisir une image",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff")],
            )
        else:
            selected = filedialog.askdirectory(title="Choisir un dossier d'images")

        if selected:
            self.source_var.set(selected)

    def pick_output(self) -> None:
        selected = filedialog.askdirectory(title="Choisir le dossier de sortie")
        if selected:
            self.output_var.set(selected)

    def append_log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def clear_log(self) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def open_output_dir(self) -> None:
        output_dir = Path(self.output_var.get().strip() or str(Path.cwd() / "sortie")).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(output_dir)

    def run(self) -> None:
        source_text = self.source_var.get().strip()
        output_text = self.output_var.get().strip()

        if not source_text:
            messagebox.showerror("Source manquante", "Choisissez une image ou un dossier.")
            return

        source = Path(source_text).expanduser().resolve()
        output_dir = Path(output_text).expanduser().resolve() if output_text else (Path.cwd() / "sortie").resolve()

        self.clear_log()
        self.append_log(f"Source: {source}")
        self.append_log(f"Sortie: {output_dir}")
        self.status_var.set("Analyse des images...")

        images = list(iter_images(source))
        if not images:
            messagebox.showerror("Aucune image", "Aucune image compatible trouvée.")
            self.status_var.set("Aucune image compatible trouvée.")
            return

        self.append_log(f"{len(images)} image(s) à traiter.")
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        skipped_count = 0

        for image_path in images:
            self.status_var.set(f"Traitement de {image_path.name}...")
            try:
                output_path = crop_image(image_path, output_dir, parent=self.root)
                saved_count += 1
                self.append_log(f"OK  {image_path.name} -> {output_path}")
            except RuntimeError as error:
                skipped_count += 1
                self.append_log(f"IGNORÉE  {image_path.name} -> {error}")
            except Exception as error:
                skipped_count += 1
                self.append_log(f"ERREUR  {image_path.name} -> {error}")

        self.status_var.set(f"Terminé. {saved_count} enregistrée(s), {skipped_count} ignorée(s).")

        if saved_count > 0:
            os.startfile(output_dir)
            messagebox.showinfo(
                "Terminé",
                f"{saved_count} image(s) enregistrée(s) dans :\n{output_dir}",
            )
        else:
            messagebox.showwarning("Aucun fichier créé", "Aucune image n'a été enregistrée.")

    def start(self) -> None:
        self.root.mainloop()


def iter_images(path: Path) -> Iterable[Path]:
    if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
        yield path
        return

    if path.is_dir():
        for file_path in sorted(path.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield file_path


def crop_image(image_path: Path, output_dir: Path, parent: tk.Misc | None = None) -> Path:
    selector = CropSelector(image_path, parent=parent)
    crop_box = selector.choose_crop()

    with Image.open(image_path) as image:
        cropped = image.crop((crop_box.left, crop_box.top, crop_box.right, crop_box.bottom))
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{image_path.stem}_carre{image_path.suffix}"
        cropped.save(output_path)
        return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rogne une image ou un dossier d'images au format carré en vous laissant choisir la zone à garder.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="Chemin vers une image ou un dossier contenant des images.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("sortie"),
        help="Dossier de sortie. Par défaut: ./sortie",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Ouvre l'interface graphique.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.gui or args.source is None:
        CropApplication().start()
        return 0

    source = args.source.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()

    images = list(iter_images(source))
    if not images:
        print("Aucune image compatible trouvée.")
        return 1

    for image_path in images:
        try:
            output_path = crop_image(image_path, output_dir)
            print(f"Image enregistrée: {output_path}")
        except RuntimeError as error:
            print(f"Image ignorée ({image_path.name}): {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())