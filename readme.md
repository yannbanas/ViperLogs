# ViperLogs Technical Documentation

## Overview

ViperLogs is an advanced, asynchronous Python logging library designed for modern applications. It provides sophisticated features including real-time log analysis, anomaly detection, advanced search capabilities, and flexible log aggregation. The library is built with a focus on performance, extensibility, and developer experience.

## Core Features

- Asynchronous logging with built-in performance optimizations
- Advanced search capabilities including fuzzy and boolean search
- Real-time anomaly detection with multiple detection strategies
- Flexible log aggregation and analysis
- Secure logging with automatic sanitization of sensitive data
- Rich display options with customizable formatting and colors
- Distributed logging support through client-server architecture
- ULID-based log identification for guaranteed ordering
- Configurable log rotation and retention policies

## Architecture

### Component Overview

The library is organized into several key components, each handling specific responsibilities:

1. **Core Logging (logger.py)**
   - Central logging implementation
   - Log event handling and processing
   - Integration point for all other components

2. **Configuration (config.py)**
   - Configuration management
   - Default settings
   - YAML/JSON configuration support
   - Runtime configuration updates

3. **Event Processing (core.py)**
   - Log event representation
   - Event aggregation
   - Metrics collection
   - Data sanitization

4. **Storage (storage.py)**
   - Log persistence
   - File rotation
   - Retention management
   - Efficient log retrieval

5. **Search Capabilities**
   - Text indexing (indexer.py)
   - Fuzzy search (fuzzy_search.py)
   - Boolean search (boolean_search.py)
   - Query building (search.py)

6. **Analysis**
   - Log aggregation (aggregations.py)
   - Anomaly detection (anomaly_detection.py)
   - Statistical analysis
   - Pattern recognition

7. **Display (display.py)**
   - Formatting configurations
   - Color support
   - Custom themes
   - Multiple output formats

### Data Flow

1. Log events are created through the AdvancedLogger interface
2. Events are processed through the event pipeline:
   - Sanitization of sensitive data
   - Event aggregation
   - Metrics collection
3. Processed events are:
   - Displayed according to configuration
   - Stored in the configured storage system
   - Indexed for search
   - Analyzed for anomalies

## Usage Examples

### Basic Logging

```python
from viper_logs import AdvancedLogger

# Initialize logger
logger = AdvancedLogger("my_service")

# Basic logging
await logger.log(
    level="INFO",
    user_id="user123",
    action="login",
    description="User logged in successfully",
    component="auth"
)
```

### Advanced Search

```python
# Fuzzy search
results = await logger.fuzzy_search(
    query="authentication",
    threshold=0.7
)

# Boolean search
results = await logger.boolean_search(
    "auth AND (error OR warning) NOT timeout"
)

# Query builder
results = await logger.search()\
    .with_level("ERROR")\
    .from_component("auth")\
    .containing("failed")\
    .execute()
```

### Anomaly Detection

```python
from viper_logs.anomaly_detection import AnomalyConfig, AnomalyType

# Configure anomaly detection
config = AnomalyConfig(
    type=AnomalyType.ZSCORE,
    field="response_time",
    params={"threshold": 3.0}
)

# Detect anomalies
anomalies = await logger.analyze_anomalies(config)
```

### Log Aggregation

```python
from viper_logs.aggregations import AggregationConfig, AggregationType

# Configure aggregation
config = AggregationConfig(
    type=AggregationType.TIME_HISTOGRAM,
    field="timestamp",
    params={"interval": "1h"}
)

# Get aggregated results
results = await logger.aggregate_logs(config)
```

## Configuration

### Default Configuration

```python
default_config = {
    "log_dir": "logs",
    "rotation_size": 5 * 1024 * 1024,  # 5 MB
    "retention_days": 30,
    "default_level": "INFO",
    "sensitive_fields": ["password", "token", "key", "secret"],
    "similarity_threshold": 0.85,
    "metrics_enabled": True,
    "compression_enabled": True
}
```

### Custom Configuration

```python
from viper_logs import LogConfig

config = LogConfig("config.yaml")
logger = AdvancedLogger("my_service", config_path="config.yaml")
```

## Display Configuration

The library provides rich display options through the DisplayConfig class:

```python
from viper_logs import DisplayConfig, Color

display_config = DisplayConfig(
    display_fields=["timestamp", "level", "component", "description"],
    colored_output=True,
    timestamp_format="%Y-%m-%d %H:%M:%S",
    separator=" | "
)

logger = AdvancedLogger("my_service", display_config=display_config)
```

## Advanced Features

### ULID Implementation

The library uses ULIDs (Universally Unique Lexicographically Sortable Identifier) for log identification. This provides:

- Guaranteed chronological sorting
- Monotonic sequence within the same millisecond
- URL-safe base32 encoding
- 128-bit compatibility with UUID

### Sanitization

Automatic sanitization of sensitive data:
- Configurable sensitive field patterns
- Deep object traversal
- Preservation of data structure
- Configurable redaction patterns

### Performance Optimization

- Asynchronous I/O operations
- Efficient indexing strategies
- Optimized search algorithms
- Configurable buffer sizes
- Compression support

## Best Practices

1. **Configuration Management**
   - Use external configuration files
   - Set appropriate log rotation sizes
   - Configure retention policies
   - Define sensitive fields

2. **Search Optimization**
   - Use appropriate search methods
   - Set reasonable similarity thresholds
   - Index only necessary fields
   - Use query builders for complex searches

3. **Anomaly Detection**
   - Choose appropriate detection methods
   - Set context-aware thresholds
   - Use seasonal detection when appropriate
   - Combine multiple detection strategies

4. **Error Handling**
   - Implement proper error handling
   - Use appropriate log levels
   - Include relevant context
   - Handle asynchronous operations properly

## API Reference

The library exposes several key classes and methods:

### AdvancedLogger

Main interface for logging operations:
- `log(level, user_id, action, description, component, metadata)`
- `search()`
- `analyze_logs(timeframe, components)`
- `execute_search(query)`
- `close()`

### LogQuery

Query builder for log searches:
- `with_level(level)`
- `from_component(component)`
- `containing(text)`
- `in_timeframe(start, end)`
- `execute()`

### DisplayConfig

Configuration for log display:
- `format_single_log(log_data)`
- `format_log_table(logs)`
- Color and theme customization
- Field formatting options

## Dependencies

- Python 3.9+
- aiohttp >= 3.8.0
- pyyaml >= 6.0.0

## Future Enhancements

Planned features and improvements:

1. Distributed logging support
2. Real-time alerting system
3. Machine learning-based anomaly detection
4. Enhanced visualization options
5. Additional search algorithms
6. Performance optimization for large-scale deployments

## Contributing

When contributing to ViperLogs:

1. Follow the established coding style
2. Write comprehensive tests
3. Document new features
4. Update the technical documentation
5. Submit detailed pull requests

## License

This library is released under the MIT License. See LICENSE file for details.