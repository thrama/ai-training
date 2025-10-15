"""
Helper per la selezione intelligente dei classTypes EDC.
Mappa richieste naturali ai classTypes appropriati.
"""
from typing import List, Optional, Set
from enum import Enum


class EDCClassType(str, Enum):
    """ClassTypes EDC supportati per API bulk."""
    
    # Relational Objects
    COLUMN = "com.infa.ldm.relational.Column"
    VIEW_COLUMN = "com.infa.ldm.relational.ViewColumn"
    TABLE = "com.infa.ldm.relational.Table"
    VIEW = "com.infa.ldm.relational.View"
    SCHEMA = "com.infa.ldm.relational.DatabaseSchema"
    DATABASE = "com.infa.ldm.relational.DatabaseServer"
    
    # Altri tipi comuni (estendibile)
    PRIMARY_KEY = "com.infa.ldm.relational.PrimaryKey"
    FOREIGN_KEY = "com.infa.ldm.relational.ForeignKey"
    INDEX = "com.infa.ldm.relational.Index"


class ClassTypeSelector:
    """
    Selettore intelligente di classTypes basato su keyword e contesto.
    """
    
    # Mappatura keyword -> classTypes
    KEYWORD_MAP = {
        # Colonne
        'column': [EDCClassType.COLUMN],
        'columns': [EDCClassType.COLUMN],
        'colonna': [EDCClassType.COLUMN],
        'colonne': [EDCClassType.COLUMN],
        'field': [EDCClassType.COLUMN],
        'fields': [EDCClassType.COLUMN],
        'campo': [EDCClassType.COLUMN],
        'campi': [EDCClassType.COLUMN],
        
        # View Columns
        'view column': [EDCClassType.VIEW_COLUMN],
        'view columns': [EDCClassType.VIEW_COLUMN],
        'colonna vista': [EDCClassType.VIEW_COLUMN],
        'colonne vista': [EDCClassType.VIEW_COLUMN],
        
        # Tutte le colonne (table + view)
        'all columns': [EDCClassType.COLUMN, EDCClassType.VIEW_COLUMN],
        'tutte le colonne': [EDCClassType.COLUMN, EDCClassType.VIEW_COLUMN],
        
        # Tabelle
        'table': [EDCClassType.TABLE],
        'tables': [EDCClassType.TABLE],
        'tabella': [EDCClassType.TABLE],
        'tabelle': [EDCClassType.TABLE],
        
        # View
        'view': [EDCClassType.VIEW],
        'views': [EDCClassType.VIEW],
        'vista': [EDCClassType.VIEW],
        'viste': [EDCClassType.VIEW],
        
        # Tabelle + View
        'table and view': [EDCClassType.TABLE, EDCClassType.VIEW],
        'tables and views': [EDCClassType.TABLE, EDCClassType.VIEW],
        'tabelle e viste': [EDCClassType.TABLE, EDCClassType.VIEW],
        'all tables': [EDCClassType.TABLE, EDCClassType.VIEW],
        'tutte le tabelle': [EDCClassType.TABLE, EDCClassType.VIEW],
        
        # Schema
        'schema': [EDCClassType.SCHEMA],
        'schemas': [EDCClassType.SCHEMA],
        'schemi': [EDCClassType.SCHEMA],
        
        # Database
        'database': [EDCClassType.DATABASE],
        'databases': [EDCClassType.DATABASE],
        'db': [EDCClassType.DATABASE],
        
        # Keys
        'primary key': [EDCClassType.PRIMARY_KEY],
        'primary keys': [EDCClassType.PRIMARY_KEY],
        'foreign key': [EDCClassType.FOREIGN_KEY],
        'foreign keys': [EDCClassType.FOREIGN_KEY],
        'chiave primaria': [EDCClassType.PRIMARY_KEY],
        'chiavi primarie': [EDCClassType.PRIMARY_KEY],
        
        # Index
        'index': [EDCClassType.INDEX],
        'indexes': [EDCClassType.INDEX],
        'indice': [EDCClassType.INDEX],
        'indici': [EDCClassType.INDEX],
    }
    
    @classmethod
    def infer_class_types(
        cls,
        query: str,
        default_to_columns: bool = True
    ) -> List[str]:
        """
        Inferisce i classTypes dalla query naturale.
        
        Args:
            query: Query in linguaggio naturale
            default_to_columns: Se True, default a colonne se non trova match
            
        Returns:
            Lista di classTypes appropriati
            
        Examples:
            >>> ClassTypeSelector.infer_class_types("mostrami tutte le colonne")
            ['com.infa.ldm.relational.Column']
            
            >>> ClassTypeSelector.infer_class_types("quante tabelle ci sono")
            ['com.infa.ldm.relational.Table']
            
            >>> ClassTypeSelector.infer_class_types("elenca tabelle e viste")
            ['com.infa.ldm.relational.Table', 'com.infa.ldm.relational.View']
        """
        query_lower = query.lower()
        matched_types: Set[EDCClassType] = set()
        
        # Cerca match nelle keyword
        for keyword, class_types in cls.KEYWORD_MAP.items():
            if keyword in query_lower:
                matched_types.update(class_types)
        
        # Se non trova match, usa default
        if not matched_types and default_to_columns:
            matched_types.add(EDCClassType.COLUMN)
        
        # Converti in lista di stringhe
        return [ct.value for ct in matched_types]
    
    @classmethod
    def get_class_types_by_category(cls, category: str) -> List[str]:
        """
        Recupera classTypes per categoria predefinita.
        
        Args:
            category: Nome categoria (columns, tables, views, all, etc.)
            
        Returns:
            Lista di classTypes per la categoria
        """
        categories = {
            'columns': [EDCClassType.COLUMN],
            'all_columns': [EDCClassType.COLUMN, EDCClassType.VIEW_COLUMN],
            'view_columns': [EDCClassType.VIEW_COLUMN],
            'tables': [EDCClassType.TABLE],
            'views': [EDCClassType.VIEW],
            'tables_and_views': [EDCClassType.TABLE, EDCClassType.VIEW],
            'schemas': [EDCClassType.SCHEMA],
            'databases': [EDCClassType.DATABASE],
            'all': [
                EDCClassType.COLUMN,
                EDCClassType.VIEW_COLUMN,
                EDCClassType.TABLE,
                EDCClassType.VIEW
            ]
        }
        
        selected = categories.get(category.lower(), [EDCClassType.COLUMN])
        return [ct.value for ct in selected]
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Restituisce tutti i classTypes disponibili."""
        return [ct.value for ct in EDCClassType]
    
    @classmethod
    def describe_class_type(cls, class_type: str) -> str:
        """
        Fornisce una descrizione human-readable del classType.
        
        Args:
            class_type: ClassType completo
            
        Returns:
            Descrizione in italiano
        """
        descriptions = {
            EDCClassType.COLUMN: "Colonne delle tabelle",
            EDCClassType.VIEW_COLUMN: "Colonne delle view",
            EDCClassType.TABLE: "Tabelle del database",
            EDCClassType.VIEW: "View del database",
            EDCClassType.SCHEMA: "Schemi del database",
            EDCClassType.DATABASE: "Database",
            EDCClassType.PRIMARY_KEY: "Chiavi primarie",
            EDCClassType.FOREIGN_KEY: "Chiavi esterne",
            EDCClassType.INDEX: "Indici",
        }
        
        for ct in EDCClassType:
            if ct.value == class_type:
                return descriptions.get(ct, class_type)
        
        return class_type


# ====================================
# Esempi d'uso
# ====================================

def demo_inference():
    """Dimostra l'inferenza automatica dei classTypes."""
    
    test_queries = [
        "Mostrami tutte le colonne di DataPlatform",
        "Quante tabelle ci sono in DWHEVO?",
        "Elenca le view del database",
        "Trova tutte le colonne delle tabelle e delle viste",
        "Dammi l'elenco degli schemi",
        "Cerca primary keys",
        "Lista completa di tables and views",
    ]
    
    print("🧪 Test Inferenza Automatica ClassTypes\n")
    print("=" * 70)
    
    for query in test_queries:
        types = ClassTypeSelector.infer_class_types(query)
        
        print(f"\nQuery: {query}")
        print(f"ClassTypes inferiti:")
        for ct in types:
            desc = ClassTypeSelector.describe_class_type(ct)
            print(f"  • {desc}")
            print(f"    ({ct})")


if __name__ == "__main__":
    demo_inference()