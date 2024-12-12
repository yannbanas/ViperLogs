# search.py
import json
from typing import List, Dict, Optional, Union, Callable
import re
from datetime import datetime, timedelta
from pathlib import Path

class LogQuery:
    """Advanced log query builder with fluent interface."""
    
    def __init__(self, search_engine=None):
        self.filters = []
        self.start_time = None
        self.end_time = None
        self.limit = None
        self.sort_order = "desc"
        self._search_engine = search_engine  # Référence au moteur de recherche
        
    def in_timeframe(self, start: datetime, end: Optional[datetime] = None) -> 'LogQuery':
        self.start_time = start
        self.end_time = end or datetime.now()
        return self
        
    def with_level(self, level: Union[str, List[str]]) -> 'LogQuery':
        levels = [level] if isinstance(level, str) else level
        self.filters.append(lambda log: log["level"] in levels)
        return self
        
    def from_component(self, component: Union[str, List[str]]) -> 'LogQuery':
        components = [component] if isinstance(component, str) else component
        self.filters.append(lambda log: log["component"] in components)
        return self
        
    def by_user(self, user_id: Union[str, List[str]]) -> 'LogQuery':
        users = [user_id] if isinstance(user_id, str) else user_id
        self.filters.append(lambda log: log["user_id"] in users)
        return self
        
    def containing(self, text: str, case_sensitive: bool = False) -> 'LogQuery':
        """
        Recherche du texte dans la description.
        Ne vérifie que les champs textuels.
        """
        if not case_sensitive:
            text = text.lower()
            self.filters.append(
                lambda log: isinstance(log.get("description", ""), str) and 
                           text in log.get("description", "").lower()
            )
        else:
            self.filters.append(
                lambda log: isinstance(log.get("description", ""), str) and 
                           text in log.get("description", "")
            )
        return self

    async def execute(self) -> List[Dict]:
        """Exécute la requête et retourne les résultats."""
        if not self._search_engine:
            raise RuntimeError("Search engine not configured for this query")
        return await self._search_engine.search(self)

class LogSearchEngine:
    """Advanced log search engine with query support."""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_query(self) -> LogQuery:
        """Crée une nouvelle requête liée à ce moteur de recherche."""
        return LogQuery(search_engine=self)

    async def search(self, query: LogQuery) -> List[Dict]:
        """
        Execute a search query on log files.
        
        Args:
            query: LogQuery instance with search criteria
            
        Returns:
            List of matching log entries
        """
        results = []
        
        # Ensure directory exists
        if not self.storage_path.exists():
            return results

        # Search through all log files
        for log_file in self.storage_path.glob("*.log"):
            try:
                with log_file.open('r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Apply time filters
                            if query.start_time or query.end_time:
                                try:
                                    log_time = datetime.fromtimestamp(float(log_entry["timestamp"]))
                                    if query.start_time and log_time < query.start_time:
                                        continue
                                    if query.end_time and log_time > query.end_time:
                                        continue
                                except (TypeError, ValueError):
                                    continue

                            # Apply all other filters
                            try:
                                if all(f(log_entry) for f in query.filters):
                                    results.append(log_entry)
                            except (TypeError, AttributeError):
                                continue
                                
                        except json.JSONDecodeError:
                            continue
                            
            except IOError:
                continue

        # Sort results
        try:
            results.sort(
                key=lambda x: float(x.get("timestamp", 0)),
                reverse=(query.sort_order == "desc")
            )
        except (TypeError, ValueError):
            pass

        # Apply limit
        if query.limit:
            results = results[:query.limit]

        return results
    
    def _matches_query(self, log: Dict, query: LogQuery) -> bool:
        if query.start_time and datetime.fromtimestamp(log["timestamp"]) < query.start_time:
            return False
            
        if query.end_time and datetime.fromtimestamp(log["timestamp"]) > query.end_time:
            return False
            
        return all(f(log) for f in query.filters)
        
    def _read_logs(self) -> List[Dict]:
        # Implementation dépend du stockage
        pass

# Analysis tools
class LogAnalyzer:
    """Advanced log analysis tools."""
    
    @staticmethod
    def pattern_frequency(logs: List[Dict], pattern: str) -> Dict[str, int]:
        """Analyze frequency of regex pattern matches in logs."""
        regex = re.compile(pattern)
        matches = {}
        
        for log in logs:
            found = regex.findall(log["description"])
            for match in found:
                matches[match] = matches.get(match, 0) + 1
                
        return dict(sorted(matches.items(), key=lambda x: x[1], reverse=True))
    
    @staticmethod
    def error_distribution(logs: List[Dict], interval: timedelta = timedelta(hours=1)) -> Dict[datetime, int]:
        """Analyze error distribution over time."""
        errors = {}
        
        for log in logs:
            if log["level"] in ["ERROR", "FATAL"]:
                timestamp = datetime.fromtimestamp(log["timestamp"])
                bucket = timestamp.replace(
                    minute=0, second=0, microsecond=0
                )
                errors[bucket] = errors.get(bucket, 0) + 1
                
        return dict(sorted(errors.items()))
    
    @staticmethod
    def component_stats(logs: List[Dict]) -> Dict[str, Dict[str, Union[int, float]]]:
        """Calculate statistics per component."""
        stats = {}
        
        for log in logs:
            component = log["component"]
            if component not in stats:
                stats[component] = {
                    "total": 0,
                    "errors": 0,
                    "error_rate": 0.0,
                    "avg_response_time": 0.0,
                    "response_times": []
                }
                
            stats[component]["total"] += 1
            if log["level"] in ["ERROR", "FATAL"]:
                stats[component]["errors"] += 1
                
            if "duration" in log:
                stats[component]["response_times"].append(log["duration"])
                
        # Calculate derived metrics
        for component in stats:
            total = stats[component]["total"]
            stats[component]["error_rate"] = (
                stats[component]["errors"] / total * 100
                if total > 0 else 0
            )
            
            times = stats[component]["response_times"]
            stats[component]["avg_response_time"] = (
                sum(times) / len(times) if times else 0
            )
            del stats[component]["response_times"]
            
        return stats
