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


// Import & Export the store

// Export cache to JSON file (triggered from console)
export async function exportCacheToJson() {
  try {
    const data = await getFromDB(CACHE_KEY);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'cache_export.json';
    a.click();

    URL.revokeObjectURL(url);
    console.log('✅ Cache exported as JSON');
  } catch (err) {
    console.error('❌ Failed to export cache:', err);
  }
}

// Import cache from JSON file (triggered from console, handles file picker)
export async function importCacheFromJson() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';

  input.onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const json = JSON.parse(text);
      if (!Array.isArray(json)) throw new Error('Invalid format: expected an array.');

      await saveToDB(CACHE_KEY, json);
      searchPatternSet.set(json);
      console.log('✅ Cache imported successfully:', json);
    } catch (err) {
      console.error('❌ Failed to import cache:', err);
    }
  };

  input.click();
}


// console commands for testing

// export: 
// import('/src/components/cache.js').then(m => m.exportCacheToJson());

// import: 
// import('/src/components/cache.js').then(m => m.importCacheFromJson());

// Clear cache
// indexedDB.deleteDatabase('myCacheDB');
