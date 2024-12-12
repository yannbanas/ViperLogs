# fuzzy_search.py
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

from viper_logs.indexer import TextIndexer

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calcule la distance de Levenshtein entre deux chaînes"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

class FuzzySearchIndex:
    def __init__(self, max_distance: int = 2):
        self.max_distance = max_distance
        self.term_docs: defaultdict[str, Set[str]] = defaultdict(set)  # terme -> ensemble de doc_ids
        self.doc_terms: defaultdict[str, Set[str]] = defaultdict(set)  # doc_id -> ensemble de termes
        
    def add_term(self, term: str, doc_id: str) -> None:
        """Ajoute un terme à l'index avec son document associé"""
        term = term.lower()
        self.term_docs[term].add(doc_id)
        self.doc_terms[doc_id].add(term)
            
    def search(self, query: str, threshold: float = 0.7) -> Dict[str, float]:
        """
        Recherche les documents contenant des termes similaires.
        Retourne un dictionnaire {doc_id: score}
        """
        query = query.lower()
        matching_docs = defaultdict(float)
        
        # Pour chaque terme indexé
        for indexed_term in self.term_docs.keys():
            distance = levenshtein_distance(query, indexed_term)
            max_len = max(len(query), len(indexed_term))
            similarity = 1 - (distance / max_len)
            
            if similarity >= threshold:
                # Ajoute le score à tous les documents contenant ce terme
                for doc_id in self.term_docs[indexed_term]:
                    matching_docs[doc_id] += similarity
        
        return matching_docs

class FuzzyTextIndexer(TextIndexer):
    def __init__(self, max_distance: int = 2):
        super().__init__()
        self.fuzzy_index = FuzzySearchIndex(max_distance)
        
    def add_document(self, doc_id: str, content: Dict[str, str]) -> None:
        """Étend l'indexation avec support fuzzy"""
        super().add_document(doc_id, content)
        
        # Indexe chaque champ du document
        for field, text in content.items():
            # Indexe le texte complet et chaque mot individuellement
            self.fuzzy_index.add_term(str(text), doc_id)
            for term in self._tokenize(str(text)):
                self.fuzzy_index.add_term(term, doc_id)
                
    def fuzzy_search(self, query: str, threshold: float = 0.7, field: Optional[str] = None) -> List[Dict]:
        """Recherche avec support fuzzy"""
        # Obtient les documents correspondants avec leurs scores
        matching_docs = self.fuzzy_index.search(query, threshold)
        
        # Trie et formate les résultats
        results = [
            {
                'doc_id': doc_id,
                'score': score,
                'content': self.documents[doc_id]
            }
            for doc_id, score in sorted(matching_docs.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return results