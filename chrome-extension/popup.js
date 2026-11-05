document.addEventListener('DOMContentLoaded', () => {
  const inputText = document.getElementById('inputText');
  const outputText = document.getElementById('outputText');
  const btnClear = document.getElementById('btnClear');
  const btnCopy = document.getElementById('btnCopy');
  const copyBtnText = document.getElementById('copyBtnText');
  const btnSwap = document.getElementById('btnSwap');
  const charCount = document.getElementById('charCount');
  const directionText = document.getElementById('directionText');
  const toggleBadge = document.getElementById('toggleFieldBadge');

  const btnAuto = document.getElementById('btn-auto');
  const btnToAr = document.getElementById('btn-to-ar');
  const btnToEn = document.getElementById('btn-to-en');

  let currentMode = 'auto';

  // Load and listen to settings
  if (chrome.storage && chrome.storage.local && toggleBadge) {
    chrome.storage.local.get({ showFieldBadge: true }, (res) => {
      toggleBadge.checked = res.showFieldBadge !== false;
    });

    toggleBadge.addEventListener('change', () => {
      chrome.storage.local.set({ showFieldBadge: toggleBadge.checked });
    });
  }

  function updateConversion() {
    const text = inputText.value || '';
    charCount.textContent = `${text.length} حرف`;

    if (!text) {
      outputText.value = '';
      directionText.textContent = 'كشف تلقائي جاهز';
      return;
    }

    const detected = KeyConverter.detectLanguage(text);
    if (currentMode === 'auto') {
      directionText.textContent = detected === 'to_arabic' ? 'English ➔ عربي' : 'عربي ➔ English';
    } else if (currentMode === 'to_arabic') {
      directionText.textContent = 'تحويل إجباري ➔ عربي';
    } else {
      directionText.textContent = 'تحويل إجباري ➔ English';
    }

    outputText.value = KeyConverter.convert(text, currentMode);
  }

  inputText.addEventListener('input', updateConversion);

  btnClear.addEventListener('click', () => {
    inputText.value = '';
    outputText.value = '';
    updateConversion();
    inputText.focus();
  });

  btnCopy.addEventListener('click', async () => {
    if (!outputText.value) return;
    try {
      await navigator.clipboard.writeText(outputText.value);
      btnCopy.classList.add('copied');
      copyBtnText.textContent = '✓ تم النسخ!';
      setTimeout(() => {
        btnCopy.classList.remove('copied');
        copyBtnText.textContent = 'نسخ النتيجة';
      }, 1500);
    } catch (e) {
      console.error(e);
    }
  });

  btnSwap.addEventListener('click', () => {
    const temp = inputText.value;
    inputText.value = outputText.value;
    outputText.value = temp;
    updateConversion();
  });

  function setMode(mode, activeBtn) {
    currentMode = mode;
    [btnAuto, btnToAr, btnToEn].forEach((b) => b && b.classList.remove('active'));
    if (activeBtn) activeBtn.classList.add('active');
    updateConversion();
  }

  if (btnAuto) btnAuto.addEventListener('click', () => setMode('auto', btnAuto));
  if (btnToAr) btnToAr.addEventListener('click', () => setMode('to_arabic', btnToAr));
  if (btnToEn) btnToEn.addEventListener('click', () => setMode('to_english', btnToEn));

  inputText.focus();
  updateConversion();
});
