#!/usr/bin/env python3
"""
WorkmAIn Preview Test
Preview Test v1.0
20251224

Quick test to preview template rendering with actual database data.
"""

import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from workmain.templates_engine import get_template_renderer


def get_session():
    """Get database session."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'workmain')
    db_user = os.getenv('DB_USER', 'workmain_user')
    db_password = os.getenv('DB_PASSWORD', '')
    
    conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(conn_string)
    Session = sessionmaker(bind=engine)
    
    return Session()


def preview_daily():
    """Preview daily internal report."""
    print("\n" + "="*60)
    print("DAILY INTERNAL REPORT PREVIEW")
    print("="*60)
    
    session = get_session()
    
    try:
        renderer = get_template_renderer(session)
        
        # Render today's report (no AI)
        result = renderer.render(
            template_name='daily_internal',
            report_date=date.today(),
            use_ai=False
        )
        
        print(f"\nTemplate: {result['template_name']}")
        print(f"Date: {result['metadata']['report_date']}")
        print(f"Subject: {result['subject_line']}")
        print("\n" + "-"*60)
        print("\nOUTPUT:\n")
        print(result['output'])
        print("\n" + "-"*60)
        
        # Show data summary
        print("\nDATA SUMMARY:")
        for section in result['sections']:
            data = section['data']
            print(f"\n  {section['title']}:")
            print(f"    Notes: {data['summary']['note_count']}")
            print(f"    Time entries: {data['summary']['time_entry_count']}")
            print(f"    Total hours: {data['summary']['total_hours']:.2f}h")
        
    finally:
        session.close()


def preview_weekly():
    """Preview weekly client report."""
    print("\n" + "="*60)
    print("WEEKLY CLIENT REPORT PREVIEW")
    print("="*60)
    
    session = get_session()
    
    try:
        renderer = get_template_renderer(session)
        
        # Render this week's report (no AI)
        result = renderer.render(
            template_name='weekly_client',
            report_date=date.today(),
            use_ai=False
        )
        
        print(f"\nTemplate: {result['template_name']}")
        print(f"Date range: {result['metadata']['date_range']['start']} to {result['metadata']['date_range']['end']}")
        print(f"Subject: {result['subject_line']}")
        print("\n" + "-"*60)
        print("\nOUTPUT:\n")
        print(result['output'])
        print("\n" + "-"*60)
        
        # Show data summary
        print("\nDATA SUMMARY:")
        for section in result['sections']:
            data = section['data']
            print(f"\n  {section['title']}:")
            print(f"    Notes: {data['summary']['note_count']}")
            print(f"    Time entries: {data['summary']['time_entry_count']}")
            print(f"    Total hours: {data['summary']['total_hours']:.2f}h")
        
    finally:
        session.close()


def main():
    """Run preview tests."""
    print("\nWorkmAIn Template Preview Test")
    
    choice = input("\nPreview: (d)aily, (w)eekly, or (b)oth? [b]: ").strip().lower() or 'b'
    
    if choice in ['d', 'b']:
        preview_daily()
    
    if choice in ['w', 'b']:
        preview_weekly()
    
    print("\n" + "="*60)
    print("Preview complete!")
    print("Note: This preview shows raw data formatting.")
    print("      AI generation will be added in Phase 4.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()