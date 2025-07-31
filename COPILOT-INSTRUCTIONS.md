# Copilot Instructions for PyKiteConnect
This file provides guidelines for GitHub Copilot to follow when generating code for the PyKiteConnect project.

## 🧠 General Behavior
- **Primary Focus**: This is a financial trading API client library with a Flask web application for GTT (Good Till Triggered) order management
- **Core Domain**: Stock trading, market data, order management, and financial instruments
- **Restricted Areas**: Files inside `C:\Himanshu\REPOS\pykiteconnect\gtt_webapp` should not be modified by Copilot unless explicitly requested
- Follow instructions exactly as written in comments or prompts
- Do not assume missing details — ask or leave TODOs if unsure
- Prioritize simplicity, clarity, and readability of code
- Use only the technologies, libraries, and patterns already used in this project unless explicitly told to add something new
- Always specify the complete file path when making changes, since the codebase is extensive

## 🧹 Code Style & Standards
- **Python Style**: Follow PEP 8 standards consistently
- Match the existing code style and formatting (indentation, naming conventions, etc.)
- Use descriptive, meaningful variable and function names that reflect financial/trading context
- Comment non-trivial logic with short, clear explanations, especially for trading logic
- Avoid overly complex one-liners or unnecessary abstractions
- Use type hints where appropriate for better code clarity
- Handle exceptions gracefully, especially for API calls and database operations

## 🛠️ Languages & Technologies

### Core Technologies
- **Language**: Python 3.7+ (v5 dropped Python 2.7 support)
- **Main Library**: KiteConnect API client for Zerodha trading platform
- **Web Framework**: Flask 2.3.3 with Blueprint architecture
- **Database**: Oracle Database (using oracledb 1.4.1)
- **Frontend**: Bootstrap-Flask 2.2.0, jQuery, CSS
- **Testing**: Pytest with mocks and responses for API testing

### Key Dependencies
- **API Client**: kiteconnect==4.2.0 (financial trading APIs)
- **Web Assets**: Flask-Assets for bundling CSS/JS
- **Environment**: python-dotenv for configuration management
- **Data Processing**: pandas for market data analysis
- **HTTP**: requests for external API calls

## 🏗️ Project Structure Guidelines

### Main Library (`kiteconnect/`)
- Core API client functionality
- Keep modules focused: `connect.py` (main client), `ticker.py` (WebSocket), `exceptions.py`
- Maintain backward compatibility for public APIs

### Web Application (`gtt_webapp/`)
- **Architecture**: Flask Blueprints pattern
- **Routes**: Organize by feature in `blueprints/` directory
- **Models**: Database models and business logic in `models/`
- **Static Assets**: CSS, JS, and generated assets in `static/`
- **Templates**: Jinja2 templates organized by blueprint in `templates/`

### Testing (`tests/`)
- **Unit Tests**: Mock external dependencies, focus on logic
- **Integration Tests**: Test actual API interactions (when safe)
- **Structure**: Mirror source code structure in test directory
- **Fixtures**: Use conftest.py for shared test setup

## 📊 Financial Trading Context
- **GTT Orders**: Good Till Triggered orders for conditional trading
- **Instruments**: Stocks, derivatives, commodities traded on Indian exchanges
- **Market Data**: Real-time quotes, OHLC data, historical prices
- **Portfolio**: Holdings, positions, margins, and P&L calculations
- **Order Types**: Market, Limit, Stop-Loss, Cover Orders, Bracket Orders

## 🧪 Testing Guidelines
- **Always write tests** for new functions, especially financial calculations
- **Mock external APIs** to avoid real trading operations during tests
- **Test edge cases** for financial data (null prices, market holidays, etc.)
- **Use pytest fixtures** for common test data and setup
- **Validate data integrity** for financial calculations and order management
- **Test error handling** for API failures and invalid market data

## 🔒 Security & Safety
- **Never hardcode** API keys, access tokens, or trading credentials
- **Use environment variables** (.env files) for all sensitive configuration
- **Validate all inputs** especially for financial amounts and trading parameters
- **Handle API rate limits** and implement proper retry mechanisms
- **Log trading operations** appropriately without exposing sensitive data
- **Implement proper error handling** for trading operations to prevent accidental trades

## 📁 File Organization Patterns

### Core Library
```
kiteconnect/
├── __init__.py          # Public API exports
├── connect.py           # Main KiteConnect client
├── ticker.py            # WebSocket streaming
├── exceptions.py        # Custom exceptions
└── __version__.py       # Version information
```

### Web Application
```
gtt_webapp/
├── app.py              # Flask application factory
├── blueprints/         # Feature-based routes
├── models/             # Database models
├── static/             # CSS, JS, assets
├── templates/          # Jinja2 templates
└── db_config.py        # Database configuration
```

## 🎯 Common Patterns

### API Client Patterns
```python
# Error handling for trading APIs
try:
    response = kite.place_order(variety="regular", ...)
    return response
except KiteException as e:
    logger.error(f"Trading API error: {e}")
    raise
```

### Flask Route Patterns
```python
# Blueprint route with proper error handling
@blueprint.route('/endpoint')
def handler():
    try:
        # Business logic
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        logger.error(f"Route error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Database Patterns
```python
# Oracle database connection pattern
def get_database_connection():
    return oracledb.connect(**configuration)
```

## ⚠️ Important Rules
- **Financial Data Precision**: Always handle monetary values with proper decimal precision
- **Market Hours**: Consider market timings and holidays in business logic
- **Order Validation**: Validate all trading parameters before API calls
- **Idempotency**: Ensure operations can be safely retried
- **Audit Trail**: Log all trading operations for compliance
- **Rate Limits**: Respect API rate limits to avoid account suspension

## 📈 Development Workflow
- **Feature Branches**: Use descriptive branch names (e.g., `feature/gtt-enhancements`)
- **Testing**: Run both unit and integration tests before commits
- **Documentation**: Update docstrings for public API changes
- **Version Management**: Follow semantic versioning for releases
- **Backwards Compatibility**: Maintain compatibility for major version changes

## 🔄 API Integration Patterns
- **Lazy Loading**: Initialize KiteConnect instances only when needed
- **Connection Pooling**: Reuse database connections efficiently
- **Caching**: Cache market data appropriately (respect real-time requirements)
- **Error Recovery**: Implement retry logic for transient failures
- **Data Validation**: Validate all incoming market data and user inputs

## 🎨 Frontend Guidelines (Web App)
- **Responsive Design**: Use Bootstrap classes for mobile-friendly UI
- **Real-time Updates**: Implement WebSocket connections for live data
- **Form Validation**: Client and server-side validation for trading forms
- **User Feedback**: Clear success/error messages for trading operations
- **Asset Management**: Use Flask-Assets for optimized CSS/JS delivery

## ✅ Example Code Templates

### New API Endpoint
```python
@api_blueprint.route('/api/orders', methods=['POST'])
def create_order():
    """Create a new trading order"""
    try:
        data = request.get_json()
        # Validate required fields
        required_fields = ['symbol', 'quantity', 'order_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing {field}"}), 400
        
        # Business logic
        kite = get_kite_instance()
        result = kite.place_order(**data)
        
        return jsonify({"status": "success", "order_id": result["order_id"]})
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        return jsonify({"error": str(e)}), 500
```

### New Test Case
```python
def test_place_order_success(mock_kite):
    """Test successful order placement"""
    # Arrange
    mock_kite.place_order.return_value = {"order_id": "123456"}
    
    # Act
    result = place_order_service(symbol="SBIN", quantity=10)
    
    # Assert
    assert result["order_id"] == "123456"
    mock_kite.place_order.assert_called_once()
```

---

This ensures GitHub Copilot generates code that follows the established patterns, handles financial data appropriately, and maintains the security and reliability standards required for trading applications.
