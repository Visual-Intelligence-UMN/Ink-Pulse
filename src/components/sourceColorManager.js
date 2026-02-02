import { writable } from 'svelte/store';


const DEFAULT_PALETTE = [
  "#66C2A5", 
  "#FC8D62", 
  "#8DA0CB", 
  "#E78AC3", 
  "#A6D854", 
  "#FFD92F", 
  "#E5C494", 
  "#B3B3B3", 
  "#66C2A5", 
];

// Default source mapping
const DEFAULT_SOURCE_MAPPING = {
  user: "#66C2A5",
  api: "#FC8D62",
};

//storage key
const STORAGE_KEY = 'inkpulse_source_colors';

/**
 * load custom colors from localStorage
 */
function loadCustomColors() {
  if (typeof window === 'undefined') return {};
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.warn('Failed to load custom colors:', error);
    return {};
  }
}

/**
 * 保存自定义颜色到 localStorage
 */
function saveCustomColors(colors) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(colors));
  } catch (error) {
    console.warn('Failed to save custom colors:', error);
  }
}

/**
 * Color manager class
 */
class SourceColorManager {
  constructor() {
    // load custom colors
    this.customColors = loadCustomColors();
    
    // auto assigned colors mapping
    this.autoAssignedColors = new Map();
    
    // known sources set
    this.knownSources = new Set(Object.keys(DEFAULT_SOURCE_MAPPING));
    
    // Svelte store for reactive updates
    this.colorsStore = writable(this.getAllColors());
  }

  /**
   * get color for a given source
   * @param {string} source - source name
   * @returns {string} color value (hexadecimal)
   */
  getColor(source) {
    if (!source) return DEFAULT_PALETTE[0];

    // 1. use custom colors first
    if (this.customColors[source]) {
      return this.customColors[source];
    }

    // 2. use default mapping
    if (DEFAULT_SOURCE_MAPPING[source]) {
      return DEFAULT_SOURCE_MAPPING[source];
    }

    // 3. auto assign new color
    if (!this.autoAssignedColors.has(source)) {
      const index = this.autoAssignedColors.size % DEFAULT_PALETTE.length;
      this.autoAssignedColors.set(source, DEFAULT_PALETTE[index]);
      this.knownSources.add(source);
    }

    return this.autoAssignedColors.get(source);
  }

  /**
   * set custom color
   * @param {string} source - source name
   * @param {string} color - color value
   */
  setCustomColor(source, color) {
    this.customColors[source] = color;
    saveCustomColors(this.customColors);
    this.colorsStore.set(this.getAllColors());
  }

  /**
   * reset color to default value
   * @param {string} source - source name
   */
  resetColor(source) {
    delete this.customColors[source];
    saveCustomColors(this.customColors);
    this.colorsStore.set(this.getAllColors());
  }

  /**
   * reset all colors to default value
   */
  resetAllColors() {
    this.customColors = {};
    saveCustomColors(this.customColors);
    this.colorsStore.set(this.getAllColors());
  }

  /**
   * get all known sources and their colors
   * @returns {Object} source to color mapping
   */
  getAllColors() {
    const colors = {};
    for (const source of this.knownSources) {
      colors[source] = this.getColor(source);
    }
    return colors;
  }

  /**
   * register new sources (for pre-loading data)
   * @param {string[]} sources - source name array
   */
  registerSources(sources) {
    sources.forEach(source => {
      if (source) {
        this.knownSources.add(source);
        // trigger color assignment (if needed)
        this.getColor(source);
      }
    });
    this.colorsStore.set(this.getAllColors());
  }

  /**
   * get all known sources
   * @returns {string[]} source name array
   */
  getKnownSources() {
    return Array.from(this.knownSources);
  }

  
  subscribe(callback) {
    return this.colorsStore.subscribe(callback);
  }
}


const sourceColorManager = new SourceColorManager();


export { sourceColorManager, SourceColorManager };
export default sourceColorManager;
