"""
Module de gestion de l'affichage des logs avec support de couleurs et formats multiples.
Fournit des outils flexibles pour la personnalisation de l'affichage des logs.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import re


class Color:
    """Codes ANSI pour la coloration du texte dans le terminal."""
    
    # Base colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # Backgrounds
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKE = "\033[9m"
    
    # Reset
    RESET = "\033[0m"
    
    @classmethod
    def strip_color(cls, text: str) -> str:
        """Retire tous les codes de couleur d'une chaîne."""
        return re.sub(r'\033\[[0-9;]*m', '', text)

    @classmethod
    def get_length(cls, text: str) -> int:
        """Retourne la longueur visible d'une chaîne (sans les codes couleur)."""
        return len(cls.strip_color(text))


class LogLevel:
    """Niveaux de log standards avec leurs caractéristiques."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"
    
    @classmethod
    def get_all_levels(cls) -> List[str]:
        """Retourne tous les niveaux de log disponibles."""
        return [cls.DEBUG, cls.INFO, cls.WARN, cls.ERROR, cls.FATAL]


class DisplayTheme:
    """Thème de couleurs pour l'affichage des logs."""
    
    def __init__(self, colored_output: bool = True):
        self.colored_output = colored_output
        
        # Couleurs par niveau de log
        self.level_colors = {
            LogLevel.DEBUG: Color.BLUE,
            LogLevel.INFO: Color.GREEN,
            LogLevel.WARN: Color.YELLOW,
            LogLevel.ERROR: Color.RED,
            LogLevel.FATAL: Color.BRIGHT_RED + Color.BOLD
        }
        
        # Couleurs par type de champ
        self.field_colors = {
            "timestamp": Color.BRIGHT_BLACK,
            "component": Color.MAGENTA,
            "user_id": Color.CYAN,
            "description": Color.BRIGHT_WHITE,
            "action": Color.BRIGHT_BLUE,
            "service": Color.BRIGHT_MAGENTA
        }
        
        # Styles de bordure pour les tableaux
        self.table_chars = {
            "top_left": "┌",
            "top_right": "┐",
            "bottom_left": "└",
            "bottom_right": "┘",
            "horizontal": "─",
            "vertical": "│",
            "cross": "┼",
            "top_t": "┬",
            "bottom_t": "┴",
            "left_t": "├",
            "right_t": "┤"
        }
    
    def colorize(self, text: str, color: str) -> str:
        """Applique une couleur à un texte si la colorisation est activée."""
        if self.colored_output:
            return f"{color}{text}{Color.RESET}"
        return text
    
    def get_level_color(self, level: str) -> str:
        """Retourne la couleur associée à un niveau de log."""
        return self.level_colors.get(level, Color.WHITE)
    
    def get_field_color(self, field: str) -> str:
        """Retourne la couleur associée à un type de champ."""
        return self.field_colors.get(field, Color.WHITE)


class DisplayFormat:
    """Configuration du format d'affichage des logs."""
    
    def __init__(self,
                display_fields: Optional[List[str]] = None,
                timestamp_format: str = "%Y-%m-%d %H:%M:%S",
                separator: str = " | ",
                field_formats: Optional[Dict[str, str]] = None):
        """
        Args:
            display_fields: Liste des champs à afficher
            timestamp_format: Format de la date/heure
            separator: Séparateur entre les champs
            field_formats: Formats spécifiques pour certains champs
        """
        self.display_fields = display_fields or ["timestamp", "level", "component", "description"]
        self.timestamp_format = timestamp_format
        self.separator = separator
        self.field_formats = field_formats or {}
        
    def format_field(self, field: str, value: Any) -> str:
        """Formate un champ selon sa configuration spécifique."""
        if field in self.field_formats:
            return self.field_formats[field].format(value)
        if field == "timestamp" and isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).strftime(self.timestamp_format)
        return str(value)


class DisplayConfig:
    """Configuration complète de l'affichage des logs."""
    
    def __init__(self,
                display_fields: Optional[List[str]] = None,
                timestamp_format: str = "%Y-%m-%d %H:%M:%S",
                colored_output: bool = True,
                separator: str = " | ",
                field_formats: Optional[Dict[str, str]] = None):
        """
        Args:
            display_fields: Liste des champs à afficher
            timestamp_format: Format de la date/heure
            colored_output: Active/désactive les couleurs
            separator: Séparateur entre les champs
            field_formats: Formats spécifiques pour certains champs
        """
        self.format = DisplayFormat(
            display_fields=display_fields,
            timestamp_format=timestamp_format,
            separator=separator,
            field_formats=field_formats
        )
        self.theme = DisplayTheme(colored_output=colored_output)

    def format_single_log(self, log_data: Dict[str, Any]) -> str:
        """Formate un log en une seule ligne."""
        parts = []
        
        for field in self.format.display_fields:
            if field not in log_data:
                continue
                
            value = self.format.format_field(field, log_data[field])
            
            if field == "level":
                value = f"[{value}]"
                value = self.theme.colorize(value, self.theme.get_level_color(log_data[field]))
            elif field == "timestamp":
                value = f"[{value}]"
                value = self.theme.colorize(value, self.theme.get_field_color("timestamp"))
            else:
                value = self.theme.colorize(value, self.theme.get_field_color(field))
            
            parts.append(value)
        
        return self.format.separator.join(parts)

    def format_log_table(self, logs: List[Dict[str, Any]]) -> str:
        """Formate plusieurs logs en tableau."""
        if not logs:
            return "No logs found."
        
        # Calculate column widths
        widths = {field: len(field) for field in self.format.display_fields}
        for log in logs:
            for field in self.format.display_fields:
                value = self.format.format_field(field, log.get(field, ""))
                widths[field] = max(widths[field], Color.get_length(value))
        
        # Create borders
        tc = self.theme.table_chars
        top_border = (f"{tc['top_left']}{tc['horizontal']}" + 
                     f"{tc['horizontal']}{tc['top_t']}{tc['horizontal']}".join(
                         tc['horizontal'] * widths[field] for field in self.format.display_fields
                     ) + f"{tc['horizontal']}{tc['top_right']}")
                     
        separator = (f"{tc['left_t']}{tc['horizontal']}" + 
                    f"{tc['horizontal']}{tc['cross']}{tc['horizontal']}".join(
                        tc['horizontal'] * widths[field] for field in self.format.display_fields
                    ) + f"{tc['horizontal']}{tc['right_t']}")
                    
        bottom_border = (f"{tc['bottom_left']}{tc['horizontal']}" + 
                        f"{tc['horizontal']}{tc['bottom_t']}{tc['horizontal']}".join(
                            tc['horizontal'] * widths[field] for field in self.format.display_fields
                        ) + f"{tc['horizontal']}{tc['bottom_right']}")
        
        # Create header
        header_parts = []
        for field in self.format.display_fields:
            header_cell = f"{field:{widths[field]}}"
            header_parts.append(self.theme.colorize(header_cell, Color.BOLD))
        header = f"{tc['vertical']} " + f" {tc['vertical']} ".join(header_parts) + f" {tc['vertical']}"
        
        # Create rows
        rows = []
        for log in logs:
            row_parts = []
            for field in self.format.display_fields:
                value = self.format.format_field(field, log.get(field, ""))
                if field == "level":
                    value = self.theme.colorize(
                        f"{value:{widths[field]}}", 
                        self.theme.get_level_color(log[field])
                    )
                else:
                    value = self.theme.colorize(
                        f"{value:{widths[field]}}", 
                        self.theme.get_field_color(field)
                    )
                row_parts.append(value)
            rows.append(f"{tc['vertical']} " + f" {tc['vertical']} ".join(row_parts) + f" {tc['vertical']}")
        
        # Assemble table
        return "\n".join([
            top_border,
            header,
            separator,
            *rows,
            bottom_border
        ])


class LogMetadata:
    """Classe utilitaire pour gérer les métadonnées des logs."""
    
    @staticmethod
    def format_metadata(metadata: Dict[str, Any], color: bool = True) -> str:
        """Formate les métadonnées pour l'affichage."""
        if not metadata:
            return ""
            
        parts = []
        for key, value in metadata.items():
            if color:
                formatted = f"{Color.DIM}{key}={Color.RESET}{Color.BRIGHT_WHITE}{value}{Color.RESET}"
            else:
                formatted = f"{key}={value}"
            parts.append(formatted)
            
        return "(" + ", ".join(parts) + ")"