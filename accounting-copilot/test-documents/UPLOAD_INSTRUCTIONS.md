# How to Upload Test Documents to AWS

## Prerequisites
- AWS CLI configured with credentials for eu-west-1 region
- S3 bucket name: accounting-copilot-documents-280250685594

## Upload Commands

### Upload All Customer Invoices
```bash
cd test-documents
aws s3 cp invoices/ s3://accounting-copilot-documents-280250685594/documents/ --recursive --region eu-west-1
```

### Upload All Expense Documents
```bash
aws s3 cp expenses/ s3://accounting-copilot-documents-280250685594/documents/ --recursive --region eu-west-1
```

### Upload Everything at Once
```bash
cd test-documents
aws s3 sync . s3://accounting-copilot-documents-280250685594/documents/ --exclude "*.md" --region eu-west-1
```

## Verify Upload
```bash
aws s3 ls s3://accounting-copilot-documents-280250685594/documents/ --recursive --region eu-west-1
```

## Expected Results

After upload, the Step Functions workflow should:
1. Trigger automatically for each document
2. Process OCR via Textract
3. Classify document type (invoice vs expense)
4. Extract key information (amount, date, vendor)
5. Create transaction in DynamoDB
6. Send to approval queue if needed

## Monitor Processing

Check CloudWatch Logs for:
- `workflow_trigger` Lambda logs
- `document_processor` Lambda logs
- `transaction_api` Lambda logs
- Step Functions execution logs

## Troubleshooting

If documents don't process:
1. Check S3 event notification is configured for `documents/` prefix
2. Verify workflow_trigger Lambda has correct environment variables
3. Check Step Functions execution history
4. Review CloudWatch Logs for errors

## Alternative: Upload via Frontend

You can also upload documents through the web interface:
1. Go to http://accounting-copilot-web-280250685594.s3-website-eu-west-1.amazonaws.com
2. Navigate to Documents section
3. Click "Upload Document"
4. Select files from `invoices/` and `expenses/` folders
5. Upload one at a time or in batches
