import re

def validate_sql(sql: str) -> bool:
    """
    Verifies a query is strictly a SELECT or WITH statement.
    Blocks destructive mutations and schema alterations.
    """
    if not sql or not isinstance(sql, str):
        return False
        
    # Remove single-line and multi-line SQL comments for accurate validation
    sql_cleaned = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    sql_cleaned = re.sub(r'--.*', '', sql_cleaned)
    
    # Normalize whitespace and capitalization
    sql_cleaned = sql_cleaned.strip().upper()
    
    # Rule 1: Prevent stacked multi-statement execution via semicolons
    # Strip a trailing semicolon if present, but reject internal semicolons
    sql_trimmed = sql_cleaned.rstrip(';').strip()
    if ';' in sql_trimmed:
        return False
        
    # Rule 2: The query MUST start with SELECT or WITH
    if not (sql_trimmed.startswith("SELECT") or sql_trimmed.startswith("WITH")):
        return False
        
    # Rule 3: Strictly forbid state-mutating and schema-altering keywords
    forbidden_keywords = {
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
        "CREATE", "TRUNCATE", "REPLACE", "PRAGMA", "GRANT", 
        "REVOKE", "COMMIT", "ROLLBACK", "EXEC", "EXECUTE", "VACUUM"
    }
    
    # Tokenize the query to check against forbidden keywords
    tokens = set(re.findall(r'\b[A-Z]+\b', sql_trimmed))
    
    if tokens.intersection(forbidden_keywords):
        return False
        
    return True