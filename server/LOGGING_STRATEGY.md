# PandaTales Logging Strategy

## Overview

PandaTales uses **structured logging** via the `structlog` library to provide comprehensive, machine-readable logs for debugging, monitoring, and observability.

## Core Logging Components

### 1. Logging Configuration (`app/common/logging.py`)

#### Features:
- **Structured Logging**: JSON format for production, pretty console for development
- **Context Variables**: Automatic inclusion of request context
- **Log Levels**: Configurable via `LOG_LEVEL` environment variable (INFO, DEBUG, WARNING, ERROR)
- **Log Format**: JSON for production (machine-readable), colored console for development
- **Third-party Logger Control**: Set to WARNING level (uvicorn, sqlalchemy, httpx)

#### Configuration:
```python
# In .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json for production, text for development
```

## Application-Level Logging

### 1. Application Lifecycle (`app/main.py`)

#### Startup/Shutdown:
```python
logger.info("application_starting", environment=settings.APP_ENV)
logger.info("database_initialized")
logger.info("application_shutting_down")
logger.info("database_connections_closed")
```

### 2. Request Logging Middleware

#### Every HTTP request is automatically logged:

**Request Start:**
```json
{
  "event": "request_started",
  "method": "POST",
  "path": "/api/v1/books/generate",
  "client_ip": "192.168.1.100",
  "timestamp": "2026-03-01T17:30:00.123456"
}
```

**Request Complete:**
```json
{
  "event": "request_completed",
  "method": "POST",
  "path": "/api/v1/books/generate",
  "status_code": 202,
  "duration_ms": 245.67,
  "timestamp": "2026-03-01T17:30:00.369123"
}
```

**Request Failed:**
```json
{
  "event": "request_failed",
  "method": "POST",
  "path": "/api/v1/books/generate",
  "error": "S3Error: NoSuchBucket",
  "duration_ms": 52.34,
  "timestamp": "2026-03-01T17:30:00.175791",
  "exc_info": "..."
}
```

### 3. Exception Handler Logging

#### All exceptions are logged with context:

```python
# NotFoundException (404)
logger.warning("not_found", path=request.url.path, detail=exc.detail)

# BadRequestException (400)
logger.warning("bad_request", path=request.url.path, detail=exc.detail)

# UnauthorizedException (401)
logger.warning("unauthorized", path=request.url.path, detail=exc.detail)

# ForbiddenException (403)
logger.warning("forbidden", path=request.url.path, detail=exc.detail)

# ConflictException (409)
logger.warning("conflict", path=request.url.path, detail=exc.detail)

# ValidationException (422)
logger.warning("validation_error", path=request.url.path, detail=exc.detail, errors=exc.errors)

# Unhandled Exceptions (500)
logger.error("unhandled_exception", path=request.url.path, error=str(exc), exc_info=True)
```

## Service-Level Logging

### All services use structured logging with consistent patterns:

### 1. Address Service (`app/services/address.py`)

```python
logger.info("fetching_address", address_id=str(address_id), user_id=str(user_id))
logger.info("listing_addresses", user_id=str(user_id))
logger.info("addresses_listed", user_id=str(user_id), count=len(addresses))
logger.info("creating_address", user_id=str(user_id), city=address_data.city, country=address_data.country)
logger.info("address_created", address_id=str(address.id), user_id=str(user_id))
logger.info("updating_address", address_id=str(address_id), user_id=str(user_id))
logger.info("address_updated", address_id=str(address.id), user_id=str(user_id))
logger.info("deleting_address", address_id=str(address_id), user_id=str(user_id))
logger.info("address_deleted", address_id=str(address_id), user_id=str(user_id))
logger.info("setting_default_address", address_id=str(address_id), user_id=str(user_id))
logger.info("default_address_set", address_id=str(address.id), user_id=str(user_id))
```

### 2. Child Profile Service (`app/services/child_profile.py`)

```python
logger.info("fetching_child_profile", child_id=str(child_id), user_id=str(user_id))
logger.info("listing_child_profiles", user_id=str(user_id))
logger.info("child_profiles_listed", user_id=str(user_id), count=len(children))
logger.info("creating_child_profile", user_id=str(user_id), name=child_data.name, age=child_data.age)
logger.info("child_profile_created", child_id=str(child.id), user_id=str(user_id), name=child.name)
logger.info("updating_child_profile", child_id=str(child_id), user_id=str(user_id))
logger.info("child_profile_updated", child_id=str(child.id), user_id=str(user_id))
logger.info("updating_child_photo", child_id=str(child_id), user_id=str(user_id))
logger.info("child_photo_updated", child_id=str(child.id), user_id=str(user_id))
logger.info("deleting_child_profile", child_id=str(child_id), user_id=str(user_id))
logger.info("child_profile_deleted", child_id=str(child_id), user_id=str(user_id))
```

### 3. User Service (`app/services/user.py`)

```python
logger.info("fetching_user_profile", user_id=str(user_id))
logger.info("updating_user_profile", user_id=str(user_id))
logger.info("user_profile_updated", user_id=str(user.id), email=user.email)
logger.info("updating_user_avatar", user_id=str(user_id))
logger.info("user_avatar_updated", user_id=str(user.id))
logger.warning("account_deletion_requested", user_id=str(user_id))
logger.warning("account_deletion_failed_invalid_confirmation", user_id=str(user_id))
logger.warning("account_deleted", user_id=str(user_id))
logger.info("verifying_user_email", user_id=str(user_id))
logger.info("user_email_verified", user_id=str(user.id), email=user.email)
logger.info("verifying_user_phone", user_id=str(user_id))
logger.info("user_phone_verified", user_id=str(user.id), phone=user.phone)
```

### 4. Storage Service (`app/services/storage.py`)

```python
# Initialization
logger.error("minio_bucket_missing", bucket=self.bucket)
logger.error("minio_connection_error", error_code=e.code, error_message=str(e), exc_info=True)
logger.error("storage_init_error", error=str(e), exc_info=True)

# File Upload
logger.info("uploading_file_to_minio", object_name=object_name, size_bytes=file_size, content_type=content_type)
logger.info("file_uploaded_successfully", object_name=object_name, size_bytes=file_size)
logger.error("minio_upload_error", object_name=object_name, error_code=e.code, error_message=e.message, exc_info=True)
logger.error("unexpected_upload_error", object_name=object_name, error=str(e), exc_info=True)
logger.error("image_upload_error", error=str(e), exc_info=True)

# URL Generation
logger.info("generated_presigned_url", object_name=object_name, expires_seconds=int(expires.total_seconds()))
logger.error("minio_url_generation_error", object_name=object_name, error_code=e.code, error_message=e.message, exc_info=True)
logger.error("unexpected_url_generation_error", object_name=object_name, error=str(e), exc_info=True)

# File Deletion
logger.info("file_deleted", object_name=object_name)
logger.warning("file_not_found_for_deletion", object_name=object_name)
logger.error("minio_delete_error", object_name=object_name, error_code=e.code, error_message=e.message, exc_info=True)
logger.error("unexpected_delete_error", object_name=object_name, error=str(e), exc_info=True)

# File Existence Check
logger.error("file_exists_check_error", object_name=object_name, error=str(e), exc_info=True)
logger.error("unexpected_file_exists_error", object_name=object_name, error=str(e), exc_info=True)
```

### 5. Generated Book Service (`app/services/generated_book.py`)

```python
logger.info("checking_generation_limit", user_id=str(user_id), daily_count=daily_count, max_per_day=max_per_day)
logger.warning("generation_limit_exceeded", user_id=str(user_id), daily_count=daily_count)
logger.info("initiating_photo_to_coloring", user_id=str(user_id), photo_count=len(photos))
```

### 6. Generation Config Service (`app/services/generation_config.py`)

```python
logger.info("listing_generation_configs", filters=filters)
logger.info("generation_configs_listed", total=total)
logger.info("fetching_generation_config", config_id=str(config_id))
logger.warning("generation_config_not_found", config_id=str(config_id))
logger.info("creating_generation_config", name=data.name, config_type=data.config_type)
logger.warning("generation_config_duplicate", name=data.name, config_type=data.config_type)
```

### 7. Template Services (`app/services/story_book_template.py`, `coloring_book_template.py`)

```python
logger.info("Fetching story book template", template_id=str(template_id))
logger.info("Creating story book template", title=template_data.title)
logger.info("Story book template created", template_id=str(template.id))
logger.info("Updating story book template", template_id=str(template_id))
logger.info("Story book template updated", template_id=str(template.id))
logger.info("Deleting story book template", template_id=str(template_id))
logger.info("Story book template deleted", template_id=str(template_id))
logger.info("Fetching story book templates by genre", genre=genre)
logger.info("Fetching series templates", series_id=str(series_id))
logger.info("Fetching all genres")
```

## Log Levels

### INFO
- Normal operations
- Resource fetching
- Creation/update/deletion operations
- Successful uploads
- URL generation

### WARNING
- Resource not found
- Validation failures
- Account deletions
- Generation limits exceeded
- Duplicate resource creation attempts

### ERROR
- System failures
- MinIO connection errors
- Upload failures
- Unexpected exceptions
- Unhandled errors

## Structured Logging Best Practices

### ✅ DO:
```python
# Use key-value pairs
logger.info("user_created", user_id=str(user.id), email=user.email)

# Include relevant context
logger.error("upload_failed", object_name=object_name, error_code=e.code, exc_info=True)

# Use consistent event names (snake_case)
logger.info("generation_started")
```

### ❌ DON'T:
```python
# Don't use f-strings (not machine-readable)
logger.info(f"User {user_id} created")

# Don't log sensitive data
logger.info("user_login", password=password)  # NEVER!

# Don't use inconsistent naming
logger.info("Generation_Started")  # Use snake_case
```

## Querying Logs

### Development (Console):
Logs are pretty-printed with colors for easy reading.

### Production (JSON):

**Using jq to query:**
```bash
# Find all errors
cat app.log | jq 'select(.level == "error")'

# Find all 500 errors
cat app.log | jq 'select(.status_code == 500)'

# Find slow requests (>1 second)
cat app.log | jq 'select(.duration_ms > 1000)'

# Find all MinIO errors
cat app.log | jq 'select(.event | contains("minio"))'

# Find requests for specific user
cat app.log | jq 'select(.user_id == "123e4567-e89b-12d3-a456-426614174000")'
```

**Using grep:**
```bash
# Find all upload operations
grep "uploading_file_to_minio" app.log

# Find generation limit errors
grep "generation_limit_exceeded" app.log

# Find storage service errors
grep "storage.*error" app.log
```

## Monitoring & Alerting

### Key Metrics to Monitor:

1. **Error Rate**: `count(level == "error") / count(all_logs)`
2. **Slow Requests**: `count(duration_ms > 1000)`
3. **MinIO Errors**: `count(event contains "minio_error")`
4. **Generation Limits**: `count(event == "generation_limit_exceeded")`
5. **Failed Uploads**: `count(event contains "upload_error")`
6. **5xx Responses**: `count(status_code >= 500)`

### Alert Thresholds:

- **Critical**: Error rate > 5% over 5 minutes
- **Warning**: Error rate > 2% over 5 minutes
- **Critical**: Slow requests > 20% over 5 minutes
- **Critical**: MinIO errors > 10 in 5 minutes
- **Warning**: Failed uploads > 5 in 5 minutes

## Log Aggregation

### Recommended Tools:

1. **ELK Stack** (Elasticsearch, Logstash, Kibana)
   - Ingest JSON logs
   - Create dashboards
   - Set up alerts

2. **Splunk**
   - Real-time monitoring
   - Anomaly detection
   - Custom dashboards

3. **DataDog**
   - APM integration
   - Custom metrics
   - Trace correlation

4. **Grafana Loki**
   - Label-based indexing
   - Low cost
   - Grafana integration

## Log Rotation

### Production Setup:

```yaml
# /etc/logrotate.d/pandatales
/var/log/pandatales/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 pandatales pandatales
    sharedscripts
    postrotate
        systemctl reload pandatales
    endscript
}
```

## Environment-Specific Configuration

### Development:
```env
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### Staging:
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Production:
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=https://...@sentry.io/...
```

## Sensitive Data Protection

### Never Log:
- ❌ Passwords
- ❌ API keys
- ❌ JWT tokens
- ❌ Credit card numbers
- ❌ Social security numbers
- ❌ Personal health information

### Safe to Log:
- ✅ User IDs (UUIDs)
- ✅ Email addresses (for business purposes)
- ✅ Timestamps
- ✅ Status codes
- ✅ Resource IDs
- ✅ Operation types

## Performance Considerations

### Structured logging adds minimal overhead:

- **JSON serialization**: ~0.1ms per log
- **Context injection**: ~0.01ms
- **Console rendering**: ~0.5ms (dev only)

### Tips:
1. Use INFO level in production (avoid DEBUG)
2. Avoid logging large payloads (>1KB)
3. Use async I/O for log shipping
4. Rotate logs daily to prevent disk fill
5. Sample high-volume events if needed

## Testing Logs

### Unit Tests:
```python
def test_user_creation_logs(caplog):
    with caplog.at_level(logging.INFO):
        service.create_user(user_data)
    
    assert "user_created" in caplog.text
    assert "user_id" in caplog.text
```

### Integration Tests:
```python
@pytest.mark.asyncio
async def test_storage_upload_logs(caplog):
    with caplog.at_level(logging.INFO):
        await storage_service.upload_file(file, "test.jpg")
    
    assert "uploading_file_to_minio" in caplog.text
    assert "file_uploaded_successfully" in caplog.text
```

## Summary

PandaTales logging provides:

- ✅ **Structured logs** for machine parsing
- ✅ **Comprehensive coverage** across all services
- ✅ **Performance metrics** via request logging
- ✅ **Error tracking** with full stack traces
- ✅ **Consistent format** across all components
- ✅ **Context preservation** through request lifecycle
- ✅ **Production-ready** JSON output
- ✅ **Development-friendly** colored console output
- ✅ **Security-conscious** (no sensitive data)
- ✅ **Queryable** via standard tools (jq, grep)

All services and critical operations are instrumented with appropriate logging levels for effective monitoring, debugging, and observability in production environments.
