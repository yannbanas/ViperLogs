# anomaly_detection.py
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
from enum import Enum
import math

class AnomalyType(Enum):
    THRESHOLD = "threshold"
    ZSCORE = "zscore"
    IQR = "iqr"
    MOVING_AVERAGE = "moving_average"

@dataclass
class AnomalyConfig:
    type: AnomalyType
    field: str
    params: Dict[str, Any]

class AnomalyDetector:
    def __init__(self):
        self._detection_methods = {
            AnomalyType.THRESHOLD: self._threshold_detection,
            AnomalyType.ZSCORE: self._zscore_detection,
            AnomalyType.IQR: self._iqr_detection,
            AnomalyType.MOVING_AVERAGE: self._moving_average_detection
        }

    def detect(self, logs: List[Dict], config: AnomalyConfig) -> List[Dict]:
        """Détecte les anomalies selon la configuration donnée."""
        if config.type not in self._detection_methods:
            raise ValueError(f"Méthode de détection non supportée: {config.type}")

        detector = self._detection_methods[config.type]
        return detector(logs, config.field, config.params)

    def _extract_numerical_values(self, logs: List[Dict], field: str) -> List[float]:
        """Extrait les valeurs numériques d'un champ."""
        values = []
        for log in logs:
            try:
                value = log
                for key in field.split('.'):
                    value = value[key]
                if isinstance(value, (int, float)):
                    values.append(float(value))
            except (KeyError, TypeError):
                continue
        return values

    def _threshold_detection(self, logs: List[Dict], field: str, params: Dict) -> List[Dict]:
        """Détection basée sur des seuils simples."""
        min_threshold = params.get("min")
        max_threshold = params.get("max")
        
        anomalies = []
        for log in logs:
            try:
                value = log
                for key in field.split('.'):
                    value = value[key]
                
                is_anomaly = False
                if min_threshold is not None and value < min_threshold:
                    is_anomaly = True
                if max_threshold is not None and value > max_threshold:
                    is_anomaly = True
                
                if is_anomaly:
                    anomaly_log = log.copy()
                    anomaly_log["anomaly"] = {
                        "type": "threshold",
                        "field": field,
                        "value": value,
                        "thresholds": {
                            "min": min_threshold,
                            "max": max_threshold
                        }
                    }
                    anomalies.append(anomaly_log)
            except (KeyError, TypeError):
                continue
                
        return anomalies

    def _zscore_detection(self, logs: List[Dict], field: str, params: Dict) -> List[Dict]:
        """Détection basée sur le Z-score."""
        threshold = params.get("threshold", 3)
        values = self._extract_numerical_values(logs, field)
        
        if not values:
            return []
            
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0
        
        anomalies = []
        for log in logs:
            try:
                value = log
                for key in field.split('.'):
                    value = value[key]
                
                if isinstance(value, (int, float)):
                    zscore = abs((value - mean) / std) if std > 0 else 0
                    if zscore > threshold:
                        anomaly_log = log.copy()
                        anomaly_log["anomaly"] = {
                            "type": "zscore",
                            "field": field,
                            "value": value,
                            "zscore": zscore,
                            "threshold": threshold
                        }
                        anomalies.append(anomaly_log)
            except (KeyError, TypeError):
                continue
                
        return anomalies

    def _iqr_detection(self, logs: List[Dict], field: str, params: Dict) -> List[Dict]:
        """Détection basée sur l'écart interquartile (IQR)."""
        multiplier = params.get("multiplier", 1.5)
        values = self._extract_numerical_values(logs, field)
        
        if len(values) < 4:  # Besoin de suffisamment de données
            return []
            
        values.sort()
        q1 = values[len(values) // 4]
        q3 = values[3 * len(values) // 4]
        iqr = q3 - q1
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        
        anomalies = []
        for log in logs:
            try:
                value = log
                for key in field.split('.'):
                    value = value[key]
                
                if isinstance(value, (int, float)):
                    if value < lower_bound or value > upper_bound:
                        anomaly_log = log.copy()
                        anomaly_log["anomaly"] = {
                            "type": "iqr",
                            "field": field,
                            "value": value,
                            "bounds": {
                                "lower": lower_bound,
                                "upper": upper_bound
                            }
                        }
                        anomalies.append(anomaly_log)
            except (KeyError, TypeError):
                continue
                
        return anomalies

# anomaly_detection.py (suite)

    def _moving_average_detection(self, logs: List[Dict], field: str, params: Dict) -> List[Dict]:
        """
        Détection basée sur la moyenne mobile.
        
        Args:
            logs: Liste des logs à analyser
            field: Champ à surveiller
            params: Paramètres de configuration incluant:
                - window_size: Taille de la fenêtre glissante
                - threshold: Seuil de déviation pour considérer une anomalie
                - min_periods: Nombre minimum de points pour calculer la moyenne
        """
        window_size = params.get("window_size", 5)
        threshold = params.get("threshold", 2.0)
        min_periods = params.get("min_periods", 3)

        # Trie les logs par timestamp
        sorted_logs = sorted(
            logs,
            key=lambda x: x.get('timestamp', 0)
        )

        # Extraction des valeurs
        values = []
        valid_logs = []
        for log in sorted_logs:
            try:
                value = log
                for key in field.split('.'):
                    value = value[key]
                if isinstance(value, (int, float)):
                    values.append(float(value))
                    valid_logs.append(log)
            except (KeyError, TypeError):
                continue

        if len(values) < min_periods:
            return []

        anomalies = []
        moving_averages = []
        moving_stds = []

        # Calcul des moyennes mobiles et écarts-types
        for i in range(len(values)):
            start_idx = max(0, i - window_size + 1)
            window = values[start_idx:i + 1]
            
            if len(window) >= min_periods:
                moving_avg = statistics.mean(window)
                moving_std = statistics.stdev(window) if len(window) > 1 else 0
            else:
                moving_avg = values[i]
                moving_std = 0

            moving_averages.append(moving_avg)
            moving_stds.append(moving_std)

            # Détection d'anomalie
            current_value = values[i]
            deviation = abs(current_value - moving_avg)
            if moving_std > 0:
                z_score = deviation / moving_std
                if z_score > threshold:
                    anomaly_log = valid_logs[i].copy()
                    anomaly_log["anomaly"] = {
                        "type": "moving_average",
                        "field": field,
                        "value": current_value,
                        "moving_average": moving_avg,
                        "deviation": deviation,
                        "z_score": z_score,
                        "threshold": threshold
                    }
                    anomalies.append(anomaly_log)

        return anomalies

    def detect_multi_field(self, logs: List[Dict], configs: List[AnomalyConfig]) -> List[Dict]:
        """
        Détecte les anomalies sur plusieurs champs simultanément.
        
        Args:
            logs: Liste des logs à analyser
            configs: Liste des configurations de détection
            
        Returns:
            Liste des logs contenant des anomalies
        """
        all_anomalies = set()
        for config in configs:
            anomalies = self.detect(logs, config)
            for anomaly in anomalies:
                all_anomalies.add(anomaly["id"])  # Suppose qu'un ID unique existe

        return [
            log for log in logs 
            if log.get("id") in all_anomalies
        ]

    def detect_seasonal(self, 
                       logs: List[Dict], 
                       field: str, 
                       period: timedelta,
                       params: Optional[Dict] = None) -> List[Dict]:
        """
        Détecte les anomalies en tenant compte des patterns saisonniers.
        
        Args:
            logs: Liste des logs à analyser
            field: Champ à surveiller
            period: Période de saisonnalité (ex: 24h pour un pattern journalier)
            params: Paramètres additionnels
            
        Returns:
            Liste des logs contenant des anomalies
        """
        params = params or {}
        threshold = params.get("threshold", 2.0)
        min_periods = params.get("min_periods", 2)

        # Groupe les données par période
        period_seconds = period.total_seconds()
        periodic_values = defaultdict(list)
        
        for log in logs:
            try:
                timestamp = log.get("timestamp", 0)
                value = log
                for key in field.split('.'):
                    value = value[key]
                
                if isinstance(value, (int, float)):
                    # Calcule la position dans la période
                    position = timestamp % period_seconds
                    periodic_values[position].append(float(value))
            except (KeyError, TypeError):
                continue

        # Calcule les statistiques pour chaque position dans la période
        seasonal_stats = {}
        for position, values in periodic_values.items():
            if len(values) >= min_periods:
                seasonal_stats[position] = {
                    "mean": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0
                }

        # Détecte les anomalies
        anomalies = []
        for log in logs:
            try:
                timestamp = log.get("timestamp", 0)
                value = log
                for key in field.split('.'):
                    value = value[key]

                if isinstance(value, (int, float)):
                    position = timestamp % period_seconds
                    stats = seasonal_stats.get(position)
                    
                    if stats and stats["std"] > 0:
                        z_score = abs(value - stats["mean"]) / stats["std"]
                        if z_score > threshold:
                            anomaly_log = log.copy()
                            anomaly_log["anomaly"] = {
                                "type": "seasonal",
                                "field": field,
                                "value": value,
                                "expected": stats["mean"],
                                "z_score": z_score,
                                "threshold": threshold,
                                "position_in_period": position
                            }
                            anomalies.append(anomaly_log)
            except (KeyError, TypeError):
                continue

        return anomalies