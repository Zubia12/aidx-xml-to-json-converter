#!/usr/bin/env python3
"""
IATA AIDX XML Parser Module

This module provides functionality to parse IATA Aviation Information Data Exchange (AIDX) 
XML files and convert them to clean JSON/Python dictionary structures while preserving 
hierarchy, attributes, text content, and handling namespaces.

The AIDX standard is used for exchanging flight information between airlines and airports,
including arrival/departure times, gate assignments, operational statuses, and more.

Author: AI Assistant
Version: 1.0
Python: 3.9+
"""

# Import required standard library modules
import xml.etree.ElementTree as ET  # For XML parsing
import json                         # For JSON serialization
import re                          # For regular expressions (namespace cleaning)
from typing import Dict, Any, List, Optional, Union  # For type hints
from pathlib import Path           # For file path handling
import logging                     # For logging functionality

# Configure logging to show INFO level messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIDXParseError(Exception):
    """
    Custom exception class for AIDX parsing errors.
    
    This exception is raised when:
    - XML files cannot be read or parsed
    - Invalid XML structure is encountered
    - File access errors occur
    """
    pass


class AIDXParser:
    """
    IATA AIDX XML Parser class that converts XML to structured JSON/dict format.
    
    This parser handles complex AIDX XML structures including:
    - Complex nested XML hierarchies (FlightLeg, LegData, AirportResources, etc.)
    - XML namespaces (removes prefixes for cleaner output)
    - Attributes and text content preservation (using @attribute and #text notation)
    - Repeating elements (converted to lists when multiple instances exist)
    - Optional elements and missing fields (gracefully handled)
    - Customizable tag filtering (skip unwanted tags or include only specific ones)
    - TPA_Extension elements (Amadeus-specific extensions)
    
    The parser maintains data integrity while producing clean, readable JSON output
    suitable for further processing or API consumption.
    """
    
    def __init__(self, 
                 skip_tags: Optional[List[str]] = None,
                 include_only_tags: Optional[List[str]] = None,
                 preserve_namespaces: bool = False,
                 include_attributes: bool = True):
        """
        Initialize the AIDX parser with configuration options.
        
        Args:
            skip_tags: List of tag names to skip during parsing (e.g., ['TPA_Extension'])
                      Useful for excluding complex vendor-specific extensions
            include_only_tags: List of tag names to include (all others skipped)
                              Useful for extracting only specific data sections
            preserve_namespaces: Whether to keep namespace prefixes in tag names
                               False (default) = cleaner output, True = full XML fidelity
            include_attributes: Whether to include XML attributes in output
                              True (default) = full data preservation
        
        Example:
            # Skip TPA extensions for cleaner output
            parser = AIDXParser(skip_tags=['TPA_Extension'])
            
            # Only extract flight leg information
            parser = AIDXParser(include_only_tags=['FlightLeg'])
        """
        # Store configuration options for use during parsing
        self.skip_tags = skip_tags or []           # Tags to exclude from parsing
        self.include_only_tags = include_only_tags # Tags to include (exclusive filter)
        self.preserve_namespaces = preserve_namespaces  # Namespace handling preference
        self.include_attributes = include_attributes    # Attribute inclusion preference
        
        # Log the parser configuration for debugging
        logger.info(f"AIDX Parser initialized with config: "
                   f"skip_tags={self.skip_tags}, "
                   f"include_only_tags={self.include_only_tags}, "
                   f"preserve_namespaces={self.preserve_namespaces}, "
                   f"include_attributes={self.include_attributes}")

    def _clean_tag_name(self, tag: str) -> str:
        """
        Clean XML tag names by removing namespace prefixes for readability.
        
        AIDX XML files often contain namespace prefixes like:
        - {http://www.iata.org/IATA/2007/00}FlightLeg -> FlightLeg
        - {http://xml.amadeus.com/2010/06/Types_v1}FunctionalID -> FunctionalID
        
        Args:
            tag: Raw XML tag name with potential namespace prefix
            
        Returns:
            Cleaned tag name without namespace prefix
            
        Example:
            Input:  "{http://www.iata.org/IATA/2007/00}IATA_AIDX_FlightLegNotifRQ"
            Output: "IATA_AIDX_FlightLegNotifRQ"
        """
        if self.preserve_namespaces:
            # Return tag as-is if namespace preservation is requested
            return tag
        
        # Use regex to remove namespace URI in curly braces: {namespace}tagname -> tagname
        # Pattern explanation: {.*?} matches {anything} non-greedily
        return re.sub(r'\{.*?\}', '', tag)

    def _should_process_tag(self, tag: str) -> bool:
        """
        Determine whether a specific XML tag should be processed based on filter settings.
        
        This method implements the tag filtering logic:
        1. If include_only_tags is set, only process tags in that list
        2. If skip_tags is set, skip tags in that list
        3. Otherwise, process all tags
        
        Args:
            tag: Cleaned tag name to check
            
        Returns:
            True if tag should be processed, False if it should be skipped
            
        Example:
            # With skip_tags=['TPA_Extension']
            _should_process_tag('FlightLeg') -> True
            _should_process_tag('TPA_Extension') -> False
            
            # With include_only_tags=['FlightLeg']
            _should_process_tag('FlightLeg') -> True
            _should_process_tag('Originator') -> False
        """
        # Clean the tag name for consistent comparison
        clean_tag = self._clean_tag_name(tag)
        
        # If include_only_tags is specified, only process tags in that list
        if self.include_only_tags:
            return clean_tag in self.include_only_tags
        
        # If skip_tags is specified, skip tags in that list
        if self.skip_tags:
            return clean_tag not in self.skip_tags
        
        # Default: process all tags
        return True

    def _parse_element(self, element: ET.Element) -> Union[Dict[str, Any], str, List[Any]]:
        """
        Recursively parse an XML element and its children into a Python data structure.
        
        This is the core parsing method that handles:
        - Element attributes (stored with @ prefix)
        - Text content (stored as #text key)
        - Child elements (recursively parsed)
        - Repeating elements (converted to lists)
        - Mixed content (text + child elements)
        
        Args:
            element: XML element to parse
            
        Returns:
            Parsed data structure:
            - Dict: For elements with attributes or children
            - str: For simple text-only elements
            - List: For repeating elements with same tag name
            
        Example XML:
            <FlightLeg>
                <LegIdentifier>
                    <Airline CodeContext="IATA">JQ</Airline>
                    <FlightNumber>255</FlightNumber>
                </LegIdentifier>
            </FlightLeg>
            
        Example Output:
            {
                "FlightLeg": {
                    "LegIdentifier": {
                        "Airline": {
                            "@CodeContext": "IATA",
                            "#text": "JQ"
                        },
                        "FlightNumber": "255"
                    }
                }
            }
        """
        # Initialize result dictionary to store parsed data
        result = {}
        
        # Step 1: Process XML attributes if attribute inclusion is enabled
        if self.include_attributes and element.attrib:
            # Add attributes with @ prefix to distinguish from child elements
            for attr_name, attr_value in element.attrib.items():
                # Clean attribute names to remove namespace prefixes
                clean_attr_name = self._clean_tag_name(attr_name)
                result[f"@{clean_attr_name}"] = attr_value
        
        # Step 2: Process text content
        # Get direct text content (not including text from child elements)
        text_content = element.text.strip() if element.text else ""
        
        # Step 3: Process child elements
        # Group children by tag name to handle repeating elements
        children_by_tag = {}
        
        for child in element:
            # Clean the child tag name
            clean_child_tag = self._clean_tag_name(child.tag)
            
            # Skip this child if it doesn't pass the filter
            if not self._should_process_tag(child.tag):
                continue
            
            # Recursively parse the child element
            child_data = self._parse_element(child)
            
            # Group children by tag name to detect repeating elements
            if clean_child_tag not in children_by_tag:
                children_by_tag[clean_child_tag] = []
            children_by_tag[clean_child_tag].append(child_data)
        
        # Step 4: Add child elements to result
        for tag_name, child_list in children_by_tag.items():
            if len(child_list) == 1:
                # Single occurrence: add directly
                result[tag_name] = child_list[0]
            else:
                # Multiple occurrences: create list
                result[tag_name] = child_list
        
        # Step 5: Handle text content
        if text_content:
            if result:
                # Mixed content: element has both text and children/attributes
                # Store text content with special #text key
                result["#text"] = text_content
            else:
                # Text-only element: return just the text
                return text_content
        
        # Step 6: Return appropriate data structure
        if not result:
            # Empty element: return empty string
            return ""
        elif len(result) == 1 and "#text" in result:
            # Element with only text content: return the text
            return result["#text"]
        else:
            # Element with attributes, children, or mixed content: return dictionary
            return result

    def parse_xml_string(self, xml_string: str) -> Dict[str, Any]:
        """
        Parse an AIDX XML string into a Python dictionary.
        
        This method:
        1. Validates the XML string is not empty
        2. Parses the XML using ElementTree
        3. Processes the root element and all children
        4. Returns a dictionary with the root element as the top-level key
        
        Args:
            xml_string: Valid XML string containing AIDX data
            
        Returns:
            Dictionary with parsed XML data
            
        Raises:
            AIDXParseError: If XML parsing fails or string is empty
            
        Example:
            xml_data = '''<?xml version="1.0"?>
            <IATA_AIDX_FlightLegNotifRQ>
                <FlightLeg>...</FlightLeg>
            </IATA_AIDX_FlightLegNotifRQ>'''
            
            result = parser.parse_xml_string(xml_data)
            # Returns: {"IATA_AIDX_FlightLegNotifRQ": {...}}
        """
        # Validate input
        if not xml_string or not xml_string.strip():
            raise AIDXParseError("XML string cannot be empty")
        
        try:
            # Parse XML string using ElementTree
            # fromstring() creates an Element object from the XML string
            root = ET.fromstring(xml_string)
            
            # Log successful parsing with root element info
            clean_root_tag = self._clean_tag_name(root.tag)
            logger.info(f"Successfully parsed XML with root element: {root.tag}")
            
            # Parse the root element and all its children
            parsed_data = self._parse_element(root)
            
            # Return data wrapped in dictionary with root tag as key
            # This maintains the XML structure where there's always a root element
            return {clean_root_tag: parsed_data}
            
        except ET.ParseError as e:
            # Handle XML parsing errors (malformed XML, syntax errors, etc.)
            error_msg = f"Failed to parse XML: {str(e)}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg) from e
        except Exception as e:
            # Handle any other unexpected errors
            error_msg = f"Unexpected error during XML parsing: {str(e)}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg) from e

    def parse_xml_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse an AIDX XML file into a Python dictionary.
        
        This method:
        1. Validates the file exists and is readable
        2. Reads the file content with UTF-8 encoding
        3. Delegates to parse_xml_string() for actual parsing
        4. Provides detailed error handling for file operations
        
        Args:
            file_path: Path to XML file (string or Path object)
            
        Returns:
            Dictionary with parsed XML data
            
        Raises:
            AIDXParseError: If file cannot be read or parsed
            
        Example:
            result = parser.parse_xml_file("flight_data.xml")
            # Returns: {"IATA_AIDX_FlightLegNotifRQ": {...}}
        """
        # Convert string path to Path object for consistent handling
        file_path = Path(file_path)
        
        try:
            # Validate file exists
            if not file_path.exists():
                raise AIDXParseError(f"File not found: {file_path}")
            
            # Validate it's actually a file (not a directory)
            if not file_path.is_file():
                raise AIDXParseError(f"Path is not a file: {file_path}")
            
            # Read file content with UTF-8 encoding
            # UTF-8 is standard for XML files and handles international characters
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            
            # Log successful file read
            logger.info(f"Successfully read XML file: {file_path}")
            
            # Delegate to string parsing method
            return self.parse_xml_string(xml_content)
            
        except AIDXParseError:
            # Re-raise our custom errors without modification
            raise
        except FileNotFoundError:
            # Handle file not found specifically
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg)
        except PermissionError:
            # Handle permission denied errors
            error_msg = f"Permission denied reading file: {file_path}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg)
        except UnicodeDecodeError as e:
            # Handle encoding errors (non-UTF-8 files)
            error_msg = f"File encoding error: {str(e)}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg) from e
        except Exception as e:
            # Handle any other unexpected file operation errors
            error_msg = f"Unexpected error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg) from e

    def to_json(self, data: Dict[str, Any], indent: int = 2) -> str:
        """
        Convert parsed AIDX data to formatted JSON string.
        
        This method:
        1. Serializes Python dictionary to JSON
        2. Uses proper indentation for readability
        3. Ensures UTF-8 encoding for international characters
        4. Handles JSON serialization errors gracefully
        
        Args:
            data: Parsed AIDX data dictionary
            indent: Number of spaces for JSON indentation (default: 2)
            
        Returns:
            Formatted JSON string
            
        Raises:
            AIDXParseError: If JSON serialization fails
            
        Example:
            json_output = parser.to_json(parsed_data, indent=4)
            print(json_output)  # Pretty-printed JSON
        """
        try:
            # Convert dictionary to JSON string with formatting
            # ensure_ascii=False allows Unicode characters (important for international data)
            # indent creates readable formatting
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Handle JSON serialization errors (non-serializable objects, etc.)
            error_msg = f"Failed to convert data to JSON: {str(e)}"
            logger.error(error_msg)
            raise AIDXParseError(error_msg) from e


def parse_aidx(input_source: Union[str, Path], 
               output_format: str = 'dict',
               **parser_kwargs) -> Union[Dict[str, Any], str]:
    """
    Convenience function to parse AIDX XML with minimal setup.
    
    This function provides a simple interface for common parsing tasks without
    requiring explicit parser instantiation. It automatically handles:
    - Parser creation with custom options
    - File vs string input detection
    - Output format conversion
    
    Args:
        input_source: XML file path or XML string content
        output_format: 'dict' for Python dictionary, 'json' for JSON string
        **parser_kwargs: Additional arguments passed to AIDXParser constructor
                        (skip_tags, include_only_tags, preserve_namespaces, etc.)
        
    Returns:
        Parsed data as dictionary or JSON string based on output_format
        
    Raises:
        AIDXParseError: If parsing fails
        ValueError: If output_format is invalid
        
    Example:
        # Parse file to dictionary
        data = parse_aidx("flight.xml")
        
        # Parse file to JSON string
        json_str = parse_aidx("flight.xml", output_format='json')
        
        # Parse with custom options
        data = parse_aidx("flight.xml", skip_tags=['TPA_Extension'])
        
        # Parse XML string directly
        xml_content = "<IATA_AIDX_FlightLegNotifRQ>...</IATA_AIDX_FlightLegNotifRQ>"
        data = parse_aidx(xml_content)
    """
    # Validate output format parameter
    if output_format not in ['dict', 'json']:
        raise ValueError("output_format must be 'dict' or 'json'")
    
    # Create parser instance with provided configuration
    parser = AIDXParser(**parser_kwargs)
    
    # Determine if input is file path or XML string
    # Simple heuristic: if it contains '<' it's likely XML content
    if isinstance(input_source, (str, Path)) and not str(input_source).strip().startswith('<'):
        # Treat as file path
        try:
            # Check if file exists to confirm it's a file path
            path_obj = Path(input_source)
            if path_obj.exists():
                # Parse as file
                data = parser.parse_xml_file(input_source)
            else:
                # File doesn't exist, treat as XML string
                data = parser.parse_xml_string(str(input_source))
        except Exception:
            # If file parsing fails, try as XML string
            data = parser.parse_xml_string(str(input_source))
    else:
        # Treat as XML string content
        data = parser.parse_xml_string(str(input_source))
    
    # Return data in requested format
    if output_format == 'json':
        return parser.to_json(data)
    else:
        return data


def main():
    """
    Demonstration function showing AIDX parser capabilities.
    
    This function:
    1. Tests the parser with sample AIDX XML files
    2. Demonstrates different parsing options
    3. Shows JSON conversion capabilities
    4. Provides usage examples for developers
    
    The demo processes real AIDX files and shows:
    - Basic parsing functionality
    - JSON output formatting
    - Parser configuration options
    - Error handling
    """
    print("AIDX Parser Demo")
    print("=" * 50)
    
    # Define sample XML files to test (if they exist)
    sample_files = [
        "AOS xml files/Arrival_ETA_LATE_10MIN_STA.xml",
        "AOS xml files/Departure_with_OperationTime_&_Resource_CHK_GTO_BST_FCT_BEN_GCL.xml"
    ]
    
    # Test each sample file
    for file_path in sample_files:
        file_path_obj = Path(file_path)
        
        # Check if sample file exists
        if not file_path_obj.exists():
            print(f"\n⚠️  Sample file not found: {file_path}")
            continue
        
        print(f"\n🔍 Processing: {file_path_obj.name}")
        print("-" * 40)
        
        try:
            # Create parser instance with default settings
            parser = AIDXParser()
            
            # Parse the XML file
            data = parser.parse_xml_file(file_path)
            
            # Convert to JSON for display
            json_output = parser.to_json(data)
            
            # Show basic statistics about the parsed data
            print(f"✅ Successfully parsed XML file")
            print(f"📊 JSON output length: {len(json_output)} characters")
            print(f"🔑 Root keys: {list(data.keys())}")
            
            # Show first 500 characters of JSON output
            print(f"\n📄 JSON Preview (first 500 chars):")
            print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
            
        except AIDXParseError as e:
            print(f"❌ Parsing error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Demonstrate different parser configurations
    print(f"\n🛠️  Parser Configuration Examples")
    print("-" * 40)
    
    # Example 1: Skip TPA_Extension tags
    print("1. Parsing with TPA_Extension tags skipped:")
    try:
        parser_no_tpa = AIDXParser(skip_tags=['TPA_Extension'])
        if Path(sample_files[0]).exists():
            data_no_tpa = parser_no_tpa.parse_xml_file(sample_files[0])
            print(f"   ✅ Parsed successfully (skipped TPA extensions)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Example 2: Include only FlightLeg data
    print("2. Parsing with only FlightLeg data included:")
    try:
        parser_flight_only = AIDXParser(include_only_tags=['FlightLeg'])
        if Path(sample_files[0]).exists():
            data_flight_only = parser_flight_only.parse_xml_file(sample_files[0])
            print(f"   ✅ Parsed successfully (FlightLeg data only)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Example 3: Using convenience function
    print("3. Using convenience function:")
    try:
        if Path(sample_files[0]).exists():
            # Parse to dictionary
            data_dict = parse_aidx(sample_files[0], output_format='dict')
            # Parse to JSON
            data_json = parse_aidx(sample_files[0], output_format='json')
            print(f"   ✅ Convenience function works for both dict and JSON output")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 Demo completed!")
    print(f"\n📚 Usage Examples:")
    print("   # Basic usage")
    print("   parser = AIDXParser()")
    print("   data = parser.parse_xml_file('flight.xml')")
    print("   json_str = parser.to_json(data)")
    print()
    print("   # With custom options")
    print("   parser = AIDXParser(skip_tags=['TPA_Extension'])")
    print("   data = parser.parse_xml_file('flight.xml')")
    print()
    print("   # Convenience function")
    print("   data = parse_aidx('flight.xml')")
    print("   json_str = parse_aidx('flight.xml', output_format='json')")


# Entry point: run demo if script is executed directly
if __name__ == "__main__":
    main()