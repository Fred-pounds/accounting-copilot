# Frontend Integration Tests

This directory contains comprehensive integration tests for the AI Accounting Copilot frontend application.

## Test Coverage

### 1. Authentication Flow (`authentication.test.tsx`)
**Validates: Requirements 1.1, 5.6, 6.1, 8.4**

Tests:
- Login form rendering
- Successful authentication with valid credentials
- Error handling for invalid credentials
- Loading states during authentication
- Session timeout handling
- Redirect behavior for authenticated users
- Form validation
- Network error handling

### 2. Document Upload Flow (`documentUpload.test.tsx`)
**Validates: Requirement 1.1 - Document capture and OCR processing**

Tests:
- Upload dropzone rendering
- Single file upload
- Multiple file uploads
- File size validation (max 10 MB)
- File type validation (JPEG, PNG, PDF)
- Upload progress tracking
- Success and error handling
- Visual feedback during drag operations

### 3. Dashboard Rendering (`dashboard.test.tsx`)
**Validates: Requirement 5.6 - Dashboard loads within 3 seconds**
**Validates: Requirement 8.4 - Display pending approvals on dashboard**

Tests:
- Summary cards rendering (cash balance, income, expenses, profit)
- Financial data accuracy
- Load time performance (< 3 seconds)
- Pending approvals badge display
- Profit trend chart rendering (6 months)
- Top 5 expense categories chart
- Loading states
- Error handling and retry functionality
- Auto-refresh every 60 seconds
- Color coding for positive/negative values

### 4. Transaction Approval Flow (`transactionApproval.test.tsx`)
**Validates: Requirement 8.4 - Display pending approvals on dashboard**

Tests:
- Transaction list rendering
- Status badge display
- Filtering by status, type, and category
- Sorting by date and amount
- Confidence score display with color coding
- Approve button visibility for pending transactions
- Transaction approval action
- Transaction detail modal
- Approvals page rendering
- Approval type badges
- Approve and reject actions
- Empty state display
- Approval detail modal

### 5. Assistant Chat Interaction (`assistantChat.test.tsx`)
**Validates: Requirement 6.1 - Assistant responds within 5 seconds**

Tests:
- Assistant interface rendering
- Welcome message and example questions
- Conversation history loading
- Sending questions and receiving responses
- Response time validation (< 5 seconds)
- Loading indicator during response
- Input field clearing after submission
- Send button enable/disable logic
- Citations display with responses
- Confidence score display
- Error handling
- Empty message prevention
- Loading state message prevention
- Auto-scroll to bottom
- Message timestamps
- Visual distinction between user and assistant messages
- Form submission with Enter key

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run specific test file
npm test authentication.test.tsx
```

## Test Infrastructure

### Mock Service Worker (MSW)
All API calls are mocked using MSW to provide consistent, fast, and reliable test execution without requiring a backend server.

### Mock Data
Comprehensive mock data is provided in `mocks/mockData.ts` including:
- User profiles
- Transactions
- Documents
- Dashboard summaries
- Pending approvals
- Conversation history

### Test Utilities
Custom render function in `utils/testUtils.tsx` that wraps components with necessary providers:
- BrowserRouter for routing
- AuthProvider for authentication context

## Requirements Validation

| Requirement | Test File | Status |
|-------------|-----------|--------|
| 1.1 - Document capture and OCR | documentUpload.test.tsx | ✅ Covered |
| 5.6 - Dashboard loads < 3s | dashboard.test.tsx | ✅ Covered |
| 6.1 - Assistant responds < 5s | assistantChat.test.tsx | ✅ Covered |
| 8.4 - Display pending approvals | dashboard.test.tsx, transactionApproval.test.tsx | ✅ Covered |

## Notes

- Tests use fake timers for time-dependent functionality
- ResizeObserver is mocked for Recharts compatibility
- scrollIntoView is mocked for auto-scroll functionality
- Cognito authentication is mocked to avoid external dependencies
