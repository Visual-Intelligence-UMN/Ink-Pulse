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

// ✅ Import and merge DB from a .bin file
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

        for (const { key, value: newValue } of importedItems) {
          const getRequest = store.get(key);

          getRequest.onsuccess = () => {
            const existingValue = getRequest.result;

            let mergedValue;

            if (key === 'searchPatternSet') {
              const existingList = Array.isArray(existingValue) ? existingValue : [];
              const importedList = Array.isArray(newValue) ? newValue : [];

              const existingIds = new Set(existingList.map(item => item.id));
              const filteredNew = importedList.filter(item => !existingIds.has(item.id));

              mergedValue = [...existingList, ...filteredNew];
              console.log(`Merged ${filteredNew.length} new patterns into ${key}`);
            } else if (Array.isArray(existingValue) && Array.isArray(newValue)) {
              mergedValue = [...existingValue, ...newValue];
            } else if (
              existingValue && newValue &&
              typeof existingValue === 'object' &&
              typeof newValue === 'object'
            ) {
              mergedValue = { ...existingValue, ...newValue };
            } else {
              mergedValue = newValue;
            }

            store.put(mergedValue, key);
          };

          getRequest.onerror = () => {
            store.put(newValue, key);
          };
        }

        tx.oncomplete = () => {
          console.log('Import (with id-filter merge) complete');
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

// ✅ Svelte store setup
export const searchPatternSet = writable([]);

// Load initial value from IndexedDB and then subscribe to save changes
getFromDB(CACHE_KEY)
  .then(data => {
    searchPatternSet.set(data);
    console.log('Loaded from IndexedDB:', data);

    searchPatternSet.subscribe(value => {
      saveToDB(CACHE_KEY, value)
        .then(() => console.log('Saved to IndexedDB:', value))
        .catch(err => console.warn('Failed to save to IndexedDB:', err));
    });
  })
  .catch(err => {
    console.warn('Failed to load from IndexedDB:', err);
  });

/*
Console Tool Usage:

  Export the database in console:
  import('/src/components/cache.js').then(mod => mod.exportDB())

  Import a .bin file and merge it:
  import('/src/components/cache.js').then(mod => mod.triggerImport())

  Clear the cache:
  indexedDB.deleteDatabase('myCacheDB')
*/