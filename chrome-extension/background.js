// Background service worker

const MENU_ID = 'convert-text-arabic-english';
const BLOCKED_PREFIXES = [
  'chrome://', 'chrome-extension://', 'chrome-search://', 'chrome-untrusted://',
  'edge://', 'about:', 'view-source:', 'devtools://', 'moz-extension://'
];
const BLOCKED_HOSTS = ['chromewebstore.google.com', 'chrome.google.com/webstore', 'microsoftedge.microsoft.com/addons'];

function createMenu() {
  // removeAll first so a reload/update never hits "duplicate id"
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: '🔄 تحويل الكتابة (عربي ⇋ إنجليزي)',
      contexts: ['selection', 'editable']
    }, () => void chrome.runtime.lastError);
  });
}

chrome.runtime.onInstalled.addListener(createMenu);
chrome.runtime.onStartup.addListener(createMenu);

function isRestricted(url) {
  if (!url) return false; // unknown: try anyway
  return BLOCKED_PREFIXES.some((p) => url.startsWith(p)) || BLOCKED_HOSTS.some((h) => url.includes(h));
}

function sendToTab(tabId, options) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, { action: 'convert_selection' }, options || {}, () => {
      resolve(!chrome.runtime.lastError);
    });
  });
}

async function triggerConversionInTab(tab, frameId) {
  if (!tab || !tab.id || isRestricted(tab.url)) return;

  const options = typeof frameId === 'number' ? { frameId } : undefined;
  if (await sendToTab(tab.id, options)) return;

  // No receiver: the tab was opened before the extension was installed/updated.
  // activeTab (granted by the shortcut / menu click) lets us inject on demand.
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id, allFrames: true },
      files: ['converter.js', 'content.js']
    });
    await new Promise((r) => setTimeout(r, 150));
    await sendToTab(tab.id, options);
  } catch (e) {
    // Injection blocked by policy for this page - nothing else we can do.
  }
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === MENU_ID) triggerConversionInTab(tab, info.frameId);
});

chrome.commands.onCommand.addListener((command, tab) => {
  if (command !== 'convert-text') return;
  if (tab && tab.id) {
    triggerConversionInTab(tab);
    return;
  }
  chrome.tabs.query({ active: true, lastFocusedWindow: true }, (tabs) => {
    if (tabs && tabs[0]) triggerConversionInTab(tabs[0]);
  });
});

// Child frames ask us to show their toast in the top frame (never clipped by small iframes).
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg && msg.action === 'show_toast' && sender.tab && sender.tab.id) {
    chrome.tabs.sendMessage(sender.tab.id, { action: 'toast', text: msg.text, ok: msg.ok }, { frameId: 0 }, () => void chrome.runtime.lastError);
  }
});
