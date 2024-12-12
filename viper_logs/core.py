"""Core components for the logging system."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict
import hashlib
import asyncio

@dataclass
class LogEvent:
    """Représentation d'un événement de log."""
    id: str
    timestamp: float
    level: str
    user_id: str
    action: str
    description: str
    component: str
    service: str
    duration: float
    context: Dict[str, Any]
    metadata: Dict[str, Any]

    @property
    def what(self):
        return {
            "action": self.action,
            "level": self.level
        }

    @property
    def who(self):
        return {
            "user_id": self.user_id,
            "service": self.service
        }

    @property
    def where(self):
        return {
            "component": self.component
        }

    @property
    def why(self):
        return {
            "description": self.description,
            "context": self.context
        }
    
class EventAggregator:
    def __init__(self, similarity_threshold: float = 0.85):
        self.event_groups = defaultdict(list)
        self.similarity_threshold = similarity_threshold
        self.lock = asyncio.Lock()

    def _compute_hash(self, event: LogEvent) -> str:
        key_parts = [
            str(event.action),
            str(event.component),
            str(event.description)
        ]
        return hashlib.sha256("".join(key_parts).encode()).hexdigest()

    async def add_event(self, event: LogEvent) -> bool:
        event_hash = self._compute_hash(event)
        
        async with self.lock:
            if self._is_duplicate(event, event_hash):
                self.event_groups[event_hash].append(event)
                return False
            
            self.event_groups[event_hash] = [event]
            return True

    def _is_duplicate(self, event: LogEvent, event_hash: str) -> bool:
        if event_hash not in self.event_groups:
            return False
            
        recent_events = self.event_groups[event_hash][-10:]
        for recent in recent_events:
            time_diff = (event.timestamp - recent.timestamp)
            if time_diff < 60:  # Within 1 minute
                return True
        return False

class LogMetrics:
    """Métriques de logging."""
    def __init__(self):
        self.metrics = defaultdict(int)
        self.start_time = datetime.now()
        self._lock = asyncio.Lock()

    async def record_event(self, event: LogEvent):
        async with self._lock:
            self.metrics[f"level_{event.level}"] += 1
            self.metrics[f"component_{event.component}"] += 1
            self.metrics["total"] += 1

    def get_metrics(self) -> Dict:
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            **self.metrics
        }

    async def save(self):
        #print("Saving metrics...")
        #await asyncio.sleep(1)
        #print("Metrics saved.")
        pass

class LogSanitizer:
    def __init__(self, sensitive_fields: list):
        self.sensitive_fields = sensitive_fields

    def sanitize(self, data: Dict) -> Dict:
        if not isinstance(data, dict):
            return data

        sanitized = data.copy()
        for key, value in sanitized.items():
            if any(field in key.lower() for field in self.sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize(value)
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize(item) if isinstance(item, dict) else item 
                                for item in value]
        return sanitized
