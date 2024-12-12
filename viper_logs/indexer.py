# indexer.py
from typing import Dict, Set, List, Optional
import re
from collections import defaultdict
from dataclasses import dataclass
import math

@dataclass
class IndexEntry:
    """Représente une entrée dans l'index inversé"""
    doc_id: str
    positions: List[int]
    field: str
    tf: float = 0.0  # term frequency
    
class TextIndexer:
    def __init__(self):
        self.index: Dict[str, Dict[str, IndexEntry]] = defaultdict(dict)
        self.documents: Dict[str, Dict] = {}
        self.doc_count = 0
        self.stop_words = set(['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est'])
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize le texte en mots"""
        # Convertit en minuscules et découpe en mots
        words = re.findall(r'\b\w+\b', text.lower())
        # Retire les stop words
        return [w for w in words if w not in self.stop_words]
        
    def _calculate_tf(self, term_count: int, doc_length: int) -> float:
        """Calcule la fréquence du terme (TF)"""
        return term_count / doc_length if doc_length > 0 else 0
        
    def _calculate_idf(self, term: str) -> float:
        """Calcule l'IDF (Inverse Document Frequency)"""
        doc_with_term = len(self.index[term])
        return math.log((1 + self.doc_count) / (1 + doc_with_term)) + 1
        
    def add_document(self, doc_id: str, content: Dict[str, str]) -> None:
        """Ajoute un document à l'index"""
        self.documents[doc_id] = content
        self.doc_count += 1
        
        # Pour chaque champ du document
        for field, text in content.items():
            tokens = self._tokenize(text)
            doc_length = len(tokens)
            
            # Compte les positions de chaque terme
            term_positions: Dict[str, List[int]] = defaultdict(list)
            for pos, term in enumerate(tokens):
                term_positions[term].append(pos)
            
            # Mise à jour de l'index
            for term, positions in term_positions.items():
                entry = IndexEntry(
                    doc_id=doc_id,
                    positions=positions,
                    field=field,
                    tf=self._calculate_tf(len(positions), doc_length)
                )
                self.index[term][doc_id] = entry
                
    def remove_document(self, doc_id: str) -> None:
        """Supprime un document de l'index"""
        if doc_id in self.documents:
            # Supprime les entrées d'index pour ce document
            for term in list(self.index.keys()):
                if doc_id in self.index[term]:
                    del self.index[term][doc_id]
                if not self.index[term]:
                    del self.index[term]
            
            # Supprime le document
            del self.documents[doc_id]
            self.doc_count -= 1
            
    def search(self, query: str, field: Optional[str] = None) -> List[Dict]:
        """Recherche basique avec score TF-IDF"""
        query_terms = self._tokenize(query)
        scores: Dict[str, float] = defaultdict(float)
        
        for term in query_terms:
            if term in self.index:
                idf = self._calculate_idf(term)
                
                for doc_id, entry in self.index[term].items():
                    if field is None or entry.field == field:
                        # Score TF-IDF
                        scores[doc_id] += entry.tf * idf
        
        # Trie les résultats par score
        results = [
            {
                'doc_id': doc_id,
                'score': score,
                'content': self.documents[doc_id]
            }
            for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return results