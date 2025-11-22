import os
from google import genai
from google.genai import types
from app.core.config import settings
import json
from typing import List, Dict, Any
from datetime import datetime

class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )
        self.model = "gemini-3-pro-preview" 
        
    def detect_structure(self, sample_content: str, file_type: str, bank_name: str = "") -> Dict[str, Any]:
        """
        Detect the structure of the bank statement from a sample.
        Returns: { "header_row_index": int, "date_col": "...", ... }
        """

        prompt = ""
        if file_type == 'pdf':
            prompt = f"""
You are a financial data extraction expert. I'm providing you with a SAMPLE (text extracted from PDF) of a bank statement from {bank_name}.

**IMPORTANT:** PDF text extraction often causes issues:
- Descriptions may wrap across multiple lines
- Columns may merge together without clear spacing
- Example: "23-Jul-2025 23-Jul-2025 UPI/CR/520424270100/SUBHAYU\\nKUMAR BA LA/HDFC/9382877751/NA0.00 300.00 300.00"

Your task is to **Create a Python Regular Expression (Regex)** that can extract transaction data.

**Strategy:** Look for patterns that identify a transaction line, typically:
1. Starts with a date (e.g., "23-Jul-2025")
2. Has another date (value date)
3. Followed by description text
4. Ends with numeric amounts (withdrawal, deposit, balance)

**Requirements:**
1. Use `re.DOTALL` mode if needed (`.` matches newlines)
2. Make description group flexible: `(?P<description>.*?)` should be lazy but match across lines if needed
3. Make withdrawal/deposit OPTIONAL groups (use `?:` for non-capturing, `?` for optional)
4. Named groups needed:
   - `date`: Transaction date (required)
   - `description`: The narration/details (required, can be multi-line)
   - `withdrawal`: Debit amount (OPTIONAL)
   - `deposit`: Credit amount (OPTIONAL)
   - `balance`: Closing balance (OPTIONAL but helps validate)

5. Date format string for Python's strptime

**Example regex approach:**
```
(?P<date>\\d{{2}}-[A-Za-z]{{3}}-\\s?\\d{{4}})\\s+\\d{{2}}-[A-Za-z]{{3}}-\\s?\\d{{4}}\\s+(?P<description>.*?)\\s+(?P<withdrawal>[\\d,]+\\.\\d{{2}})?\\s*(?P<deposit>[\\d,]+\\.\\d{{2}})?\\s*(?P<balance>[\\d,]+\\.\\d{{2}})
```

Return JSON:
{{
  "transaction_regex": "YOUR_REGEX_HERE",
  "date_format": "%d-%b-%Y",
  "amount_type": "separate",
  "use_dotall": true
}}

Sample text:

{sample_content}

Output ONLY valid JSON. Ensure regex is escaped for JSON (double backslashes).
"""
        else:
            # CSV/Excel Prompt
            prompt = f"""
You are a financial data extraction expert. I'm providing you with a SAMPLE (first few rows) of a raw bank statement from {bank_name} in {file_type} format. Each line is indexed starting from 0.

Your task is to:
1. **Find the Header Row:** Identify the row index (0-based) that contains the column names for the transaction table. It usually contains words like 'Date', 'Description', 'Amount', 'Balance', etc.
2. **Identify Column Mappings:** Based on that header row, identify the column names.

Identify:
1. 'header_row_index': The 0-based index of the row containing the headers.
2. 'date_col': The exact column name containing the transaction date.
3. 'date_format': The Python datetime format string that matches the date column (e.g., "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y"). Be precise.
4. 'desc_col': The exact column name containing the description/particulars/narration.
5. 'amount_type': "single" (one column) or "separate" (credit/debit columns).
6. 'amount_col': The column name for amount (if amount_type is "single").
7. 'credit_col': The column name for credit/deposit (if amount_type is "separate").
8. 'debit_col': The column name for debit/withdrawal (if amount_type is "separate").

Return a JSON object with this structure:
{{
  "header_row_index": 12,
  "date_col": "Transaction Date",
  "date_format": "%d/%m/%Y",
  "desc_col": "Particulars",
  "amount_type": "separate",
  "credit_col": "Credit",
  "debit_col": "Debit",
  "amount_col": null
}}

Here's the sample data (raw CSV dump):

{sample_content}

Output ONLY valid JSON.
"""
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            thinkingConfig={
                "thinkingLevel": "HIGH",
            },
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            if response.text:
                return json.loads(response.text)
            return {}
            
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return {}

gemini_service = GeminiService()
