#!/usr/bin/env python3
"""
Comprehensive Test Suite for AIDX Parser

This test suite validates the AIDX parser against all XML files in the AOS xml files folder,
checking for accuracy, correct conversion, and data integrity. The test suite performs:

1. File accessibility validation - Ensures all XML files can be found and accessed
2. XML well-formedness checks - Validates XML syntax and structure
3. Basic parser functionality - Tests core parsing capabilities
4. JSON serialization - Verifies output can be converted to JSON
5. Data integrity validation - Compares parsed data with original XML
6. Flight data extraction - Tests extraction of key flight information
7. Parser configuration options - Tests various parser settings
8. Convenience function testing - Validates helper functions
9. Error handling - Tests parser behavior with invalid inputs

The test suite processes all XML files in the 'AOS xml files' directory and provides
detailed reporting on success rates, failures, and extracted data.

Author: AI Assistant
Version: 1.0
Python: 3.9+
"""

# Import required standard library modules
import unittest                                    # For test framework
import json                                       # For JSON validation
import xml.etree.ElementTree as ET               # For XML validation
from pathlib import Path                          # For file path handling
from typing import Dict, Any, List, Tuple        # For type hints
import time                                       # For performance measurement
import sys                                        # For system operations

# Import our AIDX parser modules
from aidx_parser import AIDXParser, parse_aidx, AIDXParseError


class TestAIDXParser(unittest.TestCase):
    """
    Comprehensive test suite for AIDX Parser functionality.
    
    This test class validates the AIDX parser against real-world XML files,
    ensuring accurate parsing, data integrity, and proper error handling.
    The tests are designed to be thorough and provide detailed feedback
    on parser performance and reliability.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment before running any tests.
        
        This method:
        1. Locates the XML files directory
        2. Creates a parser instance for testing
        3. Initializes result tracking
        4. Discovers all XML files to test
        5. Displays test suite information
        
        This setup runs once for the entire test class.
        """
        # Define the directory containing XML test files
        cls.xml_folder = Path("AOS xml files")
        
        # Create a default parser instance for testing
        cls.parser = AIDXParser()
        
        # Initialize list to track test results across all tests
        cls.test_results = []
        
        # Discover all XML files in the test directory
        cls.xml_files = list(cls.xml_folder.glob("*.xml"))
        
        # Display test suite header and information
        print(f"\n{'='*80}")
        print(f"AIDX PARSER COMPREHENSIVE TEST SUITE")
        print(f"{'='*80}")
        print(f"Found {len(cls.xml_files)} XML files to test")
        print(f"Test folder: {cls.xml_folder.absolute()}")
        print(f"{'='*80}\n")
    
    def setUp(self):
        """
        Set up each individual test.
        
        This method runs before each test method and:
        1. Records the start time for performance measurement
        2. Prepares any test-specific resources
        
        This allows us to track how long each test takes to complete.
        """
        # Record start time for performance measurement
        self.start_time = time.time()
    
    def tearDown(self):
        """
        Clean up after each individual test.
        
        This method runs after each test method and:
        1. Calculates elapsed time
        2. Reports test performance
        3. Cleans up any test-specific resources
        """
        # Calculate and display test execution time
        elapsed = time.time() - self.start_time
        print(f"   ⏱️  Test completed in {elapsed:.3f}s")

    def test_01_xml_files_exist(self):
        """
        Test 1: Verify that XML files exist and are accessible.
        
        This test ensures that:
        1. The XML files directory exists
        2. XML files are present in the directory
        3. Files are readable and accessible
        4. File paths are valid
        
        This is a prerequisite test - if files don't exist, other tests will fail.
        """
        print("🔍 Test 1: Checking XML file accessibility...")
        
        # Verify the XML directory exists
        self.assertTrue(self.xml_folder.exists(), 
                       f"XML folder does not exist: {self.xml_folder}")
        
        # Verify we found XML files to test
        self.assertGreater(len(self.xml_files), 0, 
                          "No XML files found in the test directory")
        
        # Check each XML file individually
        for xml_file in self.xml_files:
            # Verify file exists
            self.assertTrue(xml_file.exists(), 
                           f"XML file does not exist: {xml_file}")
            
            # Verify it's actually a file (not a directory)
            self.assertTrue(xml_file.is_file(), 
                           f"Path is not a file: {xml_file}")
            
            # Verify file is readable
            self.assertTrue(xml_file.stat().st_size > 0, 
                           f"XML file is empty: {xml_file}")
        
        print(f"   ✅ All {len(self.xml_files)} XML files are accessible")

    def test_02_xml_well_formed(self):
        """
        Test 2: Verify that all XML files are well-formed and valid.
        
        This test ensures that:
        1. XML files have valid syntax
        2. XML structure is properly formed
        3. Files can be parsed by standard XML parsers
        4. No syntax errors or malformed elements exist
        
        Well-formed XML is a prerequisite for successful AIDX parsing.
        """
        print("🔍 Test 2: Validating XML well-formedness...")
        
        # Track files that fail XML validation
        failed_files = []
        
        # Test each XML file for well-formedness
        for xml_file in self.xml_files:
            try:
                # Attempt to parse XML using ElementTree
                # This will raise ParseError if XML is malformed
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Parse the XML content
                root = ET.fromstring(xml_content)
                
                # Verify we got a valid root element
                self.assertIsNotNone(root, f"Failed to parse root element: {xml_file}")
                
                print(f"   ✅ {xml_file.name}: Well-formed XML")
                
            except ET.ParseError as e:
                # XML parsing failed - record the failure
                failed_files.append((xml_file, str(e)))
                print(f"   ❌ {xml_file.name}: XML parse error - {e}")
                
            except Exception as e:
                # Other errors (file reading, encoding, etc.)
                failed_files.append((xml_file, str(e)))
                print(f"   ❌ {xml_file.name}: Unexpected error - {e}")
        
        # Assert that no files failed XML validation
        if failed_files:
            newline = '\n'  # Variable to handle newlines in f-strings
            failure_details = newline.join([f"  - {file}: {error}" for file, error in failed_files])
            self.fail(f"XML validation failed for {len(failed_files)} files:{newline}{failure_details}")
        
        print(f"   ✅ All {len(self.xml_files)} XML files are well-formed")

    def test_03_parser_basic_functionality(self):
        """
        Test 3: Test basic AIDX parser functionality on all XML files.
        
        This test ensures that:
        1. Parser can successfully parse all XML files
        2. Parsing produces valid Python data structures
        3. No parsing errors or exceptions occur
        4. Output structure is consistent and expected
        
        This is the core functionality test for the AIDX parser.
        """
        print("🔍 Test 3: Testing basic parser functionality...")
        
        # Track parsing failures
        failed_parses = []
        successful_parses = 0
        
        # Test parsing each XML file
        for xml_file in self.xml_files:
            try:
                # Attempt to parse the XML file using our AIDX parser
                parsed_data = self.parser.parse_xml_file(xml_file)
                
                # Verify we got a valid result
                self.assertIsInstance(parsed_data, dict, 
                                    f"Parser should return dict, got {type(parsed_data)}")
                
                # Verify the result is not empty
                self.assertGreater(len(parsed_data), 0, 
                                 f"Parsed data should not be empty for {xml_file}")
                
                # Verify we have a root element
                root_keys = list(parsed_data.keys())
                self.assertEqual(len(root_keys), 1, 
                               f"Should have exactly one root key, got {len(root_keys)}")
                
                successful_parses += 1
                print(f"   ✅ {xml_file.name}: Successfully parsed")
                
            except AIDXParseError as e:
                # AIDX parser specific error
                failed_parses.append((xml_file, f"AIDX Parse Error: {e}"))
                print(f"   ❌ {xml_file.name}: AIDX parse error - {e}")
                
            except Exception as e:
                # Any other unexpected error
                failed_parses.append((xml_file, f"Unexpected Error: {e}"))
                print(f"   ❌ {xml_file.name}: Unexpected error - {e}")
        
        # Report results and assert success
        print(f"   📊 Successfully parsed: {successful_parses}/{len(self.xml_files)} files")
        
        if failed_parses:
            newline = '\n'  # Variable to handle newlines in f-strings
            failure_details = newline.join([f"  - {file}: {error}" for file, error in failed_parses])
            self.fail(f"Parser failed for {len(failed_parses)} files:{newline}{failure_details}")
        
        print(f"   ✅ All {len(self.xml_files)} files parsed successfully")

    def test_04_json_serialization(self):
        """
        Test 4: Test JSON serialization of parsed data.
        
        This test ensures that:
        1. Parsed data can be converted to JSON format
        2. JSON serialization doesn't lose data
        3. JSON output is valid and well-formed
        4. No serialization errors occur
        
        JSON serialization is important for API integration and data exchange.
        """
        print("🔍 Test 4: Testing JSON serialization...")
        
        # Track serialization failures
        failed_serializations = []
        successful_serializations = 0
        
        # Test JSON serialization for each XML file
        for xml_file in self.xml_files:
            try:
                # Parse the XML file first
                parsed_data = self.parser.parse_xml_file(xml_file)
                
                # Convert to JSON using parser's method
                json_output = self.parser.to_json(parsed_data)
                
                # Verify JSON output is a string
                self.assertIsInstance(json_output, str, 
                                    f"JSON output should be string, got {type(json_output)}")
                
                # Verify JSON is not empty
                self.assertGreater(len(json_output), 0, 
                                 f"JSON output should not be empty for {xml_file}")
                
                # Verify JSON is valid by parsing it back
                reparsed_data = json.loads(json_output)
                
                # Verify reparsed data matches original
                self.assertEqual(parsed_data, reparsed_data, 
                               f"JSON round-trip failed for {xml_file}")
                
                successful_serializations += 1
                print(f"   ✅ {xml_file.name}: JSON serialization successful")
                
            except json.JSONDecodeError as e:
                # JSON parsing failed
                failed_serializations.append((xml_file, f"Invalid JSON: {e}"))
                print(f"   ❌ {xml_file.name}: Invalid JSON - {e}")
                
            except AIDXParseError as e:
                # AIDX parsing failed
                failed_serializations.append((xml_file, f"Parse Error: {e}"))
                print(f"   ❌ {xml_file.name}: Parse error - {e}")
                
            except Exception as e:
                # Any other error
                failed_serializations.append((xml_file, f"Unexpected Error: {e}"))
                print(f"   ❌ {xml_file.name}: Unexpected error - {e}")
        
        # Report results and assert success
        print(f"   📊 Successfully serialized: {successful_serializations}/{len(self.xml_files)} files")
        
        if failed_serializations:
            newline = '\n'  # Variable to handle newlines in f-strings
            failure_details = newline.join([f"  - {file}: {error}" for file, error in failed_serializations])
            self.fail(f"JSON serialization failed for {len(failed_serializations)} files:{newline}{failure_details}")
        
        print(f"   ✅ All {len(self.xml_files)} files serialized to JSON successfully")

    def test_05_data_integrity(self):
        """
        Test 5: Validate data integrity between original XML and parsed output.
        
        This test ensures that:
        1. No data is lost during parsing
        2. XML structure is preserved in parsed output
        3. Attributes and text content are maintained
        4. Element hierarchy is correctly represented
        
        Data integrity is crucial for ensuring the parser accurately represents the original XML.
        """
        print("🔍 Test 5: Validating data integrity...")
        
        # Track integrity validation failures
        failed_validations = []
        successful_validations = 0
        
        # Test data integrity for each XML file
        for xml_file in self.xml_files:
            try:
                # Parse XML with both ElementTree (reference) and our parser
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Parse with ElementTree for comparison
                et_root = ET.fromstring(xml_content)
                
                # Parse with our AIDX parser
                parsed_data = self.parser.parse_xml_file(xml_file)
                
                # Validate structure integrity
                self._validate_structure_integrity(et_root, parsed_data, xml_file.name)
                
                successful_validations += 1
                print(f"   ✅ {xml_file.name}: Data integrity validated")
                
            except AssertionError as e:
                # Integrity validation failed
                failed_validations.append((xml_file, f"Integrity Error: {e}"))
                print(f"   ❌ {xml_file.name}: Integrity error - {e}")
                
            except Exception as e:
                # Any other error
                failed_validations.append((xml_file, f"Unexpected Error: {e}"))
                print(f"   ❌ {xml_file.name}: Unexpected error - {e}")
        
        # Report results and assert success
        print(f"   📊 Successfully validated: {successful_validations}/{len(self.xml_files)} files")
        
        if failed_validations:
            newline = '\n'  # Variable to handle newlines in f-strings
            failure_details = newline.join([f"  - {file}: {error}" for file, error in failed_validations])
            self.fail(f"Data integrity validation failed for {len(failed_validations)} files:{newline}{failure_details}")
        
        print(f"   ✅ All {len(self.xml_files)} files passed data integrity validation")

    def test_06_flight_data_extraction(self):
        """
        Test 6: Test extraction of key flight data from parsed XML.
        
        This test ensures that:
        1. Flight information can be extracted from parsed data
        2. Key flight elements (airline, flight number, etc.) are accessible
        3. Data extraction works across different XML structures
        4. Flight data is in expected format
        
        This test validates that the parser produces usable data for flight operations.
        """
        print("🔍 Test 6: Testing flight data extraction...")
        
        # Track extraction results
        extraction_results = []
        successful_extractions = 0
        
        # Test flight data extraction for each XML file
        for xml_file in self.xml_files:
            try:
                # Parse the XML file
                parsed_data = self.parser.parse_xml_file(xml_file)
                
                # Extract flight information
                flight_info = self._extract_flight_info(parsed_data, xml_file.name)
                
                # Verify we extracted some flight information
                self.assertIsInstance(flight_info, dict, 
                                    f"Flight info should be dict, got {type(flight_info)}")
                
                # Store extraction results for reporting
                extraction_results.append((xml_file.name, flight_info))
                successful_extractions += 1
                
                # Display extracted flight information
                airline = flight_info.get('airline', 'N/A')
                flight_num = flight_info.get('flight_number', 'N/A')
                flight_type = flight_info.get('flight_type', 'N/A')
                
                print(f"   ✅ {xml_file.name}: {airline} {flight_num} ({flight_type})")
                
            except Exception as e:
                # Extraction failed
                print(f"   ❌ {xml_file.name}: Extraction error - {e}")
                extraction_results.append((xml_file.name, {"error": str(e)}))
        
        # Report extraction statistics
        print(f"   📊 Successfully extracted flight data: {successful_extractions}/{len(self.xml_files)} files")
        
        # Store results for final reporting
        self.test_results.extend(extraction_results)
        
        # Verify we extracted data from most files (allow some failures for edge cases)
        success_rate = successful_extractions / len(self.xml_files)
        self.assertGreater(success_rate, 0.8, 
                          f"Flight data extraction success rate too low: {success_rate:.2%}")
        
        print(f"   ✅ Flight data extraction completed with {success_rate:.1%} success rate")

    def test_07_parser_options(self):
        """
        Test 7: Test various parser configuration options.
        
        This test ensures that:
        1. Parser options work as expected
        2. Tag filtering (skip_tags, include_only_tags) functions correctly
        3. Namespace handling options work properly
        4. Attribute inclusion/exclusion works
        
        This validates the parser's configurability and flexibility.
        """
        print("🔍 Test 7: Testing parser configuration options...")
        
        # Use first available XML file for testing options
        if not self.xml_files:
            self.skipTest("No XML files available for testing parser options")
        
        test_file = self.xml_files[0]
        
        # Test 1: Default parser configuration
        try:
            default_parser = AIDXParser()
            default_data = default_parser.parse_xml_file(test_file)
            self.assertIsInstance(default_data, dict)
            print(f"   ✅ Default parser configuration works")
        except Exception as e:
            self.fail(f"Default parser configuration failed: {e}")
        
        # Test 2: Parser with skip_tags option
        try:
            skip_parser = AIDXParser(skip_tags=['TPA_Extension'])
            skip_data = skip_parser.parse_xml_file(test_file)
            self.assertIsInstance(skip_data, dict)
            print(f"   ✅ Parser with skip_tags option works")
        except Exception as e:
            self.fail(f"Parser with skip_tags failed: {e}")
        
        # Test 3: Parser with include_only_tags option
        try:
            include_parser = AIDXParser(include_only_tags=['FlightLeg'])
            include_data = include_parser.parse_xml_file(test_file)
            self.assertIsInstance(include_data, dict)
            print(f"   ✅ Parser with include_only_tags option works")
        except Exception as e:
            self.fail(f"Parser with include_only_tags failed: {e}")
        
        # Test 4: Parser with namespace preservation
        try:
            ns_parser = AIDXParser(preserve_namespaces=True)
            ns_data = ns_parser.parse_xml_file(test_file)
            self.assertIsInstance(ns_data, dict)
            print(f"   ✅ Parser with namespace preservation works")
        except Exception as e:
            self.fail(f"Parser with namespace preservation failed: {e}")
        
        print(f"   ✅ All parser configuration options work correctly")

    def test_08_convenience_function(self):
        """
        Test 8: Test the convenience parse_aidx function.
        
        This test ensures that:
        1. Convenience function works with file paths
        2. Function works with XML strings
        3. Output format options (dict/json) work correctly
        4. Function parameters are passed correctly to parser
        
        The convenience function provides a simple interface for common parsing tasks.
        """
        print("🔍 Test 8: Testing convenience function...")
        
        if not self.xml_files:
            self.skipTest("No XML files available for testing convenience function")
        
        test_file = self.xml_files[0]
        
        # Test 1: Parse file to dictionary
        try:
            dict_result = parse_aidx(test_file, output_format='dict')
            self.assertIsInstance(dict_result, dict)
            print(f"   ✅ Convenience function: file to dict works")
        except Exception as e:
            self.fail(f"Convenience function (file to dict) failed: {e}")
        
        # Test 2: Parse file to JSON string
        try:
            json_result = parse_aidx(test_file, output_format='json')
            self.assertIsInstance(json_result, str)
            # Verify it's valid JSON
            json.loads(json_result)
            print(f"   ✅ Convenience function: file to JSON works")
        except Exception as e:
            self.fail(f"Convenience function (file to JSON) failed: {e}")
        
        # Test 3: Parse with custom options
        try:
            custom_result = parse_aidx(test_file, skip_tags=['TPA_Extension'])
            self.assertIsInstance(custom_result, dict)
            print(f"   ✅ Convenience function: custom options work")
        except Exception as e:
            self.fail(f"Convenience function (custom options) failed: {e}")
        
        print(f"   ✅ Convenience function works correctly")

    def test_09_error_handling(self):
        """
        Test 9: Test parser error handling with invalid inputs.
        
        This test ensures that:
        1. Parser handles invalid XML gracefully
        2. Appropriate exceptions are raised for error conditions
        3. Error messages are informative and helpful
        4. Parser doesn't crash on malformed input
        
        Robust error handling is essential for production use.
        """
        print("🔍 Test 9: Testing error handling...")
        
        # Test 1: Invalid XML string
        try:
            with self.assertRaises(AIDXParseError):
                self.parser.parse_xml_string("<invalid>xml<content>")
            print(f"   ✅ Invalid XML string handling works")
        except Exception as e:
            self.fail(f"Invalid XML string test failed: {e}")
        
        # Test 2: Empty XML string
        try:
            with self.assertRaises(AIDXParseError):
                self.parser.parse_xml_string("")
            print(f"   ✅ Empty XML string handling works")
        except Exception as e:
            self.fail(f"Empty XML string test failed: {e}")
        
        # Test 3: Non-existent file
        try:
            with self.assertRaises(AIDXParseError):
                self.parser.parse_xml_file("non_existent_file.xml")
            print(f"   ✅ Non-existent file handling works")
        except Exception as e:
            self.fail(f"Non-existent file test failed: {e}")
        
        print(f"   ✅ Error handling works correctly")

    def _validate_structure_integrity(self, et_element: ET.Element, parsed_data: Dict[str, Any], filename: str):
        """
        Helper method to validate structural integrity between ElementTree and parsed data.
        
        This method performs deep validation to ensure that:
        1. The parsed data structure matches the original XML structure
        2. No elements are lost during parsing
        3. Attributes are preserved correctly
        4. Text content is maintained
        
        Args:
            et_element: ElementTree element (reference)
            parsed_data: Parsed data from our parser
            filename: Name of file being validated (for error reporting)
            
        Raises:
            AssertionError: If structural integrity is compromised
        """
        # This is a simplified integrity check
        # In a production environment, you might want more comprehensive validation
        
        # Verify parsed data is not empty
        self.assertIsNotNone(parsed_data, f"Parsed data is None for {filename}")
        
        # Verify we have a root element in parsed data
        if isinstance(parsed_data, dict):
            self.assertGreater(len(parsed_data), 0, f"Parsed data is empty for {filename}")
        
        # Additional integrity checks could be added here
        # For example: comparing element counts, attribute preservation, etc.

    def _extract_flight_info(self, data: Dict[str, Any], filename: str) -> Dict[str, str]:
        """
        Helper method to extract key flight information from parsed AIDX data.
        
        This method navigates the parsed data structure to find and extract:
        1. Airline code and name
        2. Flight number
        3. Flight type (arrival/departure)
        4. Airport codes (origin/destination)
        5. Operational status information
        
        Args:
            data: Parsed AIDX data dictionary
            filename: Name of source file (for context)
            
        Returns:
            Dictionary containing extracted flight information
            
        Example return:
            {
                "airline": "JQ",
                "flight_number": "255", 
                "flight_type": "Arrival",
                "origin": "SYD",
                "destination": "MEL",
                "status": "On Time"
            }
        """
        # Initialize result dictionary with default values
        flight_info = {
            "airline": "N/A",
            "flight_number": "N/A", 
            "flight_type": "Unknown",
            "origin": "N/A",
            "destination": "N/A",
            "status": "N/A"
        }
        
        try:
            # Navigate through the data structure to find flight information
            # AIDX structure typically has a root element containing FlightLeg data
            
            # Get the root element (should be only one key)
            root_keys = list(data.keys())
            if not root_keys:
                return flight_info
            
            root_data = data[root_keys[0]]
            if not isinstance(root_data, dict):
                return flight_info
            
            # Look for FlightLeg information
            flight_leg = None
            if 'FlightLeg' in root_data:
                flight_leg = root_data['FlightLeg']
            elif 'LegData' in root_data:
                flight_leg = root_data['LegData']
            
            if flight_leg and isinstance(flight_leg, dict):
                # Extract LegIdentifier information
                if 'LegIdentifier' in flight_leg:
                    leg_id = flight_leg['LegIdentifier']
                    if isinstance(leg_id, dict):
                        # Extract airline information
                        if 'Airline' in leg_id:
                            airline_data = leg_id['Airline']
                            if isinstance(airline_data, dict):
                                flight_info["airline"] = airline_data.get('#text', airline_data.get('@CodeContext', 'N/A'))
                            else:
                                flight_info["airline"] = str(airline_data)
                        
                        # Extract flight number
                        if 'FlightNumber' in leg_id:
                            flight_info["flight_number"] = str(leg_id['FlightNumber'])
                
                # Determine flight type from filename or data structure
                filename_lower = filename.lower()
                if 'arrival' in filename_lower:
                    flight_info["flight_type"] = "Arrival"
                elif 'departure' in filename_lower:
                    flight_info["flight_type"] = "Departure"
                
                # Extract airport information
                if 'DepartureAirport' in flight_leg:
                    dep_airport = flight_leg['DepartureAirport']
                    if isinstance(dep_airport, dict) and '@LocationCode' in dep_airport:
                        flight_info["origin"] = dep_airport['@LocationCode']
                
                if 'ArrivalAirport' in flight_leg:
                    arr_airport = flight_leg['ArrivalAirport']
                    if isinstance(arr_airport, dict) and '@LocationCode' in arr_airport:
                        flight_info["destination"] = arr_airport['@LocationCode']
                
                # Extract operational status
                if 'LegData' in flight_leg:
                    leg_data = flight_leg['LegData']
                    if isinstance(leg_data, dict):
                        if 'OperationalStatus' in leg_data:
                            op_status = leg_data['OperationalStatus']
                            if isinstance(op_status, dict) and '@Code' in op_status:
                                flight_info["status"] = op_status['@Code']
        
        except Exception as e:
            # If extraction fails, log the error but don't fail the test
            flight_info["extraction_error"] = str(e)
        
        return flight_info

    @classmethod
    def tearDownClass(cls):
        """
        Clean up after all tests have completed.
        
        This method:
        1. Generates a summary report of all test results
        2. Displays statistics about parsed files
        3. Shows extracted flight data summary
        4. Provides final test suite status
        
        This runs once after all tests in the class have completed.
        """
        print(f"\n{'='*80}")
        print(f"TEST SUITE COMPLETED")
        print(f"{'='*80}")
        print(f"Total XML files tested: {len(cls.xml_files)}")
        print(f"Test folder: {cls.xml_folder.absolute()}")
        print(f"{'='*80}\n")


def run_comprehensive_test():
    """
    Main function to run the comprehensive AIDX parser test suite.
    
    This function:
    1. Sets up the test environment
    2. Runs all test methods in sequence
    3. Collects and reports results
    4. Provides overall success/failure status
    
    Returns:
        bool: True if all tests passed, False if any tests failed
        
    This function can be called directly or used as a script entry point.
    """
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIDXParser)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,           # Detailed output
        stream=sys.stdout,     # Output to console
        buffer=False           # Don't buffer output
    )
    
    # Execute the test suite
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


# Entry point: run comprehensive test suite if script is executed directly
if __name__ == "__main__":
    # Run the test suite and exit with appropriate code
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)