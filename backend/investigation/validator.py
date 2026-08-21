import re

def validate_sql(sql: str) -> bool:
    """
    Verifies a query is strictly a SELECT or WITH statement.
    Blocks destructive mutations and schema alterations.
    """
    if not sql or not isinstance(sql, str):
        return False
        
    # Remove single-line and multi-line SQL comments for accurate validation
    sql_cleaned = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    sql_cleaned = re.sub(r'/\*.*?\*/', '', sql_cleaned, flags=re.DOTALL)
    
    # Normalize whitespace and capitalization
    sql_cleaned = sql_cleaned.strip().upper()
    
    # Rule 1: The query MUST start with SELECT or WITH
    if not (sql_cleaned.startswith("SELECT") or sql_cleaned.startswith("WITH")):
        return False
        
    # Rule 2: Strictly forbid state-mutating and schema-altering keywords
    forbidden_keywords = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
        "CREATE", "TRUNCATE", "REPLACE", "PRAGMA", "GRANT", 
        "REVOKE", "COMMIT", "ROLLBACK", "EXEC", "EXECUTE"
    }
    
    # Tokenize the query to check against forbidden keywords
    # Using \b to ensure we match whole words (e.g., 'UPDATE', not 'UPDATED_AT')
    tokens = set(re.findall(r'\b[A-Z]+\b', sql_cleaned))
    
    if tokens.intersection(forbidden_keywords):
        return False
        
    return True