# Session Timeout and Redirect System

## Overview

This system automatically handles session timeouts and redirects users back to their last visited page after re-login. When a user's session expires and they need to log in again, they will be seamlessly returned to the page they were trying to access.

## How It Works

### 1. Page Tracking
- Every time a user visits a page (except login/register/logout), the URL is stored in `sessionStorage`
- This happens automatically on page load, form submissions, and navigation events

### 2. Session Timeout Detection
- When a session expires (after 30 minutes of inactivity), any request to a protected route redirects to login
- The system detects this in several ways:
  - Regular page requests include the `next` parameter in the login URL
  - AJAX requests that return 401 or redirect to login are intercepted
  - Form submissions that encounter timeouts are handled

### 3. Login Process
- Login page shows a timeout message when accessed via redirect
- The intended destination URL is preserved in the `next` parameter
- After successful login, user is redirected back to their original page

### 4. Clean Redirect
- JavaScript handles the final redirect to remove tracking parameters
- Browser history is cleaned up to provide a smooth user experience

## Files Modified

### Backend (Python/Flask)
- `config/auth_routes.py`: Enhanced login route to handle redirects properly
- `app.py`: Session timeout configuration (30 minutes)

### Frontend (JavaScript)
- `static/assets/js/session-manager.js`: Main session management logic
- `static/assets/js/auth/auth.js`: Authentication-specific handling

### Templates
- `templates/auth/login.html`: Added timeout message display
- `templates/layouts/base.html`: Included session manager script
- `templates/layouts/base-login.html`: Included session manager script

## Key Features

### Automatic URL Storage
```javascript
// Stores current page URL automatically
storeCurrentPageForRedirect();
```

### Session Timeout Detection
```javascript
// Detects AJAX/fetch requests that encounter session timeout
setupAjaxSessionHandler();
setupFetchSessionHandler();
```

### Form Submission Handling
```javascript
// Handles form submissions that might encounter timeout
setupFormSessionHandler();
```

### Clean Redirect After Login
```javascript
// Redirects user back to intended page after successful login
handlePostLoginRedirect();
```

## User Experience

1. **Normal Usage**: User navigates normally, no interruption
2. **Session Expires**: User sees timeout message on login page
3. **Re-login**: User logs in again with clear indication of what happened
4. **Seamless Return**: User is automatically returned to their intended page

## Configuration

### Session Timeout
```python
# In app.py
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
```

### Security
- All redirect URLs are validated using `is_safe_url()` function
- Only same-origin URLs are allowed for redirects
- CSRF protection is maintained throughout the process

## Testing

Run the test script to see how the system works:
```bash
python test_session_redirect.py
```

## Browser Compatibility

- Works with all modern browsers that support `sessionStorage`
- Handles both regular navigation and AJAX requests
- Compatible with browser back/forward navigation

## Troubleshooting

### Common Issues

1. **Redirect not working**: Check browser console for JavaScript errors
2. **Timeout message not showing**: Verify the `next` parameter is present in login URL
3. **Multiple redirects**: Ensure `from_login` parameter is being cleaned up properly

### Debug Information

The system logs debug information to the browser console:
- Page storage events
- Redirect decisions
- Session timeout detections

Enable browser developer tools to see these logs during development.