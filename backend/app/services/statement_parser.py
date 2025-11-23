import pandas as pd
import io
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from app.services.gemini_service import gemini_service
from app.models.template import StatementTemplate
from app.utils.merchant_normalizer import MerchantNormalizer

class StatementParserService:
    """Service for parsing bank statements using templates or AI detection"""
    
    @staticmethod
    def _extract_text_from_pdf(file_bytes: bytes) -> str:
        pdf = PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in pdf.pages:
            text.append(page.extract_text())
        return "\n".join(text)

    @staticmethod
    def _find_transaction_table(df: pd.DataFrame) -> tuple:
        """
        Intelligently find the transaction table in the DataFrame.
        Returns: (header_row_index, data_start_row_index)
        """
        # Keywords grouped by category
        date_keywords = ['date', 'txn date', 'transaction date', 'value date']
        desc_keywords = ['description', 'particulars', 'narration', 'details', 'transaction details', 'remarks']
        amount_keywords = ['amount', 'debit', 'credit', 'withdrawal', 'deposit', 'balance']
        
        # Look for rows that contain keywords from multiple categories
        for idx, row in df.iterrows():
            # Convert row to string and lowercase
            row_str = ' '.join([str(val).lower() for val in row if pd.notna(val)])
            
            has_date = any(k in row_str for k in date_keywords)
            has_desc = any(k in row_str for k in desc_keywords)
            has_amt = any(k in row_str for k in amount_keywords)
            
            # Strong match: Has Date AND Description AND Amount
            # This avoids matching summary rows which usually only have amounts/balances
            if has_date and has_desc and has_amt:
                return int(idx), int(idx) + 1
            
            # Medium match: Has Date AND (Description OR Amount) AND matches count >= 4
            # (To handle cases where description might be named weirdly or amount is implicit)
            all_keywords = date_keywords + desc_keywords + amount_keywords
            matches = sum(1 for k in all_keywords if k in row_str)
            
            if has_date and matches >= 4:
                 return int(idx), int(idx) + 1
        
        # Fallback: assume header is at row 0
        return 0, 1
    
    @staticmethod
    def _clean_dataframe(df: pd.DataFrame, header_row: int) -> pd.DataFrame:
        """
        Clean the DataFrame by:
        1. Setting proper headers
        2. Removing empty rows
        3. Removing rows that are clearly not transactions
        """
        # Set the header
        if header_row > 0:
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row + 1:].reset_index(drop=True)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # Remove rows where most columns are empty (likely separator rows)
        threshold = len(df.columns) * 0.3  # At least 30% of columns should have data
        df = df.dropna(thresh=threshold)
        
        # Remove rows that look like totals/summaries (common patterns)
        if len(df) > 0 and 'Particulars' in df.columns:
            df = df[~df['Particulars'].astype(str).str.lower().str.contains(
                'total|opening balance|closing balance|balance brought forward|balance carried forward',
                na=False
            )]
        
        return df.reset_index(drop=True)

    @staticmethod
    def _read_tabular_file(file_bytes: bytes, file_ext: str, header_row: int = 0) -> pd.DataFrame:
        if file_ext == 'csv':
            return pd.read_csv(io.BytesIO(file_bytes), header=header_row)
        elif file_ext in ['xls', 'xlsx']:
            return pd.read_excel(io.BytesIO(file_bytes), header=header_row)
        return pd.DataFrame()

    @staticmethod
    def parse_with_template(file_bytes: bytes, file_ext: str, template: StatementTemplate) -> List[Dict[str, Any]]:
        """Parse file using a known template structure"""
        config = template.structure
        transactions = []
        
        if file_ext in ['csv', 'xls', 'xlsx']:
            # Tabular parsing logic
            try:
                header_row = config.get('header_row', 0)
                df = StatementParserService._read_tabular_file(file_bytes, file_ext, header_row)                
                
                # Map columns
                date_col = config.get('date_col')
                desc_col = config.get('desc_col')
                amount_col = config.get('amount_col')
                credit_col = config.get('credit_col') # Optional separate credit column
                debit_col = config.get('debit_col')   # Optional separate debit column

                rows, cols = df.shape
                
                for row_num, (_, row) in enumerate(df.iterrows()):
                    try:
                        # Extract Date
                        date_str = str(row[date_col])
                        # Basic date parsing (can be improved with dateutil)
                        # For now, let's try to use pandas to_datetime flexibility or the format if provided
                        tx_date = pd.to_datetime(date_str, dayfirst=True).to_pydatetime()
                        
                        # Extract Description
                        description = str(row[desc_col])
                        
                        # Extract Amount
                        amount = 0.0
                        if amount_col:
                            # Single column with +/- or just positive numbers
                            val = row[amount_col]
                            if isinstance(val, str):
                                val = val.replace(',', '').replace(' ', '')
                            amount = float(val)
                        elif credit_col and debit_col:
                            # Separate columns
                            credit = row[credit_col] if pd.notna(row[credit_col]) else 0
                            debit = row[debit_col] if pd.notna(row[debit_col]) else 0
                            
                            # Clean strings if needed
                            if isinstance(credit, str): credit = float(credit.replace(',', ''))
                            if isinstance(debit, str): debit = float(debit.replace(',', ''))
                            
                            amount = float(credit) - float(debit)
                        
                        # Determine type
                        tx_type = "income" if amount > 0 else "expense"

                        if rows - row_num <= 20:
                            print("vals: ", tx_date, description, amount, tx_type)
                        
                        if pd.isna(tx_date) or pd.isna(description) or pd.isna(amount) or amount == 0:
                            continue

                        # Extract and normalize merchant name
                        merchant_name = MerchantNormalizer.extract_merchant_name(description)

                        transactions.append({
                            "transaction_date": tx_date.isoformat(),
                            "description": description,
                            "amount": amount,
                            "transaction_type": tx_type,
                            "merchant_name": merchant_name
                        })
                    except Exception as e:
                        print(f"Skipping row due to error: {e}")
                        continue
                        
            except Exception as e:
                print(f"Template parsing failed: {e}")
                # Fallback?
                return []

        elif file_ext == 'pdf':
            # PDF Template parsing using saved regex
            try:
                full_text = StatementParserService._extract_text_from_pdf(file_bytes)
                transactions = StatementParserService.parse_with_structure(None, config, full_text=full_text)
            except Exception as e:
                print(f"PDF template parsing failed: {e}")
                return []
            
        return transactions
            
    @staticmethod
    def parse_with_structure(df: pd.DataFrame, structure: Dict[str, Any], full_text: str = None) -> List[Dict[str, Any]]:
        """Parse DataFrame OR Text using the detected structure"""
        print(f"Parsing with structure: {structure}")
        
        transactions = []

        # Check if we have a regex for PDF parsing
        if 'transaction_regex' in structure and full_text:
            regex_pattern = structure['transaction_regex']
            date_format = structure.get('date_format')
            
            print(f"Using Regex: {regex_pattern}")
            print(f"Parsing text (first 2000 chars):\n{full_text[:2000]}\n{'='*50}")
            
            # Check if we should use DOTALL mode
            regex_flags = re.MULTILINE
            if structure.get('use_dotall'):
                regex_flags = re.MULTILINE | re.DOTALL
            
            try:
                matches = re.finditer(regex_pattern, full_text, regex_flags)
                for match in matches:
                    try:
                        groups = match.groupdict()
                        
                        # Date
                        raw_date = groups.get('date', '').strip()
                        dt = None
                        try:
                            if date_format:
                                # Handle potential spaces in date format if regex captured them
                                dt = datetime.strptime(raw_date, date_format)
                            else:
                                from dateutil import parser
                                dt = parser.parse(raw_date)
                        except:
                            # Try fuzzy parsing
                            try:
                                from dateutil import parser
                                dt = parser.parse(raw_date)
                            except:
                                continue
                        
                        if not dt: continue
                        
                        # Description
                        description = groups.get('description', '').strip().replace('\n', '')
                        
                        # Amount
                        amount = 0.0
                        withdrawal = groups.get('withdrawal')
                        deposit = groups.get('deposit')
                        amt_single = groups.get('amount')
                        
                        def clean_amt(v):
                            if not v: return 0.0
                            # Remove currency symbols, commas, etc.
                            s = str(v).replace(',', '').replace(' ', '')
                            # Keep only digits, dot, minus
                            s = ''.join(c for c in s if c.isdigit() or c in '.-')
                            return float(s) if s else 0.0

                        if withdrawal or deposit:
                            w_val = clean_amt(withdrawal)
                            d_val = clean_amt(deposit)
                            amount = d_val - w_val
                        elif amt_single:
                            amount = clean_amt(amt_single)
                            
                        if amount == 0: continue
                        
                        # Extract and normalize merchant name
                        merchant_name = MerchantNormalizer.extract_merchant_name(description)
                        
                        transactions.append({
                            "transaction_date": dt.isoformat(),
                            "description": description,
                            "amount": amount,
                            "transaction_type": "income" if amount > 0 else "expense",
                            "merchant_name": merchant_name
                        })
                    except Exception as e:
                        print(f"Error parsing match: {e}")
                        continue
            except Exception as e:
                print(f"Regex error: {e}")
                return []
            
            return transactions
        
        # Normalize DataFrame columns (strip whitespace)
        if df is not None:
            df.columns = [str(c).strip() for c in df.columns]
            print(f"DataFrame columns (normalized): {df.columns.tolist()}")
        
        # Get column names from structure and strip whitespace
        date_col = (structure.get('date_col') or '').strip()
        date_format = structure.get('date_format')
        desc_col = (structure.get('desc_col') or '').strip()
        amount_type = (structure.get('amount_type') or 'single')
        amount_col = (structure.get('amount_col') or '').strip()
        credit_col = (structure.get('credit_col') or '').strip()
        debit_col = (structure.get('debit_col') or '').strip()
        
        # Validate required columns exist
        if df is None or date_col not in df.columns or desc_col not in df.columns:
            print(f"Missing columns: {date_col} or {desc_col} not in {df.columns if df is not None else 'N/A'}")
            return []

        for _, row in df.iterrows():
            try:
                # Date Parsing
                raw_date = str(row[date_col])
                dt = None
                try:
                    if date_format:
                        dt = datetime.strptime(raw_date, date_format)
                    else:
                        from dateutil import parser
                        dt = parser.parse(raw_date)
                except ValueError:
                    # Fallback
                    try:
                        from dateutil import parser
                        dt = parser.parse(raw_date)
                    except:
                        continue
                
                if not dt: continue

                # Description
                description = str(row[desc_col])
                
                # Amount
                amount = 0.0
                if amount_type == 'single' and amount_col and amount_col in df.columns:
                    val = str(row[amount_col])
                    # Remove currency symbols and commas
                    val = ''.join(c for c in val if c.isdigit() or c in '.-')
                    if val:
                        amount = float(val)
                elif amount_type == 'separate' and credit_col in df.columns and debit_col in df.columns:
                    def clean_amt(v):
                        s = str(v)
                        s = ''.join(c for c in s if c.isdigit() or c == '.')
                        return float(s) if s else 0.0
                    
                    credit = clean_amt(row[credit_col]) if pd.notna(row[credit_col]) else 0.0
                    debit = clean_amt(row[debit_col]) if pd.notna(row[debit_col]) else 0.0
                    
                    amount = credit - debit
                
                # Skip invalid or zero amounts
                if amount == 0: continue
                
                # Extract and normalize merchant name
                merchant_name = MerchantNormalizer.extract_merchant_name(description)
                
                transactions.append({
                    "transaction_date": dt.isoformat(),
                    "description": description,
                    "amount": amount,
                    "transaction_type": "income" if amount > 0 else "expense",
                    "merchant_name": merchant_name
                })
            except Exception as e:
                # print(f"Skipping row: {e}")
                continue
                
        return transactions

    @staticmethod
    def _apply_ai_merchant_extraction(transactions: List[Dict[str, Any]], bank_name: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Use AI to generate a regex pattern for merchant extraction and apply it.

        Args:
            transactions: List of parsed transactions with descriptions
            bank_name: Bank name for context

        Returns:
            Tuple of (updated transactions, regex pattern used or None)
        """
        if not transactions:
            return transactions, None

        # Collect unique descriptions
        unique_descriptions = list(set(tx.get('description', '') for tx in transactions if tx.get('description')))

        if not unique_descriptions:
            return transactions, None

        print(f"Extracting merchants from {len(unique_descriptions)} unique descriptions using AI...")

        # Ask Gemini for a regex pattern
        regex_result = gemini_service.get_merchant_extraction_regex(unique_descriptions, bank_name)

        if not regex_result or 'regex' not in regex_result:
            print("AI did not return a valid regex pattern, falling back to normalizer")
            return transactions, None

        regex_pattern = regex_result['regex']
        print(f"AI generated regex: {regex_pattern}")

        # Apply the regex to extract merchants
        all_descriptions = [tx.get('description', '') for tx in transactions]
        merchant_map = gemini_service.extract_merchants_batch(all_descriptions, regex_pattern)

        # Update transactions with extracted merchant names
        for tx in transactions:
            desc = tx.get('description', '')
            if desc and desc in merchant_map:
                tx['merchant_name'] = merchant_map[desc]

        print(f"Extracted merchants for {len(merchant_map)} descriptions")
        return transactions, regex_pattern

    @staticmethod
    async def process_upload(file: UploadFile, bank_name: str, template: Optional[StatementTemplate] = None) -> Dict[str, Any]:
        """
        Process an uploaded file.
        If template is provided, use it.
        If not, use AI to detect structure and parse.

        After parsing, uses AI to extract merchant names from descriptions.

        Returns: { "transactions": [...], "detected_template": {...}, "merchant_regex": "..." }
        """
        file_ext = file.filename.split('.')[-1].lower()
        file_bytes = await file.read()
        await file.seek(0)

        result = {
            "transactions": [],
            "template_found": False,
            "detected_structure": None,
            "merchant_regex": None
        }

        # 1. Try parsing with existing template
        if template and template.file_type == file_ext:
            print(f"Using existing template for {bank_name}")
            txs = StatementParserService.parse_with_template(file_bytes, file_ext, template)
            if txs:
                # Apply AI merchant extraction
                txs, merchant_regex = StatementParserService._apply_ai_merchant_extraction(txs, bank_name)
                result["transactions"] = txs
                result["template_found"] = True
                result["merchant_regex"] = merchant_regex
                return result

        # 2. If no template or parsing failed, use AI to detect structure
        print(f"No template found or parsing failed. Using AI for {bank_name}")

        df_clean = pd.DataFrame()
        content_sample = ""
        full_text = "" # Initialize full_text for PDF
        header_row = 0

        if file_ext in ['csv', 'xls', 'xlsx']:
            # Read file without assuming header position (header=None)
            df = pd.read_excel(io.BytesIO(file_bytes), header=None) if file_ext in ['xls', 'xlsx'] else pd.read_csv(io.BytesIO(file_bytes), header=None)

            # Take a sample of the raw data (first 50 rows) to send to AI
            # We convert to CSV string so AI can see the structure including empty rows/cells
            df_sample = df.head(50)
            content_sample = df_sample.to_csv(index=True, header=False)

        elif file_ext == 'pdf':
            # Extract ALL text for parsing
            full_text = StatementParserService._extract_text_from_pdf(file_bytes)
            # Sample for AI (first 3000 chars)
            content_sample = full_text[:3000]

        # Ask AI for structure AND header row index (or regex)
        structure = gemini_service.detect_structure(content_sample, file_ext, bank_name)

        if structure:
            header_row = structure.get("header_row_index", 0)
            print(f"AI detected structure: {structure}")

            if file_ext in ['csv', 'xls', 'xlsx']:
                # Re-read with the AI-detected header
                df_clean = pd.read_excel(io.BytesIO(file_bytes), header=header_row) if file_ext in ['xls', 'xlsx'] else pd.read_csv(io.BytesIO(file_bytes), header=header_row)

                # Clean the dataframe (remove empty rows, etc.)
                df_clean = StatementParserService._clean_dataframe(df_clean, 0)

                result["transactions"] = StatementParserService.parse_with_structure(df_clean, structure)
                result["detected_structure"] = structure
            elif file_ext == 'pdf':
                # Parse using regex on full text
                result["transactions"] = StatementParserService.parse_with_structure(None, structure, full_text=full_text)
                result["detected_structure"] = structure

        # Apply AI merchant extraction to parsed transactions
        if result["transactions"]:
            result["transactions"], result["merchant_regex"] = StatementParserService._apply_ai_merchant_extraction(
                result["transactions"], bank_name
            )

        return result
