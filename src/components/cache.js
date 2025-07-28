import { writable } from 'svelte/store';

const DB_NAME = 'myCacheDB';
const STORE_NAME = 'cacheStore';
const CACHE_KEY = 'searchPatternSet';

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getFromDB(key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.get(key);
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

async function saveToDB(key, value) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const req = store.put(value, key);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}

export async function exportDB() {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, 'readonly');
  const store = tx.objectStore(STORE_NAME);
  const entries = [];

  return new Promise((resolve, reject) => {
    const cursor = store.openCursor();
    cursor.onsuccess = (e) => {
      const cur = e.target.result;
      if (cur) {
        entries.push({ key: cur.key, value: cur.value });
        cur.continue();
      } else {
        const blob = new Blob([JSON.stringify(entries)], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${DB_NAME}.bin`;
        a.click();
        URL.revokeObjectURL(url);
        console.log('Export complete');
        resolve();
      }
    };
    cursor.onerror = () => reject(cursor.error);
  });
}

async function importDBFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const raw = reader.result;
        const importedItems = JSON.parse(new TextDecoder().decode(raw));

        const db = await openDB();
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);

        for (const { key, value: importedValue } of importedItems) {
          const getRequest = store.get(key);

          getRequest.onsuccess = () => {
            const existingValue = getRequest.result;
            let mergedValue;

            if (key === CACHE_KEY) {
              const existingItems = Array.isArray(existingValue) ? existingValue : [];
              const incomingItems = Array.isArray(importedValue) ? importedValue : [];

              const existingIds = new Set(existingItems.map(item => item.id));
              const newItems = incomingItems.filter(item => !existingIds.has(item.id));
              mergedValue = [...existingItems, ...newItems];

              console.log(`Merged ${newItems.length} new items into ${key}`);
            } else if (Array.isArray(existingValue) && Array.isArray(importedValue)) {
              mergedValue = [...existingValue, ...importedValue];
            } else if (
              existingValue && importedValue &&
              typeof existingValue === 'object' &&
              typeof importedValue === 'object'
            ) {
              mergedValue = { ...existingValue, ...importedValue };
            } else {
              mergedValue = importedValue;
            }

            store.put(mergedValue, key);
          };

          getRequest.onerror = () => {
            store.put(importedValue, key);
          };
        }

        tx.oncomplete = () => {
          console.log('Import complete');
          resolve();
        };
        tx.onerror = () => reject(tx.error);
      } catch (e) {
        reject(e);
      }
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(file);
  });
}

export function triggerImport() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.bin';
  input.onchange = () => {
    const file = input.files[0];
    if (file) importDBFromFile(file);
  };
  input.click();
}

// Svelte writable store synced to IndexedDB
export const searchPatternSet = writable([]);

getFromDB(CACHE_KEY)
  .then(initialValue => {
    searchPatternSet.set(initialValue);
    // console.log('Loaded from IndexedDB:', initialValue);

    searchPatternSet.subscribe(value => {
      saveToDB(CACHE_KEY, value)
        // .then(() => console.log('Saved to IndexedDB:', value))
        .catch(err => console.warn('Failed to save to IndexedDB:', err));
    });
  })
  .catch(err => {
    console.warn('Failed to load from IndexedDB:', err);
  });


export async function loadPattern(path = 'static/patterns/load') {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Failed to load directory listing from ${path}`);

    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const links = Array.from(doc.querySelectorAll('a'))
      .map(a => a.getAttribute('href'))
      .filter(href => href && !href.startsWith('?') && !href.startsWith('/'))
      .filter(href => href.endsWith('.bin') || href.endsWith('.json'));

    for (const file of links) {
      const fileUrl = `${path}/${file}`;
      const res = await fetch(fileUrl);
      const blob = await res.blob();
      await importDBFromFile(blob);
    }

    console.log(`Successfully imported ${links.length} pattern files from ${path}`);
  } catch (err) {
    console.error('loadPattern failed:', err);
  }
}


/*
✅ Console Tool Usage:

  Export DB:
    import('/src/components/cache.js').then(mod => mod.exportDB())

  Import & merge:
    import('/src/components/cache.js').then(mod => mod.triggerImport())

  Clear DB:
    indexedDB.deleteDatabase('myCacheDB')
*/
