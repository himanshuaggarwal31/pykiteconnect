#!/usr/bin/env python3
"""
Setup script to create the NIFTY_MCAP table in the database.
Run this script to create the vlookup table for symbol-to-company mapping.
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.models import NiftyMcap

def create_nifty_table():
    """Create the NIFTY_MCAP table and populate with sample data"""
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ NIFTY_MCAP table created successfully!")
            
            # Check if table already has data
            existing_count = NiftyMcap.query.count()
            if existing_count > 0:
                print(f"ℹ️  Table already has {existing_count} records. Skipping sample data insertion.")
                return
            
            # Sample data for testing (you can replace this with your actual data)
            sample_data = [
                {
                    'symbol': 'RELIANCE',
                    'company_name': 'Reliance Industries Limited',
                    'mcap_lakhs': 1825000,  # 18.25 lakh crores
                    'nifty_rank': 1,
                    'him_rating': 'Buy',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'TCS',
                    'company_name': 'Tata Consultancy Services Limited',
                    'mcap_lakhs': 1450000,  # 14.5 lakh crores
                    'nifty_rank': 2,
                    'him_rating': 'Buy',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'HDFCBANK',
                    'company_name': 'HDFC Bank Limited',
                    'mcap_lakhs': 1200000,  # 12 lakh crores
                    'nifty_rank': 3,
                    'him_rating': 'Hold',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'INFY',
                    'company_name': 'Infosys Limited',
                    'mcap_lakhs': 750000,   # 7.5 lakh crores
                    'nifty_rank': 4,
                    'him_rating': 'Buy',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'ICICIBANK',
                    'company_name': 'ICICI Bank Limited',
                    'mcap_lakhs': 850000,   # 8.5 lakh crores
                    'nifty_rank': 5,
                    'him_rating': 'Hold',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'HINDUNILVR',
                    'company_name': 'Hindustan Unilever Limited',
                    'mcap_lakhs': 650000,   # 6.5 lakh crores
                    'nifty_rank': 6,
                    'him_rating': 'Buy',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'ITC',
                    'company_name': 'ITC Limited',
                    'mcap_lakhs': 550000,   # 5.5 lakh crores
                    'nifty_rank': 7,
                    'him_rating': 'Hold',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'SBIN',
                    'company_name': 'State Bank of India',
                    'mcap_lakhs': 475000,   # 4.75 lakh crores
                    'nifty_rank': 8,
                    'him_rating': 'Buy',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'BAJFINANCE',
                    'company_name': 'Bajaj Finance Limited',
                    'mcap_lakhs': 525000,   # 5.25 lakh crores
                    'nifty_rank': 9,
                    'him_rating': 'Hold',
                    'rating_date': datetime(2024, 12, 1).date()
                },
                {
                    'symbol': 'KOTAKBANK',
                    'company_name': 'Kotak Mahindra Bank Limited',
                    'mcap_lakhs': 425000,   # 4.25 lakh crores
                    'nifty_rank': 10,
                    'him_rating': 'Buy',
                    'rating_date': datetime(2024, 12, 1).date()
                }
            ]
            
            # Insert sample data
            for data in sample_data:
                nifty_record = NiftyMcap(
                    symbol=data['symbol'],
                    company_name=data['company_name'],
                    mcap_lakhs=data['mcap_lakhs'],
                    nifty_rank=data['nifty_rank'],
                    him_rating=data['him_rating'],
                    rating_date=data['rating_date']
                )
                db.session.add(nifty_record)
            
            db.session.commit()
            print(f"✅ Successfully inserted {len(sample_data)} sample records!")
            
            # Display the inserted data
            print("\n📋 Sample data inserted:")
            for record in NiftyMcap.query.order_by(NiftyMcap.nifty_rank).all():
                mcap_cr = record.mcap_lakhs / 100 if record.mcap_lakhs else 0
                print(f"   {record.nifty_rank:2d}. {record.symbol:12s} | {record.company_name:35s} | ₹{mcap_cr:6.0f} Cr | {record.him_rating}")
            
        except Exception as e:
            print(f"❌ Error creating table: {str(e)}")
            db.session.rollback()
            raise

def add_custom_symbols(csv_file_path=None):
    """
    Add custom symbols from a CSV file
    CSV format: symbol,company_name,mcap_lakhs,nifty_rank,him_rating,rating_date
    """
    if not csv_file_path:
        print("ℹ️  To add custom data, provide a CSV file path as argument")
        print("📝 CSV format: symbol,company_name,mcap_lakhs,nifty_rank,him_rating,rating_date")
        return
    
    try:
        import pandas as pd
        df = pd.read_csv(csv_file_path)
        
        with app.app_context():
            for _, row in df.iterrows():
                # Check if symbol already exists
                existing = NiftyMcap.query.filter_by(symbol=row['symbol']).first()
                if existing:
                    print(f"⚠️  Symbol {row['symbol']} already exists, skipping...")
                    continue
                
                # Convert date if provided
                rating_date = None
                if pd.notna(row.get('rating_date')):
                    rating_date = pd.to_datetime(row['rating_date']).date()
                
                nifty_record = NiftyMcap(
                    symbol=row['symbol'],
                    company_name=row['company_name'],
                    mcap_lakhs=row.get('mcap_lakhs'),
                    nifty_rank=row.get('nifty_rank'),
                    him_rating=row.get('him_rating'),
                    rating_date=rating_date
                )
                db.session.add(nifty_record)
            
            db.session.commit()
            print(f"✅ Successfully imported data from {csv_file_path}")
            
    except ImportError:
        print("❌ pandas not installed. Install with: pip install pandas")
    except Exception as e:
        print(f"❌ Error importing CSV: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    print("🚀 Setting up NIFTY_MCAP table...")
    create_nifty_table()
    
    # If CSV file path provided as command line argument
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        add_custom_symbols(csv_path)
    
    print("\n✅ Setup complete! You can now use the symbol lookup functionality.")
    print("💡 To add more symbols, either:")
    print("   1. Run: python setup_nifty_table.py your_data.csv")
    print("   2. Add records directly to the database")
