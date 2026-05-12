"""
OCR Text Post-Processor for Surat Masuk
==========================================
Module for fixing OCR output that is fragmented and inaccurate
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class OCRTextProcessor:
    def __init__(self):
        # Dictionary for fixing common words in official letters
        self.word_corrections = {
            # Kata-kata yang sering terpotong dalam OCR
            'permoh onan': 'permohonan',
            'permoh nan': 'permohonan',
            'per mohonan': 'permohonan',
            'per moh onan': 'permohonan',
            'sidang secara vir tual': 'sidang secara virtual',
            'vir tual': 'virtual',
            'vir tu al': 'virtual',
            'vir-tual': 'virtual',
            'peng adilan': 'pengadilan',
            'pen gadilan': 'pengadilan',
            'penga dilan': 'pengadilan',
            'mah kamah': 'mahkamah',
            'mah ka mah': 'mahkamah',
            'ma hkamah': 'mahkamah',
            'agung republik': 'agung republik',
            'repub lik': 'republik',
            'repu blik': 'republik',
            'indo nesia': 'indonesia',
            'indone sia': 'indonesia',
            'ber kenaan': 'berkenaan',
            'ber ke naan': 'berkenaan',
            'berke naan': 'berkenaan',
            'den gan': 'dengan',
            'de ngan': 'dengan',
            'ter hormat': 'terhormat',
            'ter hor mat': 'terhormat',
            'terhor mat': 'terhormat',
            'atas per hatian': 'atas perhatian',
            'per hatian': 'perhatian',
            'perha tian': 'perhatian',
            'per ha tian': 'perhatian',
            'disa mpaikan': 'disampaikan',
            'disam paikan': 'disampaikan',
            'di sampaikan': 'disampaikan',
            'meng hadiri': 'menghadiri',
            'meng ha diri': 'menghadiri',
            'mengha diri': 'menghadiri',
            'aca ra': 'acara',
            'ac ara': 'acara',
            'tem pat': 'tempat',
            'tem-pat': 'tempat',
            'wak tu': 'waktu',
            'wak-tu': 'waktu',
            'tang gal': 'tanggal',
            'tang-gal': 'tanggal',
            'tan ggal': 'tanggal',
            'jam': 'jam',
            'puk ul': 'pukul',
            'pu kul': 'pukul',
            'wib': 'WIB',
            'wita': 'WITA',
            'wit': 'WIT',
            'demi kian': 'demikian',
            'demi ki an': 'demikian',
            'demiki an': 'demikian',
            'sam paikan': 'sampaikan',
            'samp aikan': 'sampaikan',
            'terima kasih': 'terima kasih',
            'teri ma kasih': 'terima kasih',
            'terimaka sih': 'terima kasih',
            'hormat kami': 'hormat kami',
            'hor mat kami': 'hormat kami',
            'hormatkami': 'hormat kami',
            'wasser lam': 'wassalam',
            'wasser-lam': 'wassalam',
            'was salam': 'wassalam',
            'alaiku m': 'alaikum',
            'alai kum': 'alaikum',
            'sala mu': 'salamu',
            'sala-mu': 'salamu',
        }
        
        # Patterns for words that are often wrong in legal context
        self.legal_terms = {
            'peng adilan agama': 'Pengadilan Agama',
            'pen gadilan agama': 'Pengadilan Agama',
            'penga dilan agama': 'Pengadilan Agama',
            'mah kamah agung': 'Mahkamah Agung',
            'mah ka mah agung': 'Mahkamah Agung',
            'ma hkamah agung': 'Mahkamah Agung',
            'ketua pengadilan': 'Ketua Pengadilan',
            'ke tua pengadilan': 'Ketua Pengadilan',
            'pani tera': 'Panitera',
            'pani-tera': 'Panitera',
            'pan itera': 'Panitera',
            'sekre taris': 'Sekretaris',
            'sekreta ris': 'Sekretaris',
            'sek retaris': 'Sekretaris',
            'hakim': 'Hakim',
            'ha kim': 'Hakim',
            'juru sita': 'Juru Sita',
            'juru-sita': 'Juru Sita',
            'jurusita': 'Juru Sita',
        }
        
        # Patterns for letter numbers that are often wrong
        self.number_patterns = [
            (r'(\d+)\s*/\s*([A-Z]+)\s*/\s*(\d+)', r'\1/\2/\3'),  # Format nomor surat
            (r'(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+)', r'\1.\2.\3'),  # Format tanggal
            (r'No\s*\.\s*(\d+)', r'No. \1'),  # Nomor dengan spasi
            (r'Hal\s*:\s*(.+)', r'Hal: \1'),  # Format hal
        ]
        
        # Words that should be capitalized
        self.capitalize_words = [
            'pengadilan', 'agama', 'mahkamah', 'agung', 'republik', 'indonesia',
            'ketua', 'panitera', 'sekretaris', 'hakim', 'allah', 'swt', 'saw',
            'bismillah', 'assalamualaikum', 'wassalamualaikum', 'wib', 'wita', 'wit'
        ]

    def clean_ocr_text(self, text: str) -> str:
        """
        Clean and fix OCR text output
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Step 1: Basic normalization
        cleaned_text = self._normalize_text(text)
        
        # Step 2: Fix broken words
        cleaned_text = self._fix_broken_words(cleaned_text)
        
        # Step 3: Fix legal terms
        cleaned_text = self._fix_legal_terms(cleaned_text)
        
        # Step 4: Fix number and date formats
        cleaned_text = self._fix_number_formats(cleaned_text)
        
        # Step 5: Fix capitalization
        cleaned_text = self._fix_capitalization(cleaned_text)
        
        # Step 6: Final cleanup
        cleaned_text = self._final_cleanup(cleaned_text)
        
        return cleaned_text.strip()

    def _normalize_text(self, text: str) -> str:
        """Basic text normalization"""
        # Hapus karakter aneh dan normalize whitespace
        text = re.sub(r'[^\w\s\.,;:!?\-/()"\']', ' ', text)
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single
        
        # Fix punctuation that is stuck together
        text = re.sub(r'(\w)([,.;:!?])', r'\1 \2', text)
        text = re.sub(r'([,.;:!?])(\w)', r'\1 \2', text)
        
        return text

    def _fix_broken_words(self, text: str) -> str:
        """Fix broken/split words"""
        # Convert to lowercase for matching
        text_lower = text.lower()
        
        # Apply word corrections
        for broken_word, correct_word in self.word_corrections.items():
            # Case insensitive replacement
            pattern = re.escape(broken_word)
            text_lower = re.sub(pattern, correct_word, text_lower, flags=re.IGNORECASE)
        
        # Fix common pattern of excessive spaces within words
        # Example: "per moh onan" -> "permohonan"
        common_patterns = [
            (r'\b(\w{2,3})\s+(\w{2,3})\s+(\w{2,3})\b', self._merge_if_valid),
            (r'\b(\w{3,4})\s+(\w{3,4})\b', self._merge_if_valid),
        ]
        
        for pattern, handler in common_patterns:
            text_lower = re.sub(pattern, handler, text_lower)
        
        return text_lower

    def _merge_if_valid(self, match) -> str:
        """Merge kata jika menghasilkan kata yang valid"""
        parts = match.groups()
        merged = ''.join(parts)
        
        # Daftar kata-kata valid yang sering terpotong
        valid_merged_words = [
            'permohonan', 'pengadilan', 'mahkamah', 'republik', 'indonesia',
            'berkenaan', 'dengan', 'terhormat', 'perhatian', 'disampaikan',
            'menghadiri', 'demikian', 'wassalam', 'alaikum', 'virtual',
            'sekretaris', 'panitera', 'bismillah', 'assalamualaikum'
        ]
        
        if merged.lower() in valid_merged_words:
            return merged
        
        # If not valid, return with fixed spacing
        return ' '.join(parts)

    def _fix_legal_terms(self, text: str) -> str:
        """Fix legal terms"""
        for broken_term, correct_term in self.legal_terms.items():
            pattern = re.escape(broken_term)
            text = re.sub(pattern, correct_term, text, flags=re.IGNORECASE)
        
        return text

    def _fix_number_formats(self, text: str) -> str:
        """Fix letter number and date formats"""
        for pattern, replacement in self.number_patterns:
            text = re.sub(pattern, replacement, text)
        
        return text

    def _fix_capitalization(self, text: str) -> str:
        """Fix capitalization of important words"""
        words = text.split()
        fixed_words = []
        
        for i, word in enumerate(words):
            word_clean = re.sub(r'[^\w]', '', word.lower())
            
            # Kapitalisasi kata-kata penting
            if word_clean in self.capitalize_words:
                # Pertahankan tanda baca
                if word_clean == word.lower().strip('.,;:!?'):
                    word = word.replace(word_clean, word_clean.title())
                else:
                    word = word_clean.title()
            
            # Kapitalisasi awal kalimat
            elif i == 0 or (i > 0 and words[i-1].endswith(('.', '!', '?'))):
                word = word.capitalize()
            
            fixed_words.append(word)
        
        return ' '.join(fixed_words)

    def _final_cleanup(self, text: str) -> str:
        """Final cleanup"""
        # Fix excessive spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix punctuation
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        text = re.sub(r'([,.;:!?])\s*([,.;:!?])', r'\1\2', text)
        
        # Fix paragraph format
        text = re.sub(r'\.\s*([a-z])', lambda m: '. ' + m.group(1).upper(), text)
        
        return text

    def process_surat_masuk_fields(self, surat_data: Dict) -> Dict:
        """
        Process all fields in surat masuk data
        """
        processed_data = surat_data.copy()
        
        # Field yang perlu diproses
        text_fields = [
            'pengirim_suratMasuk',
            'penerima_suratMasuk', 
            'isi_suratMasuk',
            'acara_suratMasuk',
            'tempat_suratMasuk'
        ]
        
        for field in text_fields:
            if field in processed_data and processed_data[field]:
                original_text = processed_data[field]
                cleaned_text = self.clean_ocr_text(original_text)
                processed_data[field] = cleaned_text
                
                # Log perbaikan jika ada perubahan signifikan
                if len(original_text) > 10 and original_text != cleaned_text:
                    logger.info(f"OCR correction for {field}:")
                    logger.info(f"  Original: {original_text[:100]}...")
                    logger.info(f"  Cleaned:  {cleaned_text[:100]}...")
        
        return processed_data

    def get_text_quality_score(self, text: str) -> float:
        """
        Calculate text quality score (0-1)
        """
        if not text:
            return 0.0
        
        # Quality factors
        factors = []
        
        # 1. Ratio of words vs odd characters
        words = re.findall(r'\b\w+\b', text)
        if len(text) > 0:
            word_ratio = len(' '.join(words)) / len(text)
            factors.append(word_ratio)
        
        # 2. Average word length (very short words indicate poor OCR)
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            length_score = min(avg_word_length / 5.0, 1.0)  # Optimal ~5 karakter
            factors.append(length_score)
        
        # 3. Ratio of excessive spaces
        excessive_spaces = len(re.findall(r'\s{2,}', text))
        space_score = max(0, 1 - (excessive_spaces / len(text.split())))
        factors.append(space_score)
        
        # 4. Presence of common Indonesian words
        common_words = ['dan', 'atau', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada', 'yang', 'adalah']
        found_common = sum(1 for word in common_words if word in text.lower())
        common_score = min(found_common / 5.0, 1.0)
        factors.append(common_score)
        
        # Average of all factors
        return sum(factors) / len(factors) if factors else 0.0

# Instance global untuk digunakan di seluruh aplikasi
ocr_processor = OCRTextProcessor()