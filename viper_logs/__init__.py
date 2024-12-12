# __init__.py
"""
ViperLogs Library
~~~~~~~~~~~~~~~~

Une bibliothèque de logging avancée avec capacités d'indexation et de recherche.

Usage basique:
    >>> from viper_logs import AdvancedLogger
    >>> logger = AdvancedLogger("my_service")
    >>> await logger.log("INFO", "user123", "login", "User logged in", "auth")

Usage avancé:
    >>> # Recherche avec LogQuery
    >>> results = await logger.search().with_level("ERROR").from_component("auth").execute()
    
    >>> # Analyse des logs
    >>> analysis = await logger.analyze_logs(timeframe=timedelta(hours=24))
"""

from .logger import AdvancedLogger
from .config import LogConfig
from .core import LogEvent, EventAggregator, LogMetrics, LogSanitizer
from .search import LogQuery, LogSearchEngine
from .storage import LogStorage
from .client import LogClient
from .display import (
    DisplayConfig, 
    DisplayFormat, 
    DisplayTheme, 
    Color, 
    LogLevel, 
    LogMetadata
)
from .ulid import ULID

__version__ = "0.0.1"
__all__ = [
    "AdvancedLogger",
    "LogConfig",
    "LogEvent",
    "EventAggregator",
    "LogMetrics",
    "LogSanitizer",
    "LogQuery",
    "LogSearchEngine",
    "LogStorage",
    "LogClient",
    "DisplayConfig",
    "DisplayFormat",
    "DisplayTheme",
    "Color",
    "LogLevel",
    "LogMetadata",
    "ULID"
]