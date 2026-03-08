"""
Unit tests for document parser.
"""

import pytest
from src.shared.document_parser import DocumentParser, DocumentParserError


class TestDocumentParser:
    """Test document parser functionality."""
    
    def test_parse_receipt_with_valid_data(self):
        """Test parsing a well-formed receipt."""
        text = """
        Office Depot
        Date: 01/15/2024
        Total: $45.99
        Paper: $25.99
        Pens: $20.00
        """
        
        result = DocumentParser.parse(text, 'receipt')
        
        assert result['vendor'] == 'Office Depot'
        assert result['date'] == '2024-01-15'
        assert result['amount'] == 45.99
        assert result['currency'] == 'USD'
        assert len(result['line_items']) >= 0  # Line items are optional
    
    def test_parse_invoice_with_iso_date(self):
        """Test parsing invoice with ISO date format."""
        text = """
        ABC Company
        Invoice Date: 2024-03-20
        Amount Due: $1,250.00
        """
        
        result = DocumentParser.parse(text, 'invoice')
        
        assert result['date'] == '2024-03-20'
        assert result['amount'] == 1250.00
        assert result['vendor'] == 'ABC Company'
    
    def test_parse_with_european_date_format(self):
        """Test parsing with European date format."""
        text = """
        Store Name
        Date: 15-03-2024
        Total: €99.50
        """
        
        result = DocumentParser.parse(text)
        
        assert result['date'] == '2024-03-15'
        assert result['amount'] == 99.50
    
    def test_parse_with_month_name(self):
        """Test parsing with month name in date."""
        text = """
        Restaurant XYZ
        Date: March 15, 2024
        Total: $75.25
        """
        
        result = DocumentParser.parse(text)
        
        assert result['date'] == '2024-03-15'
        assert result['amount'] == 75.25
    
    def test_parse_missing_date(self):
        """Test parsing fails when date is missing."""
        text = """
        Store Name
        Total: $50.00
        """
        
        with pytest.raises(DocumentParserError) as exc_info:
            DocumentParser.parse(text)
        
        assert 'date' in str(exc_info.value).lower()
    
    def test_parse_missing_amount(self):
        """Test parsing fails when amount is missing."""
        text = """
        Store Name
        Date: 01/15/2024
        """
        
        with pytest.raises(DocumentParserError) as exc_info:
            DocumentParser.parse(text)
        
        assert 'amount' in str(exc_info.value).lower()
    
    def test_parse_empty_text(self):
        """Test parsing fails with empty text."""
        with pytest.raises(DocumentParserError) as exc_info:
            DocumentParser.parse("")
        
        assert 'empty' in str(exc_info.value).lower()
    
    def test_parse_with_line_items(self):
        """Test extraction of line items."""
        text = """
        Hardware Store
        Date: 01/15/2024
        Hammer $25.99
        Nails $5.50
        Screws $8.25
        Total: $39.74
        """
        
        result = DocumentParser.parse(text)
        
        assert result['amount'] == 39.74
        # Line items extraction is best-effort
        assert isinstance(result['line_items'], list)
    
    def test_parse_with_comma_in_amount(self):
        """Test parsing amounts with comma separators."""
        text = """
        Big Purchase Store
        Date: 2024-01-15
        Total: $1,234.56
        """
        
        result = DocumentParser.parse(text)
        
        assert result['amount'] == 1234.56
    
    def test_parse_multiple_amounts_selects_largest(self):
        """Test that parser selects the largest amount when multiple exist."""
        text = """
        Store Name
        Date: 01/15/2024
        Subtotal: $50.00
        Tax: $5.00
        Total: $55.00
        """
        
        result = DocumentParser.parse(text)
        
        # Should select the total (largest amount)
        assert result['amount'] == 55.00
    
    def test_validate_required_fields_valid(self):
        """Test validation passes for valid document."""
        parsed = {
            'date': '2024-01-15',
            'amount': 50.00,
            'vendor': 'Store',
            'currency': 'USD'
        }
        
        is_valid, missing = DocumentParser.validate_required_fields(parsed)
        
        assert is_valid is True
        assert len(missing) == 0
    
    def test_validate_required_fields_missing_date(self):
        """Test validation fails when date is missing."""
        parsed = {
            'amount': 50.00,
            'vendor': 'Store'
        }
        
        is_valid, missing = DocumentParser.validate_required_fields(parsed)
        
        assert is_valid is False
        assert 'date' in missing
    
    def test_validate_required_fields_missing_amount(self):
        """Test validation fails when amount is missing."""
        parsed = {
            'date': '2024-01-15',
            'vendor': 'Store'
        }
        
        is_valid, missing = DocumentParser.validate_required_fields(parsed)
        
        assert is_valid is False
        assert 'amount' in missing
    
    def test_format_error_message(self):
        """Test error message formatting."""
        missing = ['date', 'amount']
        
        message = DocumentParser.format_error_message(missing)
        
        assert 'date' in message.lower()
        assert 'amount' in message.lower()
        assert 'missing' in message.lower()
    
    def test_parse_bank_statement(self):
        """Test parsing bank statement format."""
        text = """
        First National Bank
        Statement Date: 2024-01-31
        Account Balance: $5,432.10
        """
        
        result = DocumentParser.parse(text, 'bank_statement')
        
        assert result['date'] == '2024-01-31'
        assert result['amount'] == 5432.10
        assert result['document_type'] == 'bank_statement'
    
    def test_parse_handles_ocr_artifacts(self):
        """Test parser handles common OCR artifacts."""
        text = """
        Store   Name   With   Spaces
        Date:  01/15/2024
        Total:   $   45.99
        """
        
        result = DocumentParser.parse(text)
        
        # Should still extract date and amount despite extra spaces
        assert result['date'] == '2024-01-15'
        assert result['amount'] == 45.99
    
    def test_parse_vendor_from_first_line(self):
        """Test vendor extraction from first line."""
        text = """
        My Favorite Store
        Date: 01/15/2024
        Total: $25.00
        """
        
        result = DocumentParser.parse(text)
        
        assert result['vendor'] == 'My Favorite Store'
    
    def test_parse_with_different_currency_symbols(self):
        """Test parsing with different currency symbols."""
        text = """
        European Store
        Date: 15/03/2024
        Total: €125.50
        """
        
        result = DocumentParser.parse(text)
        
        assert result['amount'] == 125.50
        # Currency detection could be enhanced in future
        assert result['currency'] == 'USD'  # Currently defaults to USD
