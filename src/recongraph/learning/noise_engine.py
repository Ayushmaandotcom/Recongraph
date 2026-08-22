import random
from datetime import date, timedelta
from typing import Dict, Any

class NoiseEngine:
    """
    Procedurally mutates clean GST records into realistic errors.
    """
    @staticmethod
    def ocr_mutation(s: str) -> str:
        """Simulates OCR or typo errors."""
        if not s: return s
        chars = list(s)
        # Select 1-2 random characters to mutate
        num_mutations = random.randint(1, min(2, len(chars)))
        for _ in range(num_mutations):
            idx = random.randint(0, len(chars) - 1)
            c = chars[idx]
            if c == '0': chars[idx] = 'O'
            elif c == 'O': chars[idx] = '0'
            elif c == '1': chars[idx] = 'I'
            elif c == 'I': chars[idx] = '1'
            elif c == 'B': chars[idx] = '8'
            elif c == '8': chars[idx] = 'B'
            elif c == '5': chars[idx] = 'S'
            elif c == 'S': chars[idx] = '5'
            elif c == 'Z': chars[idx] = '2'
            elif c == '2': chars[idx] = 'Z'
            else:
                # Random char insertion/deletion
                if random.random() < 0.5:
                    chars[idx] = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                else:
                    chars[idx] = '' # deletion
        return "".join(chars)

    @staticmethod
    def format_mutation(s: str) -> str:
        """Strips or replaces hyphens and slashes commonly found in invoice numbers."""
        if not s: return s
        if random.random() < 0.33:
            return s.replace("-", "").replace("/", "")
        elif random.random() < 0.66:
            return s.replace("-", "/")
        else:
            return s.replace("/", "-")

    @staticmethod
    def date_mutation(d: str) -> str:
        """Swaps DD/MM for dates where DD <= 12 or shifts by a small margin."""
        if not d: return d
        try:
            dt = date.fromisoformat(d)
        except ValueError:
            return d

        if random.random() < 0.5 and dt.day <= 12:
            # Swap month and day
            try:
                new_dt = date(dt.year, dt.day, dt.month)
                return new_dt.isoformat()
            except ValueError:
                pass
        
        # Shift by ±1-3 days (e.g. data entry lag)
        shift = random.randint(1, 3) * random.choice([-1, 1])
        new_dt = dt + timedelta(days=shift)
        return new_dt.isoformat()

    @staticmethod
    def tax_mutation(amount: float) -> float:
        """Introduces rounding errors or small fat-finger typos."""
        amount = float(amount)
        if random.random() < 0.5:
            # Rounding error +/- 1 to 5
            return round(amount + random.uniform(-5.0, 5.0), 2)
        else:
            # 10x or 0.1x magnitude error (decimal shift)
            if random.random() < 0.5:
                return round(amount * 10, 2)
            else:
                return round(amount / 10, 2)
