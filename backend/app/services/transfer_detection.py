"""
Self-transfer detection service.
Identifies potential transfers between user's accounts.
"""
from sqlmodel import Session, select
from app.models.transaction import Transaction
from app.models.transfer import Transfer
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import uuid

class TransferDetectionService:
    """Service for detecting and managing self-transfers"""
    
    @staticmethod
    def detect_potential_transfers(
        db: Session,
        user_id: uuid.UUID,
        days_window: int = 2,
        amount_tolerance: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Detect potential self-transfers between user's accounts.
        
        Args:
            db: Database session
            user_id: User ID
            days_window: Number of days to look for matching transactions
            amount_tolerance: Tolerance for amount matching (default 1%)
            
        Returns:
            List of potential transfer pairs with confidence scores
        """
        # Get all transactions not already linked as transfers
        existing_transfer_tx_ids = set()
        existing_transfers = db.exec(
            select(Transfer).where(Transfer.user_id == user_id)
        ).all()
        
        for transfer in existing_transfers:
            existing_transfer_tx_ids.add(transfer.debit_transaction_id)
            existing_transfer_tx_ids.add(transfer.credit_transaction_id)
        
        # Get unlinked transactions
        transactions = db.exec(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .where(Transaction.id.not_in(existing_transfer_tx_ids) if existing_transfer_tx_ids else True)
            .order_by(Transaction.transaction_date.desc())
        ).all()
        
        potential_transfers = []
        
        # Group by similar amounts
        for i, tx1 in enumerate(transactions):
            if tx1.transaction_type == 'transfer':
                continue  # Skip already marked as transfer
                
            for tx2 in transactions[i+1:]:
                if tx2.transaction_type == 'transfer':
                    continue
                    
                # Check if one is debit and one is credit
                if tx1.amount * tx2.amount >= 0:  # Same sign
                    continue
                
                # Check if amounts match (within tolerance)
                abs_amount1 = abs(tx1.amount)
                abs_amount2 = abs(tx2.amount)
                
                if abs(abs_amount1 - abs_amount2) > abs_amount1 * amount_tolerance:
                    continue
                
                # Check if dates are within window
                date_diff = abs((tx1.transaction_date - tx2.transaction_date).days)
                if date_diff > days_window:
                    continue
                
                # Check if different accounts
                if tx1.account_id == tx2.account_id:
                    continue
                
                # Calculate confidence score
                confidence = TransferDetectionService._calculate_confidence(
                    tx1, tx2, date_diff, abs_amount1, abs_amount2
                )
                
                # Determine which is debit and which is credit
                debit_tx = tx1 if tx1.amount < 0 else tx2
                credit_tx = tx2 if tx1.amount < 0 else tx1
                
                potential_transfers.append({
                    'debit_transaction': {
                        'id': str(debit_tx.id),
                        'date': debit_tx.transaction_date.isoformat(),
                        'amount': debit_tx.amount,
                        'description': debit_tx.description,
                        'account_id': str(debit_tx.account_id)
                    },
                    'credit_transaction': {
                        'id': str(credit_tx.id),
                        'date': credit_tx.transaction_date.isoformat(),
                        'amount': credit_tx.amount,
                        'description': credit_tx.description,
                        'account_id': str(credit_tx.account_id)
                    },
                    'confidence_score': confidence,
                    'date_diff_days': date_diff,
                    'amount': abs_amount1
                })
        
        # Sort by confidence score
        potential_transfers.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return potential_transfers
    
    @staticmethod
    def _calculate_confidence(
        tx1: Transaction,
        tx2: Transaction,
        date_diff: int,
        amount1: float,
        amount2: float
    ) -> float:
        """Calculate confidence score for transfer pair (0-1)"""
        confidence = 1.0
        
        # Penalize date difference
        if date_diff == 0:
            confidence *= 1.0
        elif date_diff == 1:
            confidence *= 0.9
        else:
            confidence *= 0.8
        
        # Penalize amount difference
        amount_diff_pct = abs(amount1 - amount2) / max(amount1, amount2)
        confidence *= (1.0 - amount_diff_pct)
        
        # Boost if descriptions suggest transfer
        transfer_keywords = ['transfer', 'trf', 'neft', 'imps', 'rtgs', 'upi']
        desc1_lower = tx1.description.lower()
        desc2_lower = tx2.description.lower()
        
        if any(kw in desc1_lower or kw in desc2_lower for kw in transfer_keywords):
            confidence *= 1.2
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    @staticmethod
    def create_transfer(
        db: Session,
        user_id: uuid.UUID,
        debit_transaction_id: uuid.UUID,
        credit_transaction_id: uuid.UUID,
        confidence_score: float = None,
        is_confirmed: bool = True
    ) -> Transfer:
        """Create a transfer link between two transactions"""
        # Get transactions
        debit_tx = db.get(Transaction, debit_transaction_id)
        credit_tx = db.get(Transaction, credit_transaction_id)
        
        if not debit_tx or not credit_tx:
            raise ValueError("Transaction not found")
        
        if debit_tx.user_id != user_id or credit_tx.user_id != user_id:
            raise ValueError("Unauthorized")
        
        # Create transfer
        transfer = Transfer(
            user_id=user_id,
            debit_transaction_id=debit_transaction_id,
            credit_transaction_id=credit_transaction_id,
            amount=abs(debit_tx.amount),
            transfer_date=debit_tx.transaction_date,
            confidence_score=confidence_score,
            is_confirmed=is_confirmed
        )
        
        # Update transaction types
        debit_tx.transaction_type = 'transfer'
        credit_tx.transaction_type = 'transfer'
        
        db.add(transfer)
        db.add(debit_tx)
        db.add(credit_tx)
        db.commit()
        db.refresh(transfer)
        
        return transfer
    
    @staticmethod
    def delete_transfer(db: Session, transfer_id: uuid.UUID, user_id: uuid.UUID):
        """Unlink a transfer"""
        transfer = db.get(Transfer, transfer_id)
        if not transfer or transfer.user_id != user_id:
            raise ValueError("Transfer not found")
        
        # Revert transaction types
        debit_tx = db.get(Transaction, transfer.debit_transaction_id)
        credit_tx = db.get(Transaction, transfer.credit_transaction_id)
        
        if debit_tx:
            debit_tx.transaction_type = 'expense'
            db.add(debit_tx)
        
        if credit_tx:
            credit_tx.transaction_type = 'income'
            db.add(credit_tx)
        
        db.delete(transfer)
        db.commit()
