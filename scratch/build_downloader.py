import os

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"

downloader_code = r'''# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import subprocess
import threading
import urllib.request
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://8movie.com/'
}

class DownloadTask:
    def __init__(self, task_id: str, task_type: str, drama_id: str, drama_title: str, title_km: str,
                 ep_num: int, url: str, poster_url: str, output_path: str):
        self.task_id = task_id
        self.task_type = task_type  # 'episode' or 'poster'
        self.drama_id = drama_id
        self.drama_title = drama_title
        self.title_km = title_km
        self.ep_num = ep_num
        self.url = url
        self.poster_url = poster_url
        self.output_path = output_path
        self.status = "queued"      # 'queued', 'downloading', 'completed', 'failed', 'cancelled'
        self.progress = 0.0
        self.speed = "0.0 MB/s"
        self.size_bytes = 0
        self.error_msg = ""
        self.created_at = time.time()
        self.completed_at = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "drama_id": self.drama_id,
            "drama_title": self.drama_title,
            "title_km": self.title_km,
            "ep_num": self.ep_num,
            "url": self.url,
            "poster_url": self.poster_url,
            "output_path": self.output_path,
            "status": self.status,
            "progress": round(self.progress, 1),
            "speed": self.speed,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2) if self.size_bytes else 0,
            "error_msg": self.error_msg,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

class DownloaderManager:
    def __init__(self, output_dir: Optional[str] = None, max_workers: int = 3):
        if not output_dir:
            self.output_dir = os.path.join(os.path.expanduser("~"), "Videos", "SYD-8Movie")
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)

        self.max_workers = max_workers
        self.tasks: Dict[str, DownloadTask] = {}
        self.queue: List[str] = []
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self._stop_event = threading.Event()

        self._load_history()

        # Background processing worker
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def sanitize_filename(self, name: str) -> str:
        clean = "".join(c for c in name if c not in '<>:"/\\|?*\n\r\t').strip()
        return clean[:80] if clean else "Drama"

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def _save_history(self):
        try:
            tmp = HISTORY_FILE + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.history[-300:], f, ensure_ascii=False, indent=1)
            os.replace(tmp, HISTORY_FILE)
        except Exception:
            pass

    def submit_poster(self, drama_id: str, drama_title: str, title_km: str, poster_url: str) -> str:
        safe_title = self.sanitize_filename(drama_title)
        drama_dir = os.path.join(self.output_dir, safe_title)
        os.makedirs(drama_dir, exist_ok=True)

        poster_path = os.path.join(drama_dir, f"{safe_title}_Poster.jpg")
        task_id = f"poster_{drama_id}"

        with self.lock:
            if task_id in self.tasks and self.tasks[task_id].status in ("queued", "downloading"):
                return task_id

            task = DownloadTask(task_id, "poster", drama_id, drama_title, title_km, 0, poster_url, poster_url, poster_path)
            self.tasks[task_id] = task
            self.queue.insert(0, task_id)  # High priority
            return task_id

    def submit_episode(self, drama_id: str, drama_title: str, title_km: str,
                       ep_num: int, hls_url: str, poster_url: str = "") -> str:
        safe_title = self.sanitize_filename(drama_title)
        drama_dir = os.path.join(self.output_dir, safe_title)
        os.makedirs(drama_dir, exist_ok=True)

        # Also queue poster download automatically
        if poster_url:
            folder_poster = os.path.join(drama_dir, "poster.jpg")
            if not os.path.exists(folder_poster):
                threading.Thread(target=self._download_poster_sync, args=(poster_url, folder_poster), daemon=True).start()

        out_file = os.path.join(drama_dir, f"EP_{ep_num:02d}.mp4")
        task_id = f"ep_{drama_id}_{ep_num}"

        with self.lock:
            if task_id in self.tasks and self.tasks[task_id].status in ("queued", "downloading"):
                return task_id

            task = DownloadTask(task_id, "episode", drama_id, drama_title, title_km, ep_num, hls_url, poster_url, out_file)
            self.tasks[task_id] = task
            self.queue.append(task_id)
            return task_id

    def submit_batch(self, drama_id: str, drama_title: str, title_km: str,
                     episodes: List[Dict[str, Any]], poster_url: str = "") -> List[str]:
        task_ids = []
        for ep in episodes:
            ep_num = ep.get("episode", 1)
            hls_url = ep.get("hls_url") or ep.get("hlsSrc", "")
            if hls_url:
                tid = self.submit_episode(drama_id, drama_title, title_km, ep_num, hls_url, poster_url)
                task_ids.append(tid)
        return task_ids

    def _download_poster_sync(self, url: str, path: str):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                with open(path, "wb") as f:
                    f.write(data)
        except Exception:
            pass

    def cancel_task(self, task_id: str):
        with self.lock:
            if task_id in self.active_processes:
                try:
                    self.active_processes[task_id].kill()
                except Exception:
                    pass
            if task_id in self.tasks:
                self.tasks[task_id].status = "cancelled"
            if task_id in self.queue:
                self.queue.remove(task_id)

    def clear_completed(self):
        with self.lock:
            to_del = [tid for tid, t in self.tasks.items() if t.status in ("completed", "cancelled", "failed")]
            for tid in to_del:
                del self.tasks[tid]

    def _process_queue(self):
        while not self._stop_event.is_set():
            active_count = 0
            with self.lock:
                for t in self.tasks.values():
                    if t.status == "downloading":
                        active_count += 1

                if active_count < self.max_workers and self.queue:
                    next_task_id = self.queue.pop(0)
                    task = self.tasks.get(next_task_id)
                    if task and task.status == "queued":
                        task.status = "downloading"
                        if task.task_type == "poster":
                            threading.Thread(target=self._run_poster_download, args=(task,), daemon=True).start()
                        else:
                            threading.Thread(target=self._run_ffmpeg_download, args=(task,), daemon=True).start()

            time.sleep(0.4)

    def _run_poster_download(self, task: DownloadTask):
        try:
            req = urllib.request.Request(task.url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
                with open(task.output_path, "wb") as f:
                    f.write(data)

            with self.lock:
                task.status = "completed"
                task.progress = 100.0
                task.size_bytes = len(data)
                task.completed_at = time.time()
                self.history.insert(0, task.to_dict())
                self._save_history()
        except Exception as e:
            with self.lock:
                task.status = "failed"
                task.error_msg = str(e)

    def _run_ffmpeg_download(self, task: DownloadTask):
        cmd = [
            "ffmpeg", "-y",
            "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: https://8movie.com/\r\n",
            "-i", task.url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            task.output_path
        ]

        t0 = time.time()
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=0x08000000 if sys.platform == 'win32' else 0, # CREATE_NO_WINDOW
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            with self.lock:
                self.active_processes[task.task_id] = proc

            _, stderr = proc.communicate()
            elapsed = max(0.1, time.time() - t0)

            with self.lock:
                self.active_processes.pop(task.task_id, None)
                if proc.returncode == 0 and os.path.exists(task.output_path) and os.path.getsize(task.output_path) > 1000:
                    file_size = os.path.getsize(task.output_path)
                    speed_mbs = round((file_size / (1024 * 1024)) / elapsed, 2)
                    task.status = "completed"
                    task.progress = 100.0
                    task.size_bytes = file_size
                    task.speed = f"{speed_mbs} MB/s"
                    task.completed_at = time.time()
                    self.history.insert(0, task.to_dict())
                    self._save_history()
                elif task.status != "cancelled":
                    task.status = "failed"
                    task.error_msg = stderr[-250:] if stderr else "ffmpeg error"
        except Exception as e:
            with self.lock:
                self.active_processes.pop(task.task_id, None)
                if task.status != "cancelled":
                    task.status = "failed"
                    task.error_msg = str(e)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            all_list = [t.to_dict() for t in self.tasks.values()]
            return {
                "output_dir": self.output_dir,
                "active_count": len([t for t in all_list if t["status"] == "downloading"]),
                "queued_count": len([t for t in all_list if t["status"] == "queued"]),
                "completed_count": len([t for t in all_list if t["status"] == "completed"]),
                "failed_count": len([t for t in all_list if t["status"] == "failed"]),
                "tasks": all_list,
                "history": self.history[:50]
            }

    def open_folder(self, target_path: Optional[str] = None):
        path = target_path or self.output_dir
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        if sys.platform == 'win32':
            os.startfile(path)
        else:
            subprocess.run(["xdg-open", path])

    def play_file(self, file_path: str):
        if os.path.exists(file_path):
            if sys.platform == 'win32':
                os.startfile(file_path)
            else:
                subprocess.run(["xdg-open", file_path])
'''

with open(os.path.join(TARGET_DIR, 'app', 'downloader.py'), 'w', encoding='utf-8') as f:
    f.write(downloader_code)

print("Written: app/downloader.py")
