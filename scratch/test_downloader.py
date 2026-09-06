import os
import sys
import time
import json
import subprocess
import threading
import urllib.request
from typing import Dict, Any, List, Optional

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://8movie.com/'
}

class DownloadTask:
    def __init__(self, task_id: str, drama_id: str, drama_title: str, ep_num: int, hls_url: str, poster_url: str, output_path: str):
        self.task_id = task_id
        self.drama_id = drama_id
        self.drama_title = drama_title
        self.ep_num = ep_num
        self.hls_url = hls_url
        self.poster_url = poster_url
        self.output_path = output_path
        self.status = "queued" # queued, downloading, completed, error, cancelled
        self.progress = 0.0
        self.speed = "0 MB/s"
        self.error_msg = ""
        self.start_time = 0
        self.end_time = 0

class DownloaderManager:
    def __init__(self, output_dir: str = None, max_workers: int = 3):
        if not output_dir:
            self.output_dir = os.path.join(os.path.expanduser("~"), "Videos", "SYD-8Movie")
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.max_workers = max_workers
        self.tasks: Dict[str, DownloadTask] = {}
        self.queue: List[str] = []
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def sanitize_filename(self, name: str) -> str:
        return "".join(c for c in name if c not in '<>:"/\\|?*').strip()

    def submit_task(self, drama_id: str, drama_title: str, ep_num: int, hls_url: str, poster_url: str = "") -> str:
        safe_title = self.sanitize_filename(drama_title) or f"Drama_{drama_id}"
        drama_dir = os.path.join(self.output_dir, safe_title)
        os.makedirs(drama_dir, exist_ok=True)
        
        # Download poster if not downloaded yet
        if poster_url:
            poster_path = os.path.join(drama_dir, "poster.jpg")
            if not os.path.exists(poster_path):
                threading.Thread(target=self.download_poster, args=(poster_url, poster_path), daemon=True).start()

        out_file = os.path.join(drama_dir, f"EP_{ep_num:02d}.mp4")
        task_id = f"{drama_id}_{ep_num}"
        
        with self.lock:
            if task_id in self.tasks and self.tasks[task_id].status in ("queued", "downloading"):
                return task_id
            
            task = DownloadTask(task_id, drama_id, drama_title, ep_num, hls_url, poster_url, out_file)
            self.tasks[task_id] = task
            self.queue.append(task_id)
            return task_id

    def download_poster(self, poster_url: str, target_path: str):
        try:
            req = urllib.request.Request(poster_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                with open(target_path, "wb") as f:
                    f.write(data)
            return True
        except Exception as e:
            print("Failed to download poster:", e)
            return False

    def cancel_task(self, task_id: str):
        with self.lock:
            if task_id in self.active_processes:
                try:
                    self.active_processes[task_id].terminate()
                except Exception:
                    pass
            if task_id in self.tasks:
                self.tasks[task_id].status = "cancelled"
            if task_id in self.queue:
                self.queue.remove(task_id)

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
                        task.start_time = time.time()
                        threading.Thread(target=self._run_download, args=(task,), daemon=True).start()
            
            time.sleep(0.5)

    def _run_download(self, task: DownloadTask):
        cmd = [
            "ffmpeg", "-y",
            "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: https://8movie.com/\r\n",
            "-i", task.hls_url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            task.output_path
        ]
        
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
            
            with self.lock:
                self.active_processes.pop(task.task_id, None)
                if proc.returncode == 0 and os.path.exists(task.output_path) and os.path.getsize(task.output_path) > 1000:
                    task.status = "completed"
                    task.progress = 100.0
                    task.end_time = time.time()
                elif task.status != "cancelled":
                    task.status = "error"
                    task.error_msg = stderr[-200:] if stderr else "ffmpeg failed"
        except Exception as e:
            with self.lock:
                self.active_processes.pop(task.task_id, None)
                if task.status != "cancelled":
                    task.status = "error"
                    task.error_msg = str(e)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            tasks_list = []
            for t in self.tasks.values():
                tasks_list.append({
                    "task_id": t.task_id,
                    "drama_id": t.drama_id,
                    "drama_title": t.drama_title,
                    "ep_num": t.ep_num,
                    "status": t.status,
                    "progress": t.progress,
                    "output_path": t.output_path,
                    "error_msg": t.error_msg
                })
            return {
                "output_dir": self.output_dir,
                "active_tasks": [t for t in tasks_list if t["status"] == "downloading"],
                "queued_tasks": [t for t in tasks_list if t["status"] == "queued"],
                "completed_tasks": [t for t in tasks_list if t["status"] == "completed"],
                "all_tasks": tasks_list
            }
