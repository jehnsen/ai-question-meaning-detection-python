# MySQL Migration Guide

## Summary

The Effortless-Respond API has been successfully migrated from PostgreSQL to MySQL.

## Changes Made

### 1. Database Driver
- **Old**: `psycopg2` (PostgreSQL)
- **New**: `pymysql` (MySQL)

### 2. Vector Storage
- **Old**: `pgvector` extension for native PostgreSQL vector type
- **New**: Custom `VectorType` class storing embeddings as JSON TEXT in MySQL

### 3. Configuration Files

#### `.env` File
```ini
# MySQL connection string
DATABASE_URL=mysql+pymysql://root:@localhost:3306/effortless_respond
```

Format: `mysql+pymysql://username:password@host:port/database_name`

#### `main.py` Changes
- Removed `pgvector` dependency
- Added custom `VectorType` TypeDecorator for storing vectors as JSON
- Changed `load_dotenv()` to `load_dotenv(override=True)` to override system env vars
- Removed `CREATE EXTENSION` for pgvector in `init_db()`

#### `reset_database.py` Changes
- Added logic to detect and handle both MySQL and PostgreSQL
- Removed pgvector extension creation
- Changed `load_dotenv()` to `load_dotenv(override=True)`

### 4. New Files

#### `create_mysql_database.py`
A helper script to create the MySQL database if it doesn't exist.

```bash
python create_mysql_database.py
```

## Installation Steps

### 1. Install MySQL Driver
```bash
pip install pymysql cryptography
```

### 2. Start MySQL Server
Ensure MySQL/MariaDB is running on your system (e.g., XAMPP, standalone MySQL).

### 3. Create Database
```bash
python create_mysql_database.py
```

### 4. Create Tables
```bash
python reset_database.py 1
```

### 5. Start Server
```bash
python main.py
```

## Current Database Configuration

- **Database System**: MySQL 8.0+ (via XAMPP)
- **Database Name**: `sbb_db` (configurable via .env)
- **Host**: localhost
- **Port**: 3306
- **User**: root
- **Password**: (empty/configured)

## Vector Storage Implementation

### Custom VectorType Class

```python
class VectorType(TypeDecorator):
    """Custom type to store vector embeddings as JSON in MySQL."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value
```

This stores the 1024-dimensional embedding vectors as JSON arrays in MySQL TEXT columns.

## Performance Considerations

### PostgreSQL vs MySQL for Vectors

**PostgreSQL with pgvector**:
- ✓ Native vector type with indexing
- ✓ Built-in similarity search operators
- ✓ Better performance for large-scale vector operations

**MySQL with JSON**:
- ✓ Works with any MySQL 5.7+ installation
- ✓ No special extensions required
- ✓ Portable across different MySQL environments
- ⚠ Similarity calculations happen in Python (no native vector operations)
- ⚠ Cannot create indexes on vector data

### Current Architecture
The current implementation calculates cosine similarity in Python after retrieving vectors from MySQL. This is acceptable for moderate datasets (<10,000 vectors) but may need optimization for larger scales.

## Compatibility

### Supported MySQL Versions
- MySQL 5.7+
- MySQL 8.0+ (recommended)
- MariaDB 10.2+

### Dependencies
```txt
pymysql>=1.1.2
cryptography>=46.0.3
sqlalchemy>=2.0.0
sqlmodel>=0.0.14
```

## Testing

### Test Create Response
```bash
curl -X POST "http://localhost:8000/create-response?question_id=TEST-001&question_text=Test&answer_text=Answer&evidence=Evidence"
```

### Test Batch Processing
```bash
python test_batch_endpoint.py
```

## Rollback to PostgreSQL

To switch back to PostgreSQL:

1. Update `.env`:
```ini
DATABASE_URL=postgresql://postgres:password@localhost:5432/effortless_respond
```

2. Revert `main.py`:
- Change `VectorType` back to `Vector(1024)` from pgvector
- Import pgvector: `from pgvector.sqlalchemy import Vector`
- Re-enable pgvector extension in `init_db()`

3. Run reset:
```bash
python reset_database.py 1
```

## Known Limitations

1. **No Native Vector Indexing**: MySQL doesn't support vector similarity indexes like PostgreSQL's IVFFlat or HNSW
2. **Slower Similarity Search**: All similarity calculations happen in Python
3. **Memory Usage**: Large vector datasets require more memory during similarity computations

## Future Optimizations

For large-scale deployments, consider:
1. **Migrate to PostgreSQL with pgvector** for better vector performance
2. **Use Elasticsearch** with vector plugin for distributed vector search
3. **Implement caching** for frequently accessed vectors
4. **Add Redis** for vector similarity result caching

## Support

For issues or questions:
- Check server logs: The server runs with SQLAlchemy echo=True for debugging
- Verify MySQL is running: `netstat -aon | findstr :3306`
- Test connection: `python create_mysql_database.py`
