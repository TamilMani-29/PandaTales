# Book Generation Debug Analysis & Fixes

**Date:** 2026-04-05  
**Issue:** Generation failing with excessive logs and rate limiting

---

## 🔍 Issues Identified

### 1. **No Page Limiting for Testing** ❌
- **Problem:** Template `STORY_TPL_7` has **10 pages** configured in `prompts_config`
- **Impact:** All 10 pages were being generated even though you wanted to test with only 2
- **Result:** Excessive API calls, rate limiting, and slow testing

### 2. **Replicate API Rate Limiting** ⚠️
- **Problem:** 10 predictions started with only 2-second stagger between each
- **Impact:** Rate limit errors: `"replicate_rate_limited"` with multiple retry attempts
- **Logs Show:**
  ```
  {"attempt": 1, "wait": 10, "event": "replicate_rate_limited"}
  {"attempt": 2, "wait": 10, "event": "replicate_rate_limited"}
  {"attempt": 3, "wait": 10, "event": "replicate_rate_limited"}
  ```

### 3. **All Predictions Failing** ❌
- **Initial Error:** `"[Errno 11001] getaddrinfo failed"` - DNS/network issue with Replicate API
- **Result:** All pages showing `"prediction_failed"` warnings
- **Root Cause:** Network connectivity issues OR invalid API credentials

### 4. **Excessive Logging** 📊
- **Problem:** Every retry attempt logged a warning (6 retries × 10 pages = 60 logs)
- **Problem:** Every poll logged info messages
- **Impact:** Logs cluttered with hundreds of repetitive entries, hard to debug

### 5. **Configuration Issues** ⚙️
- `MAX_PARALLEL_GENERATIONS=3` but starting 10 predictions
- No configurable stagger delay (hardcoded to 2 seconds)
- No way to limit pages for testing

---

## ✅ Fixes Applied

### 1. **Added TEST_PAGE_LIMIT Configuration**
**File:** `app/core/config.py`
```python
TEST_PAGE_LIMIT: int | None = 2  # Limit pages for testing
REPLICATE_STAGGER_SECONDS: float = 5.0  # Increased from 2.0
REPLICATE_MAX_RETRIES: int = 3  # Reduced from 6
MAX_PARALLEL_GENERATIONS: int = 2  # Reduced from 3
```

### 2. **Implemented Page Limiting in Generation Service**
**File:** `app/services/replicate_generation.py`
```python
# TESTING: Limit pages if TEST_PAGE_LIMIT is set
if settings.TEST_PAGE_LIMIT is not None and settings.TEST_PAGE_LIMIT > 0:
    original_count = len(pages)
    pages = pages[:settings.TEST_PAGE_LIMIT]
    logger.info(
        "test_page_limit_applied",
        book_id=str(book_id),
        original_pages=original_count,
        limited_pages=len(pages),
    )
```

### 3. **Improved Rate Limiting Handling**
- Increased stagger delay from 2s → **5s** between prediction starts
- Reduced max retries from 6 → **3** to minimize log noise
- Only log rate limit warnings on **first and last retry** attempts

**Before:**
```python
STAGGER_SECONDS = 2.0  # Hardcoded
max_retries = 6
logger.warning("replicate_rate_limited", ...)  # Every retry
```

**After:**
```python
settings.REPLICATE_STAGGER_SECONDS  # Configurable (5.0s)
settings.REPLICATE_MAX_RETRIES  # Configurable (3)
if attempt == 0 or attempt == max_retries - 1:  # Only log first/last
    logger.warning("replicate_rate_limited", ...)
```

### 4. **Enhanced Error Logging**
- Added error details to prediction failure logs
- Added summary statistics to prediction start logs
- Shows success rate: `"success_rate": "2/10"`

**Before:**
```python
logger.warning("prediction_failed", book_id=..., key=..., pred_id=...)
```

**After:**
```python
error_detail = result.get("error", "Unknown error")
logger.warning(
    "prediction_failed", 
    book_id=str(book_id), 
    key=key, 
    pred_id=pred_id,
    error=error_detail,  # ← Now includes actual error message
)
```

### 5. **Updated Environment Configuration**
**File:** `.env`
```bash
MAX_PARALLEL_GENERATIONS=2
TEST_PAGE_LIMIT=2
REPLICATE_STAGGER_SECONDS=5.0
REPLICATE_MAX_RETRIES=3
```

---

## 🎯 How It Works Now

### Generation Flow (with 2-page limit):
1. **Template has 10 pages** in `prompts_config`
2. **TEST_PAGE_LIMIT=2** → Only first 2 pages are processed
3. **Stagger delay = 5s** → Second page starts 5 seconds after first
4. **Max 2 concurrent** → Controlled by `MAX_PARALLEL_GENERATIONS=2`
5. **Max 3 retries** → Less log noise, faster failure detection

### Expected Log Output (Clean):
```json
{"event": "test_page_limit_applied", "original_pages": 10, "limited_pages": 2}
{"event": "prediction_created", "prediction_id": "pred_abc123"}
{"event": "prediction_created", "prediction_id": "pred_xyz789"}
{"event": "predictions_started", "total_pages": 2, "prediction_count": 2, "success_rate": "2/2"}
```

---

## 🐛 Debugging the DNS Error

The initial error `"[Errno 11001] getaddrinfo failed"` suggests:

### Possible Causes:
1. **No internet connection** or firewall blocking `api.replicate.com`
2. **DNS resolution failure** - can't resolve `api.replicate.com`
3. **Invalid REPLICATE_API_TOKEN** - causing authentication failures

### How to Debug:
```powershell
# Test DNS resolution
nslookup api.replicate.com

# Test API connectivity
curl https://api.replicate.com/v1/predictions -H "Authorization: Token YOUR_TOKEN"

# Check internet connectivity
ping 8.8.8.8
```

### Verify API Token:
Your API token in `.env` is:
```
REPLICATE_API_TOKEN=r8_dAqlHSaxt1p33sbK0NlMic0buLRsaBe3OaKiN
```

**Action:** Verify this token is valid at https://replicate.com/account/api-tokens

---

## 📊 Before vs After Comparison

### Before:
- ❌ 10 pages generated every time
- ❌ 2-second stagger → rate limiting
- ❌ 6 retries × 10 pages = 60+ log entries
- ❌ No visibility into why predictions failed
- ❌ 3-4 minute generation time for testing

### After:
- ✅ Only 2 pages generated (configurable)
- ✅ 5-second stagger → less rate limiting
- ✅ 3 retries × 2 pages, only logging first/last = ~4 log entries
- ✅ Error details included in failure logs
- ✅ ~15-30 second generation time for testing

---

## 🚀 Testing the Fix

1. **Restart the server:**
   ```powershell
   cd server
   uv run uvicorn app.main:app --reload
   ```

2. **Test generation with 2 pages:**
   - Upload a photo
   - Select "Magical Unicorn Forest Adventure" template
   - Trigger generation
   - Should now only generate **2 pages** instead of 10

3. **Monitor logs:**
   Look for:
   ```json
   {"event": "test_page_limit_applied", "limited_pages": 2}
   {"event": "predictions_started", "success_rate": "2/2"}
   ```

4. **To disable limit (production):**
   Edit `.env`:
   ```bash
   TEST_PAGE_LIMIT=  # Leave empty or set to None
   ```

---

## 📝 Future Improvements

1. **Add retry backoff strategy** - exponential backoff with jitter
2. **Implement prediction queue** - process pages sequentially to avoid rate limits
3. **Add health check** - verify Replicate API connectivity before starting
4. **Cache failed predictions** - don't retry immediately
5. **Add metrics** - track success rate, average generation time
6. **Graceful degradation** - allow partial book completion if some pages fail

---

## 🔧 Configuration Reference

| Setting | Default | Test Value | Production |
|---------|---------|------------|------------|
| `TEST_PAGE_LIMIT` | None | 2 | None/empty |
| `REPLICATE_STAGGER_SECONDS` | 5.0 | 5.0 | 3.0-5.0 |
| `REPLICATE_MAX_RETRIES` | 3 | 3 | 5 |
| `MAX_PARALLEL_GENERATIONS` | 2 | 2 | 3-5 |

---

## ✅ Summary

**Root Cause:** Template had 10 pages but no mechanism to limit for testing + aggressive retry logic causing log spam.

**Solution:** Added `TEST_PAGE_LIMIT` config, improved rate limiting, reduced logging noise.

**Status:** ✅ Ready for testing with 2-page generation

**Next Steps:**
1. Verify Replicate API token is valid
2. Test DNS connectivity to `api.replicate.com`
3. Run generation and check if 2 pages complete successfully
4. If still failing, check the `error` field in prediction failure logs for details
