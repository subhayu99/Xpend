from sqlmodel import Session, select, func
from app.models.transaction import Transaction
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class RecurringDetectionService:
    """Service to detect recurring transactions like subscriptions and bills"""
    
    @staticmethod
    def detect_recurring(db: Session, user_id: str) -> List[Dict[str, Any]]:
        # Fetch all expenses for the user
        # We need at least 3 occurrences to call it recurring
        query = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == 'expense'
        ).order_by(Transaction.transaction_date)
        
        transactions = db.exec(query).all()
        
        if not transactions:
            return []
            
        # Convert to DataFrame for easier analysis
        data = []
        for tx in transactions:
            data.append({
                'id': str(tx.id),
                'date': tx.transaction_date,
                'amount': abs(tx.amount),
                'description': tx.description,
                'merchant': tx.merchant_name or tx.description,
                'category_id': str(tx.category_id) if tx.category_id else None
            })
            
        df = pd.DataFrame(data)
        if df.empty:
            return []
            
        # Normalize merchant/description for grouping
        # We'll use the first 10 chars of description as a simple key if merchant is missing
        # or use the merchant normalizer logic if available. 
        # For now, let's group by 'merchant' column which should be populated/normalized already.
        
        recurring_groups = []
        
        # Group by Merchant and Amount (with some tolerance)
        # We round amount to nearest integer for grouping to handle slight currency fluctuations
        df['amount_rounded'] = df['amount'].round(0)
        
        grouped = df.groupby(['merchant', 'amount_rounded'])
        
        for (merchant, amount), group in grouped:
            if len(group) < 3:
                continue
                
            # Calculate days between transactions
            dates = group['date'].sort_values()
            diffs = dates.diff().dt.days.dropna()
            
            # Check if intervals are regular
            # We look for monthly (28-31 days) or weekly (7 days) or yearly (365 days)
            avg_diff = diffs.mean()
            std_diff = diffs.std()
            
            interval_type = None
            confidence = 0.0
            
            if 25 <= avg_diff <= 35 and std_diff < 5:
                interval_type = "Monthly"
                confidence = 0.9
            elif 6 <= avg_diff <= 8 and std_diff < 2:
                interval_type = "Weekly"
                confidence = 0.8
            elif 360 <= avg_diff <= 370 and std_diff < 10:
                interval_type = "Yearly"
                confidence = 0.9
            
            if interval_type:
                # Predict next date
                last_date = dates.iloc[-1]
                next_date = last_date + timedelta(days=int(avg_diff))
                
                recurring_groups.append({
                    'merchant': merchant,
                    'amount': float(amount),
                    'interval': interval_type,
                    'confidence': confidence,
                    'avg_days': float(avg_diff),
                    'last_date': last_date.strftime('%Y-%m-%d'),
                    'next_date': next_date.strftime('%Y-%m-%d'),
                    'transaction_count': len(group),
                    'example_tx_id': group.iloc[0]['id']
                })
                
        # Sort by confidence and amount
        recurring_groups.sort(key=lambda x: (x['confidence'], x['amount']), reverse=True)
        
        return recurring_groups
