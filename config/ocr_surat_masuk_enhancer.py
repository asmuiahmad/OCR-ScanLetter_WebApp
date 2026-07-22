"""
OCR Surat Masuk Enhancer
=========================
Peningkatan khusus untuk OCR surat masuk dengan pattern recognition
"""

import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SuratMasukOCREnhancer:
    def __init__(self):
        # Pattern khusus untuk surat masuk
        self.surat_masuk_patterns = {
            # Pattern untuk jenis surat
            'permohonan_patterns': [
                r'permoh\s*onan',
                r'per\s*moh\s*onan',
                r'per\s*mohonan',
                r'permoho\s*nan',
            ],
            
            # Pattern untuk sidang
            'sidang_patterns': [
                r'sidang\s+secara\s+vir\s*tual',
                r'sidang\s+vir\s*tual',
                r'vir\s*tual\s+sidang',
                r'sidang\s+online',
                r'sidang\s+daring',
            ],
            
            # Pattern untuk tempat
            'tempat_patterns': [
                r'ruang\s+sidang',
                r'ruang\s*sidang',
                r'aula\s+pengadilan',
                r'gedung\s+pengadilan',
                r'kantor\s+pengadilan',
            ],
            
            # Pattern untuk waktu
            'waktu_patterns': [
                r'pukul\s+(\d{1,2})[:\.](\d{2})\s*(wib|wita|wit)',
                r'jam\s+(\d{1,2})[:\.](\d{2})\s*(wib|wita|wit)',
                r'pada\s+pukul\s+(\d{1,2})[:\.](\d{2})',
            ]
        }
        
        # Konteks surat masuk yang umum
        self.context_corrections = {
            # Konteks permohonan
            'permohonan_context': {
                'permoh onan sidang': 'permohonan sidang',
                'permoh onan untuk': 'permohonan untuk',
                'permoh onan agar': 'permohonan agar',
                'mohon dike naan': 'mohon dikenaan',
                'mohon diper kenan kan': 'mohon diperkenankan',
                'dengan hor mat': 'dengan hormat',
                'kami sam paikan': 'kami sampaikan',
            },
            
            # Konteks sidang
            'sidang_context': {
                'sidang secara vir tual': 'sidang secara virtual',
                'sidang vir tual': 'sidang virtual',
                'sidang dar ing': 'sidang daring',
                'sidang on line': 'sidang online',
                'hadir dalam sidang': 'hadir dalam sidang',
                'mengha diri sidang': 'menghadiri sidang',
            },
            
            # Konteks waktu dan tempat
            'waktu_tempat_context': {
                'hari tang gal': 'hari tanggal',
                'tang gal': 'tanggal',
                'puk ul': 'pukul',
                'ber tempat di': 'bertempat di',
                'di laksana kan': 'dilaksanakan',
                'akan di adakan': 'akan diadakan',
            }
        }

    def enhance_surat_masuk_text(self, text: str, field_type: str = 'general') -> str:
        """
        Enhance teks surat masuk berdasarkan konteks dan pattern
        """
        if not text:
            return ""
        
        enhanced_text = text
        
        # Apply context-specific corrections
        if field_type == 'isi_surat':
            enhanced_text = self._enhance_isi_surat(enhanced_text)
        elif field_type == 'pengirim':
            enhanced_text = self._enhance_pengirim(enhanced_text)
        elif field_type == 'penerima':
            enhanced_text = self._enhance_penerima(enhanced_text)
        elif field_type == 'acara':
            enhanced_text = self._enhance_acara(enhanced_text)
        elif field_type == 'tempat':
            enhanced_text = self._enhance_tempat(enhanced_text)
        
        # Apply general enhancements
        enhanced_text = self._apply_general_enhancements(enhanced_text)
        
        return enhanced_text

    def _enhance_isi_surat(self, text: str) -> str:
        """Enhance isi surat dengan pattern recognition"""
        enhanced = text.lower()
        
        # Fix permohonan patterns
        for pattern in self.surat_masuk_patterns['permohonan_patterns']:
            enhanced = re.sub(pattern, 'permohonan', enhanced, flags=re.IGNORECASE)
        
        # Fix sidang patterns
        for pattern in self.surat_masuk_patterns['sidang_patterns']:
            enhanced = re.sub(pattern, 'sidang secara virtual', enhanced, flags=re.IGNORECASE)
        
        # Apply context corrections
        for context_type, corrections in self.context_corrections.items():
            for broken, fixed in corrections.items():
                enhanced = re.sub(re.escape(broken), fixed, enhanced, flags=re.IGNORECASE)
        
        # Fix common legal phrases
        legal_phrases = {
            'dengan ini mengaju kan': 'dengan ini mengajukan',
            'mohon kepada bapak': 'mohon kepada Bapak',
            'mohon kepada ibu': 'mohon kepada Ibu',
            'yang ter hormat': 'yang terhormat',
            'atas per hatian nya': 'atas perhatiannya',
            'kami ucap kan': 'kami ucapkan',
            'terima ka sih': 'terima kasih',
        }
        
        for broken, fixed in legal_phrases.items():
            enhanced = re.sub(re.escape(broken), fixed, enhanced, flags=re.IGNORECASE)
        
        return enhanced

    def _enhance_pengirim(self, text: str) -> str:
        """Enhance field pengirim"""
        enhanced = text
        
        # Fix common sender patterns
        sender_fixes = {
            'advo kat': 'Advokat',
            'kuasa hukum': 'Kuasa Hukum',
            'pen ggugat': 'Penggugat',
            'ter gugat': 'Tergugat',
            'pem ohon': 'Pemohon',
            'ter mohon': 'Termohon',
        }
        
        for broken, fixed in sender_fixes.items():
            enhanced = re.sub(re.escape(broken), fixed, enhanced, flags=re.IGNORECASE)
        
        return enhanced

    def _enhance_penerima(self, text: str) -> str:
        """Enhance field penerima"""
        enhanced = text
        
        # Fix common receiver patterns
        receiver_fixes = {
            'ketua pengadilan agama': 'Ketua Pengadilan Agama',
            'ke tua pengadilan': 'Ketua Pengadilan',
            'yang ter hormat': 'Yang Terhormat',
            'yth': 'Yth.',
            'bapak ketua': 'Bapak Ketua',
            'ibu ketua': 'Ibu Ketua',
        }
        
        for broken, fixed in receiver_fixes.items():
            enhanced = re.sub(re.escape(broken), fixed, enhanced, flags=re.IGNORECASE)
        
        return enhanced

    def _enhance_acara(self, text: str) -> str:
        """Enhance field acara"""
        enhanced = text
        
        # Fix event-related terms
        event_fixes = {
            'sidang per kara': 'sidang perkara',
            'sidang per data': 'sidang perdana',
            'sidang pem buktian': 'sidang pembuktian',
            'sidang pu tusan': 'sidang putusan',
            'mediasi': 'Mediasi',
            'eksepsi': 'Eksepsi',
        }
        
        for broken, fixed in event_fixes.items():
            enhanced = re.sub(re.escape(broken), fixed, enhanced, flags=re.IGNORECASE)
        
        return enhanced

    def _enhance_tempat(self, text: str) -> str:
        """Enhance field tempat"""
        enhanced = text
        
        # Fix place-related terms
        place_fixes = {
            'ruang sidang': 'Ruang Sidang',
            'ruang me diasi': 'Ruang Mediasi',
            'gedung pengadilan': 'Gedung Pengadilan',
            'kantor pengadilan': 'Kantor Pengadilan',
            'aula': 'Aula',
            'secara vir tual': 'secara virtual',
            'via zoom': 'via Zoom',
            'via google meet': 'via Google Meet',
        }
        
        for broken, fixed in place_fixes.items():
            enhanced = re.sub(re.escape(broken), fixed, enhanced, flags=re.IGNORECASE)
        
        return enhanced

    def _apply_general_enhancements(self, text: str) -> str:
        """Apply general text enhancements"""
        enhanced = text
        
        # Fix spacing issues
        enhanced = re.sub(r'\s+', ' ', enhanced)  # Multiple spaces to single
        enhanced = re.sub(r'\s*([,.;:!?])\s*', r'\1 ', enhanced)  # Fix punctuation spacing
        
        # Fix common OCR character mistakes
        char_fixes = {
            'l ': 'I ',  # lowercase L to uppercase I at word boundaries
            ' l ': ' I ',  # standalone lowercase L
            '0': 'O',  # Zero to O in text context (be careful with this)
        }
        
        # Apply character fixes carefully
        for broken, fixed in char_fixes.items():
            if broken == '0' and not re.search(r'\d', enhanced):  # Only if no other digits
                enhanced = enhanced.replace(broken, fixed)
            else:
                enhanced = enhanced.replace(broken, fixed)
        
        # Capitalize first letter of sentences
        enhanced = re.sub(r'(^|[.!?]\s+)([a-z])', 
                         lambda m: m.group(1) + m.group(2).upper(), enhanced)
        
        return enhanced.strip()

    def detect_surat_type(self, text: str) -> str:
        """
        Deteksi jenis surat berdasarkan konten
        """
        text_lower = text.lower()
        
        # Pattern untuk berbagai jenis surat
        surat_types = {
            'permohonan_sidang': [
                'permohonan', 'sidang', 'menghadiri', 'hadir'
            ],
            'pemberitahuan': [
                'pemberitahuan', 'memberitahukan', 'disampaikan'
            ],
            'undangan': [
                'undangan', 'mengundang', 'hadir', 'acara'
            ],
            'panggilan': [
                'panggilan', 'memanggil', 'wajib hadir'
            ]
        }
        
        scores = {}
        for surat_type, keywords in surat_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[surat_type] = score
        
        # Return type with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return 'umum'

    def get_enhancement_suggestions(self, original_text: str, enhanced_text: str) -> List[Dict]:
        """
        Get list of enhancements made to the text
        """
        suggestions = []
        
        if original_text != enhanced_text:
            # Find specific changes
            original_words = original_text.lower().split()
            enhanced_words = enhanced_text.lower().split()
            
            # Simple diff to find changes
            for i, (orig, enh) in enumerate(zip(original_words, enhanced_words)):
                if orig != enh:
                    suggestions.append({
                        'position': i,
                        'original': orig,
                        'enhanced': enh,
                        'type': 'word_correction'
                    })
        
        return suggestions

# Global instance
surat_masuk_enhancer = SuratMasukOCREnhancer()