# boolean_search.py
from typing import Set, List, Dict, Union, Optional
from enum import Enum
import re
from dataclasses import dataclass

from viper_logs.fuzzy_search import FuzzyTextIndexer

class BooleanOperator(Enum):
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'

@dataclass
class BooleanTerm:
    term: str
    is_negated: bool = False

@dataclass
class BooleanExpression:
    left: Union['BooleanExpression', BooleanTerm]
    operator: Optional[BooleanOperator]
    right: Optional[Union['BooleanExpression', BooleanTerm]] = None

class BooleanParser:
    def __init__(self):
        self.operators = {
            'AND': BooleanOperator.AND,
            'OR': BooleanOperator.OR,
            'NOT': BooleanOperator.NOT
        }
    
    def _tokenize(self, query: str) -> List[str]:
        """Tokenize la requête booléenne"""
        # Ajoute des espaces autour des parenthèses
        query = re.sub(r'([()])', r' \1 ', query)
        # Sépare les tokens
        return [token for token in query.split() if token]
        
    def parse(self, query: str) -> BooleanExpression:
        """Parse une requête booléenne"""
        tokens = self._tokenize(query.upper())
        return self._parse_expression(tokens)
        
    def _parse_expression(self, tokens: List[str]) -> BooleanExpression:
        stack = []
        current_expr = None
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if token == '(':
                # Trouve la parenthèse fermante correspondante
                level = 1
                j = i + 1
                while j < len(tokens) and level > 0:
                    if tokens[j] == '(':
                        level += 1
                    elif tokens[j] == ')':
                        level -= 1
                    j += 1
                    
                # Parse l'expression entre parenthèses
                sub_expr = self._parse_expression(tokens[i+1:j-1])
                if current_expr is None:
                    current_expr = sub_expr
                else:
                    current_expr = BooleanExpression(
                        left=current_expr,
                        operator=stack.pop(),
                        right=sub_expr
                    )
                i = j
                
            elif token in self.operators:
                if token == 'NOT':
                    # Le prochain terme sera négé
                    stack.append(True)
                else:
                    stack.append(self.operators[token])
                i += 1
                
            else:
                # Terme simple
                is_negated = stack.pop() if stack and isinstance(stack[-1], bool) else False
                term = BooleanTerm(token.lower(), is_negated)
                
                if current_expr is None:
                    current_expr = term
                else:
                    current_expr = BooleanExpression(
                        left=current_expr,
                        operator=stack.pop(),
                        right=term
                    )
                i += 1
                
        return current_expr

class BooleanSearchIndexer(FuzzyTextIndexer):
    def __init__(self):
        super().__init__()
        self.boolean_parser = BooleanParser()
        
    def _evaluate_expression(self, expr: Union[BooleanExpression, BooleanTerm], 
                           field: Optional[str] = None) -> Set[str]:
        """Évalue une expression booléenne"""
        if isinstance(expr, BooleanTerm):
            # Recherche le terme dans l'index
            term_docs = set()
            for term, entries in self.index.items():
                if expr.term.lower() in term.lower():
                    for doc_id, entry in entries.items():
                        if field is None or entry.field == field:
                            term_docs.add(doc_id)
                            
            return set(self.documents.keys()) - term_docs if expr.is_negated else term_docs
            
        # Évalue récursivement les sous-expressions
        left_result = self._evaluate_expression(expr.left, field)
        
        if expr.operator == BooleanOperator.AND:
            right_result = self._evaluate_expression(expr.right, field)
            return left_result & right_result
            
        elif expr.operator == BooleanOperator.OR:
            right_result = self._evaluate_expression(expr.right, field)
            return left_result | right_result
            
        return left_result
        
    def boolean_search(self, query: str, field: Optional[str] = None) -> List[Dict]:
        """Effectue une recherche booléenne"""
        try:
            # Parse la requête
            expression = self.boolean_parser.parse(query)
            
            # Évalue l'expression
            matching_docs = self._evaluate_expression(expression, field)
            
            # Prépare les résultats
            results = [
                {
                    'doc_id': doc_id,
                    'content': self.documents[doc_id]
                }
                for doc_id in matching_docs
            ]
            
            return results
            
        except Exception as e:
            print(f"Erreur lors de la recherche booléenne: {str(e)}")
            return []