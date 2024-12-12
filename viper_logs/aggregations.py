# aggregations.py
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from dataclasses import dataclass
from enum import Enum

class AggregationType(Enum):
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    PERCENTILE = "percentile"
    CARDINALITY = "cardinality"
    TIME_HISTOGRAM = "time_histogram"
    TERMS = "terms"
    RANGE = "range"

@dataclass
class AggregationConfig:
    type: AggregationType
    field: str
    params: Optional[Dict[str, Any]] = None

class AggregationResult:
    def __init__(self, name: str, value: Any, sub_aggregations: Optional[Dict] = None):
        self.name = name
        self.value = value
        self.sub_aggregations = sub_aggregations or {}

    def to_dict(self) -> Dict:
        result = {
            "name": self.name,
            "value": self.value
        }
        if self.sub_aggregations:
            result["sub_aggregations"] = {
                name: agg.to_dict() for name, agg in self.sub_aggregations.items()
            }
        return result

class LogAggregator:
    def __init__(self):
        self._aggregation_functions = {
            AggregationType.COUNT: self._count_aggregation,
            AggregationType.SUM: self._sum_aggregation,
            AggregationType.AVG: self._avg_aggregation,
            AggregationType.MIN: self._min_aggregation,
            AggregationType.MAX: self._max_aggregation,
            AggregationType.PERCENTILE: self._percentile_aggregation,
            AggregationType.CARDINALITY: self._cardinality_aggregation,
            AggregationType.TIME_HISTOGRAM: self._time_histogram_aggregation,
            AggregationType.TERMS: self._terms_aggregation,
            AggregationType.RANGE: self._range_aggregation
        }

    def aggregate(self, logs: List[Dict], config: AggregationConfig) -> AggregationResult:
        """Exécute une agrégation selon la configuration donnée."""
        if config.type not in self._aggregation_functions:
            raise ValueError(f"Type d'agrégation non supporté: {config.type}")

        agg_func = self._aggregation_functions[config.type]
        return agg_func(logs, config.field, config.params or {})

    def _extract_field_value(self, log: Dict, field: str) -> Any:
        """Extrait la valeur d'un champ, supporte la notation point."""
        keys = field.split('.')
        value = log
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def _count_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        return AggregationResult("count", len(logs))

    def _sum_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        values = [self._extract_field_value(log, field) for log in logs]
        values = [v for v in values if isinstance(v, (int, float))]
        return AggregationResult("sum", sum(values))

    def _avg_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        values = [self._extract_field_value(log, field) for log in logs]
        values = [v for v in values if isinstance(v, (int, float))]
        if not values:
            return AggregationResult("avg", 0)
        return AggregationResult("avg", statistics.mean(values))

    def _min_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        values = [self._extract_field_value(log, field) for log in logs]
        values = [v for v in values if v is not None]
        if not values:
            return AggregationResult("min", None)
        return AggregationResult("min", min(values))

    def _max_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        values = [self._extract_field_value(log, field) for log in logs]
        values = [v for v in values if v is not None]
        if not values:
            return AggregationResult("max", None)
        return AggregationResult("max", max(values))

    def _percentile_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        percentile = params.get("percentile", 95)
        values = [self._extract_field_value(log, field) for log in logs]
        values = sorted(v for v in values if isinstance(v, (int, float)))
        if not values:
            return AggregationResult(f"p{percentile}", None)
        
        index = (len(values) - 1) * percentile / 100
        if index.is_integer():
            return AggregationResult(f"p{percentile}", values[int(index)])
        
        i = int(index)
        fraction = index - i
        return AggregationResult(
            f"p{percentile}",
            values[i] * (1 - fraction) + values[i + 1] * fraction
        )

    def _cardinality_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        values = {self._extract_field_value(log, field) for log in logs}
        values.discard(None)
        return AggregationResult("cardinality", len(values))

    def _time_histogram_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        interval = params.get("interval", "1h")
        intervals = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "1h": timedelta(hours=1),
            "1d": timedelta(days=1),
        }
        delta = intervals.get(interval, timedelta(hours=1))

        buckets = defaultdict(list)
        for log in logs:
            timestamp = self._extract_field_value(log, field)
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
                bucket_time = dt.replace(
                    minute=0 if interval.endswith('h') or interval.endswith('d') else dt.minute - dt.minute % int(interval[:-1]),
                    second=0,
                    microsecond=0
                )
                buckets[bucket_time].append(log)

        result = {
            str(bucket_time): len(logs)
            for bucket_time, logs in sorted(buckets.items())
        }
        return AggregationResult("time_histogram", result)

    def _terms_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        size = params.get("size", 10)
        min_count = params.get("min_count", 1)
        
        terms = defaultdict(int)
        for log in logs:
            value = self._extract_field_value(log, field)
            if value is not None:
                terms[value] += 1

        # Filtre et trie les termes
        filtered_terms = {
            term: count
            for term, count in terms.items()
            if count >= min_count
        }
        sorted_terms = dict(
            sorted(filtered_terms.items(), key=lambda x: x[1], reverse=True)[:size]
        )
        
        return AggregationResult("terms", sorted_terms)

    def _range_aggregation(self, logs: List[Dict], field: str, params: Dict) -> AggregationResult:
        ranges = params.get("ranges", [])
        if not ranges:
            return AggregationResult("range", {})

        buckets = defaultdict(list)
        for log in logs:
            value = self._extract_field_value(log, field)
            if not isinstance(value, (int, float)):
                continue

            for range_def in ranges:
                from_value = range_def.get("from", float("-inf"))
                to_value = range_def.get("to", float("inf"))
                
                if from_value <= value < to_value:
                    range_key = f"{from_value}-{to_value}"
                    buckets[range_key].append(log)

        result = {
            range_key: len(logs)
            for range_key, logs in sorted(buckets.items())
        }
        return AggregationResult("range", result)