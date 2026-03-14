# Complete Testing Guide for AI Accounting Copilot

## Overview
This test dataset contains 34 realistic financial documents for AutoFix Repair Shop covering Q1 2024 (January-March). The documents are designed to test the full workflow from document upload through financial analysis.

## Quick Start

### Option 1: Upload via Script (Recommended)
```bash
cd test-documents
./upload-to-s3.sh
```

### Option 2: Upload via AWS CLI
```bash
cd test-documents
aws s3 sync invoices/ s3://accounting-copilot-documents-280250685594/documents/ --region eu-west-1
aws s3 sync expenses/ s3://accounting-copilot-documents-280250685594/documents/ --region eu-west-1
```

### Option 3: Upload via Web Interface
1. Go to http://accounting-copilot-web-280250685594.s3-website-eu-west-1.amazonaws.com
2. Navigate to Documents section
3. Upload files from `invoices/` and `expenses/` folders

## What to Test

### 1. Document Processing Workflow
**Expected Behavior:**
- S3 upload triggers workflow_trigger Lambda
- Step Functions workflow starts
- Textract extracts text from document
- Document classifier identifies type (invoice/expense)
- Transaction API creates transaction in DynamoDB
- Transaction appears in web interface

**How to Verify:**
- Check CloudWatch Logs for workflow_trigger
- View Step Functions execution history
- Check DynamoDB table for new transactions
- View transactions in web interface

### 2. Transaction Creation
**Expected Results:**
- 16 income transactions (customer invoices)
- 18 expense transactions
- Total: 34 transactions

**Verify:**
- All amounts extracted correctly
- Dates match invoice dates
- Categories assigned appropriately
- Vendor/customer names captured

### 3. Financial Assistant Queries

Try these queries to test the assistant:

**Revenue Analysis:**
- "What was my total revenue in Q1 2024?"
- "Show me revenue by month"
- "What's my average invoice amount?"
- "Which month had the highest revenue?"

**Expense Analysis:**
- "What are my top 5 expense categories?"
- "How much did I spend on parts suppliers?"
- "What's my total payroll cost for Q1?"
- "Show me all rent payments"

**Profitability:**
- "What's my profit margin for Q1?"
- "Calculate my net income for each month"
- "What's my break-even point?"
- "Am I profitable?"

**Specific Categories:**
- "How much did I spend on marketing?"
- "What are my facility costs?"
- "Show me all tire-related revenue"
- "What did I spend on tools and equipment?"

**Trends & Comparisons:**
- "Compare January vs February revenue"
- "What's my expense trend over Q1?"
- "Which service type generates the most revenue?"
- "How do my parts costs compare to revenue?"

### 4. Transaction Corrections

**Test Scenario:**
1. Find a transaction with incorrect category
2. Click "Correct" button
3. Change category or amount
4. Save correction
5. Verify change appears in transaction list
6. Check that assistant uses corrected data

### 5. Document Review

**Test Scenario:**
1. Navigate to Documents section
2. View uploaded documents
3. Check OCR extraction quality
4. Verify document classification
5. Review linked transactions

## Expected Financial Results

### Revenue Summary
- **Q1 Total:** ~$12,270
- **January:** ~$3,859 (6 invoices)
- **February:** ~$4,567 (7 invoices)
- **March:** ~$3,843 (3 invoices)
- **Average Invoice:** ~$767

### Expense Summary
- **Q1 Total:** ~$99,623
- **Payroll:** $59,772 (60%)
- **Facility:** $18,703 (19%)
- **Parts/Inventory:** $8,683 (9%)
- **Marketing:** $5,426 (5%)
- **Insurance:** $4,000 (4%)
- **Other:** $3,040 (3%)

### Top Expense Categories
1. Payroll & Benefits: $59,772
2. Rent: $15,600
3. Parts & Inventory: $8,683
4. Marketing: $5,426
5. Insurance: $4,000

### Service Type Revenue
- Tire Services: ~$2,485
- Major Services (timing belt, AC, etc.): ~$3,888
- Oil Changes & Maintenance: ~$2,442
- Brake Services: ~$1,499
- Diagnostics & Repairs: ~$1,956

## Monitoring & Troubleshooting

### CloudWatch Logs to Check
```bash
# Workflow trigger
aws logs tail /aws/lambda/workflow-trigger --follow --region eu-west-1

# Document processor
aws logs tail /aws/lambda/document-processor --follow --region eu-west-1

# Transaction API
aws logs tail /aws/lambda/transaction-api --follow --region eu-west-1

# Financial Assistant
aws logs tail /aws/lambda/financial-assistant --follow --region eu-west-1
```

### Common Issues

**Documents not processing:**
- Check S3 event notification configured for `documents/` prefix
- Verify workflow_trigger has correct environment variables
- Check Step Functions execution history for errors

**Transactions not appearing:**
- Check DynamoDB table directly
- Verify transaction_api Lambda permissions
- Check for errors in CloudWatch Logs

**Assistant not finding transactions:**
- Verify date range (default is last 10 years)
- Check transaction dates are in correct format
- Verify DynamoDB query is working

**Incorrect amounts:**
- Review Textract extraction in CloudWatch Logs
- Check document_processor parsing logic
- May need to adjust OCR confidence thresholds

## Success Criteria

✅ All 34 documents uploaded successfully
✅ All 34 transactions created in DynamoDB
✅ Transactions visible in web interface
✅ Financial Assistant can query transactions
✅ Revenue and expense totals match expected values
✅ Transaction corrections work properly
✅ Document classification is accurate (>90%)
✅ Amount extraction is accurate (>95%)

## Performance Benchmarks

- **Document Upload:** < 5 seconds per document
- **OCR Processing:** < 10 seconds per document
- **Transaction Creation:** < 2 seconds
- **Assistant Query:** < 5 seconds
- **End-to-End:** < 30 seconds from upload to queryable

## Next Steps After Testing

1. **Review Results:** Check accuracy of OCR and classification
2. **Tune Parameters:** Adjust confidence thresholds if needed
3. **Add More Documents:** Create additional test scenarios
4. **Test Edge Cases:** Try malformed documents, missing data
5. **Load Testing:** Upload many documents simultaneously
6. **User Acceptance:** Have repair shop owner test queries

## Additional Test Scenarios

### Edge Cases to Test
- Upload duplicate documents
- Upload non-financial documents
- Upload corrupted files
- Upload very large files
- Upload documents with poor image quality
- Upload handwritten receipts

### Advanced Queries
- "Show me customers who spent over $1000"
- "What's my cost per service hour?"
- "Calculate my parts markup percentage"
- "Which employees generated the most revenue?"
- "What's my customer acquisition cost?"

## Resources

- **Frontend:** http://accounting-copilot-web-280250685594.s3-website-eu-west-1.amazonaws.com
- **API:** https://l91194lhci.execute-api.eu-west-1.amazonaws.com/dev
- **Region:** eu-west-1
- **S3 Bucket:** accounting-copilot-documents-280250685594
- **DynamoDB Table:** accounting-copilot-transactions

## Support

If you encounter issues:
1. Check CloudWatch Logs for error messages
2. Verify AWS credentials and permissions
3. Review Step Functions execution history
4. Check DynamoDB table contents directly
5. Test API endpoints with curl/Postman
