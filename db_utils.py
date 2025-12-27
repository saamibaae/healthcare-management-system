"""
Database utility functions for executing raw MySQL queries in Flask.
Provides a centralized interface for database operations with proper connection management,
parameterized queries, and error handling.
"""
from flask import current_app
from config import Config
import pymysql
from typing import List, Dict, Any, Optional, Tuple


def get_db_connection():
    """
    Get MySQL database connection using Flask's config.
    
    Returns:
        pymysql.connections.Connection: MySQL connection object
    """
    return pymysql.connect(
        host=current_app.config.get('DB_HOST', Config.DB_HOST),
        port=current_app.config.get('DB_PORT', Config.DB_PORT),
        user=current_app.config.get('DB_USER', Config.DB_USER),
        password=current_app.config.get('DB_PASSWORD', Config.DB_PASSWORD),
        database=current_app.config.get('DB_NAME', Config.DB_NAME),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def dict_fetch_all(cursor) -> List[Dict[str, Any]]:
    """
    Convert cursor results to list of dictionaries.
    
    Args:
        cursor: Database cursor
    
    Returns:
        List of dictionaries representing rows
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_one(sql: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    """
    Execute SELECT query and return single row.
    
    Args:
        sql: SQL query string with %s placeholders
        params: Tuple of parameters for query
    
    Returns:
        Dictionary representing single row, or None if not found
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
    finally:
        conn.close()


def fetch_all(sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute SELECT query and return all rows.
    
    Args:
        sql: SQL query string with %s placeholders
        params: Tuple or list of parameters for query
    
    Returns:
        List of dictionaries representing rows
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return dict_fetch_all(cursor)
    finally:
        conn.close()


def fetch_count(sql: str, params: Optional[Tuple] = None) -> int:
    """
    Execute COUNT query and return integer count.
    
    Args:
        sql: SQL query string with %s placeholders (should contain COUNT)
        params: Tuple or list of parameters for query
    
    Returns:
        Integer count value
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            result = cursor.fetchone()
            if result:
                return result[0]
            return 0
    finally:
        conn.close()


def execute_update(sql: str, params: Optional[Tuple] = None) -> int:
    """
    Execute INSERT, UPDATE, or DELETE query.
    
    Args:
        sql: SQL query string with %s placeholders
        params: Tuple or list of parameters for query
    
    Returns:
        Number of affected rows
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_insert(sql: str, params: Optional[Tuple] = None) -> int:
    """
    Execute INSERT query and return the last inserted ID.
    
    Args:
        sql: INSERT SQL query string with %s placeholders
        params: Tuple or list of parameters for query
    
    Returns:
        Last inserted ID (primary key)
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_transaction(queries: List[Tuple[str, Optional[Tuple]]]) -> List[Any]:
    """
    Execute multiple queries in a single transaction.
    Rolls back all changes if any query fails.
    
    Args:
        queries: List of (sql, params) tuples
    
    Returns:
        List of results from each query
    
    Raises:
        Exception: If any query fails, transaction is rolled back
    """
    conn = get_db_connection()
    results = []
    try:
        with conn.cursor() as cursor:
            for sql, params in queries:
                cursor.execute(sql, params or ())
                if sql.strip().upper().startswith('SELECT'):
                    results.append(dict_fetch_all(cursor))
                else:
                    results.append(cursor.rowcount)
        conn.commit()
        return results
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def check_exists(sql: str, params: Optional[Tuple] = None) -> bool:
    """
    Check if a record exists based on query.
    
    Args:
        sql: SQL query string with %s placeholders
        params: Tuple or list of parameters for query
    
    Returns:
        True if record exists, False otherwise
    """
    result = fetch_one(sql, params)
    return result is not None


def get_or_create(table: str, lookup_fields: Dict[str, Any], defaults: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """
    Get existing record or create new one.
    Similar to Django's get_or_create but using raw SQL.
    
    Args:
        table: Table name (e.g., 'core_district')
        lookup_fields: Dictionary of fields to search for
        defaults: Dictionary of default values for creation
    
    Returns:
        Tuple of (record_dict, created_boolean)
    """
    # Build WHERE clause
    where_clauses = []
    params = []
    for field, value in lookup_fields.items():
        where_clauses.append(f"{field} = %s")
        params.append(value)
    
    where_sql = " AND ".join(where_clauses)
    select_sql = f"SELECT * FROM {table} WHERE {where_sql} LIMIT 1"
    
    # Try to get existing record
    existing = fetch_one(select_sql, tuple(params))
    if existing:
        return existing, False
    
    # Create new record
    all_fields = {**lookup_fields, **defaults}
    field_names = list(all_fields.keys())
    field_values = [all_fields[f] for f in field_names]
    placeholders = ', '.join(['%s'] * len(field_names))
    
    insert_sql = f"INSERT INTO {table} ({', '.join(field_names)}) VALUES ({placeholders})"
    new_id = execute_insert(insert_sql, tuple(field_values))
    
    # Fetch the newly created record
    # Get primary key name (assuming it ends with _id)
    pk_name = f"{table.split('_')[-1]}_id"
    created = fetch_one(f"SELECT * FROM {table} WHERE {pk_name} = %s", (new_id,))
    return created, True

