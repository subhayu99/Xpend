import uuid

def hash_transaction(date: str, amount: float, description: str, account_id: uuid.UUID, index: int = 0) -> str:
    """
    Generates a unique hash for a transaction to prevent duplicates.
    Format: "{date}_{amount}_{description}_{account_id}_{index}"
    """
    # Normalize inputs
    date_str = str(date).split('T')[0] # Use only YYYY-MM-DD
    desc_norm = description.strip().lower()
    amount_str = f"{float(amount):.2f}"
    
    # Create a unique string signature
    signature = f"{date_str}_{amount_str}_{desc_norm}_{account_id}_{index}"
    
    # Generate UUID using uuid3 (MD5 based)
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, signature))
