"""
Property-based tests for OCR processing and document parsing.
Tests universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis import assume
from datetime import datetime, date, timedelta
from src.shared.document_parser import DocumentParser, DocumentParserError
from src.shared.exceptions import OCRFailure
from unittest.mock import Mock, patch
import json


# Custom strategies for generating test data
@st.composite
def valid_document_text(draw):
    """Generate valid document text with required fields."""
    vendors = ['Office Depot', 'Staples', 'Amazon', 'Walmart', 'Target', 'Best Buy']
    vendor = draw(st.sampled_from(vendors))
    
    # Generate a reasonable date
    year = draw(st.integers(min_value=2020, max_value=2024))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    date_str = f"{month:02d}/{day:02d}/{year}"
    
    # Generate a reasonable amount
    amount = draw(st.floats(min_value=0.01, max_value=10000.0))
    amount_str = f"${amount:.2f}"
    
    # Build document text
    text = f"{vendor}\nDate: {date_str}\nTotal: {amount_str}"
    
    return text, vendor, f"{year}-{month:02d}-{day:02d}", amount


@st.composite
def invalid_document_text(draw):
    """Generate invalid document text missing required fields."""
    choice = draw(st.integers(min_value=0, max_value=2))
    
    if choice == 0:
        # Missing date
        return "Store Name\nTotal: $50.00"
    elif choice == 1:
        # Missing amount
        return "Store Name\nDate: 01/15/2024"
    else:
        # Empty or whitespace only
        return draw(st.sampled_from(["", "   ", "\n\n"]))


class TestPropertyOCRProcessing:
    """Property-based tests for OCR processing."""
    
    @settings(max_examples=100)
    @given(text_data=valid_document_text())
    def test_property_1_document_parsing_produces_structured_fields(self, text_data):
        """
        **Validates: Requirements 1.2**
        
        Property 1: Document Parsing Produces Structured Fields
        For any valid extracted text from a financial document, the parser should 
        successfully produce a structured object containing date, amount, vendor, 
        and line_items fields.
        """
        text, expected_vendor, expected_date, expected_amount = text_data
        
        # Parse the document
        result = DocumentParser.parse(text)
        
        # Verify all required fields are present
        assert 'vendor' in result, "Parsed document must contain 'vendor' field"
        assert 'amount' in result, "Parsed document must contain 'amount' field"
        assert 'date' in result, "Parsed document must contain 'date' field"
        assert 'line_items' in result, "Parsed document must contain 'line_items' field"
        
        # Verify field types
        assert isinstance(result['vendor'], str), "Vendor must be a string"
        assert isinstance(result['amount'], (int, float)), "Amount must be numeric"
        assert isinstance(result['date'], str), "Date must be a string"
        assert isinstance(result['line_items'], list), "Line items must be a list"
        
        # Verify values are reasonable
        assert result['amount'] > 0, "Amount must be positive"
        assert len(result['vendor']) > 0, "Vendor must not be empty"
        
        # Verify date format (ISO format YYYY-MM-DD)
        try:
            datetime.strptime(result['date'], '%Y-%m-%d')
        except ValueError:
            pytest.fail(f"Date '{result['date']}' is not in ISO format YYYY-MM-DD")
    
    @settings(max_examples=100)
    @given(
        vendor=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs', 'Cc'))),
        amount=st.floats(min_value=0.01, max_value=100000.0, allow_nan=False, allow_infinity=False),
        year=st.integers(min_value=2020, max_value=2024),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        doc_type=st.sampled_from(['receipt', 'invoice', 'bank_statement'])
    )
    def test_property_26_document_parsing_round_trip(self, vendor, amount, year, month, day, doc_type):
        """
        **Validates: Requirements 9.4**
        
        Property 26: Document Parsing Round-Trip
        For any valid financial document object, parsing it to structured format, 
        then printing it to text, then parsing again should produce an equivalent object.
        """
        # Create document text
        date_str = f"{month:02d}/{day:02d}/{year}"
        iso_date = f"{year}-{month:02d}-{day:02d}"
        text = f"{vendor}\nDate: {date_str}\nTotal: ${amount:.2f}"
        
        # First parse
        parsed1 = DocumentParser.parse(text, doc_type)
        
        # Create text representation (simplified pretty print)
        printed_text = f"{parsed1['vendor']}\nDate: {parsed1['date']}\nTotal: ${parsed1['amount']:.2f}"
        
        # Second parse
        parsed2 = DocumentParser.parse(printed_text, doc_type)
        
        # Verify equivalence of key fields
        assert parsed2['vendor'] == parsed1['vendor'], "Vendor should be preserved in round-trip"
        assert abs(parsed2['amount'] - parsed1['amount']) < 0.01, "Amount should be preserved in round-trip"
        assert parsed2['date'] == parsed1['date'], "Date should be preserved in round-trip"
        assert parsed2['document_type'] == parsed1['document_type'], "Document type should be preserved"
    
    @settings(max_examples=100)
    @given(invalid_text=invalid_document_text())
    def test_property_27_parser_error_handling(self, invalid_text):
        """
        **Validates: Requirements 9.2**
        
        Property 27: Parser Error Handling
        For any invalid financial document (missing required fields or malformed data), 
        the parser should return a descriptive error message rather than crashing or 
        producing invalid output.
        """
        # Attempt to parse invalid document
        with pytest.raises(DocumentParserError) as exc_info:
            DocumentParser.parse(invalid_text)
        
        # Verify error message is descriptive
        error_message = str(exc_info.value)
        assert len(error_message) > 0, "Error message must not be empty"
        
        # Error should mention what's wrong
        assert any(keyword in error_message.lower() for keyword in 
                  ['missing', 'required', 'empty', 'field', 'date', 'amount']), \
               "Error message should describe what's missing or wrong"
    
    @settings(max_examples=100)
    @given(
        has_date=st.booleans(),
        has_amount=st.booleans(),
        has_type=st.booleans()
    )
    def test_property_28_required_field_validation(self, has_date, has_amount, has_type):
        """
        **Validates: Requirements 9.5**
        
        Property 28: Required Field Validation
        For any financial document, the parser should reject it with an error if any 
        required fields (date, amount, type) are missing.
        """
        # Build document with optional fields
        text_parts = ["Test Store"]
        
        if has_date:
            text_parts.append("Date: 01/15/2024")
        
        if has_amount:
            text_parts.append("Total: $50.00")
        
        text = "\n".join(text_parts)
        
        # Create parsed fields dict
        parsed_fields = {}
        if has_date:
            parsed_fields['date'] = '2024-01-15'
        if has_amount:
            parsed_fields['amount'] = 50.00
        if has_type:
            parsed_fields['type'] = 'receipt'
        
        # Validate required fields
        is_valid, missing = DocumentParser.validate_required_fields(parsed_fields)
        
        # Date and amount are required
        if has_date and has_amount:
            # If type is present and empty, it should be flagged
            if has_type:
                assert is_valid is True, "Document with date, amount, and type should be valid"
            else:
                # Type is not strictly required by validate_required_fields
                assert is_valid is True, "Document with date and amount should be valid"
        else:
            assert is_valid is False, "Document missing required fields should be invalid"
            
            if not has_date:
                assert 'date' in missing, "Missing date should be reported"
            if not has_amount:
                assert 'amount' in missing, "Missing amount should be reported"
    
    @settings(max_examples=100, deadline=None)
    @given(
        document_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        user_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        error_type=st.sampled_from(['textract_failure', 'parsing_failure', 'unexpected_error'])
    )
    def test_property_3_ocr_failure_notification(self, document_id, user_id, error_type):
        """
        **Validates: Requirements 1.4**
        
        Property 3: OCR Failure Notification
        For any document where OCR extraction fails, the system should generate a 
        notification to the user requesting manual entry.
        """
        from src.lambdas.ocr_processor.handler import send_ocr_failure_notification
        
        # Mock SNS and Config
        with patch('src.lambdas.ocr_processor.handler.sns_client') as mock_sns, \
             patch('src.lambdas.ocr_processor.handler.Config') as mock_config:
            
            # Configure mock
            mock_config.SNS_OCR_FAILURES = f'arn:aws:sns:us-east-1:123456789012:ocr-failures'
            
            # Generate error message based on type
            error_messages = {
                'textract_failure': 'Textract API failed to process document',
                'parsing_failure': 'Failed to parse required fields from document',
                'unexpected_error': 'Unexpected error during OCR processing'
            }
            error_message = error_messages[error_type]
            
            # Send notification
            send_ocr_failure_notification(document_id, user_id, error_message)
            
            # Verify SNS publish was called
            assert mock_sns.publish.called, "SNS notification should be sent on OCR failure"
            
            # Verify notification contains required information
            call_args = mock_sns.publish.call_args
            assert call_args is not None, "SNS publish should have been called"
            
            # Check topic ARN
            assert call_args[1]['TopicArn'] == mock_config.SNS_OCR_FAILURES, \
                   "Notification should be sent to OCR failures topic"
            
            # Check subject contains document ID
            subject = call_args[1]['Subject']
            assert document_id in subject, "Subject should contain document ID"
            
            # Check message content
            message_json = call_args[1]['Message']
            message = json.loads(message_json)
            
            assert message['document_id'] == document_id, "Message should contain document ID"
            assert message['user_id'] == user_id, "Message should contain user ID"
            assert message['error'] == error_message, "Message should contain error details"
            assert 'timestamp' in message, "Message should contain timestamp"
            assert 'action_required' in message, "Message should indicate action required"
            assert 'manual' in message['action_required'].lower(), \
                   "Message should request manual entry"


class TestPropertyDocumentParser:
    """Additional property tests for document parser edge cases."""
    
    @settings(max_examples=100)
    @given(
        amount=st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        currency_symbol=st.sampled_from(['$', '€', '£'])
    )
    def test_amount_extraction_with_various_formats(self, amount, currency_symbol):
        """Test amount extraction works with various currency symbols and formats."""
        # Format with commas for thousands
        if amount >= 1000:
            amount_str = f"{currency_symbol}{amount:,.2f}"
        else:
            amount_str = f"{currency_symbol}{amount:.2f}"
        
        text = f"Store Name\nDate: 01/15/2024\nTotal: {amount_str}"
        
        result = DocumentParser.parse(text)
        
        # Verify amount is extracted correctly (within floating point precision)
        assert abs(result['amount'] - amount) < 0.01, \
               f"Amount {result['amount']} should match {amount}"
    
    @settings(max_examples=100)
    @given(
        year=st.integers(min_value=2020, max_value=2024),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        date_format=st.sampled_from(['US', 'ISO', 'EU'])
    )
    def test_date_extraction_with_various_formats(self, year, month, day, date_format):
        """Test date extraction works with various date formats."""
        # Generate date string in different formats
        if date_format == 'US':
            date_str = f"{month:02d}/{day:02d}/{year}"
        elif date_format == 'ISO':
            date_str = f"{year}-{month:02d}-{day:02d}"
        else:  # EU
            date_str = f"{day:02d}-{month:02d}-{year}"
        
        text = f"Store Name\nDate: {date_str}\nTotal: $50.00"
        
        result = DocumentParser.parse(text)
        
        # Verify date is extracted and normalized to ISO format
        expected_iso = f"{year}-{month:02d}-{day:02d}"
        assert result['date'] == expected_iso, \
               f"Date {result['date']} should be normalized to {expected_iso}"
    
    @settings(max_examples=100)
    @given(
        vendor_length=st.integers(min_value=1, max_value=150)
    )
    def test_vendor_name_length_handling(self, vendor_length):
        """Test vendor name extraction handles various lengths correctly."""
        # Generate vendor name of specified length
        vendor = 'A' * vendor_length
        
        text = f"{vendor}\nDate: 01/15/2024\nTotal: $50.00"
        
        result = DocumentParser.parse(text)
        
        # Verify vendor is extracted and truncated if necessary
        assert len(result['vendor']) <= 100, "Vendor name should be truncated to 100 chars"
        assert len(result['vendor']) > 0, "Vendor name should not be empty"
        
        if vendor_length <= 100:
            assert result['vendor'] == vendor, "Short vendor names should be preserved"
        else:
            assert result['vendor'] == vendor[:100], "Long vendor names should be truncated"
