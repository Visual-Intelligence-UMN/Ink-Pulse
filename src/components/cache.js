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

// ✅ Export entire DB to a file
export async function exportDB() {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, 'readonly');
  const store = tx.objectStore(STORE_NAME);
  const data = [];

  return new Promise((resolve, reject) => {
    const cursor = store.openCursor();
    cursor.onsuccess = (e) => {
      const cur = e.target.result;
      if (cur) {
        data.push({ key: cur.key, value: cur.value });
        cur.continue();
      } else {
        const blob = new Blob([JSON.stringify(data)], { type: 'application/octet-stream' });
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

// ✅ Import DB from a .bin file
async function importDBFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const raw = reader.result;
        const items = JSON.parse(new TextDecoder().decode(raw));

        const db = await openDB();
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        for (const { key, value } of items) {
          store.put(value, key);
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

// ✅ Trigger file input to start import
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

export const searchPatternSet = writable([]);

// Load initial value from IndexedDB
getFromDB(CACHE_KEY)
  .then(data => {
    searchPatternSet.set(data);
    console.log('Loaded from IndexedDB:', data);
  })
  .catch(err => {
    console.warn('Failed to load from IndexedDB:', err);
  });

// Subscribe to changes and save to IndexedDB
searchPatternSet.subscribe(value => {
  saveToDB(CACHE_KEY, value)
    .then(() => console.log('Saved to IndexedDB:', value))
    .catch(err => console.warn('Failed to save to IndexedDB:', err));
});
