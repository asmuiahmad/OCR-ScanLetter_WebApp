# Error Templates Guide

Sistem error handling yang baru menyediakan 4 template berbeda untuk menangani error dengan ukuran dan kompleksitas yang berbeda.

## Template yang Tersedia

### 1. Micro Template (`error-micro.html`)
- **Ukuran**: Sangat kecil (~320px max width)
- **Penggunaan**: Mobile devices, space terbatas, embedded views
- **Fitur**: Minimal UI, emoji icons, basic actions
- **Cocok untuk**: Quick errors, mobile apps, widgets

### 2. Minimal Template (`error-minimal.html`)
- **Ukuran**: Kecil (~400px max width)
- **Penggunaan**: Mobile-first, simple errors
- **Fitur**: Clean design, essential information only
- **Cocok untuk**: 404 errors, permission errors, mobile web

### 3. Compact Template (`error-compact.html`)
- **Ukuran**: Medium (~480px max width)
- **Penggunaan**: Default untuk most cases
- **Fitur**: Balanced design, help section, responsive
- **Cocok untuk**: General errors, desktop/tablet, production

### 4. Full Template (`error.html`)
- **Ukuran**: Large (~1200px max width)
- **Penggunaan**: Complex errors, development
- **Fitur**: Detailed information, extensive help, animations
- **Cocok untuk**: Development mode, detailed debugging

## Automatic Template Selection

Error handler secara otomatis memilih template berdasarkan:

1. **User Agent Detection**
   - Mobile devices → minimal/compact
   - Desktop → compact/full
   - Tablet → compact

2. **Content Length Preference**
   - `micro` → error-micro.html
   - `minimal` → error-minimal.html
   - `compact` → error-compact.html (default)
   - `full` → error.html

3. **Error Type**
   - 404 → minimal (no retry needed)
   - 403 → minimal (no retry needed)
   - 500 → compact (with retry)
   - Exceptions → micro (space-saving)

## Usage Examples

### Basic Usage
```python
from config.error_handler import ErrorHandler

# Auto-select template
return ErrorHandler.handle_error(
    error="Something went wrong",
    error_code=500
)

# Force specific template
return ErrorHandler.handle_error(
    error="Page not found",
    error_code=404,
    template_size='minimal',
    show_retry=False
)
```

### Convenience Functions
```python
from config.error_handler import handle_404, handle_500, handle_403, handle_micro_error

# Quick error handling
return handle_404("Page not found")
return handle_500(exception)
return handle_403("Access denied")
return handle_micro_error("Quick error", 400)
```

### In Route Handlers
```python
@app.route('/some-route')
def some_route():
    try:
        # Your code here
        pass
    except Exception as e:
        return ErrorHandler.handle_error(
            error=e,
            error_code=500,
            template_size='compact',
            show_retry=True
        )
```

## Template Features Comparison

| Feature | Micro | Minimal | Compact | Full |
|---------|-------|---------|---------|------|
| Size | ~8KB | ~12KB | ~16KB | ~25KB |
| Mobile Optimized | ✅ | ✅ | ✅ | ⚠️ |
| Help Section | Basic | List | Grid | Detailed |
| Animations | None | Simple | Medium | Rich |
| Error Details | Hidden | Basic | Medium | Full |
| Retry Button | ✅ | ✅ | ✅ | ✅ |
| Navigation | ✅ | ✅ | ✅ | ✅ |
| Responsive | ✅ | ✅ | ✅ | ✅ |

## Testing Error Templates

In development mode, you can test different templates:

```
/test-error/micro     - Test micro template
/test-error/minimal   - Test minimal template  
/test-error/compact   - Test compact template
/test-error/full      - Test full template
/test-error/404       - Test 404 error
/test-error/403       - Test 403 error
/test-error/auto      - Test auto-selection
/test-error/long-message - Test with long error message
```

## Customization

### Adding New Templates
1. Create new template file in `templates/`
2. Update `ErrorHandler.get_error_template()` method
3. Add template size option to `handle_error()` calls

### Styling
- Micro: Inline CSS for minimal footprint
- Minimal: Inline CSS with simple animations
- Compact: Inline CSS with medium complexity
- Full: External CSS file for rich features

### Context Variables
All templates receive:
- `error_code`: HTTP status code
- `error_title`: Main error title
- `error_description`: User-friendly description
- `error_message`: Technical details (optional)
- `show_retry`: Whether to show retry button

## Best Practices

1. **Use compact template as default** - Good balance of features and size
2. **Use minimal for mobile** - Better UX on small screens
3. **Use micro for embedded contexts** - Widgets, iframes, etc.
4. **Use full only in development** - Too large for production
5. **Hide technical details in production** - Set `HIDE_ERROR_DETAILS=True`
6. **Provide helpful error messages** - User-friendly language
7. **Include retry option for transient errors** - 500, 502, 503
8. **Don't show retry for permanent errors** - 404, 403, 401

## Configuration

```python
# In your config
HIDE_ERROR_DETAILS = True  # Hide technical error messages in production
ERROR_TEMPLATE_SIZE = 'compact'  # Default template size
```

## Fallback Handling

If template rendering fails, the system provides:
1. Try requested template
2. Fallback to micro template
3. Ultimate fallback to plain HTML response

This ensures users always see some error page, even if templates are broken.