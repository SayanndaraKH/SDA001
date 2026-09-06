import os

TARGET = r"C:\Users\Administrator\Desktop\SYD-8Move\app\downloader.py"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# Modify _run_poster_download to save to both drama dir and Posters gallery dir
target_block = """            with self.lock:
                task.status = "completed"
                task.progress = 100.0
                task.size_bytes = len(data)
                task.completed_at = time.time()
                self.history.insert(0, task.to_dict())
                self._save_history()"""

replacement_block = """            # Also copy to centralized Posters folder for easy browsing
            try:
                gallery_dir = os.path.join(self.output_dir, "Posters")
                os.makedirs(gallery_dir, exist_ok=True)
                safe_name = self.sanitize_filename(task.drama_title) or f"Drama_{task.drama_id}"
                gallery_path = os.path.join(gallery_dir, f"{safe_name}_{task.drama_id}.jpg")
                with open(gallery_path, "wb") as f_gal:
                    f_gal.write(data)
                # Also save standard poster.jpg in drama folder
                drama_folder = os.path.dirname(task.output_path)
                std_poster = os.path.join(drama_folder, "poster.jpg")
                if not os.path.exists(std_poster):
                    with open(std_poster, "wb") as f_std:
                        f_std.write(data)
            except Exception:
                pass

            with self.lock:
                task.status = "completed"
                task.progress = 100.0
                task.size_bytes = len(data)
                task.completed_at = time.time()
                self.history.insert(0, task.to_dict())
                self._save_history()"""

if target_block in content:
    content = content.replace(target_block, replacement_block)
    with open(TARGET, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated _run_poster_download with centralized Posters gallery folder.")
else:
    print("target_block not found in downloader.py")
