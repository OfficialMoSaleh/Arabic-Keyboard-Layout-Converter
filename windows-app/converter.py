"""
Arabic-English Keyboard Layout Converter
Maps character keystrokes between standard US QWERTY and Arabic 101/102 keyboard layouts.
Includes automatic Caps Lock detection.
"""

EN_TO_AR = {
    '`': 'ذ', '~': 'ّ',
    'q': 'ض', 'Q': 'َ',
    'w': 'ص', 'W': 'ً',
    'e': 'ث', 'E': 'ُ',
    'r': 'ق', 'R': 'ٌ',
    't': 'ف', 'T': 'لإ',
    'y': 'غ', 'Y': 'إ',
    'u': 'ع', 'U': '‘',
    'i': 'ه', 'I': '÷',
    'o': 'خ', 'O': '×',
    'p': 'ح', 'P': '؛',
    '[': 'ج', '{': '<',
    ']': 'د', '}': '>',
    'a': 'ش', 'A': 'ِ',
    's': 'س', 'S': 'ٍ',
    'd': 'ي', 'D': ']',
    'f': 'ب', 'F': '[',
    'g': 'ل', 'G': 'لأ',
    'h': 'ا', 'H': 'أ',
    'j': 'ت', 'J': 'ـ',
    'k': 'ن', 'K': '،',
    'l': 'م', 'L': '/',
    ';': 'ك', ':': ':',
    "'": 'ط', '"': '"',
    'z': 'ئ', 'Z': '~',
    'x': 'ء', 'X': 'ْ',
    'c': 'ؤ', 'C': '}',
    'v': 'ر', 'V': '{',
    'b': 'لا', 'B': 'لآ',
    'n': 'ى', 'N': 'آ',
    'm': 'ة', 'M': '’',
    ',': 'و', '<': ',',
    '.': 'ز', '>': '.',
    '/': 'ظ', '?': '؟'
}

AR_TO_EN_LIGATURES = {
    'لآ': 'B',
    'لأ': 'G',
    'لإ': 'T',
    'لا': 'b'
}

AR_TO_EN = {}
for en_char, ar_char in EN_TO_AR.items():
    if ar_char not in AR_TO_EN_LIGATURES:
        AR_TO_EN[ar_char] = en_char

AR_TO_EN.update({
    '‘': 'U',
    '÷': 'I',
    '×': 'O',
    '؛': 'P',
    '،': 'K',
    'ـ': 'J',
    '؟': '?',
    '’': 'M'
})

def detect_language(text: str) -> str:
    """Returns 'to_arabic' or 'to_english' based on majority character count."""
    ar_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    en_count = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    return 'to_arabic' if en_count >= ar_count else 'to_english'

def convert_en_to_ar(text: str) -> str:
    # Caps Lock detection: if uppercase letters outnumber lowercase
    upper_cnt = sum(1 for c in text if 'A' <= c <= 'Z')
    lower_cnt = sum(1 for c in text if 'a' <= c <= 'z')
    is_caps_lock = upper_cnt > 0 and upper_cnt >= lower_cnt

    res = []
    for ch in text:
        if is_caps_lock and 'A' <= ch <= 'Z':
            ch = ch.lower()
        res.append(EN_TO_AR.get(ch, ch))
    return "".join(res)

def convert_ar_to_en(text: str) -> str:
    res = []
    i = 0
    n = len(text)
    while i < n:
        if i + 1 < n and text[i:i+2] in AR_TO_EN_LIGATURES:
            res.append(AR_TO_EN_LIGATURES[text[i:i+2]])
            i += 2
        else:
            res.append(AR_TO_EN.get(text[i], text[i]))
            i += 1
    return "".join(res)

def convert(text: str, force_direction: str = 'auto') -> str:
    if not text:
        return ""
    
    direction = force_direction
    if direction == 'auto':
        direction = detect_language(text)
    
    if direction == 'to_arabic':
        return convert_en_to_ar(text)
    else:
        return convert_ar_to_en(text)
