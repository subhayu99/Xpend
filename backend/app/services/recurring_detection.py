from sqlmodel import Session, select, func
from app.models.transaction import Transaction
from typing import List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import uuid


class RecurringDetectionService:
    """Service to detect recurring transactions like subscriptions and bills"""

    @staticmethod
    def detect_recurring(db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Detect recurring transactions using two strategies:
        1. Exact amount match - for subscriptions with fixed amounts
        2. Merchant-only match - for variable bills (utilities, etc.)
        """
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
            tx_date = tx.transaction_date
            if isinstance(tx_date, str):
                tx_date = datetime.fromisoformat(tx_date)
            elif hasattr(tx_date, 'date') and not isinstance(tx_date, datetime):
                tx_date = datetime.combine(tx_date, datetime.min.time())

            data.append({
                'id': str(tx.id),
                'date': pd.Timestamp(tx_date),
                'amount': abs(tx.amount),
                'description': tx.description,
                'merchant': tx.merchant_name or tx.description or 'Unknown',
                'category_id': str(tx.category_id) if tx.category_id else None
            })

        df = pd.DataFrame(data)
        if df.empty:
            return []

        recurring_groups = []
        seen_merchants = set()

        # Strategy 1: Group by Merchant + Amount (exact matches, high confidence)
        df['amount_rounded'] = df['amount'].round(0)
        grouped_exact = df.groupby(['merchant', 'amount_rounded'])

        for (merchant, amount), group in grouped_exact:
            if len(group) < 3:
                continue

            result = RecurringDetectionService._analyze_interval(
                group, merchant, amount, is_exact_amount=True
            )
            if result:
                recurring_groups.append(result)
                seen_merchants.add(merchant)

        # Strategy 2: Group by Merchant only (for variable bills)
        # Only check merchants not already detected with exact amounts
        grouped_merchant = df.groupby('merchant')

        for merchant, group in grouped_merchant:
            if merchant in seen_merchants:
                continue
            if len(group) < 3:
                continue

            # Use median amount for variable bills
            median_amount = group['amount'].median()

            result = RecurringDetectionService._analyze_interval(
                group, merchant, median_amount, is_exact_amount=False
            )
            if result:
                recurring_groups.append(result)

        # Sort by confidence (desc), then by amount (desc)
        recurring_groups.sort(key=lambda x: (x['confidence'], x['amount']), reverse=True)

        return recurring_groups

    @staticmethod
    def _analyze_interval(
        group: pd.DataFrame,
        merchant: str,
        amount: float,
        is_exact_amount: bool
    ) -> Dict[str, Any] | None:
        """
        Analyze a group of transactions to detect recurring patterns.

        Args:
            group: DataFrame with transactions for this merchant/amount
            merchant: Merchant name
            amount: Amount (exact or median)
            is_exact_amount: Whether this is an exact amount match

        Returns:
            Recurring pattern dict or None if no pattern detected
        """
        dates = group['date'].sort_values().reset_index(drop=True)
        diffs = dates.diff().dt.days.dropna()

        if len(diffs) < 2:
            return None

        avg_diff = diffs.mean()
        std_diff = diffs.std()

        if pd.isna(avg_diff) or pd.isna(std_diff):
            return None

        interval_type = None
        confidence = 0.0

        # Adjust thresholds based on exact vs variable amounts
        # Variable amounts get slightly lower confidence
        conf_modifier = 1.0 if is_exact_amount else 0.85

        # Monthly: 25-35 days
        if 25 <= avg_diff <= 35:
            # More lenient std for variable bills
            max_std = 5 if is_exact_amount else 8
            if std_diff < max_std:
                interval_type = "Monthly"
                # Higher confidence for lower std
                confidence = 0.9 * conf_modifier * (1 - std_diff / (max_std * 2))
                confidence = max(0.6, min(0.95, confidence))

        # Bi-weekly: 13-16 days
        elif 13 <= avg_diff <= 16:
            max_std = 3 if is_exact_amount else 5
            if std_diff < max_std:
                interval_type = "Bi-weekly"
                confidence = 0.85 * conf_modifier * (1 - std_diff / (max_std * 2))
                confidence = max(0.5, min(0.9, confidence))

        # Weekly: 6-8 days
        elif 6 <= avg_diff <= 8:
            max_std = 2 if is_exact_amount else 3
            if std_diff < max_std:
                interval_type = "Weekly"
                confidence = 0.8 * conf_modifier * (1 - std_diff / (max_std * 2))
                confidence = max(0.5, min(0.85, confidence))

        # Quarterly: 85-95 days
        elif 85 <= avg_diff <= 95:
            max_std = 10 if is_exact_amount else 15
            if std_diff < max_std:
                interval_type = "Quarterly"
                confidence = 0.85 * conf_modifier * (1 - std_diff / (max_std * 2))
                confidence = max(0.5, min(0.9, confidence))

        # Yearly: 360-370 days
        elif 360 <= avg_diff <= 370:
            max_std = 10 if is_exact_amount else 20
            if std_diff < max_std:
                interval_type = "Yearly"
                confidence = 0.9 * conf_modifier * (1 - std_diff / (max_std * 2))
                confidence = max(0.6, min(0.95, confidence))

        if not interval_type:
            return None

        # Predict next date
        last_date = dates.iloc[-1]
        next_date = last_date + pd.Timedelta(days=int(avg_diff))

        last_date_str = last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else str(last_date)[:10]
        next_date_str = next_date.strftime('%Y-%m-%d') if hasattr(next_date, 'strftime') else str(next_date)[:10]

        # Calculate amount range for variable bills
        amount_min = float(group['amount'].min())
        amount_max = float(group['amount'].max())

        return {
            'merchant': str(merchant) if merchant else 'Unknown',
            'amount': float(amount),
            'amount_min': amount_min,
            'amount_max': amount_max,
            'is_variable_amount': not is_exact_amount or (amount_max - amount_min > 1),
            'interval': interval_type,
            'confidence': round(confidence, 2),
            'avg_days': round(float(avg_diff), 1),
            'std_days': round(float(std_diff), 1),
            'last_date': last_date_str,
            'next_date': next_date_str,
            'transaction_count': len(group),
            'transaction_ids': group['id'].tolist(),
            'transactions': [
                {
                    'id': str(tx_id),
                    'date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10],
                    'amount': float(amt)
                }
                for tx_id, date, amt in zip(group['id'], group['date'], group['amount'])
            ],
            'example_tx_id': group.iloc[0]['id'],
            'status': 'suggested'  # Can be 'suggested', 'confirmed', 'dismissed'
        }
