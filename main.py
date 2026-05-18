import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
from collections import defaultdict
from datetime import datetime
import send2trash

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ScreenShorganiser(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ScreenShorganiser")
        self.geometry("1200x700")
        self.minsize(900, 600)

        self.folder_path = None
        self.screenshots = defaultdict(list)
        self.thumbnails = {}
        self.selected = set()

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top bar
        topbar = ctk.CTkFrame(self, height=50, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(topbar, text="Open Folder", width=120, command=self.open_folder).grid(row=0, column=0, padx=12, pady=10)
        self.folder_label = ctk.CTkLabel(topbar, text="No folder selected", text_color="gray")
        self.folder_label.grid(row=0, column=1, padx=8, sticky="w")
        self.delete_btn = ctk.CTkButton(topbar, text="Delete Selected", width=130, fg_color="#c0392b", hover_color="#922b21", command=self.delete_selected, state="disabled")
        self.delete_btn.grid(row=0, column=2, padx=12, pady=10)

        # Main scroll area
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        # Status bar
        self.statusbar = ctk.CTkLabel(self, text="Open a folder to get started", anchor="w", text_color="gray")
        self.statusbar.grid(row=2, column=0, sticky="ew", padx=12, pady=4)

    def open_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return
        self.folder_path = path
        self.folder_label.configure(text=path)
        self.load_screenshots()

    def load_screenshots(self):
        self.screenshots.clear()
        self.thumbnails.clear()
        self.selected.clear()

        exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
        for f in os.listdir(self.folder_path):
            if os.path.splitext(f)[1].lower() in exts:
                full_path = os.path.join(self.folder_path, f)
                mtime = os.path.getmtime(full_path)
                date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                self.screenshots[date].append(full_path)

        for date in self.screenshots:
            self.screenshots[date].sort(reverse=True)

        self.render_grid()

    def render_grid(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not self.screenshots:
            ctk.CTkLabel(self.scroll, text="No screenshots found in this folder.").grid(row=0, column=0, pady=40)
            return

        total = sum(len(v) for v in self.screenshots.values())
        self.statusbar.configure(text=f"{total} screenshots loaded — {len(self.screenshots)} days")

        row = 0
        for date in sorted(self.screenshots.keys(), reverse=True):
            files = self.screenshots[date]

            # Date header
            header = ctk.CTkFrame(self.scroll, fg_color="transparent")
            header.grid(row=row, column=0, sticky="ew", padx=12, pady=(16, 4))
            header.grid_columnconfigure(1, weight=1)

            select_all_btn = ctk.CTkButton(header, text="Select all", width=80, height=24, font=ctk.CTkFont(size=12), command=lambda d=date: self.select_day(d))
            select_all_btn.grid(row=0, column=0, padx=(0, 10))
            ctk.CTkLabel(header, text=f"{date}  ·  {len(files)} files", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(row=0, column=1, sticky="w")

            row += 1

            # Thumbnail grid
            thumb_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
            thumb_frame.grid(row=row, column=0, sticky="ew", padx=12)

            cols = 10
            for i, filepath in enumerate(files):
                thumb = self.get_thumbnail(filepath)
                is_selected = filepath in self.selected

                btn = ctk.CTkButton(
                    thumb_frame,
                    image=thumb,
                    text="",
                    width=100, height=60,
                    fg_color="#2980b9" if is_selected else "#2b2b2b",
                    hover_color="#3498db",
                    border_width=2 if is_selected else 0,
                    border_color="#5dade2" if is_selected else "#2b2b2b",
                    command=lambda fp=filepath: self.toggle_select(fp)
                )
                btn.grid(row=i // cols, column=i % cols, padx=3, pady=3)

            row += 1

        self.update_status()

    def get_thumbnail(self, filepath):
        if filepath in self.thumbnails:
            return self.thumbnails[filepath]
        try:
            img = Image.open(filepath)
            img.thumbnail((100, 60))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 60))
            self.thumbnails[filepath] = ctk_img
            return ctk_img
        except:
            return None

    def toggle_select(self, filepath):
        if filepath in self.selected:
            self.selected.discard(filepath)
        else:
            self.selected.add(filepath)
        self.render_grid()

    def select_day(self, date):
        files = self.screenshots[date]
        all_selected = all(f in self.selected for f in files)
        if all_selected:
            for f in files:
                self.selected.discard(f)
        else:
            for f in files:
                self.selected.add(f)
        self.render_grid()

    def update_status(self):
        total = sum(len(v) for v in self.screenshots.values())
        sel = len(self.selected)
        self.statusbar.configure(text=f"{total} screenshots · {sel} selected")
        self.delete_btn.configure(state="normal" if sel > 0 else "disabled")

    def delete_selected(self):
        if not self.selected:
            return
        for filepath in list(self.selected):
            try:
                send2trash.send2trash(os.path.abspath(filepath))
            except Exception as e:
                print(f"Error deleting {filepath}: {e}")
        self.selected.clear()
        self.load_screenshots()

if __name__ == "__main__":
    app = ScreenShorganiser()
    app.mainloop()