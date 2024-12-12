"""Main logger implementation with advanced features."""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import json
from pathlib import Path
from .config import LogConfig
from .core import LogEvent, EventAggregator, LogMetrics, LogSanitizer
from .storage import LogStorage
from .ulid import ULID
from .display import DisplayConfig, Color, LogLevel
from .search import LogQuery, LogSearchEngine
from .fuzzy_search import FuzzySearchIndex, FuzzyTextIndexer
from .boolean_search import BooleanSearchIndexer

class AdvancedLogger:
    """Advanced logger implementation with rich features and async support."""
    
    LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]

    def __init__(self, 
                 service_name: str, 
                 config_path: Optional[str] = None,
                 display_config: Optional[DisplayConfig] = None):
        """
        Initialize the logger.
        
        Args:
            service_name: Name of the service using the logger
            config_path: Optional path to config file
            display_config: Optional custom display configuration
        """
        self._cleanup_task = None
        self.config = LogConfig(config_path)
        self.service_name = service_name
        
        # Initialize display configuration
        self.display_config = display_config or DisplayConfig(
            display_fields=["timestamp", "level", "component", "description"],
            colored_output=True,
            separator=" | "
        )
        
        self.storage = LogStorage(
            Path(self.config.config["log_dir"]),
            self.config.config["rotation_size"],
            self.config.config["retention_days"]
        )
        
        # Initialiser les indexeurs comme des classes indépendantes
        self.search_engine = LogSearchEngine(self.config.config["log_dir"])
        self.fuzzy_indexer = FuzzyTextIndexer(max_distance=2)
        self.boolean_indexer = BooleanSearchIndexer()
        
        self.aggregator = EventAggregator(
            self.config.config["similarity_threshold"]
        )
        
        self.metrics = LogMetrics() if self.config.config["metrics_enabled"] else None
        self.sanitizer = LogSanitizer(self.config.config["sensitive_fields"])
        
        self.log_level = self.config.config["default_level"]
        
        # Initialize cleanup task
        self._init_cleanup_task()
    
    def _init_cleanup_task(self):
        """Initialize the cleanup task safely."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._cleanup_task = loop.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old log files."""
        while True:
            try:
                await asyncio.sleep(24 * 3600)  # 24 hours
                await self.storage.cleanup_old_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Cleanup error: {str(e)}")

    def _display_console(self, level: str, message: Dict[str, Any]) -> None:
        """Display log message to console with formatting."""
        try:
            print(self.display_config.format_single_log(message))
        except Exception as e:
            print(f"{Color.RED}[ERROR] Display error: {str(e)}{Color.RESET}")

    async def log(self, level: str, user_id: str, action: str, description: str, 
                component: str, metadata: Optional[Dict] = None) -> Optional[str]:
        try:
            if not self._should_log(level) or level not in self.LEVELS:
                return None

            timestamp = time.time()
            metadata = self.sanitizer.sanitize(metadata or {})
            
            log_id = str(ULID.generate())
            
            log_data = {
                "id": log_id,
                "timestamp": timestamp,
                "level": str(level),
                "user_id": str(user_id),
                "action": str(action),
                "description": str(description),
                "component": str(component),
                "service": str(self.service_name),
                "duration": time.time() - timestamp,
                "context": metadata.get("context", {}),
                "metadata": metadata
            }

            self._display_console(level, log_data)
            await self.storage.write_log(log_data)

            # Indexer pour les recherches spécialisées
            search_content = {
                "level": log_data["level"],
                "action": log_data["action"],
                "description": log_data["description"],
                "component": log_data["component"]
            }
            self.fuzzy_indexer.add_document(log_id, search_content)
            self.boolean_indexer.add_document(log_id, search_content)

            if self.metrics:
                await self.metrics.record_event(LogEvent(**log_data))

            return log_id

        except Exception as e:
            print(f"{Color.BRIGHT_RED}[FATAL] Logging error: {str(e)}{Color.RESET}")
            return None
    
    async def _index_log(self, log_id: str, log_data: Dict):
        """Indexe un log pour les différents types de recherche."""
        # Indexation pour la recherche fuzzy
        self.fuzzy_indexer.add_document(log_id, {
            "description": log_data["description"],
            "action": log_data["action"],
            "component": log_data["component"],
            "level": log_data["level"]
        })

        # Indexation pour la recherche booléenne
        self.boolean_indexer.add_document(log_id, {
            "description": log_data["description"],
            "level": log_data["level"],
            "component": log_data["component"]
        })

    async def fuzzy_search(self, query: str, threshold: float = 0.7) -> List[Dict]:
        """Recherche avec support fuzzy."""
        try:
            results = self.fuzzy_indexer.fuzzy_search(query, threshold)
            if results:
                formatted_results = []
                for result in results:
                    doc_id = result['doc_id']
                    # Récupérer le log complet depuis le stockage
                    log = await self.storage.get_log(doc_id)
                    if log:
                        formatted_results.append(log)
                return formatted_results
            return []
        except Exception as e:
            print(f"Erreur lors de la recherche fuzzy: {str(e)}")
            return []

    async def boolean_search(self, query: str) -> List[Dict]:
        """Recherche avec support booléen."""
        try:
            results = self.boolean_indexer.boolean_search(query)
            if results:
                formatted_results = []
                for result in results:
                    doc_id = result['doc_id']
                    # Récupérer le log complet depuis le stockage
                    log = await self.storage.get_log(doc_id)
                    if log:
                        formatted_results.append(log)
                return formatted_results
            return []
        except Exception as e:
            print(f"Erreur lors de la recherche booléenne: {str(e)}")
            return []
    
    async def _load_existing_logs_into_indexers(self):
        """Charge les logs existants dans les indexeurs."""
        try:
            async for log in self.storage.iter_logs():
                if 'id' in log:
                    await self._index_log(log['id'], log)
        except Exception as e:
            print(f"Erreur lors du chargement des logs existants: {str(e)}")

    def _should_log(self, level: str) -> bool:
        """Check if message should be logged based on level."""
        try:
            return self.LEVELS.index(level) >= self.LEVELS.index(self.log_level)
        except ValueError:
            return False

    async def close(self) -> None:
        """Clean up logger resources."""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
                
            if self.metrics:
                print(f"{Color.CYAN}Saving metrics...{Color.RESET}")
                await self.metrics.save()
                print(f"{Color.GREEN}Metrics saved.{Color.RESET}")
                
            await self.storage.cleanup_old_logs()
        except Exception as e:
            print(f"{Color.BRIGHT_RED}[FATAL] Close error: {str(e)}{Color.RESET}")

    def search(self) -> LogQuery:
        """Create a new search query for logs."""
        return self.search_engine.create_query()

    async def execute_search(self, query: LogQuery) -> List[Dict]:
        """Execute a search query."""
        return await self.search_engine.search(query)

    async def analyze_logs(self, timeframe: timedelta = timedelta(days=1), 
                       components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive log analysis.
        
        Args:
            timeframe: Time period to analyze
            components: Optional list of components to analyze
            
        Returns:
            Dict containing various analysis results
        """
        query = LogQuery()
        query.in_timeframe(datetime.now() - timeframe)
        if components:
            query.from_component(components)
            
        logs = await self.execute_search(query)
        
        return {
            "total_logs": len(logs),
            "logs_by_level": self._count_by_field(logs, "level"),
            "logs_by_component": self._count_by_field(logs, "component"),
            "error_rate": self._calculate_error_rate(logs),
            "avg_response_time": self._calculate_avg_response_time(logs),
            "peak_times": self._find_peak_times(logs),
            "common_patterns": self._find_common_patterns(logs)
        }

    def _count_by_field(self, logs: List[Dict], field: str) -> Dict[str, int]:
        """Count logs by a specific field."""
        counts = {}
        for log in logs:
            value = log.get(field)
            if value:
                counts[value] = counts.get(value, 0) + 1
        return counts

    def _calculate_error_rate(self, logs: List[Dict]) -> float:
        """Calculate error rate from logs."""
        if not logs:
            return 0.0
        error_count = sum(1 for log in logs if log["level"] in ["ERROR", "FATAL"])
        return (error_count / len(logs)) * 100

    def _calculate_avg_response_time(self, logs: List[Dict]) -> float:
        """Calculate average response time from logs."""
        times = [log.get("duration", 0) for log in logs if "duration" in log]
        return sum(times) / len(times) if times else 0

    def _find_peak_times(self, logs: List[Dict]) -> Dict[str, int]:
        """Find peak logging times."""
        hours = {}
        for log in logs:
            hour = datetime.fromtimestamp(log["timestamp"]).hour
            hours[hour] = hours.get(hour, 0) + 1
        return dict(sorted(hours.items(), key=lambda x: x[1], reverse=True))

    def _find_common_patterns(self, logs: List[Dict]) -> Dict[str, List[str]]:
        """Find common patterns in logs."""
        patterns = {
            "actions": self._get_top_values(logs, "action", 5),
            "components": self._get_top_values(logs, "component", 5),
            "users": self._get_top_values(logs, "user_id", 5)
        }
        return patterns

    def _get_top_values(self, logs: List[Dict], field: str, limit: int) -> List[str]:
        """Get top values for a field in logs."""
        counts = {}
        for log in logs:
            value = log.get(field)
            if value:
                counts[value] = counts.get(value, 0) + 1
        return [k for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]]

    def __del__(self):
        """Ensure cleanup on deletion."""
        if self._cleanup_task and not self._cleanup_task.done():
            loop = asyncio.get_event_loop_policy().get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())