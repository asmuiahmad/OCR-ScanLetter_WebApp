"""
Error Test Routes
Routes for testing different error templates
Only available in development mode
"""

from flask import Blueprint, request, current_app
from config.error_handler import ErrorHandler

# Only create blueprint if in debug mode
def create_error_test_blueprint():
    """Create error test blueprint only in development"""
    
    error_test_bp = Blueprint('error_test', __name__, url_prefix='/test-error')
    
    @error_test_bp.route('/micro')
    def test_micro():
        """Test micro error template"""
        return ErrorHandler.handle_error(
            error="This is a test of the micro error template",
            error_code=500,
            template_size='micro',
            show_retry=True
        )
    
    @error_test_bp.route('/minimal')
    def test_minimal():
        """Test minimal error template"""
        return ErrorHandler.handle_error(
            error="This is a test of the minimal error template",
            error_code=500,
            template_size='minimal',
            show_retry=True
        )
    
    @error_test_bp.route('/compact')
    def test_compact():
        """Test compact error template"""
        return ErrorHandler.handle_error(
            error="This is a test of the compact error template",
            error_code=500,
            template_size='compact',
            show_retry=True
        )
    
    @error_test_bp.route('/full')
    def test_full():
        """Test full error template"""
        return ErrorHandler.handle_error(
            error="This is a test of the full error template",
            error_code=500,
            template_size='full',
            show_retry=True
        )
    
    @error_test_bp.route('/404')
    def test_404():
        """Test 404 error"""
        return ErrorHandler.handle_error(
            error="Page not found - this is a test",
            error_code=404,
            template_size='minimal',
            show_retry=False
        )
    
    @error_test_bp.route('/400')
    def test_400():
        """Test 400 error"""
        from flask import abort
        abort(400, 'CSRF token is missing or invalid. Please refresh the page and try again.')
    
    @error_test_bp.route('/403')
    def test_403():
        """Test 403 error"""
        return ErrorHandler.handle_error(
            error="Access denied - this is a test",
            error_code=403,
            template_size='minimal',
            show_retry=False
        )
    
    @error_test_bp.route('/auto')
    def test_auto():
        """Test automatic template selection based on user agent"""
        user_agent = request.headers.get('User-Agent', '')
        
        # Simulate different error conditions
        if 'Mobile' in user_agent:
            template_size = 'minimal'
        elif 'tablet' in user_agent.lower():
            template_size = 'compact'
        else:
            template_size = 'compact'  # Default to compact for better UX
        
        return ErrorHandler.handle_error(
            error=f"Auto-selected template: {template_size} (User-Agent: {user_agent[:50]}...)",
            error_code=500,
            template_size=template_size,
            show_retry=True
        )
    
    @error_test_bp.route('/long-message')
    def test_long_message():
        """Test error with very long message"""
        long_message = """
        This is a very long error message to test how the templates handle extensive text content. 
        It includes multiple sentences and should demonstrate how the different template sizes 
        handle content overflow and text wrapping. The micro template should be very compact, 
        the minimal template should be clean and simple, the compact template should be 
        well-balanced, and the full template should accommodate all this text comfortably.
        
        Additional details: The error occurred during a complex operation involving multiple 
        database transactions, file operations, and network requests. The system attempted 
        to recover automatically but was unable to complete the requested operation due to 
        resource constraints and timeout limitations.
        """
        
        return ErrorHandler.handle_error(
            error=long_message.strip(),
            error_code=500,
            template_size='compact',
            show_retry=True
        )
    
    return error_test_bp

# Function to register blueprint conditionally
def register_error_test_routes(app):
    """Register error test routes only in development mode"""
    if app.debug or app.config.get('TESTING', False):
        error_test_bp = create_error_test_blueprint()
        app.register_blueprint(error_test_bp)
        app.logger.info("Error test routes registered at /test-error/*")