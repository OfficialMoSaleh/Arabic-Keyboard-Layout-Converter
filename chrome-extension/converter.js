// Keyboard Layout Mappings between US QWERTY and Arabic 101
(function () {
  const enToAr = {
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
  };

  const arToEnLigatures = {
    'لآ': 'B',
    'لأ': 'G',
    'لإ': 'T',
    'لا': 'b'
  };

  const arToEn = {};
  for (const [en, ar] of Object.entries(enToAr)) {
    if (!arToEnLigatures[ar]) {
      arToEn[ar] = en;
    }
  }

  arToEn['‘'] = 'U';
  arToEn['÷'] = 'I';
  arToEn['×'] = 'O';
  arToEn['؛'] = 'P';
  arToEn['،'] = 'K';
  arToEn['ـ'] = 'J';
  arToEn['؟'] = '?';
  arToEn['’'] = 'M';

  function detectLanguage(text) {
    let arCount = 0;
    let enCount = 0;

    for (let i = 0; i < text.length; i++) {
      const code = text.charCodeAt(i);
      const ch = text[i];
      if (code >= 0x0600 && code <= 0x06FF) {
        arCount++;
      } else if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
        enCount++;
      }
    }

    return enCount >= arCount ? 'to_arabic' : 'to_english';
  }

  function convertEnglishToArabic(text) {
    // Detect Caps Lock: if text contains English letters and is mostly uppercase
    let upperCount = 0;
    let lowerCount = 0;
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (ch >= 'A' && ch <= 'Z') upperCount++;
      else if (ch >= 'a' && ch <= 'z') lowerCount++;
    }

    // Caps Lock is active if uppercase letters are the majority
    const isCapsLock = upperCount > 0 && upperCount >= lowerCount;

    let result = '';
    for (let i = 0; i < text.length; i++) {
      let ch = text[i];
      // If Caps Lock was on, normalize uppercase English letters to lowercase
      if (isCapsLock && ch >= 'A' && ch <= 'Z') {
        ch = ch.toLowerCase();
      }
      result += enToAr[ch] !== undefined ? enToAr[ch] : ch;
    }
    return result;
  }

  function convertArabicToEnglish(text) {
    let result = '';
    let i = 0;
    const n = text.length;
    while (i < n) {
      if (i + 1 < n) {
        const pair = text.substring(i, i + 2);
        if (arToEnLigatures[pair]) {
          result += arToEnLigatures[pair];
          i += 2;
          continue;
        }
      }
      const ch = text[i];
      result += arToEn[ch] !== undefined ? arToEn[ch] : ch;
      i++;
    }
    return result;
  }

  function convert(text, forceDirection = 'auto') {
    if (!text) return '';
    let direction = forceDirection;
    if (direction === 'auto') {
      direction = detectLanguage(text);
    }

    if (direction === 'to_arabic') {
      return convertEnglishToArabic(text);
    } else {
      return convertArabicToEnglish(text);
    }
  }

  const KeyConverter = {
    convert,
    convertEnglishToArabic,
    convertArabicToEnglish,
    detectLanguage
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyConverter;
  }
  if (typeof globalThis !== 'undefined') {
    globalThis.KeyConverter = KeyConverter;
  }
  if (typeof window !== 'undefined') {
    window.KeyConverter = KeyConverter;
  }
})();
