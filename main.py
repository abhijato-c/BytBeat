# Fucntions
# 1. Add song to songfile (Title, url) - compulsary, (artist, genre) - optional
# 2. List all undownloaded songs
# 3. List all files in music folder not in songfile
# 4. Download all undownloaded songs
# 5. List all songs in folder, then undownloaded ones, with option to delete any entry, either from folder or both folder and songfile
# 6. Update all images
# 7. Open images folder in appdata

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import os
import Backend as bk
import subprocess

class MusicManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Manager")
        #self.root.geometry("600x500")

        # Create UI Elements
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        # --- Section 1: Add New Song ---
        add_frame = tk.LabelFrame(self.root, text="Add New Song")
        add_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(add_frame, text="Title:").grid(row=0, column=0, padx=5, pady=2)
        self.title_entry = tk.Entry(add_frame, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(add_frame, text="URL:").grid(row=1, column=0, padx=5, pady=2)
        self.url_entry = tk.Entry(add_frame, width=30)
        self.url_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Button(add_frame, text="Add to List", command=self.action_add_song).grid(row=0, column=2, rowspan=2, padx=10)

        # --- Section 2: Song List ---
        list_frame = tk.LabelFrame(self.root, text="Library Status")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.configure("Treeview", rowheight=30)
        self.tree = ttk.Treeview(list_frame, columns=("Title", "Status"), show='headings', style='Treeview')
        self.tree.heading("Title", text="Song Title")
        self.tree.heading("Status", text="Status")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # --- Section 3: Actions ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        tk.Button(btn_frame, text="Download All", command=self.start_download_thread, bg="#4CAF50", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update Images", command=self.action_update_images).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Open Image Folder", command=self.action_open_images).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=self.action_delete_entry, fg="red").pack(side="right", padx=5)

    def refresh_list(self):
        # Refreshes the Treeview
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        undownloaded = bk.GetUndownloadedSongs()
        
        for index, row in bk.SongDF.iterrows():
            status = "Pending" if row['title'] in undownloaded else "Downloaded"
            self.tree.insert("", "end", values=(row['title'], status))

    def action_add_song(self):
        title = self.title_entry.get()
        url = self.url_entry.get()
        if title and url:
            bk.AddSongToSongfile(title, url)
            self.title_entry.delete(0, tk.END)
            self.url_entry.delete(0, tk.END)
            self.refresh_list()
        else:
            messagebox.showwarning("Input Error", "Please provide both a Title and a URL.")

    def start_download_thread(self):
        # Download song in a seperate thread so that the GUI doesn't freeze
        thread = threading.Thread(target=self.action_download_all, daemon=True)
        thread.start()

    def action_download_all(self):
        undownloaded_titles = bk.GetUndownloadedSongs()
        if not undownloaded_titles:
            messagebox.showinfo("Done", "All songs are already downloaded!")
            return

        for title in undownloaded_titles:
            # Get URL from DataFrame for this title
            url = bk.SongDF.loc[bk.SongDF['title'] == title, 'URL'].values[0]
            print(f"Starting download for: {title}")
            bk.DownloadSong(url, title)
            self.root.after(0, self.refresh_list) # Safely update UI from thread
            
        messagebox.showinfo("Success", "Download process completed!")

    def action_delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        title = self.tree.item(selected[0])['values'][0]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete '{title}' from list?")
        
        if confirm:
            # Update DataFrame and CSV
            bk.SongDF = bk.SongDF[bk.SongDF.title != title]
            bk.SaveSongfile()
            self.refresh_list()

    def action_update_images(self):
        # Re-runs metadata/image download for existing files
        for index, row in bk.SongDF.iterrows():
            bk.DownloadCover(row['URL'], row['title'])
            # Attempt to apply to mp3 by default for this batch update
            path = bk.MusicDir / f"{row['title']}.mp3"
            if path.exists():
                bk.AddCoverArt(path, bk.AppData/"Images"/(row['title']+'.jpg'), 'mp3')
        messagebox.showinfo("Update", "Images updated for found files.")

    def action_open_images(self):
        path = bk.AppData / "Images"
        if os.name == 'nt': # Windows
            os.startfile(path)
        elif os.name == 'posix': # macOS/Linux
            subprocess.Popen(['open' if bk.platform.system() == 'Darwin' else 'xdg-open', path])

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicManagerGUI(root)
    root.mainloop()