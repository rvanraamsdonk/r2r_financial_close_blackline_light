#!/usr/bin/env python3
"""
Script to enhance AP/AR subledger data by multiplying volume and adding complex scenarios
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

def enhance_ap_data():
    """Enhance AP detail data with 5-10x volume and complex scenarios"""
    
    # Read original AP data
    ap_file = Path("data/lite/subledgers/ap_detail_aug.csv")
    df = pd.read_csv(ap_file)
    
    # Create enhanced dataset with 8x multiplier
    enhanced_rows = []
    
    # Add original data
    enhanced_rows.extend(df.to_dict('records'))
    
    # Generate additional complex scenarios
    vendors = [
        "Microsoft Corporation", "Google LLC", "Amazon Web Services", "Salesforce Inc",
        "Oracle Corporation", "IBM Corporation", "SAP SE", "Adobe Inc", "Workday Inc",
        "ServiceNow Inc", "Snowflake Inc", "Databricks Inc", "UiPath Inc", "Palantir Technologies",
        "CrowdStrike Holdings", "Palo Alto Networks", "Okta Inc", "Splunk Inc", "Elastic NV",
        "MongoDB Inc", "Atlassian Corporation", "Slack Technologies", "Zoom Video Communications",
        "DocuSign Inc", "Dropbox Inc", "Box Inc", "Twilio Inc", "SendGrid Inc", "HubSpot Inc",
        "Marketo Inc", "Pardot", "Eloqua Corporation", "Act-On Software", "SharpSpring Inc"
    ]
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    # Generate 7x more data with complex scenarios
    bill_counter = 101
    for multiplier in range(7):
        for entity in entities:
            for i in range(50):  # 50 bills per entity per multiplier
                vendor = random.choice(vendors)
                
                # Create complex scenarios
                scenarios = [
                    {"status": "Outstanding", "notes": "", "age_days": random.randint(1, 45)},
                    {"status": "Overdue", "notes": "Payment delayed - approval pending", "age_days": random.randint(46, 90)},
                    {"status": "Outstanding", "notes": "Duplicate payment detected", "age_days": random.randint(15, 35)},
                    {"status": "Outstanding", "notes": "Invoice disputed - amount variance", "age_days": random.randint(20, 60)},
                    {"status": "Outstanding", "notes": "PO number missing", "age_days": random.randint(5, 25)},
                    {"status": "Overdue", "notes": "Vendor payment terms exceeded", "age_days": random.randint(61, 120)},
                    {"status": "Outstanding", "notes": "Three-way match failed", "age_days": random.randint(10, 40)},
                    {"status": "Outstanding", "notes": "Awaiting goods receipt", "age_days": random.randint(3, 20)},
                    {"status": "Outstanding", "notes": "Tax calculation error", "age_days": random.randint(8, 30)},
                    {"status": "Overdue", "notes": "Credit limit exceeded", "age_days": random.randint(75, 150)}
                ]
                
                scenario = random.choice(scenarios)
                
                # Generate realistic amounts based on entity and vendor
                base_amount = random.uniform(1000, 25000)
                if "Microsoft" in vendor or "Google" in vendor or "Amazon" in vendor:
                    base_amount *= random.uniform(1.5, 3.0)  # Larger vendors
                
                # Add some very large invoices occasionally
                if random.random() < 0.05:  # 5% chance
                    base_amount *= random.uniform(3.0, 8.0)
                
                bill_date = datetime(2025, 8, random.randint(1, 31))
                
                row = {
                    "period": "2025-08",
                    "entity": entity,
                    "bill_id": f"BILL-2025-08-{entity}-{bill_counter:04d}",
                    "vendor_name": vendor,
                    "bill_date": bill_date.strftime("%Y-%m-%d"),
                    "amount": round(base_amount, 2),
                    "currency": currencies[entity],
                    "age_days": scenario["age_days"],
                    "status": scenario["status"],
                    "notes": scenario["notes"]
                }
                
                enhanced_rows.append(row)
                bill_counter += 1
    
    # Create enhanced dataframe
    enhanced_df = pd.DataFrame(enhanced_rows)
    
    # Save enhanced AP data
    output_file = Path("data/lite/subledgers/ap_detail_aug_enhanced.csv")
    enhanced_df.to_csv(output_file, index=False)
    print(f"Enhanced AP data saved to {output_file}")
    print(f"Original rows: {len(df)}, Enhanced rows: {len(enhanced_df)}")

def enhance_ar_data():
    """Enhance AR detail data with 5-10x volume and complex scenarios"""
    
    # Read original AR data
    ar_file = Path("data/lite/subledgers/ar_detail_aug.csv")
    df = pd.read_csv(ar_file)
    
    # Create enhanced dataset
    enhanced_rows = []
    
    # Add original data
    enhanced_rows.extend(df.to_dict('records'))
    
    # Generate additional complex scenarios
    customers = [
        "Acme Corporation", "Global Tech Solutions", "Enterprise Systems Inc", "Digital Innovations LLC",
        "Advanced Analytics Corp", "Cloud Services Ltd", "Data Solutions Group", "Tech Consulting Partners",
        "Innovation Labs Inc", "Future Systems Corp", "Smart Technologies Ltd", "Digital Transformation Co",
        "AI Solutions Group", "Automation Systems Inc", "Business Intelligence Corp", "Data Analytics Ltd",
        "Cloud Computing Solutions", "Enterprise Software Corp", "Technology Partners LLC", "Digital Solutions Inc",
        "Advanced Computing Corp", "Information Systems Ltd", "Software Development Group", "Tech Innovation Partners",
        "Digital Services Corp", "Enterprise Technology Ltd", "Business Solutions Inc", "Technology Consulting Group",
        "Data Management Corp", "Cloud Infrastructure Ltd", "Software Solutions Inc", "Digital Platform Corp",
        "Technology Integration Ltd", "Business Analytics Group", "Enterprise Solutions Corp"
    ]
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    # Generate 7x more data with complex scenarios
    invoice_counter = 101
    for multiplier in range(7):
        for entity in entities:
            for i in range(45):  # 45 invoices per entity per multiplier
                customer = random.choice(customers)
                
                # Create complex AR scenarios
                scenarios = [
                    {"status": "Outstanding", "notes": "", "age_days": random.randint(1, 30)},
                    {"status": "Overdue", "notes": "Customer payment delayed", "age_days": random.randint(31, 60)},
                    {"status": "Outstanding", "notes": "Payment plan established", "age_days": random.randint(15, 45)},
                    {"status": "Outstanding", "notes": "Invoice disputed by customer", "age_days": random.randint(20, 50)},
                    {"status": "Overdue", "notes": "Collection agency assigned", "age_days": random.randint(61, 120)},
                    {"status": "Outstanding", "notes": "Partial payment received", "age_days": random.randint(10, 35)},
                    {"status": "Outstanding", "notes": "Credit hold applied", "age_days": random.randint(25, 55)},
                    {"status": "Overdue", "notes": "Legal action initiated", "age_days": random.randint(91, 180)},
                    {"status": "Outstanding", "notes": "Customer bankruptcy filing", "age_days": random.randint(45, 90)},
                    {"status": "Outstanding", "notes": "Currency exchange dispute", "age_days": random.randint(12, 40)}
                ]
                
                scenario = random.choice(scenarios)
                
                # Generate realistic amounts
                base_amount = random.uniform(2000, 50000)
                
                # Add some very large invoices occasionally
                if random.random() < 0.08:  # 8% chance
                    base_amount *= random.uniform(2.0, 6.0)
                
                invoice_date = datetime(2025, 8, random.randint(1, 31))
                
                row = {
                    "period": "2025-08",
                    "entity": entity,
                    "invoice_id": f"INV-2025-08-{entity}-{invoice_counter:04d}",
                    "customer_name": customer,
                    "invoice_date": invoice_date.strftime("%Y-%m-%d"),
                    "amount": round(base_amount, 2),
                    "currency": currencies[entity],
                    "age_days": scenario["age_days"],
                    "status": scenario["status"],
                    "notes": scenario["notes"]
                }
                
                enhanced_rows.append(row)
                invoice_counter += 1
    
    # Create enhanced dataframe
    enhanced_df = pd.DataFrame(enhanced_rows)
    
    # Save enhanced AR data
    output_file = Path("data/lite/subledgers/ar_detail_aug_enhanced.csv")
    enhanced_df.to_csv(output_file, index=False)
    print(f"Enhanced AR data saved to {output_file}")
    print(f"Original rows: {len(df)}, Enhanced rows: {len(enhanced_df)}")

if __name__ == "__main__":
    print("Enhancing subledger data...")
    enhance_ap_data()
    enhance_ar_data()
    print("Subledger enhancement complete!")
