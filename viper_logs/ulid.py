from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional, Tuple, Union
from dataclasses import dataclass
import threading

@dataclass
class ULID:
    """
    Implémentation de ULID (Universally Unique Lexicographically Sortable Identifier).
    
    Format: ttttttttttttCCCCCCCCCCCCCCCC (26 caractères)
    - t: timestamp en millisecondes (48 bits)
    - C: composante aléatoire (80 bits)
    
    Spécifications:
    - Triable lexicographiquement
    - Compatible avec UUID
    - Case insensitive
    - Pas de caractères ambigus (I, L, O, U)
    - Monotonic factory option pour garantir l'ordre dans la même milliseconde
    """
    
    # Alphabet Crockford's Base32 (RFC)
    ENCODING_CHARS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    DECODING_CHARS = {char: index for index, char in enumerate(ENCODING_CHARS)}
    
    # Constantes de validation
    TIME_MAX = 281474976710655  # 2^48 - 1, maximum timestamp en millisecondes
    RANDOM_MAX = (1 << 80) - 1  # 2^80 - 1, maximum valeur aléatoire
    
    # Longueurs des composants
    TIME_LEN = 10
    RANDOM_LEN = 16
    TOTAL_LEN = TIME_LEN + RANDOM_LEN
    
    # Lock pour la factory monotonic
    _lock = threading.Lock()
    _last_timestamp = 0
    _last_randomness = 0

    def __init__(self, timestamp_ms: int, randomness: int):
        """
        Initialize un ULID avec un timestamp et une valeur aléatoire.
        
        Args:
            timestamp_ms: Timestamp Unix en millisecondes
            randomness: Valeur aléatoire (80 bits)
            
        Raises:
            ValueError: Si les valeurs sont hors limites
        """
        if not 0 <= timestamp_ms <= self.TIME_MAX:
            raise ValueError(f"Timestamp doit être entre 0 et {self.TIME_MAX}")
        if not 0 <= randomness <= self.RANDOM_MAX:
            raise ValueError(f"Randomness doit être entre 0 et {self.RANDOM_MAX}")
            
        self.timestamp_ms = timestamp_ms
        self.randomness = randomness
    
    @classmethod
    def from_str(cls, ulid_str: str) -> ULID:
        """
        Crée un ULID à partir d'une chaîne.
        
        Args:
            ulid_str: Chaîne ULID de 26 caractères
            
        Returns:
            Instance ULID
            
        Raises:
            ValueError: Si la chaîne est invalide
        """
        if len(ulid_str) != cls.TOTAL_LEN:
            raise ValueError(f"ULID doit faire {cls.TOTAL_LEN} caractères")
            
        # Normalisation en majuscules
        ulid_str = ulid_str.upper()
        
        # Validation des caractères
        if not all(c in cls.DECODING_CHARS for c in ulid_str):
            raise ValueError("ULID contient des caractères invalides")
            
        # Décodage timestamp
        timestamp_ms = 0
        for char in ulid_str[:cls.TIME_LEN]:
            timestamp_ms = timestamp_ms * 32 + cls.DECODING_CHARS[char]
            
        # Décodage randomness
        randomness = 0
        for char in ulid_str[cls.TIME_LEN:]:
            randomness = randomness * 32 + cls.DECODING_CHARS[char]
            
        return cls(timestamp_ms, randomness)
    
    @classmethod
    def from_datetime(cls, dt: datetime) -> ULID:
        """
        Crée un ULID à partir d'un datetime.
        
        Args:
            dt: Datetime (sera converti en UTC si nécessaire)
            
        Returns:
            Instance ULID
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        timestamp_ms = int(dt.timestamp() * 1000)
        randomness = int.from_bytes(os.urandom(10), byteorder='big')
        return cls(timestamp_ms, randomness)
    
    @classmethod
    def generate(cls, timestamp_ms: Optional[int] = None) -> ULID:
        """
        Génère un nouveau ULID.
        
        Args:
            timestamp_ms: Timestamp optionnel (utilise le temps actuel par défaut)
            
        Returns:
            Instance ULID
        """
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)
        randomness = int.from_bytes(os.urandom(10), byteorder='big')
        return cls(timestamp_ms, randomness)
    
    @classmethod
    def generate_monotonic(cls) -> ULID:
        """
        Génère un ULID monotone (garantit l'ordre dans la même milliseconde).
        
        Returns:
            Instance ULID
        """
        with cls._lock:
            timestamp_ms = int(time.time() * 1000)
            
            # Si même milliseconde, incrémente randomness
            if timestamp_ms == cls._last_timestamp:
                if cls._last_randomness == cls.RANDOM_MAX:
                    # Force nouvelle milliseconde si randomness maximal
                    while timestamp_ms == cls._last_timestamp:
                        timestamp_ms = int(time.time() * 1000)
                    randomness = int.from_bytes(os.urandom(10), byteorder='big')
                else:
                    randomness = cls._last_randomness + 1
            else:
                randomness = int.from_bytes(os.urandom(10), byteorder='big')
            
            cls._last_timestamp = timestamp_ms
            cls._last_randomness = randomness
            
            return cls(timestamp_ms, randomness)
    
    def datetime(self) -> datetime:
        """
        Convertit le timestamp en datetime UTC.
        
        Returns:
            Datetime correspondant au timestamp
        """
        return datetime.fromtimestamp(self.timestamp_ms / 1000.0, timezone.utc)
    
    def __str__(self) -> str:
        """
        Convertit le ULID en chaîne de 26 caractères.
        
        Returns:
            Représentation string du ULID
        """
        encoding = ""
        
        # Encode timestamp
        val = self.timestamp_ms
        for _ in range(self.TIME_LEN):
            encoding = self.ENCODING_CHARS[val & 0x1F] + encoding
            val >>= 5
            
        # Encode randomness
        val = self.randomness
        for _ in range(self.RANDOM_LEN):
            encoding += self.ENCODING_CHARS[val & 0x1F]
            val >>= 5
            
        return encoding
    
    def __repr__(self) -> str:
        return f"ULID({self})"
        
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ULID):
            return NotImplemented
        return (self.timestamp_ms == other.timestamp_ms and 
                self.randomness == other.randomness)
    
    def __lt__(self, other: ULID) -> bool:
        if not isinstance(other, ULID):
            return NotImplemented
        if self.timestamp_ms != other.timestamp_ms:
            return self.timestamp_ms < other.timestamp_ms
        return self.randomness < other.randomness
    
    def __le__(self, other: ULID) -> bool:
        return self < other or self == other
        
    def __hash__(self) -> int:
        return hash((self.timestamp_ms, self.randomness))

# Exemple d'utilisation
if __name__ == "__main__":
    # Générer un ULID simple
    ulid = ULID.generate()
    print(f"ULID généré: {ulid}")
    print(f"Datetime: {ulid.datetime()}")
    
    # Générer une séquence monotone
    print("\nSéquence monotone:")
    for _ in range(5):
        print(ULID.generate_monotonic())
    
    # Créer depuis un datetime
    custom_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    ulid_from_dt = ULID.from_datetime(custom_dt)
    print(f"\nULID depuis datetime: {ulid_from_dt}")
    
    # Parser une chaîne ULID
    ulid_str = str(ulid)
    parsed_ulid = ULID.from_str(ulid_str)
    print(f"\nULID parsé: {parsed_ulid}")
    print(f"Timestamp: {parsed_ulid.datetime()}")
    
    # Démonstration de tri
    ulids = [ULID.generate() for _ in range(3)]
    print("\nTri de ULIDs:")
    for u in sorted(ulids):
        print(f"{u} - {u.datetime()}")