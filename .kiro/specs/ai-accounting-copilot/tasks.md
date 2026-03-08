# Implementation Plan: AI Accounting Copilot

## Overview

This implementation plan breaks down the AI Accounting Copilot into discrete coding tasks. The system is built using AWS serverless architecture with Python 3.11 Lambda functions, DynamoDB for data storage, S3 for document storage, API Gateway for REST endpoints, Step Functions for workflow orchestration, and AWS AI services (Textract for OCR, Bedrock for classification and conversational AI).

The implementation follows an incremental approach: infrastructure setup → core data models → document processing → classification → validation → reconciliation → dashboard API → financial assistant → audit trail → approvals → frontend integration.

## Tasks

- [x] 1. Set up AWS infrastructure and project structure
  - Create CloudFormation/Terraform templates for all AWS resources
  - Set up S3 buckets (documents, static website) with encryption and lifecycle policies
  - Configure DynamoDB table with GSI indexes for query patterns
  - Set up Cognito user pool with password policies and JWT configuration
  - Configure API Gateway with CORS, rate limiting, and Cognito authorizer
  - Set up SNS topics for notifications (pending-approvals, ocr-failures, unmatched-transactions, approval-reminders)
  - Configure CloudWatch log groups and alarms for monitoring
  - Create IAM roles and policies for Lambda execution
  - Set up Python project structure with shared libraries and utilities
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 2. Implement core data models and DynamoDB access layer
  - [x] 2.1 Create DynamoDB entity models and serialization
    - Implement entity classes for User, Document, Transaction, BankTransaction, AuditEntry, PendingApproval, ConversationMessage, CategoryStats
    - Write serialization/deserialization functions for DynamoDB format
    - Implement partition key (PK) and sort key (SK) generation functions
    - Implement GSI key generation for query access patterns
    - _Requirements: 1.5, 2.6, 4.6, 7.1, 7.2, 7.3_

  - [ ]* 2.2 Write property test for data model round-trip
    - **Property 2: Document Storage Round-Trip**
    - **Validates: Requirements 1.5**

  - [x] 2.3 Create DynamoDB repository layer
    - Implement CRUD operations for all entity types
    - Implement query functions using GSI indexes (by category, by date, by status)
    - Implement batch write operations for performance
    - Add error handling for throttling and conditional check failures
    - _Requirements: 1.5, 7.5_

  - [ ]* 2.4 Write unit tests for DynamoDB operations
    - Test CRUD operations with moto mocks
    - Test query patterns and pagination
    - Test error handling for throttling scenarios
    - _Requirements: 1.5_

- [x] 3. Implement document upload and storage
  - [x] 3.1 Create document upload Lambda handler
    - Validate file type (JPEG, PNG, PDF) and size (< 10 MB)
    - Generate unique document ID and S3 key
    - Generate pre-signed S3 upload URL with 15-minute expiration
    - Store document metadata in DynamoDB
    - Initiate Step Functions workflow for processing
    - Return document ID and upload URL to client
    - _Requirements: 1.1, 1.3, 1.5, 10.1_

  - [ ]* 3.2 Write unit tests for upload handler
    - Test file validation (valid and invalid types/sizes)
    - Test S3 pre-signed URL generation
    - Test DynamoDB metadata storage
    - Test Step Functions workflow initiation
    - _Requirements: 1.1, 1.3_

- [x] 4. Implement OCR processing with Textract
  - [x] 4.1 Create OCR processor Lambda function
    - Call Textract DetectDocumentText API with document from S3
    - Parse Textract response to extract text blocks
    - Implement retry logic with exponential backoff
    - Handle OCR failures gracefully with SNS notification
    - Update document status in DynamoDB
    - _Requirements: 1.1, 1.4_

  - [x] 4.2 Implement document parser for structured field extraction
    - Parse extracted text to identify date, amount, vendor, line items
    - Support multiple document formats (receipts, invoices, bank statements)
    - Handle missing or malformed fields with descriptive errors
    - Validate required fields (date, amount, type) are present
    - _Requirements: 1.2, 9.1, 9.2, 9.5_

  - [ ]* 4.3 Write property test for document parsing
    - **Property 1: Document Parsing Produces Structured Fields**
    - **Validates: Requirements 1.2**

  - [ ]* 4.4 Write property test for parser error handling
    - **Property 27: Parser Error Handling**
    - **Validates: Requirements 9.2**

  - [ ]* 4.5 Write property test for required field validation
    - **Property 28: Required Field Validation**
    - **Validates: Requirements 9.5**

  - [ ]* 4.6 Write property test for parsing round-trip
    - **Property 26: Document Parsing Round-Trip**
    - **Validates: Requirements 9.4**

  - [ ]* 4.7 Write property test for OCR failure notification
    - **Property 3: OCR Failure Notification**
    - **Validates: Requirements 1.4**

  - [ ]* 4.8 Write unit tests for OCR processor
    - Test Textract API integration with mocked responses
    - Test retry logic and error handling
    - Test SNS notification on failure
    - _Requirements: 1.1, 1.4_

- [x] 5. Checkpoint - Ensure document upload and OCR tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement transaction classification with Bedrock
  - [x] 6.1 Create transaction classifier Lambda function
    - Build classification prompt template with transaction details and category list
    - Call Bedrock Claude 3 Haiku model with prompt
    - Parse JSON response to extract category, confidence score, and reasoning
    - Implement retry logic with exponential backoff for Bedrock failures
    - Implement fallback rule-based classification if Bedrock unavailable
    - Store classification result in DynamoDB
    - Flag transactions with confidence < 0.7 for review
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [ ]* 6.2 Write property test for confidence score validity
    - **Property 4: Classification Confidence Score Validity**
    - **Validates: Requirements 2.2**

  - [ ]* 6.3 Write property test for low confidence flagging
    - **Property 5: Low Confidence Flagging**
    - **Validates: Requirements 2.3**

  - [ ]* 6.4 Write property test for custom category support
    - **Property 6: Custom Category Support**
    - **Validates: Requirements 2.5**

  - [ ]* 6.5 Write unit tests for classifier
    - Test Bedrock API integration with mocked responses
    - Test prompt template generation
    - Test confidence score calculation
    - Test flagging logic for low confidence
    - Test fallback classification
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 7. Implement data validation engine
  - [x] 7.1 Create data validator Lambda function
    - Implement duplicate detection (same amount, vendor, date within 24 hours)
    - Query DynamoDB for potential duplicates using date range and amount
    - Implement outlier detection (> 3 standard deviations from category average)
    - Query category statistics from DynamoDB
    - Calculate z-score for transaction amount
    - Implement sequential invoice number gap detection
    - Query transactions by vendor and extract invoice numbers
    - Identify missing numbers in sequence
    - Flag transactions with validation issues for review
    - Send SNS notifications for detected issues
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 7.2 Write property test for duplicate detection
    - **Property 7: Duplicate Detection**
    - **Validates: Requirements 3.1**

  - [ ]* 7.3 Write property test for outlier detection
    - **Property 8: Outlier Detection**
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 7.4 Write property test for invoice gap detection
    - **Property 9: Sequential Invoice Gap Detection**
    - **Validates: Requirements 3.5**

  - [ ]* 7.5 Write property test for issue notification
    - **Property 10: Issue Notification**
    - **Validates: Requirements 3.2, 3.6, 4.5**

  - [ ]* 7.6 Write unit tests for validator
    - Test duplicate detection with various scenarios
    - Test outlier detection with statistical calculations
    - Test invoice gap detection with sequences
    - Test SNS notification sending
    - _Requirements: 3.1, 3.3, 3.5_

- [x] 8. Implement reconciliation engine
  - [x] 8.1 Create reconciliation Lambda function
    - Implement fuzzy matching algorithm for receipts and bank transactions
    - Calculate amount similarity (±5% tolerance) with 40% weight
    - Calculate date proximity (±3 days) with 30% weight
    - Calculate vendor name similarity using Levenshtein distance with 30% weight
    - Compute overall match confidence score
    - Auto-link matches with confidence > 0.8
    - Flag matches with confidence 0.5-0.8 for approval
    - Identify unmatched bank transactions > 7 days old
    - Send SNS notifications for unmatched transactions
    - Update reconciliation status in DynamoDB
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 8.2 Write property test for high confidence auto-matching
    - **Property 11: High Confidence Auto-Matching**
    - **Validates: Requirements 4.2**

  - [ ]* 8.3 Write property test for medium confidence approval requirement
    - **Property 12: Medium Confidence Approval Requirement**
    - **Validates: Requirements 4.3**

  - [ ]* 8.4 Write property test for unmatched transaction identification
    - **Property 13: Unmatched Transaction Identification**
    - **Validates: Requirements 4.4**

  - [ ]* 8.5 Write unit tests for reconciliation engine
    - Test fuzzy matching algorithm with various scenarios
    - Test confidence score calculation
    - Test auto-linking and flagging logic
    - Test unmatched transaction identification
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 9. Checkpoint - Ensure classification, validation, and reconciliation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Step Functions workflow orchestration
  - [x] 10.1 Create Step Functions state machine definition
    - Define states: ExtractText, ClassifyTransaction, ValidateData, CheckConfidence, FlagForReview, NotifyPendingApproval, ReconcileReceipts, LogAuditTrail, NotifyOCRFailure
    - Configure retry policies for transient failures
    - Configure catch blocks for error handling
    - Add SNS notification tasks for failures and pending approvals
    - _Requirements: 1.1, 1.4, 2.1, 2.3, 3.1, 4.1_

  - [ ]* 10.2 Write integration tests for Step Functions workflow
    - Test successful document processing flow
    - Test OCR failure handling
    - Test low confidence flagging flow
    - Test error handling and retries
    - _Requirements: 1.1, 2.1, 3.1_

- [x] 11. Implement audit trail logging
  - [x] 11.1 Create audit logger Lambda function
    - Accept audit entry parameters (action_type, actor, subject, details)
    - Generate unique audit entry ID and timestamp
    - Store audit entry in DynamoDB with proper PK/SK
    - Support batch writes for performance
    - _Requirements: 2.6, 4.6, 6.6, 7.1, 7.2, 7.3, 10.6_

  - [x] 11.2 Integrate audit logging into all AI actions
    - Add audit logging calls to classifier Lambda
    - Add audit logging calls to reconciliation Lambda
    - Add audit logging calls to financial assistant Lambda
    - Include confidence scores and reasoning in audit details
    - _Requirements: 2.6, 4.6, 6.6, 7.1, 7.2, 7.3_

  - [ ]* 11.3 Write property test for comprehensive audit trail
    - **Property 19: Comprehensive Audit Trail**
    - **Validates: Requirements 2.6, 4.6, 6.6, 7.1, 7.2, 7.3, 10.6**

  - [ ]* 11.4 Write unit tests for audit logger
    - Test audit entry creation
    - Test batch write operations
    - Test integration with other Lambda functions
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 12. Implement dashboard API
  - [x] 12.1 Create dashboard API Lambda function
    - Implement GET /dashboard/summary endpoint
    - Query DynamoDB for user transactions
    - Calculate current cash balance (sum of income - sum of expenses)
    - Calculate total income for current month
    - Calculate total expenses for current month
    - Calculate monthly profit for last 6 months
    - Identify top 5 expense categories by total amount
    - Return dashboard data with < 3 second response time
    - Enable API Gateway caching with 5-minute TTL
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 12.2 Write property test for transaction aggregation accuracy
    - **Property 14: Transaction Aggregation Accuracy**
    - **Validates: Requirements 5.2, 5.3**

  - [ ]* 12.3 Write property test for profit trend calculation
    - **Property 15: Profit Trend Calculation**
    - **Validates: Requirements 5.4**

  - [ ]* 12.4 Write property test for top categories ranking
    - **Property 16: Top Categories Ranking**
    - **Validates: Requirements 5.5**

  - [ ]* 12.5 Write unit tests for dashboard API
    - Test cash balance calculation
    - Test income and expense aggregation
    - Test profit trend calculation
    - Test top categories ranking
    - Test API Gateway caching
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 12.6 Write performance tests for dashboard load time
    - Test dashboard loads within 3 seconds with 100 transactions
    - _Requirements: 5.6_

- [x] 13. Implement financial assistant with Bedrock
  - [x] 13.1 Create financial assistant Lambda function
    - Implement POST /assistant/query endpoint
    - Parse user question from request
    - Query relevant transaction data from DynamoDB based on question context
    - Build conversation context with last 10 turns
    - Build prompt template with transaction data and conversation history
    - Call Bedrock Claude 3 Haiku model with prompt
    - Parse response and extract citations to transactions
    - Handle insufficient data scenarios with explanatory messages
    - Store conversation message in DynamoDB
    - Return response within 5 seconds
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 13.2 Write property test for assistant response citations
    - **Property 17: Assistant Response Citations**
    - **Validates: Requirements 6.3**

  - [ ]* 13.3 Write property test for insufficient data explanation
    - **Property 18: Insufficient Data Explanation**
    - **Validates: Requirements 6.4**

  - [ ]* 13.4 Write unit tests for financial assistant
    - Test question parsing
    - Test transaction data retrieval
    - Test Bedrock API integration
    - Test citation extraction
    - Test insufficient data handling
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 13.5 Write performance tests for assistant response time
    - Test assistant responds within 5 seconds
    - _Requirements: 6.1_

- [x] 14. Checkpoint - Ensure dashboard and assistant tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement audit trail query and export APIs
  - [x] 15.1 Create audit trail API Lambda function
    - Implement GET /audit-trail endpoint with filtering
    - Support filters: date range, action type, transaction ID
    - Query DynamoDB with appropriate filters
    - Implement pagination for large result sets
    - Return filtered audit entries
    - _Requirements: 7.4_

  - [x] 15.2 Implement audit trail CSV export
    - Implement GET /audit-trail/export endpoint
    - Query all audit entries for user
    - Format entries as CSV with headers
    - Return CSV file with proper content-type header
    - _Requirements: 7.6_

  - [ ]* 15.3 Write property test for audit trail filtering
    - **Property 20: Audit Trail Filtering**
    - **Validates: Requirements 7.4**

  - [ ]* 15.4 Write property test for CSV export round-trip
    - **Property 21: Audit Trail CSV Export**
    - **Validates: Requirements 7.6**

  - [ ]* 15.5 Write unit tests for audit trail API
    - Test filtering by date range
    - Test filtering by action type
    - Test filtering by transaction ID
    - Test pagination
    - Test CSV export format
    - _Requirements: 7.4, 7.6_

- [x] 16. Implement approval workflow
  - [x] 16.1 Create approval management Lambda functions
    - Implement logic to detect large transactions (> 10% of average monthly expenses)
    - Implement logic to detect new vendors
    - Implement logic to detect bulk reclassification operations (>= 2 transactions)
    - Create pending approval records in DynamoDB
    - Implement GET /approvals/pending endpoint to list pending approvals
    - Implement POST /approvals/{id}/approve endpoint
    - Implement POST /approvals/{id}/reject endpoint
    - Update transaction status after approval/rejection
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 16.2 Implement approval reminder system
    - Create scheduled Lambda function (runs daily)
    - Query pending approvals older than 48 hours
    - Send SNS reminder notifications for each pending approval
    - Update reminder_sent_at timestamp in DynamoDB
    - _Requirements: 8.5_

  - [ ]* 16.3 Write property test for large transaction approval requirement
    - **Property 22: Large Transaction Approval Requirement**
    - **Validates: Requirements 8.1**

  - [ ]* 16.4 Write property test for new vendor approval requirement
    - **Property 23: New Vendor Approval Requirement**
    - **Validates: Requirements 8.2**

  - [ ]* 16.5 Write property test for bulk reclassification approval
    - **Property 24: Bulk Reclassification Approval**
    - **Validates: Requirements 8.3**

  - [ ]* 16.6 Write property test for approval reminder timing
    - **Property 25: Approval Reminder Timing**
    - **Validates: Requirements 8.5**

  - [ ]* 16.7 Write unit tests for approval workflow
    - Test large transaction detection
    - Test new vendor detection
    - Test bulk reclassification detection
    - Test approval and rejection flows
    - Test reminder scheduling
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [x] 17. Implement transaction CRUD APIs
  - [x] 17.1 Create transaction API Lambda function
    - Implement POST /transactions endpoint for manual transaction creation
    - Implement GET /transactions/{id} endpoint
    - Implement GET /transactions endpoint with filtering and pagination
    - Implement PUT /transactions/{id} endpoint for updates
    - Implement DELETE /transactions/{id} endpoint
    - Implement POST /transactions/{id}/approve endpoint for flagged transactions
    - Implement POST /transactions/{id}/correct endpoint for classification corrections
    - Update category statistics after transaction changes
    - _Requirements: 2.4, 3.1, 4.1_

  - [ ]* 17.2 Write unit tests for transaction APIs
    - Test CRUD operations
    - Test filtering and pagination
    - Test approval flow
    - Test correction flow
    - _Requirements: 2.4_

- [x] 18. Implement document retrieval APIs
  - [x] 18.1 Create document API Lambda function
    - Implement GET /documents/{id} endpoint
    - Retrieve document metadata from DynamoDB
    - Generate pre-signed S3 download URL with 5-minute expiration
    - Return document details with download URL
    - Implement GET /documents endpoint with pagination
    - _Requirements: 1.5, 10.1_

  - [ ]* 18.2 Write unit tests for document APIs
    - Test document retrieval
    - Test pre-signed URL generation
    - Test pagination
    - _Requirements: 1.5_

- [x] 19. Implement authentication and authorization
  - [x] 19.1 Create authentication utilities
    - Implement JWT token validation function using Cognito JWKS
    - Implement token expiration checking
    - Implement user ID extraction from token
    - Create Lambda authorizer for API Gateway
    - Implement session timeout logic (15 minutes inactivity)
    - _Requirements: 10.4, 10.5_

  - [x] 19.2 Add authorization checks to all Lambda functions
    - Verify user can only access their own data
    - Check PK starts with USER#{user_id} from token
    - Return 403 Forbidden for unauthorized access attempts
    - Log all data access attempts to audit trail
    - _Requirements: 10.4, 10.6_

  - [ ]* 19.3 Write property test for authentication requirement
    - **Property 29: Authentication Requirement**
    - **Validates: Requirements 10.4**

  - [ ]* 19.4 Write property test for session timeout
    - **Property 30: Session Timeout**
    - **Validates: Requirements 10.5**

  - [ ]* 19.5 Write unit tests for authentication
    - Test JWT validation with valid and invalid tokens
    - Test token expiration checking
    - Test user ID extraction
    - Test authorization checks
    - _Requirements: 10.4, 10.5_

- [x] 20. Checkpoint - Ensure all backend APIs and security tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Implement error handling and monitoring
  - [x] 21.1 Add comprehensive error handling to all Lambda functions
    - Implement custom exception classes (ValidationError, NotFoundError, AuthenticationError)
    - Add try-catch blocks with proper error responses
    - Return consistent error JSON format with error code, message, details, request_id, timestamp
    - Log errors to CloudWatch with appropriate severity levels
    - _Requirements: 9.2_

  - [x] 21.2 Configure CloudWatch alarms and dashboards
    - Create alarms for Lambda error rates > 5%
    - Create alarms for API Gateway 5xx errors > 10/minute
    - Create alarms for DynamoDB throttling events
    - Create alarms for Textract failure rate > 20%
    - Create alarms for Step Functions execution failures > 5/hour
    - Create CloudWatch dashboard with key metrics
    - _Requirements: 1.4, 3.2, 3.6, 4.5_

  - [x] 21.3 Enable AWS X-Ray tracing
    - Add X-Ray SDK to all Lambda functions
    - Patch boto3 clients for automatic tracing
    - Add custom subsegments for key operations
    - _Requirements: Performance monitoring_

  - [ ]* 21.4 Write unit tests for error handling
    - Test error response format
    - Test error logging
    - Test exception handling for various error types
    - _Requirements: 9.2_

- [x] 22. Implement category statistics maintenance
  - [x] 22.1 Create category statistics updater Lambda function
    - Trigger on transaction create/update/delete events
    - Calculate transaction count, total, average, std deviation, min, max for category
    - Update category statistics record in DynamoDB
    - Run as scheduled job (daily) to recalculate all statistics
    - _Requirements: 3.3, 3.4_

  - [ ]* 22.2 Write unit tests for statistics updater
    - Test statistics calculation
    - Test incremental updates
    - Test batch recalculation
    - _Requirements: 3.3_

- [x] 23. Build React frontend application
  - [x] 23.1 Set up React project with routing and state management
    - Initialize React app with TypeScript
    - Configure React Router for navigation
    - Set up Redux or Context API for state management
    - Configure Axios for API calls with authentication interceptors
    - _Requirements: 5.1, 5.6_npm --version
Waiting on your input
￼Reject
￼Trust
￼R

  - [x] 23.2 Implement authentication UI
    - Create login page with Cognito integration
    - Implement JWT token storage and refresh
    - Implement automatic logout on session timeout
    - Create protected route wrapper component
    - _Requirements: 10.4, 10.5_

  - [x] 23.3 Implement document upload UI
    - Create file upload component with drag-and-drop
    - Validate file type and size on client side
    - Upload to S3 using pre-signed URL
    - Display upload progress
    - Show processing status
    - _Requirements: 1.1, 1.3_

  - [x] 23.4 Implement dashboard UI
    - Create dashboard layout with summary cards
    - Display cash balance, income, expenses
    - Create profit trend line chart using Chart.js or Recharts
    - Create top categories bar chart
    - Implement auto-refresh every 60 seconds
    - Display pending approvals count badge
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 8.4_

  - [x] 23.5 Implement transaction list and detail UI
    - Create transaction list with filtering and sorting
    - Display transaction details in modal or detail page
    - Show classification confidence and reasoning
    - Show reconciliation status
    - Implement approve and correct actions for flagged transactions
    - _Requirements: 2.2, 2.3, 4.2, 4.3_

  - [x] 23.6 Implement financial assistant chat UI
    - Create chat interface with message history
    - Display user questions and assistant responses
    - Highlight citations as clickable links to transactions
    - Show loading indicator during response generation
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 23.7 Implement audit trail UI
    - Create audit trail list with filtering
    - Support filters: date range, action type, transaction
    - Display audit entry details (timestamp, actor, action, confidence)
    - Implement CSV export button
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [x] 23.8 Implement approvals UI
    - Create pending approvals list
    - Display approval details (reason, amount, vendor)
    - Implement approve and reject buttons
    - Show approval history
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 23.9 Write frontend integration tests
    - Test authentication flow
    - Test document upload flow
    - Test dashboard rendering
    - Test transaction approval flow
    - Test assistant chat interaction
    - _Requirements: 1.1, 5.6, 6.1, 8.4_

- [x] 24. Deploy frontend to S3 and CloudFront
  - [x] 24.1 Build and deploy frontend application
    - Build React app for production
    - Upload build artifacts to S3 static website bucket
    - Configure CloudFront distribution with S3 origin
    - Set up custom error responses for SPA routing
    - Configure SSL/TLS certificate
    - Invalidate CloudFront cache after deployment
    - _Requirements: 10.3_

  - [ ]* 24.2 Test frontend deployment
    - Test website loads via CloudFront URL
    - Test HTTPS redirect
    - Test SPA routing works correctly
    - _Requirements: 10.3_

- [x] 25. Implement deployment automation
  - [x] 25.1 Create deployment scripts
    - Create script to build Lambda deployment packages
    - Create script to deploy Lambda functions
    - Create script to deploy CloudFormation stack
    - Create script to build and deploy frontend
    - _Requirements: Infrastructure_

  - [x] 25.2 Set up CI/CD pipeline with GitHub Actions
    - Create workflow for running tests on push
    - Create workflow for deploying to staging on merge to main
    - Create workflow for deploying to production with manual approval
    - Configure AWS credentials as GitHub secrets
    - _Requirements: Infrastructure_

- [x] 26. Final checkpoint - End-to-end testing and validation
  - Run complete end-to-end test: upload document → OCR → classify → validate → reconcile → view dashboard → ask assistant → check audit trail
  - Verify all 30 correctness properties pass
  - Verify all performance requirements met (OCR < 5s, classification < 2s, dashboard < 3s, assistant < 5s)
  - Verify all security requirements met (encryption, authentication, session timeout)
  - Verify CloudWatch alarms configured correctly
  - Verify SNS notifications working
  - Ask the user if any issues or questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python 3.11 for all Lambda functions
- AWS services used: S3, CloudFront, Cognito, API Gateway, Lambda, DynamoDB, Step Functions, SNS, CloudWatch, Textract, Bedrock
- Estimated monthly cost: $2-6 for typical SME usage (100-200 documents/month)
- All AWS Free Tier limits are considered in the design
