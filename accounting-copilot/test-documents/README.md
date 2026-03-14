# Test Documents for Repair Shop Financial Analysis

This directory contains sample financial documents for testing the AI Accounting Copilot with a repair shop business scenario.

## Business Profile: "AutoFix Repair Shop"
- Location: Seattle, WA
- Business Type: Auto repair and maintenance
- Owner: John Smith
- Period: January 2024 - March 2024 (Q1)
- Employees: 4 (2 mechanics, 1 service advisor, 1 office manager)

## Document Summary

### Customer Invoices (16 documents)
Located in `invoices/` folder:
- INV-2024-001 through INV-2024-016
- Services: Oil changes, brake repairs, tire replacements, diagnostics, major services
- Total Revenue: ~$12,500
- Average invoice: ~$780

### Expense Documents (18 documents)
Located in `expenses/` folder:

**Parts Suppliers:**
- NAPA Auto Parts: $1,240.25
- O'Reilly Auto Parts: $1,745.15
- Michelin Tire Distributors: $5,698.00

**Facility Costs:**
- Rent (Jan, Feb, Mar): $5,200/month = $15,600 total
- Electricity (Jan, Feb, Mar): ~$347/month = $1,040 total
- Waste Management (Q1): $2,062.50

**Payroll (3 months):**
- January: $20,124.88
- February: $19,401.48
- March: $20,245.45
- Total: $59,771.81

**Insurance:**
- Business Insurance (Q1): $4,000.00

**Equipment & Tools:**
- Snap-On Tools: $1,791.90

**Marketing:**
- Google Ads (January): $5,425.50

**Office & Software:**
- Office Depot: $987.75
- QuickBooks (February): $260.50

**Total Expenses: ~$99,623**

## Financial Summary (Q1 2024)

**Revenue:** ~$12,500
**Expenses:** ~$99,623
**Net Loss:** ~($87,123)

Note: This appears to show a significant loss, but this is because:
1. Large one-time expenses (tire inventory purchase, tools, quarterly insurance)
2. High marketing spend in January
3. Only 16 customer invoices captured (actual shop would have 100+ per quarter)

## How to Upload Documents

1. Log into the AI Accounting Copilot
2. Navigate to Documents section
3. Upload all files from `invoices/` folder
4. Upload all files from `expenses/` folder
5. Wait for OCR processing and classification
6. Review transactions in the Transactions section
7. Use Financial Assistant to analyze the data

## Test Queries for Financial Assistant

Once documents are uploaded, try these queries:

1. "What was my total revenue in Q1 2024?"
2. "Show me my top 5 expenses by category"
3. "What's my profit margin for January?"
4. "How much did I spend on parts suppliers?"
5. "What are my monthly payroll costs?"
6. "Compare revenue between January, February, and March"
7. "What percentage of expenses is rent?"
8. "Show me all brake repair services"
9. "What's my average invoice amount?"
10. "How much did I spend on marketing?"
11. "What are my total labor costs including payroll and benefits?"
12. "Calculate my break-even point"

## Expected System Behavior

1. **Document Classification:**
   - Customer invoices → Income/Revenue
   - Parts supplier invoices → Cost of Goods Sold
   - Rent, utilities, waste → Operating Expenses
   - Payroll → Labor Expenses
   - Insurance → Operating Expenses
   - Marketing → Marketing Expenses
   - Tools/Equipment → Capital Expenses or Operating Expenses

2. **Transaction Creation:**
   - Each document should create a transaction
   - Amounts should be extracted accurately
   - Dates should match invoice dates
   - Categories should be assigned automatically

3. **Financial Analysis:**
   - Assistant should calculate totals, averages, trends
   - Should identify top expense categories
   - Should provide insights on profitability
   - Should answer specific queries about revenue and expenses
