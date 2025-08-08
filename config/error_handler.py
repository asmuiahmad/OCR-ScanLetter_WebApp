"""
Error Handler Utility
Handles different types of errors with appropriate templates
"""

from flask import render_template, request, current_app
import traceback
import sys

class ErrorHandler:
    """Handles application errors with appropriate templates"""
    
    @staticmethod
    def get_error_template(error_code=500, user_agent=None, content_length=None):
        """
        Determine which error template to use based on context
        
        Args:
            error_code: HTTP error code
            user_agent: User agent string
            content_length: Preferred content length (micro, minimal, compact, full)
        
        Returns:
            Template name to use
        """
        
        # Force micro template for very small screens or specific request
        if content_length == 'micro':
            return 'error-micro.html'
        
        # Check if mobile device
        if user_agent and ErrorHandler._is_mobile(user_agent):
            if content_length == 'minimal':
                return 'error-minimal.html'
            return 'error-compact.html'
        
        # Default template selection based on content_length preference
        template_map = {
            'micro': 'error-micro.html',
            'minimal': 'error-minimal.html', 
            'compact': 'error-compact.html',
            'full': 'error.html'
        }
        
        return template_map.get(content_length, 'error-compact.html')
    
    @staticmethod
    def _is_mobile(user_agent):
        """Check if user agent indicates mobile device"""
        mobile_indicators = [
            'Mobile', 'Android', 'iPhone', 'iPad', 'iPod',
            'BlackBerry', 'Windows Phone', 'Opera Mini'
        ]
        return any(indicator in user_agent for indicator in mobile_indicators)
    
    @staticmethod
    def handle_error(error, error_code=500, template_size='compact', show_retry=True):
        """
        Handle error with appropriate template and context
        
        Args:
            error: Exception object or error message
            error_code: HTTP status code
            template_size: Template size preference (micro, minimal, compact, full)
            show_retry: Whether to show retry button
        
        Returns:
            Rendered template response
        """
        
        # Determine error details
        if isinstance(error, Exception):
            error_message = str(error)
            error_title = f"Error {error_code}"
            
            # Get more specific error info for development
            if current_app.debug:
                error_message = f"{error.__class__.__name__}: {str(error)}"
        else:
            error_message = str(error)
            error_title = f"Error {error_code}"
        
        # Set error descriptions based on code
        error_descriptions = {
            400: "Permintaan tidak valid",
            401: "Akses tidak diizinkan", 
            403: "Akses ditolak",
            404: "Halaman tidak ditemukan",
            405: "Metode tidak diizinkan",
            500: "Terjadi kesalahan server internal",
            502: "Gateway bermasalah",
            503: "Layanan tidak tersedia"
        }
        
        error_description = error_descriptions.get(error_code, "Terjadi kesalahan sistem")
        
        # Get appropriate template
        user_agent = request.headers.get('User-Agent', '') if request else ''
        template_name = ErrorHandler.get_error_template(
            error_code=error_code,
            user_agent=user_agent, 
            content_length=template_size
        )
        
        # Prepare context
        context = {
            'error_code': error_code,
            'error_title': error_title,
            'error_description': error_description,
            'error_message': error_message if not current_app.config.get('HIDE_ERROR_DETAILS', False) else None,
            'show_retry': show_retry
        }
        
        try:
            return render_template(template_name, **context), error_code
        except Exception as template_error:
            # Fallback to micro template if others fail
            current_app.logger.error(f"Template error: {template_error}")
            try:
                return render_template('error-micro.html', **context), error_code
            except:
                # Ultimate fallback - plain HTML
                return ErrorHandler._fallback_html_response(context), error_code
    
    @staticmethod
    def _fallback_html_response(context):
        """Generate minimal HTML response when templates fail"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error {context.get('error_code', 500)}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 2rem; 
                    background: #f5f5f5; 
                }}
                .error {{ 
                    background: white; 
                    padding: 2rem; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                    max-width: 400px; 
                    margin: 0 auto; 
                }}
                .btn {{ 
                    background: #007bff; 
                    color: white; 
                    padding: 0.5rem 1rem; 
                    text-decoration: none; 
                    border-radius: 4px; 
                    margin: 0.5rem; 
                    display: inline-block; 
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>⚠️ {context.get('error_title', 'Error')}</h1>
                <p>{context.get('error_description', 'Terjadi kesalahan')}</p>
                {f'<p><small>{context["error_message"]}</small></p>' if context.get('error_message') else ''}
                <div>
                    {'<a href="javascript:location.reload()" class="btn">🔄 Coba Lagi</a>' if context.get('show_retry') else ''}
                    <a href="/" class="btn">🏠 Dashboard</a>
                    <a href="javascript:history.back()" class="btn">← Kembali</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html

# Convenience functions for common error types
def handle_404(error):
    """Handle 404 errors"""
    return ErrorHandler.handle_error(
        error="Halaman yang Anda cari tidak ditemukan",
        error_code=404,
        template_size='minimal',
        show_retry=False
    )

def handle_500(error):
    """Handle 500 errors"""
    return ErrorHandler.handle_error(
        error=error,
        error_code=500,
        template_size='compact',
        show_retry=True
    )

def handle_403(error):
    """Handle 403 errors"""
    return ErrorHandler.handle_error(
        error="Anda tidak memiliki izin untuk mengakses halaman ini",
        error_code=403,
        template_size='minimal',
        show_retry=False
    )

def handle_micro_error(error, error_code=500):
    """Handle errors with micro template (for very limited space)"""
    return ErrorHandler.handle_error(
        error=error,
        error_code=error_code,
        template_size='micro',
        show_retry=True
    )