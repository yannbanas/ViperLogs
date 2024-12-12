# storage.py
"""Enhanced log storage with search capabilities."""
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator
import os

class LogStorage:
    def __init__(self, log_dir: Path, max_size: int, retention_days: int):
        self.log_dir = log_dir
        self.max_size = max_size
        self.retention_days = retention_days
        self.current_file: Optional[Path] = None
        self.current_size = 0
        self._lock = asyncio.Lock()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._init_current_file()

    async def get_log(self, log_id: str) -> Optional[Dict]:
        """Récupère un log spécifique par son ID."""
        for file_path in self.log_dir.glob("*.log"):
            try:
                logs_files = sorted(self.log_dir.glob("*.log"), reverse=True)
                for log_file in logs_files:
                    with log_file.open('r') as f:
                        for line in f:
                            try:
                                log = json.loads(line.strip())
                                if log.get("id") == log_id:
                                    return log
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                print(f"Erreur lors de la récupération du log {log_id}: {str(e)}")
            return None

    async def iter_logs(self) -> AsyncGenerator[Dict, None]:
        """Itère sur tous les logs existants."""
        for file_path in sorted(self.log_dir.glob("*.log")):
            try:
                with file_path.open('r') as f:
                    for line in f:
                        try:
                            yield json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue
            except IOError:
                continue

    async def write_log(self, log_data: Dict) -> None:
        """Write log data to storage with proper rotation."""
        async with self._lock:
            try:
                log_line = json.dumps(log_data) + "\n"
                log_size = len(log_line.encode('utf-8'))

                # Check if we need to rotate
                if self.current_size + log_size > self.max_size:
                    self.current_file = self._create_new_file()
                    self.current_size = 0

                # Append to file
                with self.current_file.open('a', encoding='utf-8') as f:
                    f.write(log_line)
                self.current_size += log_size

            except Exception as e:
                print(f"Error writing log: {e}")
                raise

    async def cleanup_old_logs(self) -> None:
        """Remove logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        for file_path in self.log_dir.glob("*.log"):
            try:
                stats = file_path.stat()
                if datetime.fromtimestamp(stats.st_mtime) < cutoff:
                    file_path.unlink()
            except (OSError, IOError):
                continue

    def _init_current_file(self):
        """Initialize or find the current log file."""
        existing_files = list(self.log_dir.glob("*.log"))
        if existing_files:
            latest_file = max(existing_files, key=os.path.getctime)
            if os.path.getsize(latest_file) < self.max_size:
                self.current_file = latest_file
                self.current_size = os.path.getsize(latest_file)
                return
        self.current_file = self._create_new_file()
        self.current_size = 0

    def _create_new_file(self) -> Path:
        """Create a new log file with timestamp."""
        timestamp = datetime.now().strftime("%Y%m")  # Changed to monthly files
        file_path = self.log_dir / f"log_{timestamp}.log"
        if not file_path.exists():
            file_path.touch()
        return file_path

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self.cleanup_old_logs()
        except Exception as e:
            print(f"Cleanup error: {str(e)}")

    async def search_logs(self, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> AsyncGenerator[Dict, None]:
        """
        Search logs with time range filtering.
        
        Args:
            start_time: Optional start of time range
            end_time: Optional end of time range
            
        Yields:
            Dict: Log entries matching the criteria
        """
        for file_path in sorted(self.log_dir.glob("*.log"), reverse=True):
            try:
                with file_path.open() as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line)
                            log_time = datetime.fromtimestamp(log_entry["timestamp"])
                            
                            if start_time and log_time < start_time:
                                continue
                            if end_time and log_time > end_time:
                                continue
                                
                            yield log_entry
                            
                        except json.JSONDecodeError:
                            continue
                            
            except IOError:
                continue