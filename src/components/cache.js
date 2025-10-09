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
        // 找到searchPatternSet数据
        const searchPatternEntry = entries.find(entry => entry.key === CACHE_KEY);
        if (searchPatternEntry && Array.isArray(searchPatternEntry.value)) {
          const patterns = searchPatternEntry.value;
          
          if (patterns.length === 0) {
            alert('No patterns to export');
            resolve();
            return;
          }

          // 为每个pattern创建独立文件
          patterns.forEach((pattern, index) => {
            const patternData = {
              key: CACHE_KEY,
              value: [pattern] // 单个pattern包装成数组
            };
            
            const blob = new Blob([JSON.stringify([patternData])], { 
              type: 'application/octet-stream' 
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // 使用pattern名称和ID作为文件名
            const safeName = (pattern.name || 'Unnamed').replace(/[^a-zA-Z0-9]/g, '_');
            const fileName = `${safeName}_${pattern.id}_${pattern.dataset}.bin`;
            a.download = fileName;
            
            // 延迟下载，避免浏览器阻止多个下载
            setTimeout(() => {
              a.click();
              URL.revokeObjectURL(url);
            }, index * 100);
          });
          
          console.log(`Export complete: ${patterns.length} pattern files created`);
        } else {
          // 如果没有patterns，导出所有数据（兼容性）
          const blob = new Blob([JSON.stringify(entries)], { 
            type: 'application/octet-stream' 
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${DB_NAME}_all.bin`;
          a.click();
          URL.revokeObjectURL(url);
          console.log('Export complete: all data exported');
        }
        
        resolve();
      }
    };
    cursor.onerror = () => reject(cursor.error);
  });
}

// 导出单个pattern
export async function exportSinglePattern(patternId) {
  const db = await openDB();
  const tx = db.transaction(STORE_NAME, 'readonly');
  const store = tx.objectStore(STORE_NAME);
  
  return new Promise((resolve, reject) => {
    const req = store.get(CACHE_KEY);
    req.onsuccess = () => {
      const patterns = req.result || [];
      const pattern = patterns.find(p => p.id === patternId);
      
      if (!pattern) {
        alert('Pattern not found');
        resolve();
        return;
      }

      const patternData = {
        key: CACHE_KEY,
        value: [pattern]
      };
      
      const blob = new Blob([JSON.stringify([patternData])], { 
        type: 'application/octet-stream' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      const safeName = (pattern.name || 'Unnamed').replace(/[^a-zA-Z0-9]/g, '_');
      const fileName = `${safeName}_${pattern.id}_${pattern.dataset}.bin`;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);
      
      console.log(`Single pattern exported: ${fileName}`);
      resolve();
    };
    req.onerror = () => reject(req.error);
  });
}

async function importDBFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const raw = reader.result;
        if (!(raw instanceof ArrayBuffer)) {
          throw new Error('Invalid file format: expected binary data');
        }
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

        tx.oncomplete = async () => {
          console.log('Import complete');
          // Refresh the store with updated data
          try {
            const updatedData = await getFromDB(CACHE_KEY);
            searchPatternSet.set(updatedData);
            console.log('Store updated with imported data:', updatedData);
          } catch (error) {
            console.warn('Failed to refresh store:', error);
          }
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
  return new Promise((resolve, reject) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.bin';
    
    // Handle file selection
    input.onchange = async () => {
      const file = input.files[0];
      if (file) {
        try {
          console.log('Starting import of file:', file.name, 'Size:', file.size);
          await importDBFromFile(file);
          console.log('Import completed successfully!');
          resolve();
        } catch (error) {
          console.error('Import failed:', error);
          reject(error);
        }
      } else {
        resolve(); // No file selected
      }
    };
    
    // Handle file dialog cancellation
    input.oncancel = () => {
      resolve(); // User cancelled file selection
    };
    
    input.click();
  });
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

  export async function loadPattern(dir = '/static/patterns/load') {
  try {
    const listRes = await fetch(`${dir}/filelist.json`);
    if (!listRes.ok)
      throw new Error(`Cannot read ${dir}/filelist.json — status ${listRes.status}`);
    const fileNames = await listRes.json();

    for (const name of fileNames) {
      const fileRes = await fetch(`${dir}/${name}`);
      if (!fileRes.ok) {
        console.warn(`Skip ${name}: HTTP ${fileRes.status}`);
        continue;
      }
      const blob = await fileRes.blob();
      const file = new File([blob], name, { type: blob.type || 'application/octet-stream' });
      await importDBFromFile(file);  
      console.info(`✔ Imported ${name}`);
    }

    console.info(`loadPattern(): finished — ${fileNames.length} file(s) processed.`);
  } catch (err) {
    console.error('loadPattern(): failed →', err);
    throw err;   
  }
}


/*
✅ Console Tool Usage:

  Export all patterns as separate files:
    import('/src/components/cache.js').then(mod => mod.exportDB())

  Export single pattern:
    import('/src/components/cache.js').then(mod => mod.exportSinglePattern('pattern_1234567890'))

  Import & merge:
    import('/src/components/cache.js').then(mod => mod.triggerImport())

  Clear DB:
    indexedDB.deleteDatabase('myCacheDB')
*/
