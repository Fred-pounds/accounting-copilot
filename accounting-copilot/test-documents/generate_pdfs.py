"""Generate 5 income (invoice) PDFs and 5 expense PDFs for upload testing."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def make_doc(filename):
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    return doc, path

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', fontSize=16, fontName='Helvetica-Bold', spaceAfter=2)
H2 = ParagraphStyle('H2', fontSize=11, fontName='Helvetica-Bold', spaceAfter=2)
BODY = ParagraphStyle('BODY', fontSize=9, fontName='Helvetica', spaceAfter=2, leading=13)
SMALL = ParagraphStyle('SMALL', fontSize=8, fontName='Helvetica', textColor=colors.grey)
RIGHT = ParagraphStyle('RIGHT', fontSize=9, fontName='Helvetica', alignment=TA_RIGHT)
CENTER = ParagraphStyle('CENTER', fontSize=9, fontName='Helvetica', alignment=TA_CENTER)

def hr(): return HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=6, spaceBefore=6)
def sp(h=6): return Spacer(1, h)

def line_table(rows, col_widths, header_row=True):
    t = Table(rows, colWidths=col_widths)
    style = [
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.lightgrey),
    ]
    if header_row:
        style += [
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.95,0.95,0.97)),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.Color(0.6,0.6,0.8)),
        ]
    t.setStyle(TableStyle(style))
    return t

def total_table(rows):
    t = Table(rows, colWidths=[4.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 10),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,-1), (-1,-1), colors.Color(0.93,0.97,0.93)),
    ]))
    return t

# ─────────────────────────────────────────────
# INCOME DOCUMENTS (5 invoices)
# ─────────────────────────────────────────────

def income_1():
    doc, path = make_doc("invoices/INV-2024-017.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-017", H2),
        Paragraph("Date: April 5, 2024 &nbsp;&nbsp; Due Date: April 20, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Marcus Thompson | 88 Lakeview Blvd, Seattle, WA 98105 | (206) 555-2211", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2020 Toyota Camry | VIN: 4T1B11HK5LU123456 | Mileage: 41,200", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Full Synthetic Oil Change (5W-30)", "1", "$89.00", "$89.00"],
            ["Tire Rotation & Balance", "1", "$65.00", "$65.00"],
            ["Cabin Air Filter Replacement", "1", "$55.00", "$55.00"],
            ["Multi-Point Inspection", "1", "$45.00", "$45.00"],
            ["Labor (1.5 hrs @ $95/hr)", "1.5", "$95.00", "$142.50"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$396.50"],
            ["Sales Tax (10%):", "$39.65"],
            ["TOTAL DUE:", "$436.15"],
        ]),
        sp(),
        Paragraph("Payment Method: Credit Card &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_2():
    doc, path = make_doc("invoices/INV-2024-018.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-018", H2),
        Paragraph("Date: April 11, 2024 &nbsp;&nbsp; Due Date: April 26, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Priya Nair | 14 Birchwood Ave, Bellevue, WA 98004 | (425) 555-7733", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2018 Honda Accord | VIN: 1HGCV1F34JA045678 | Mileage: 67,800", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Brake Pad Replacement (Front)", "1", "$220.00", "$220.00"],
            ["Brake Rotor Resurfacing (Front)", "1", "$110.00", "$110.00"],
            ["Brake Fluid Flush", "1", "$75.00", "$75.00"],
            ["Labor (3 hrs @ $95/hr)", "3", "$95.00", "$285.00"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$690.00"],
            ["Sales Tax (10%):", "$69.00"],
            ["TOTAL DUE:", "$759.00"],
        ]),
        sp(),
        Paragraph("Payment Method: Debit Card &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_3():
    doc, path = make_doc("invoices/INV-2024-019.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-019", H2),
        Paragraph("Date: April 18, 2024 &nbsp;&nbsp; Due Date: May 3, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Derek Okafor | 502 Pine St, Seattle, WA 98101 | (206) 555-4499", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2021 Chevrolet Silverado | VIN: 3GCUYDED5MG123789 | Mileage: 28,500", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Transmission Fluid Service", "1", "$185.00", "$185.00"],
            ["Differential Fluid Change", "1", "$120.00", "$120.00"],
            ["Transfer Case Fluid Change", "1", "$95.00", "$95.00"],
            ["4WD System Inspection", "1", "$65.00", "$65.00"],
            ["Labor (2.5 hrs @ $95/hr)", "2.5", "$95.00", "$237.50"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$702.50"],
            ["Sales Tax (10%):", "$70.25"],
            ["TOTAL DUE:", "$772.75"],
        ]),
        sp(),
        Paragraph("Payment Method: Cash &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_4():
    doc, path = make_doc("invoices/INV-2024-020.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-020", H2),
        Paragraph("Date: April 24, 2024 &nbsp;&nbsp; Due Date: May 9, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Sandra Kowalski | 77 Maple Lane, Renton, WA 98057 | (425) 555-8822", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2017 Subaru Outback | VIN: 4S4BSANC5H3123456 | Mileage: 89,300", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Timing Belt Replacement", "1", "$650.00", "$650.00"],
            ["Water Pump Replacement", "1", "$280.00", "$280.00"],
            ["Serpentine Belt Replacement", "1", "$95.00", "$95.00"],
            ["Coolant System Flush", "1", "$85.00", "$85.00"],
            ["Labor (5 hrs @ $95/hr)", "5", "$95.00", "$475.00"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$1,585.00"],
            ["Sales Tax (10%):", "$158.50"],
            ["TOTAL DUE:", "$1,743.50"],
        ]),
        sp(),
        Paragraph("Payment Method: Check #4421 &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_5():
    doc, path = make_doc("invoices/INV-2024-021.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-021", H2),
        Paragraph("Date: April 30, 2024 &nbsp;&nbsp; Due Date: May 15, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Fleet Services - King County Metro | 201 S Jackson St, Seattle, WA 98104", BODY),
        sp(),
        Paragraph("<b>FLEET SERVICE — Multiple Vehicles (April 2024)</b>", BODY),
        sp(4),
        line_table([
            ["Description", "Vehicle", "Rate", "Amount"],
            ["Oil Change + Filter (Unit #KC-441)", "2019 Ford Transit", "$89.00", "$89.00"],
            ["Oil Change + Filter (Unit #KC-442)", "2019 Ford Transit", "$89.00", "$89.00"],
            ["Tire Rotation (Unit #KC-441)", "2019 Ford Transit", "$55.00", "$55.00"],
            ["Tire Rotation (Unit #KC-442)", "2019 Ford Transit", "$55.00", "$55.00"],
            ["Brake Inspection x2 units", "Both", "$65.00", "$130.00"],
            ["Labor (4 hrs @ $95/hr)", "—", "$95.00", "$380.00"],
        ], [2.8*inch, 1.4*inch, 0.8*inch, 0.8*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$798.00"],
            ["Fleet Discount (5%):", "-$39.90"],
            ["Sales Tax (10%):", "$75.81"],
            ["TOTAL DUE:", "$833.91"],
        ]),
        sp(),
        Paragraph("Payment Method: Net-30 Invoice &nbsp;&nbsp; Status: <b>PENDING</b>", BODY),
        Paragraph("Thank you for your continued fleet business!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

# ─────────────────────────────────────────────
# EXPENSE DOCUMENTS (5 receipts/invoices)
# ─────────────────────────────────────────────

def expense_1():
    doc, path = make_doc("expenses/SEATTLE-POWER-APR-2024.pdf")
    story = [
        Paragraph("SEATTLE CITY LIGHT", H1),
        Paragraph("700 5th Ave, Suite 3200, Seattle, WA 98104 | (206) 684-3000 | seattle.gov/light", SMALL),
        hr(),
        Paragraph("COMMERCIAL UTILITY BILL", H2),
        Paragraph("Account #: 4821-0093-7 &nbsp;&nbsp; Bill Date: April 1, 2024 &nbsp;&nbsp; Due Date: April 22, 2024", BODY),
        sp(),
        Paragraph("<b>SERVICE ADDRESS:</b>", BODY),
        Paragraph("AutoFix Repair Shop | 123 Main Street, Seattle, WA 98101", BODY),
        sp(4),
        line_table([
            ["Charge Description", "Usage", "Rate", "Amount"],
            ["Basic Service Charge", "—", "—", "$18.50"],
            ["Energy Charge (Tier 1: 0–1,000 kWh)", "1,000 kWh", "$0.0752", "$75.20"],
            ["Energy Charge (Tier 2: 1,001–2,500 kWh)", "1,180 kWh", "$0.1021", "$120.48"],
            ["Demand Charge", "18.4 kW", "$4.85", "$89.24"],
            ["City Tax (6%)", "—", "—", "$18.21"],
        ], [3.0*inch, 1.0*inch, 0.9*inch, 0.9*inch]),
        sp(4),
        total_table([
            ["Previous Balance:", "$0.00"],
            ["Current Charges:", "$321.63"],
            ["TOTAL DUE:", "$321.63"],
        ]),
        sp(),
        Paragraph("Payment Method: ACH Auto-Pay &nbsp;&nbsp; Status: <b>PAID — April 18, 2024</b>", BODY),
        Paragraph("Billing Period: March 1 – March 31, 2024", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def expense_2():
    doc, path = make_doc("expenses/SNAP-ON-TOOLS-APR-2024.pdf")
    story = [
        Paragraph("SNAP-ON TOOLS CORPORATION", H1),
        Paragraph("2801 80th St, Kenosha, WI 53143 | (877) 762-7664 | snapon.com", SMALL),
        hr(),
        Paragraph("PURCHASE ORDER / INVOICE #SNP-2024-04-8821", H2),
        Paragraph("Invoice Date: April 8, 2024 &nbsp;&nbsp; Due Date: May 8, 2024", BODY),
        sp(),
        Paragraph("<b>SOLD TO:</b>", BODY),
        Paragraph("AutoFix Repair Shop | 123 Main Street, Seattle, WA 98101 | Account #: AF-88210", BODY),
        sp(4),
        line_table([
            ["Item", "Part #", "Qty", "Unit Price", "Total"],
            ["3/8\" Drive Digital Torque Wrench", "ATECH3FR250B", "1", "$389.00", "$389.00"],
            ["Serpentine Belt Tool Kit", "YA8875", "1", "$215.00", "$215.00"],
            ["Pry Bar Set (5-piece)", "PB5", "2", "$78.00", "$156.00"],
            ["Shop Creeper (Low Profile)", "KCRP31B", "1", "$145.00", "$145.00"],
            ["Nitrile Gloves Box (100ct)", "GLOVE-L", "4", "$22.00", "$88.00"],
        ], [2.5*inch, 1.2*inch, 0.5*inch, 0.9*inch, 0.7*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$993.00"],
            ["Shipping & Handling:", "$45.00"],
            ["Sales Tax (10.1%):", "$104.29"],
            ["TOTAL DUE:", "$1,142.29"],
        ]),
        sp(),
        Paragraph("Payment Terms: Net-30 &nbsp;&nbsp; Status: <b>PAID — April 30, 2024</b>", BODY),
        Paragraph("Dealer Rep: Mike Callahan | Territory: Pacific Northwest", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def expense_3():
    doc, path = make_doc("expenses/OFFICE-DEPOT-APR-2024.pdf")
    story = [
        Paragraph("OFFICE DEPOT / OFFICEMAX", H1),
        Paragraph("1234 Aurora Ave N, Seattle, WA 98109 | (206) 555-3300 | officedepot.com", SMALL),
        hr(),
        Paragraph("SALES RECEIPT #OD-20240415-9934", H2),
        Paragraph("Date: April 15, 2024 &nbsp;&nbsp; Cashier: Store #1142", BODY),
        sp(),
        Paragraph("<b>SOLD TO:</b>", BODY),
        Paragraph("AutoFix Repair Shop | Business Account #: BIZ-44821", BODY),
        sp(4),
        line_table([
            ["Item Description", "SKU", "Qty", "Price", "Total"],
            ["HP 67XL Black Ink Cartridge", "HP-67XL-BK", "3", "$38.99", "$116.97"],
            ["HP 67XL Color Ink Cartridge", "HP-67XL-CL", "2", "$42.99", "$85.98"],
            ["Copy Paper (Case, 8.5x11, 20lb)", "OD-PAPER-CS", "2", "$54.99", "$109.98"],
            ["Manila File Folders (100pk)", "OD-FOLD-100", "1", "$18.99", "$18.99"],
            ["Ballpoint Pens (Box of 12)", "OD-PEN-12", "2", "$9.99", "$19.98"],
            ["Sticky Notes Assorted (12pk)", "OD-STICKY-12", "1", "$14.99", "$14.99"],
        ], [2.5*inch, 1.1*inch, 0.5*inch, 0.8*inch, 0.8*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$366.89"],
            ["Business Discount (5%):", "-$18.34"],
            ["Sales Tax (10.1%):", "$35.24"],
            ["TOTAL CHARGED:", "$383.79"],
        ]),
        sp(),
        Paragraph("Payment Method: Business Visa ending 4821 &nbsp;&nbsp; Status: <b>APPROVED</b>", BODY),
        Paragraph("Thank you for shopping at Office Depot!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def expense_4():
    doc, path = make_doc("expenses/GOOGLE-ADS-APR-2024.pdf")
    story = [
        Paragraph("GOOGLE LLC", H1),
        Paragraph("1600 Amphitheatre Pkwy, Mountain View, CA 94043 | google.com/ads", SMALL),
        hr(),
        Paragraph("GOOGLE ADS — MONTHLY INVOICE", H2),
        Paragraph("Invoice #: 1234-5678-9012 &nbsp;&nbsp; Invoice Date: April 30, 2024", BODY),
        Paragraph("Billing Period: April 1 – April 30, 2024", BODY),
        sp(),
        Paragraph("<b>BILLED TO:</b>", BODY),
        Paragraph("AutoFix Repair Shop | 123 Main Street, Seattle, WA 98101", BODY),
        Paragraph("Customer ID: 412-889-2201", BODY),
        sp(4),
        line_table([
            ["Campaign", "Impressions", "Clicks", "Spend"],
            ["Auto Repair Seattle — Search", "48,220", "1,104", "$612.40"],
            ["Oil Change Special — Display", "182,500", "438", "$198.75"],
            ["Brake Service Promo — Search", "31,100", "720", "$389.85"],
        ], [2.8*inch, 1.1*inch, 0.9*inch, 0.9*inch]),
        sp(4),
        total_table([
            ["Total Ad Spend:", "$1,201.00"],
            ["Credits Applied:", "$0.00"],
            ["AMOUNT CHARGED:", "$1,201.00"],
        ]),
        sp(),
        Paragraph("Payment Method: Visa ending 4821 (Auto-charge) &nbsp;&nbsp; Status: <b>PAID — May 1, 2024</b>", BODY),
        Paragraph("For billing questions: ads-billing-support@google.com", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def expense_5():
    doc, path = make_doc("expenses/RENT-APR-2024.pdf")
    story = [
        Paragraph("SEATTLE COMMERCIAL PROPERTIES LLC", H1),
        Paragraph("890 Real Estate Plaza, Seattle, WA 98101 | (206) 555-7368 | payments@seattlecommercial.com", SMALL),
        hr(),
        Paragraph("COMMERCIAL RENT INVOICE", H2),
        Paragraph("Invoice Date: April 1, 2024 &nbsp;&nbsp; Due Date: April 5, 2024", BODY),
        sp(),
        Paragraph("<b>TENANT:</b>", BODY),
        Paragraph("AutoFix Repair Shop | 123 Main Street, Seattle, WA 98101", BODY),
        sp(),
        Paragraph("<b>PROPERTY:</b> 123 Main Street, Seattle, WA 98101", BODY),
        Paragraph("Commercial Auto Repair Facility — 3,500 sq ft shop + 500 sq ft office", BODY),
        sp(4),
        line_table([
            ["Description", "Amount"],
            ["Base Rent (April 2024)", "$4,500.00"],
            ["Property Tax Contribution (Monthly)", "$450.00"],
            ["Common Area Maintenance (CAM)", "$250.00"],
            ["Parking Lot Maintenance", "$75.00"],
        ], [4.5*inch, 1.3*inch], header_row=True),
        sp(4),
        total_table([
            ["Subtotal:", "$5,275.00"],
            ["Late Fee (if paid after Apr 5):", "$150.00"],
            ["TOTAL DUE (by Apr 5):", "$5,275.00"],
        ]),
        sp(),
        Paragraph("Payment Method: ACH Transfer &nbsp;&nbsp; Status: <b>PAID — April 3, 2024</b>", BODY),
        Paragraph("Lease Term: 5 years (2022–2027) | Monthly Base Rent: $4,500.00", SMALL),
        Paragraph("Thank you for your prompt payment.", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────
# RUN ALL
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating income PDFs...")
    income_1(); income_2(); income_3(); income_4(); income_5()
    print("Generating expense PDFs...")
    expense_1(); expense_2(); expense_3(); expense_4(); expense_5()
    print("Done — 10 PDFs generated.")


# ─────────────────────────────────────────────
# ADDITIONAL INVOICES (INV-2024-022 to 026)
# ─────────────────────────────────────────────

def income_6():
    doc, path = make_doc("invoices/INV-2024-022.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-022", H2),
        Paragraph("Date: May 3, 2024 &nbsp;&nbsp; Due Date: May 18, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("James Whitfield | 34 Eastlake Ave E, Seattle, WA 98102 | (206) 555-6612", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2019 Ford F-150 | VIN: 1FTEW1EP5KFA12345 | Mileage: 54,700", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Spark Plug Replacement (8 plugs)", "8", "$28.00", "$224.00"],
            ["Ignition Coil Replacement (2 coils)", "2", "$95.00", "$190.00"],
            ["Throttle Body Cleaning", "1", "$85.00", "$85.00"],
            ["Air Filter Replacement", "1", "$45.00", "$45.00"],
            ["Labor (2.5 hrs @ $95/hr)", "2.5", "$95.00", "$237.50"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$781.50"],
            ["Sales Tax (10%):", "$78.15"],
            ["TOTAL DUE:", "$859.65"],
        ]),
        sp(),
        Paragraph("Payment Method: Credit Card &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_7():
    doc, path = make_doc("invoices/INV-2024-023.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-023", H2),
        Paragraph("Date: May 9, 2024 &nbsp;&nbsp; Due Date: May 24, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Aisha Mensah | 210 Queen Anne Ave N, Seattle, WA 98109 | (206) 555-3344", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2022 Tesla Model 3 | VIN: 5YJ3E1EA5NF123456 | Mileage: 18,200", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Tire Rotation & Balance (4 wheels)", "1", "$75.00", "$75.00"],
            ["Cabin Air Filter Replacement", "1", "$65.00", "$65.00"],
            ["Wiper Blade Replacement (pair)", "1", "$55.00", "$55.00"],
            ["Multi-Point EV Inspection", "1", "$95.00", "$95.00"],
            ["Labor (1 hr @ $95/hr)", "1", "$95.00", "$95.00"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$385.00"],
            ["Sales Tax (10%):", "$38.50"],
            ["TOTAL DUE:", "$423.50"],
        ]),
        sp(),
        Paragraph("Payment Method: Apple Pay &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_8():
    doc, path = make_doc("invoices/INV-2024-024.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-024", H2),
        Paragraph("Date: May 15, 2024 &nbsp;&nbsp; Due Date: May 30, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Roberto Vasquez | 88 Rainier Ave S, Seattle, WA 98144 | (206) 555-9901", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2016 BMW 328i | VIN: WBA8E9G58GNT12345 | Mileage: 102,400", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["Alternator Replacement (Reman)", "1", "$420.00", "$420.00"],
            ["Drive Belt Replacement", "1", "$85.00", "$85.00"],
            ["Battery Test & Replacement", "1", "$195.00", "$195.00"],
            ["Charging System Diagnostic", "1", "$95.00", "$95.00"],
            ["Labor (3.5 hrs @ $95/hr)", "3.5", "$95.00", "$332.50"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$1,127.50"],
            ["Sales Tax (10%):", "$112.75"],
            ["TOTAL DUE:", "$1,240.25"],
        ]),
        sp(),
        Paragraph("Payment Method: Debit Card &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_9():
    doc, path = make_doc("invoices/INV-2024-025.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-025", H2),
        Paragraph("Date: May 21, 2024 &nbsp;&nbsp; Due Date: June 5, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Linda Park | 450 Mercer St, Seattle, WA 98109 | (206) 555-7788", BODY),
        sp(),
        Paragraph("<b>VEHICLE:</b> 2020 Hyundai Tucson | VIN: KM8J3CA46LU123456 | Mileage: 37,600", BODY),
        sp(4),
        line_table([
            ["Description", "Qty", "Rate", "Amount"],
            ["AC System Recharge (R-134a)", "1", "$145.00", "$145.00"],
            ["AC Compressor Inspection", "1", "$75.00", "$75.00"],
            ["Cabin Air Filter Replacement", "1", "$55.00", "$55.00"],
            ["Coolant Top-Up", "1", "$35.00", "$35.00"],
            ["Labor (1.5 hrs @ $95/hr)", "1.5", "$95.00", "$142.50"],
        ], [3.2*inch, 0.6*inch, 1.0*inch, 1.0*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$452.50"],
            ["Sales Tax (10%):", "$45.25"],
            ["TOTAL DUE:", "$497.75"],
        ]),
        sp(),
        Paragraph("Payment Method: Cash &nbsp;&nbsp; Status: <b>PAID</b>", BODY),
        Paragraph("Thank you for choosing AutoFix Repair Shop!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")

def income_10():
    doc, path = make_doc("invoices/INV-2024-026.pdf")
    story = [
        Paragraph("AUTOFIX REPAIR SHOP", H1),
        Paragraph("123 Main Street, Seattle, WA 98101 | (206) 555-0123 | info@autofixseattle.com", SMALL),
        hr(),
        Paragraph("INVOICE #INV-2024-026", H2),
        Paragraph("Date: May 28, 2024 &nbsp;&nbsp; Due Date: June 12, 2024", BODY),
        sp(),
        Paragraph("<b>BILL TO:</b>", BODY),
        Paragraph("Fleet Services - Amazon Logistics | 410 Terry Ave N, Seattle, WA 98109", BODY),
        sp(),
        Paragraph("<b>FLEET SERVICE — Multiple Vehicles (May 2024)</b>", BODY),
        sp(4),
        line_table([
            ["Description", "Vehicle", "Rate", "Amount"],
            ["Oil Change + Filter (Unit #AMZ-881)", "2021 Ram ProMaster", "$99.00", "$99.00"],
            ["Oil Change + Filter (Unit #AMZ-882)", "2021 Ram ProMaster", "$99.00", "$99.00"],
            ["Oil Change + Filter (Unit #AMZ-883)", "2021 Ram ProMaster", "$99.00", "$99.00"],
            ["Tire Rotation x3 units", "All Units", "$55.00", "$165.00"],
            ["Multi-Point Inspection x3 units", "All Units", "$45.00", "$135.00"],
            ["Labor (6 hrs @ $95/hr)", "—", "$95.00", "$570.00"],
        ], [2.8*inch, 1.4*inch, 0.8*inch, 0.8*inch]),
        sp(4),
        total_table([
            ["Subtotal:", "$1,167.00"],
            ["Fleet Discount (5%):", "-$58.35"],
            ["Sales Tax (10%):", "$110.87"],
            ["TOTAL DUE:", "$1,219.52"],
        ]),
        sp(),
        Paragraph("Payment Method: Net-30 Invoice &nbsp;&nbsp; Status: <b>PENDING</b>", BODY),
        Paragraph("PO Reference: AMZ-SEA-2024-0528 | Thank you for your fleet business!", SMALL),
    ]
    doc.build(story)
    print(f"  Created: {path}")


if __name__ == "__main__":
    print("Generating additional invoices (022-026)...")
    income_6(); income_7(); income_8(); income_9(); income_10()
    print("Done.")
