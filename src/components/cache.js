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
