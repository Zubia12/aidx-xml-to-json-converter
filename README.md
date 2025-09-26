# 🚀 AIDX XML to JSON Converter

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-100%25%20Pass-brightgreen.svg)](test_results_summary.md)

A comprehensive web application for converting AIDX (Airport Information Data Exchange) XML files to JSON format with an intuitive drag-and-drop interface.

## Features

- ✅ **Complete XML Parsing**: Handles complex nested AIDX XML structures
- ✅ **Namespace Support**: Automatically cleans namespace prefixes for readable output
- ✅ **Attribute Preservation**: Maintains XML attributes with `@` prefix notation
- ✅ **Hierarchy Preservation**: Maintains original XML structure in output
- ✅ **Repeating Elements**: Automatically converts repeating XML elements to lists
- ✅ **Customizable Filtering**: Skip or include specific XML tags
- ✅ **Error Handling**: Comprehensive error handling with custom exceptions
- ✅ **Multiple Input Types**: Accept file paths or XML strings
- ✅ **JSON Export**: Convert parsed data to JSON format
- ✅ **Python 3.9+ Compatible**: Uses only standard library (no external dependencies)

## Installation

No external dependencies required! The module uses only Python standard library.

```bash
# Clone or download the aidx_parser.py file
# Optionally install enhanced XML parsing (not required):
pip install lxml xmlschema
```

## Quick Start

### Basic Usage

```python
from aidx_parser import parse_aidx, AIDXParser

# Parse from file (returns Python dict)
data = parse_aidx('flight_data.xml')

# Parse to JSON string
json_output = parse_aidx('flight_data.xml', output_format='json')

# Parse from XML string
xml_string = "<?xml version='1.0'?>..."
data = parse_aidx(xml_string)
```

### Advanced Usage

```python
# Create custom parser with filtering
parser = AIDXParser(
    skip_tags=['TPA_Extension'],           # Skip specific tags
    include_only_tags=['FlightLeg'],       # Only parse specific tags
    preserve_namespaces=False,             # Clean namespace prefixes
    include_attributes=True                # Include XML attributes
)

# Parse with custom settings
data = parser.parse_xml_file('flight.xml')
json_output = parser.to_json(data, indent=4)
```

## API Reference

### `parse_aidx(input_source, output_format='dict', **parser_kwargs)`

Convenience function for quick parsing.

**Parameters:**
- `input_source` (str|Path): File path or XML string
- `output_format` (str): 'dict' or 'json'
- `**parser_kwargs`: Additional AIDXParser arguments

**Returns:** Parsed data as dict or JSON string

### `AIDXParser` Class

Main parser class with full customization options.

**Constructor Parameters:**
- `skip_tags` (List[str]): XML tags to skip during parsing
- `include_only_tags` (List[str]): Only parse these specific tags
- `preserve_namespaces` (bool): Keep namespace prefixes (default: False)
- `include_attributes` (bool): Include XML attributes (default: True)

**Methods:**
- `parse_xml_file(file_path)`: Parse XML from file
- `parse_xml_string(xml_string)`: Parse XML from string
- `to_json(data, indent=2)`: Convert data to JSON string

## Output Format

The parser converts XML to a clean dictionary structure:

```python
# XML Input:
# <FlightLeg>
#   <LegIdentifier>
#     <Airline CodeContext="3">JQ</Airline>
#     <FlightNumber>255</FlightNumber>
#   </LegIdentifier>
# </FlightLeg>

# Python Output:
{
  "FlightLeg": {
    "LegIdentifier": {
      "Airline": {
        "@CodeContext": "3",
        "#text": "JQ"
      },
      "FlightNumber": "255"
    }
  }
}
```

### Key Conventions:
- **Attributes**: Prefixed with `@` (e.g., `@CodeContext`)
- **Text Content**: Stored as `#text` when element has both text and children
- **Repeating Elements**: Automatically converted to lists
- **Namespaces**: Removed by default for cleaner output

## Examples

### Example 1: Basic Flight Data Parsing

```python
from aidx_parser import parse_aidx

# Parse AIDX flight notification
data = parse_aidx('arrival_notification.xml')

# Access flight information
flight_leg = data['IATA_AIDX_FlightLegNotifRQ']['FlightLeg']
airline = flight_leg['LegIdentifier']['Airline']['#text']
flight_number = flight_leg['LegIdentifier']['FlightNumber']

print(f"Flight: {airline} {flight_number}")
```

### Example 2: Custom Filtering

```python
from aidx_parser import AIDXParser

# Skip technical extensions, focus on core flight data
parser = AIDXParser(skip_tags=['TPA_Extension', 'DeliveringSystem'])
data = parser.parse_xml_file('flight.xml')

# Convert to pretty JSON
json_output = parser.to_json(data, indent=2)
print(json_output)
```

### Example 3: Processing Multiple Files

```python
from pathlib import Path
from aidx_parser import AIDXParser

parser = AIDXParser()
xml_files = Path('.').glob('*.xml')

for xml_file in xml_files:
    try:
        data = parser.parse_xml_file(xml_file)
        print(f"✅ Processed: {xml_file}")
        
        # Extract key flight info
        root_key = list(data.keys())[0]
        if 'FlightLeg' in data[root_key]:
            flight_info = data[root_key]['FlightLeg']['LegIdentifier']
            airline = flight_info['Airline']['#text']
            flight_num = flight_info['FlightNumber']
            print(f"   Flight: {airline} {flight_num}")
            
    except Exception as e:
        print(f"❌ Error processing {xml_file}: {e}")
```

## Error Handling

The module provides comprehensive error handling:

```python
from aidx_parser import parse_aidx, AIDXParseError

try:
    data = parse_aidx('flight.xml')
except AIDXParseError as e:
    print(f"AIDX parsing error: {e}")
except FileNotFoundError:
    print("XML file not found")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Demo

Run the included demo to see the parser in action:

```bash
python aidx_parser.py
```

This will process sample AIDX files and display:
- Parsed JSON output (first 1000 characters)
- File statistics
- Key flight information extracted

## AIDX Standard

This parser supports the IATA Aviation Information Data Exchange (AIDX) standard, which is:
- IATA Recommended Practice 1797A <mcreference link="https://www.iata.org/en/publications/info-data-exchange/#tab-3" index="0">0</mcreference>
- ACI Recommended Practice 501A07 <mcreference link="https://www.iata.org/en/publications/info-data-exchange/#tab-3" index="0">0</mcreference>
- ATA Recommended Practice 30.201A <mcreference link="https://www.iata.org/en/publications/info-data-exchange/#tab-3" index="0">0</mcreference>

Used for exchanging flight data between airlines, airports, and third parties in operational environments.

## Requirements

- Python 3.9+
- No external dependencies (uses standard library only)

## License

This module is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues, feature requests, or improvements to enhance the parser's functionality.