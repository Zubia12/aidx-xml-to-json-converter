#!/usr/bin/env python3
"""
AIDX XML to JSON Converter - Flask Web Application

This Flask application provides a web interface for converting AIDX XML files to JSON format.
It integrates with the aidx_parser module to provide:

- File upload handling via drag-and-drop or file selection
- XML validation and parsing using the AIDX parser
- JSON conversion and formatting
- Error handling and user feedback
- RESTful API endpoints for frontend communication

Features:
- Multiple file upload support
- Real-time conversion progress
- Detailed error reporting
- File size and format validation
- CORS support for development
- Production-ready configuration

Author: AI Assistant
Version: 1.0
Python: 3.9+
"""

# Import required modules
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import traceback
from datetime import datetime

# Flask and related imports
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our AIDX parser
from aidx_parser import AIDXParser, parse_aidx, AIDXParseError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)

# Configuration
class Config:
    """Application configuration class"""
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'xml'}
    
    # AIDX Parser settings
    PARSER_SKIP_TAGS = ['TPA_Extension']  # Skip complex vendor extensions by default
    PARSER_INCLUDE_ATTRIBUTES = True
    PARSER_PRESERVE_NAMESPACES = False
    
    # Environment settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '127.0.0.1' if DEBUG else '0.0.0.0')
    
    # CORS settings - more permissive for production
    CORS_ORIGINS = [
        'http://localhost:5000', 
        'http://127.0.0.1:5000',
        'https://*.herokuapp.com',
        'https://*.railway.app',
        'https://*.render.com'
    ]

# Apply configuration
app.config.from_object(Config)

# Enable CORS for development
CORS(app, origins=Config.CORS_ORIGINS)

# Create upload directory if it doesn't exist
upload_dir = Path(app.config['UPLOAD_FOLDER'])
upload_dir.mkdir(exist_ok=True)

# Initialize AIDX parser with default configuration
default_parser = AIDXParser(
    skip_tags=Config.PARSER_SKIP_TAGS,
    include_attributes=Config.PARSER_INCLUDE_ATTRIBUTES,
    preserve_namespaces=Config.PARSER_PRESERVE_NAMESPACES
)

def allowed_file(filename: str) -> bool:
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def validate_xml_file(file_content: str, filename: str) -> Tuple[bool, str]:
    """
    Validate XML file content and structure.
    
    Args:
        file_content: Content of the XML file as string
        filename: Name of the file for error reporting
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # Check if file is empty
        if not file_content.strip():
            return False, "File is empty"
        
        # Check if content looks like XML
        if not file_content.strip().startswith('<?xml') and not file_content.strip().startswith('<'):
            return False, "File does not appear to be valid XML"
        
        # Try to parse with our AIDX parser (this will validate XML structure)
        default_parser.parse_xml_string(file_content)
        
        return True, ""
        
    except AIDXParseError as e:
        return False, f"AIDX parsing error: {str(e)}"
    except Exception as e:
        return False, f"XML validation error: {str(e)}"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Formatted file size (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

@app.route('/')
def index():
    """
    Serve the main application page.
    
    Returns:
        Rendered HTML template for the main application
    """
    logger.info("Serving main application page")
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_xml_to_json():
    """
    Convert uploaded XML file to JSON format.
    
    This endpoint handles:
    - File upload validation
    - XML parsing and conversion
    - Error handling and reporting
    - JSON response formatting
    
    Returns:
        JSON response with conversion results or error information
    """
    start_time = datetime.now()
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            logger.warning("No file uploaded in request")
            return jsonify({
                'error': 'No file uploaded',
                'details': 'Please select an XML file to convert'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({
                'error': 'No file selected',
                'details': 'Please select a valid XML file'
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({
                'error': 'Invalid file type',
                'details': 'Only XML files are supported'
            }), 400
        
        # Read file content
        try:
            file_content = file.read().decode('utf-8')
            file_size = len(file_content.encode('utf-8'))
            
            logger.info(f"Processing file: {file.filename} ({format_file_size(file_size)})")
            
        except UnicodeDecodeError:
            logger.error(f"Failed to decode file: {file.filename}")
            return jsonify({
                'error': 'File encoding error',
                'details': 'File must be UTF-8 encoded XML'
            }), 400
        
        # Validate XML content
        is_valid, validation_error = validate_xml_file(file_content, file.filename)
        if not is_valid:
            logger.error(f"XML validation failed for {file.filename}: {validation_error}")
            return jsonify({
                'error': 'XML validation failed',
                'details': validation_error
            }), 400
        
        # Parse XML to JSON using AIDX parser
        try:
            # Parse the XML content
            parsed_data = default_parser.parse_xml_string(file_content)
            
            # Convert to JSON string for size calculation
            json_string = json.dumps(parsed_data, indent=2)
            json_size = len(json_string.encode('utf-8'))
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Successfully converted {file.filename} in {processing_time:.2f}ms")
            
            # Return successful conversion result
            return jsonify({
                'success': True,
                'filename': file.filename,
                'original_size': file_size,
                'json_size': json_size,
                'processing_time_ms': round(processing_time, 2),
                'json_data': parsed_data,
                'metadata': {
                    'parser_version': '1.0',
                    'conversion_timestamp': datetime.now().isoformat(),
                    'file_info': {
                        'name': file.filename,
                        'size_bytes': file_size,
                        'size_formatted': format_file_size(file_size)
                    },
                    'json_info': {
                        'size_bytes': json_size,
                        'size_formatted': format_file_size(json_size),
                        'line_count': len(json_string.split('\n'))
                    }
                }
            })
            
        except AIDXParseError as e:
            logger.error(f"AIDX parsing error for {file.filename}: {str(e)}")
            return jsonify({
                'error': 'AIDX parsing failed',
                'details': str(e),
                'filename': file.filename
            }), 422
            
        except Exception as e:
            logger.error(f"Unexpected parsing error for {file.filename}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Conversion failed',
                'details': f'An unexpected error occurred: {str(e)}',
                'filename': file.filename
            }), 500
    
    except RequestEntityTooLarge:
        logger.error("File too large")
        return jsonify({
            'error': 'File too large',
            'details': f'Maximum file size is {format_file_size(app.config["MAX_CONTENT_LENGTH"])}'
        }), 413
    
    except Exception as e:
        logger.error(f"Unexpected server error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Server error',
            'details': 'An unexpected server error occurred'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON response with application health status
    """
    try:
        # Test parser functionality
        test_xml = '<?xml version="1.0"?><test>Hello</test>'
        default_parser.parse_xml_string(test_xml)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'parser_status': 'operational'
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.route('/api/info', methods=['GET'])
def api_info():
    """
    Get API information and capabilities.
    
    Returns:
        JSON response with API information
    """
    return jsonify({
        'name': 'AIDX XML to JSON Converter API',
        'version': '1.0',
        'description': 'Convert AIDX XML files to JSON format',
        'endpoints': {
            '/': 'Main application page',
            '/convert': 'Convert XML file to JSON (POST)',
            '/health': 'Health check endpoint',
            '/api/info': 'API information'
        },
        'supported_formats': ['xml'],
        'max_file_size': format_file_size(app.config['MAX_CONTENT_LENGTH']),
        'parser_config': {
            'skip_tags': Config.PARSER_SKIP_TAGS,
            'include_attributes': Config.PARSER_INCLUDE_ATTRIBUTES,
            'preserve_namespaces': Config.PARSER_PRESERVE_NAMESPACES
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'details': 'The requested resource was not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'error': 'Method not allowed',
        'details': 'The requested method is not allowed for this endpoint'
    }), 405

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return jsonify({
        'error': 'File too large',
        'details': f'Maximum file size is {format_file_size(app.config["MAX_CONTENT_LENGTH"])}'
    }), 413

@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'details': 'An unexpected server error occurred'
    }), 500

if __name__ == '__main__':
    """
    Run the Flask application.
    
    This section handles application startup and configuration for both
    development and production environments.
    """
    
    # Log startup information
    logger.info("Starting AIDX XML to JSON Converter Web Application")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info(f"Max file size: {format_file_size(app.config['MAX_CONTENT_LENGTH'])}")
    logger.info(f"Upload directory: {upload_dir.absolute()}")
    
    # Server configuration based on environment
    if app.config['DEBUG']:
        logger.info("Running in development mode")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=True,
            threaded=True
        )
    else:
        # Production configuration
        logger.info("Running in production mode")
        logger.info(f"Server will bind to {Config.HOST}:{Config.PORT}")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=False,
            threaded=True
        )