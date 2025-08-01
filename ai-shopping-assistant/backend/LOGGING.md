# Logging Configuration

This document explains the logging configuration for the AI Shopping Assistant backend.

## Environment Variables

### DEBUG
- **Default**: `False`
- **Description**: Enables debug mode for the application
- **When `True`**: 
  - Sets default log level to `DEBUG`
  - Enables detailed request/response logging
  - Shows SQL queries (if `DB_ECHO_SQL=True`)
  - Enables uvicorn debug logging

### LOG_LEVEL
- **Default**: `DEBUG` (when `DEBUG=True`), `INFO` (when `DEBUG=False`)
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Sets the minimum log level for the application

### DB_ECHO_SQL
- **Default**: `False`
- **Description**: When `True` and `DEBUG=True`, enables SQL query logging
- **Note**: Only works in debug mode to prevent production log spam

## Log Levels

### DEBUG
- Detailed information for diagnosing problems
- Request/response details
- Database operations
- Internal state changes

### INFO
- General information about application flow
- Startup/shutdown messages
- Request completion status
- Configuration loading

### WARNING
- Something unexpected happened but the application can continue
- Missing optional configuration
- Deprecated feature usage

### ERROR
- A serious problem occurred
- Request failures
- Database connection issues
- External service failures

### CRITICAL
- A very serious error occurred
- Application may not be able to continue
- System-level failures

## Log Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example:
```
2025-07-27 17:41:27,223 - app.config - INFO - Starting AI Shopping Assistant API
```

## Testing Logging

Use the provided test script to verify logging configuration:

```bash
# Test with current environment settings
python test_logging.py

# Test with specific settings
DEBUG=True LOG_LEVEL=DEBUG python test_logging.py
DEBUG=False LOG_LEVEL=INFO python test_logging.py
```

## Production Recommendations

- Set `DEBUG=False`
- Set `LOG_LEVEL=INFO` or `WARNING`
- Set `DB_ECHO_SQL=False`
- Consider using structured logging for better log analysis
- Use log aggregation services for production monitoring

## Development Recommendations

- Set `DEBUG=True`
- Set `LOG_LEVEL=DEBUG`
- Set `DB_ECHO_SQL=True` for database debugging
- Monitor logs in terminal for immediate feedback