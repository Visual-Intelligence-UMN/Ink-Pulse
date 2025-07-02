<script>
  import { onMount } from "svelte";
  import "chartjs-adapter-date-fns";
  import { writable } from "svelte/store";
  import { tick } from "svelte";
  import { base } from "$app/paths";
  import tippy from "tippy.js";
  import "tippy.js/dist/tippy.css";
  import { get } from "svelte/store";
  import LineChart from "../components/lineChart.svelte";
  import BarChartY from "../components/barChartY.svelte";
  import ZoomoutChart from "../components/zoomoutChart.svelte";
  import * as d3 from "d3";
  import PatternChartPreview from "../components/patternChartPreview.svelte";
  import PatternChartPreviewSerach from "../components/patternChartPreviewSerach.svelte";
  import SkeletonLoading from "../components/skeletonLoading.svelte";
  import { resolve } from "chart.js/helpers";
  import { VList } from "virtua/svelte";
  import { topicIcons, getCategoryIcon } from "../components/topicIcons.js";
  import SemanticExpansionCircle from "../components/scoreIcon.svelte";
  import '../components/styles.css';
  import LineChartPreview from "../components/lineChartPreview.svelte";
  
  let chartRefs = {};
  function resetZoom(sessionId) {
    chartRefs[sessionId]?.resetZoom();
  }

  let filterButton;
  let collapseButton;
  let selectionMode = false;
  let selectedPatterns = {};
  // let showPatternResults = false;
  let showPatternSearch = false;
  let exactSourceButton;
  let exactTrendButton;

  function initTippy(el, content) {
    if (!el._tippy) {
      tippy(el, {
        content,
        placement: 'top',
      });
    }
  }
  $: filterButton && initTippy(filterButton, "Filter based on prompt type");
  $: collapseButton && initTippy(collapseButton, "Collapse/Expand table view");
  $: exactSourceButton && initTippy(exactSourceButton, "Open/Close exact search");
  $: exactTrendButton && initTippy(exactTrendButton, "Open/Close exact search");

  let dataDict = {
    init_text: [], // Initial text
    init_time: [], // Start time
    json: [], // all operation
    text: [], // final text
    info: [], // insert, delete and suggestion-open operation
    end_time: [],
  };
  let textElements = []; // text data
  let chartData = []; // chart data
  let currentTime = 0;
  let paragraphTime = [];
  let paragraphColor = [];
  let selectedSession = [];
  let sessions = [];
  let time0 = null; // process bar's start time
  let time100 = null; // process bar's end time
  let endTime = null; // last paragraph time
  let isOpen = false;
  let showFilter = false;
  export const selectedTags = writable([]);
  let filterOptions = [];
  let showMulti = false;
  export const storeSessionData = writable(new Map());
  let tableData = [];
  let firstSession = true;
  export const filterTableData = writable([]);
  let isCollapsed = false;
  // store to track filter states
  const promptFilterStatus = writable({});
  const margin = { top: 20, right: 0, bottom: 30, left: 50 };
  const height = 200;
  let yScale = d3
    .scaleLinear()
    .domain([0, 100])
    .range([height - margin.top - margin.bottom, 0]);
  let zoomTransforms = {};
  export const clickSession = writable(null);
  let patternData = [];
  let RangeSlider = null;
  let writingProgressRange = [];
  let timeRange = [];
  let sourceRange = [];
  let semanticRange = [];
  let semanticData = [];
  let semanticTrend = [];
  onMount(async () => {
    const mod = await import("svelte-range-slider-pips");
    RangeSlider = mod.default;
  });
  let isProgressChecked = true;
  let isTimeChecked = true;
  let isSourceChecked = true;
  let isSemanticChecked = true;
  let isValueRangeChecked = true;
  let isValueTrendChecked = true;
  $: if (!isSemanticChecked) {
    isValueRangeChecked = false;
    isValueTrendChecked = false;
  }
  // let patternDataList = [];
  export const patternDataList = writable([]);
  export const initData = writable([]);
  let currentResults = {};
  let isSearch = 0; // 0: not searching, 1: searching, 2: search done
  let searchCount = 5; // count of search results
  export const showResultCount = writable(searchCount); // count of results to show in the UI

  let isExactSearchSource = false;
  let isExactSearchTrend = false;
  $: if (!isSemanticChecked || !isValueTrendChecked) {
    isExactSearchTrend = false;
  }
  $: if (!isSourceChecked) {
    isExactSearchSource = false;
  }

  export const searchPatternSet = writable([]);
  const removepattern = () => {
    showResultCount.update(count => count - 1);
  };

  function getPromptCode(sessionId) {
    const found = sessions.find((s) => s.session_id === sessionId);
    return found?.prompt_code ?? "";
  }

  // Functions about tables
  function handleRowClick(sessionData) {
    handleContainerClick({ detail: { sessionId: sessionData.sessionId } });
  }
  // TOPIC ICONS
  let sortColumn = '';
  let sortDirection = 'none';

  function handleSort(column) {
    if (sortColumn === column) {

      if (sortDirection === 'none') {
        sortDirection = 'asc';
      } else if (sortDirection === 'asc') {
        sortDirection = 'desc';
      } else {
        sortDirection = 'none';
      }
    } else {
    
      sortColumn = column;
      sortDirection = 'asc';
    }
  }

  function getSortIcon(column) {
      if (sortColumn !== column || sortDirection === 'none') {
        return '↕️'; 
      }
      return sortDirection === 'asc' ? '↑' : '↓';
  }
    // FETCH SCORES
   const fetchLLMScore = async (sessionFile) => {
    console.log("🔍 Trying to fetch LLM score for:", sessionFile);
    
    const url = `${base}/chi2022-coauthor-v1.0/eval_results/${sessionFile}.json`;
    console.log("🔗 URL:", url);
    
    try {
      const response = await fetch(url);
      console.log("📡 Response status:", response.status);
      console.log("📡 Response ok:", response.ok);
      
      if (!response.ok) {
        console.error("❌ Response not ok:", response.status, response.statusText);
        throw new Error(`Failed to fetch LLM score: ${response.status}`);
      }

      const data = await response.json();
      console.log("📄 Raw data:", data);
      
      // 新格式：data 直接是数字数组 [6]
      const totalScore = data[0]; // 直接取第一个元素
      console.log("🎯 Total score:", totalScore);
      
      return totalScore;
    } catch (error) {
      console.error("💥 Error when reading LLM score file:", error);
      return null;
    }
  };

  function getColumnGroups() {
    let sessions = getDisplaySessions();
    // Topic
    if (sortColumn === 'topic' && sortDirection !== 'none') {
      sessions = [...sessions].sort((a, b) => {
        const aCode = getPromptCode(a.sessionId);
        const bCode = getPromptCode(b.sessionId);
        
        if (sortDirection === 'asc') {
          return aCode.localeCompare(bCode);
        } else {
          return bCode.localeCompare(aCode);
        }
      });
    }
    // Score 
    if (sortColumn === 'score' && sortDirection !== 'none') {
      sessions = [...sessions].sort((a, b) => {
        const aScore = a.llmScore || 0; 
        const bScore = b.llmScore || 0;
        if (sortDirection === 'asc') {
          return aScore - bScore; 
        } else {
          return bScore - aScore; 
        }
      });
    }
    const groups = [[], [], []];
    sessions.forEach((session, index) => {
      const columnIndex = index % 3;
      groups[columnIndex].push(session);
    });

    return groups;
  }

$: if (sortColumn || sortDirection) {}

  function calculateAccumulatedSemanticScore(data) {
    if (!data || data.length === 0) return 0;
    
    const totalScore = data.reduce((sum, item) => {
      return sum + (item.residual_vector_norm || 0);
    }, 0);
    
    return totalScore;
  }

  function waitForSessionData(sessionId) {
    return new Promise((resolve) => {
      let _unsubscribe;
      const unsubscribe = storeSessionData.subscribe((sessionMap) => {
        const data = sessionMap.get(sessionId);
        if (data) {
          _unsubscribe?.();
          resolve(data);
        }
      });
      _unsubscribe = unsubscribe;
    });
  }

  let groupingMode = false;
  let selectedGroupAttribute = null;
  let selectedCategoryFilter = null; 
  let groupedSessions = {};
  let sortedSessions = [];
  let filteredSessions = [];

  function groupSessionsByAttribute(attribute, specificValue = null) {
    const grouped = {};
    $initData.forEach(sessionData => {
      const sessionInfo = sessions.find(s => s.session_id === sessionData.sessionId);
      if (sessionInfo) {
        const key = sessionInfo[attribute] || 'unknown';
        if (specificValue && key !== specificValue) {
          return;
        }
        
        if (!grouped[key]) {
          grouped[key] = [];
        }
        grouped[key].push(sessionData);
      }
    });
    
    return grouped;
  }

  function filterSessionsByCategory(category) {
    return $initData.filter(sessionData => {
      const sessionInfo = sessions.find(s => s.session_id === sessionData.sessionId);
      return sessionInfo && sessionInfo.prompt_code === category;
    });
  }

  function rankSessionsByAttribute(attribute, sessionsData) {
    const sessionsCopy = [...sessionsData];
    
    switch(attribute) {
      case 'prompt_code':
        return sessionsCopy.sort((a, b) => {
          const aCode = getPromptCode(a.sessionId);
          const bCode = getPromptCode(b.sessionId);
          return aCode.localeCompare(bCode);
        });
        
      case 'writing_time':
        return sessionsCopy.sort((a, b) => {
          const aTime = a.time100 || 0;
          const bTime = b.time100 || 0;
          return bTime - aTime;
        });
        
      case 'text_length':
        return sessionsCopy.sort((a, b) => {
          const aLength = a.summaryData?.totalProcessedCharacters || 0;
          const bLength = b.summaryData?.totalProcessedCharacters || 0;
          return bLength - aLength;
        });
        
      case 'suggestions_count':
        return sessionsCopy.sort((a, b) => {
          const aSuggestions = a.summaryData?.totalSuggestions || 0;
          const bSuggestions = b.summaryData?.totalSuggestions || 0;
          return bSuggestions - aSuggestions;
        });
        
      default:
        return sessionsCopy;
    }
  }

  function handleIconClick(attribute, mode = 'group', specificValue = null) {
    if (selectedCategoryFilter === specificValue && specificValue) {
      groupingMode = false;
      selectedGroupAttribute = null;
      selectedCategoryFilter = null;
      groupedSessions = {};
      sortedSessions = [];
      filteredSessions = [];
      return;
    }
    
    if (specificValue) {
      groupingMode = true;
      selectedGroupAttribute = attribute;
      selectedCategoryFilter = specificValue;
      
      filteredSessions = filterSessionsByCategory(specificValue);
      groupedSessions = {};
      sortedSessions = [];
      return;
    }

    if (groupingMode && selectedGroupAttribute === attribute && !selectedCategoryFilter) {
      groupingMode = false;
      selectedGroupAttribute = null;
      selectedCategoryFilter = null;
      groupedSessions = {};
      sortedSessions = [];
      filteredSessions = [];
    } else {
      groupingMode = true;
      selectedGroupAttribute = attribute;
      selectedCategoryFilter = null;
      
      if (mode === 'group') {
        groupedSessions = groupSessionsByAttribute(attribute);
        sortedSessions = [];
        filteredSessions = [];
      } else if (mode === 'rank') {
        sortedSessions = rankSessionsByAttribute(attribute, $initData);
        groupedSessions = {};
        filteredSessions = [];
      }
    }
  }

  let filteredByCategory = []; 
  function handleCategoryIconClick(category) {
    if (selectedCategoryFilter === category) {
      selectedCategoryFilter = null;
      filteredByCategory = [];
      
      const originalFilteredData = tableData.filter((session) =>
        $selectedTags.includes(session.prompt_code)
      );
      const originalUpdatedData = originalFilteredData.map((row) => ({
        ...row,
        selected: true
      }));
      filterTableData.set(originalUpdatedData);
      
    } else {
      selectedCategoryFilter = category;

      filteredByCategory = $initData.filter(sessionData => {
        const sessionInfo = sessions.find(s => s.session_id === sessionData.sessionId);
        return sessionInfo && sessionInfo.prompt_code === category;
      });  

      const categoryTableRows = tableData.filter(row => row.prompt_code === category);
      filterTableData.set(categoryTableRows.map(row => ({
        ...row,
        selected: true
      })));
      
      categoryTableRows.forEach(row => {
        fetchInitData(row.session_id, false, true);
      });
    }
  }

  function getDisplaySessions() {
      if (selectedCategoryFilter && filteredSessions.length >= 0) {
        return filteredSessions;
      }
      
      if (!groupingMode) {
        return $initData;
      }
      
      if (Object.keys(groupedSessions).length > 0) {
        return Object.values(groupedSessions).flat();
      }
      
      if (sortedSessions.length > 0) {
        return sortedSessions;
      }
      
      return $initData;
    }

  function isIconActive(promptCode) {
    return selectedCategoryFilter === promptCode;
  }

  function getGridItemClass(sessionId) {
    if (!groupingMode) return '';
    
    const sessionInfo = sessions.find(s => s.session_id === sessionId);
    if (!sessionInfo) return '';
    
    const attributeValue = sessionInfo[selectedGroupAttribute];
    return `grouped-${attributeValue}`;
  }

  async function handleContainerClick(event) {
    const sessionId = event.detail.sessionId;
    loadedMap = {
      ...loadedMap,
      [sessionId]: false,
    };
    showMulti = true;
    try {
      await fetchData(sessionId, false, true);
      const data = await waitForSessionData(sessionId);
      clickSession.set(data);
    } catch (error) {
      console.error("Failed to fetch session data:", error);
    }
  }

  let loadedMap = {};
  function handleChartLoaded(event) {
    const sessionId = event.detail;
    loadedMap = {
      ...loadedMap,
      [sessionId]: true,
    };
  }

  function open2close() {
    isOpen = !isOpen;
  }

  function togglePatternSearch() {
    if (!selectionMode) {
      selectionMode = true;
      showPatternSearch = true;
    } else {
      closePatternSearch();
    }
  }

  function deletePattern(sessionId) {
    isSearch = 0; // reset search state; 0: not searching, 1: searching, 2: search done
    const newSelectedPatterns = { ...selectedPatterns };
    delete newSelectedPatterns[sessionId];
    patternData = [];
    patternDataList.set([]);
    currentResults = {};

    selectedPatterns = newSelectedPatterns;
  }

  function isDataValid(item, checks) {
    const fieldMap = {
      progress: (d) => d.end_progress * 100,
      time: (d) => d.end_time / 60,
      semantic: (d) => d.residual_vector_norm,
    };

    for (const [key, [checked, range]] of Object.entries(checks)) {
      if (!checked || !(key in fieldMap)) continue;
      const value = fieldMap[key](item);
      if (value < range[0] || value > range[1]) return false;
    }

    return true;
  }

  function getTrendPattern(values) {
    const pattern = [];
    for (let i = 1; i < values.length; i++) {
      if (values[i] > values[i - 1]) pattern.push(1);
      else if (values[i] < values[i - 1]) pattern.push(-1);
    }
    return pattern;
  }

  function matchesTrend(values, expectedTrend) {
    const actual = getTrendPattern(values);
    return actual.every((v, i) => v === expectedTrend[i]);
  }

  function findSegments(data, checks, minCount) {
    const segments = [];
    for (let i = 0; i <= data.length - minCount; i++) {
      const window = data.slice(i, i + minCount);
      const allValid = window.every(item => isDataValid(item, checks));
      if (!allValid) continue;
      if (isExactSearchSource && checks.source && checks.source[1]) {
        const expectedSources = checks.source[1];
        if (expectedSources.length !== minCount) continue;

        const actualSources = window.map(item => item.source);
        const matches = actualSources.every((src, idx) => src === expectedSources[idx]);
        if (!matches) continue;
      }
      if (isExactSearchTrend && checks.trend && checks.trend[1]) {
        const values = window.map(item => item.residual_vector_norm);
        if (!matchesTrend(values, checks.trend[1])) continue;
      }
      segments.push([...window]);
    }

    return segments;
  }

  function buildVectorForCurrentSegment(currentResults, checks) {
    const currentVector = {};
    if (checks.source[0]) currentVector.s = [];
    if (checks.time[0]) currentVector.t = [];
    if (checks.progress[0]) currentVector.p = [];
    if (checks.trend[0]) currentVector.tr = [];
    if (checks.semantic[0]) currentVector.sem = [];
    for (let i = 0; i < currentResults.length; i++) {
      const currentItem = currentResults[i];
      if (checks.source[0]) {
        currentVector.s.push(checks.source[1][i] === "user" ? 1 : 0);
      }

      if (checks.time[0]) {
        currentVector.t.push(currentItem.endTime * 60 - currentItem.startTime * 60);
      }

      if (checks.progress[0]) {
        currentVector.p.push(currentItem.endProgress / 100 - currentItem.startProgress / 100);
      }

      if (checks.semantic[0]) {
        currentVector.sem.push(currentItem.residual_vector_norm)
      }
    }

    if (checks.trend[0]) {
        currentVector.tr = semanticTrend;
    }

    return currentVector;
  }

  function buildVectorFromSegment(segment, checks) {
    const vector = {};

    if (checks.source[0]) vector.s = [];
    if (checks.time[0]) vector.t = [];
    if (checks.progress[0]) vector.p = [];
    if (checks.trend[0]) vector.tr = [];
    if (checks.semantic[0]) vector.sem = [];

    for (let i = 0; i < segment.length; i++) {
      const item = segment[i];

      if (checks.source[0]) {
        const source = item.source?.toLowerCase();
        vector.s.push(source === "user" ? 1 : 0); // user is 1, api is 0
      }
      if (checks.time[0]) {
        const tStart = item.start_time ?? 0;
        const tEnd = item.end_time ?? 0;
        vector.t.push(tEnd - tStart);
      }
      if (checks.progress[0]) {
        const y1 = item.start_progress ?? 0;
        const y2 = item.end_progress ?? 0;
        vector.p.push(y2 - y1);
      }
      if (checks.trend[0]) {
        if (i > 0) {
          const trend = getTrend(segment[i - 1].residual_vector_norm, item.residual_vector_norm);
          vector.tr.push(trend);
        }
      }
      if (checks.semantic[0]) {
        vector.sem.push(item.residual_vector_norm ?? null);
      }
    }
    return vector;
  }

  async function searchPattern(sessionId) {
    isSearch = 1; // 0: not searching, 1: searching, 2: search done
    const sessionData = selectedPatterns[sessionId];
    const count = sessionData.count;
    let results = [];
    let patternVectors = [];
    const checks = {
      progress: [isProgressChecked, writingProgressRange],
      time: [isTimeChecked, timeRange],
      source: [isSourceChecked, sourceRange],
      semantic: [isValueRangeChecked, semanticRange],
      trend: [isValueTrendChecked, semanticTrend],
    };

    try {
      const fileListResponse = await fetch(`${base}/session_name.json`);
      const fileList = await fileListResponse.json();

      for (const fileName of fileList) {
        const fileId = fileName.split(".")[0].replace(/_similarity$/, "");
        if (fileId === sessionId) {
          continue;
        }
        const dataResponse = await fetch(
          `${base}/chi2022-coauthor-v1.0/similarity_results/${fileName}`
        );
        const data = await dataResponse.json();
        const segments = findSegments(data, checks, count);
        const extractedFileName = fileName
          .split(".")[0]
          .replace(/_similarity$/, "");

        const taggedSegments = segments.map((segment, index) =>
          segment.map((item) => ({ ...item, id: extractedFileName, segmentId:`${extractedFileName}_${index}` }))
        );

        for (const segment of taggedSegments) {
          const vector = buildVectorFromSegment(segment, checks);
          vector.id = segment[0]?.id ?? null;
          vector.segmentId = segment[0]?.segmentId ?? null;
          patternVectors.push(vector);
        }

        results.push(...taggedSegments);
      }
      const currentVector = buildVectorForCurrentSegment(currentResults, checks)

      patternData = results;
      const finalScore = calculateRank(patternVectors, currentVector)
      const idToData = Object.fromEntries(patternData.map(d => [d[0].segmentId, d]));
      // const top5Data = finalScore.slice(0, 5)
      //     .map(([segmentId]) => idToData[segmentId]);
      const fullData = finalScore.map(([segmentId]) => idToData[segmentId]);

      // showResultCount = 5; // Initialize to show 5 results
      searchCount = fullData.length;
      patternDataLoad(fullData);
    } catch (error) {
      isSearch = 0; // reset search state; 0: not searching, 1: searching, 2: search done
      console.error("Search failed", error);
    }
  }

  function l2(arr1, arr2) {
    let sum = 0;
    for (let i = 0; i < arr1.length; i++) {
      sum += (arr1[i] - arr2[i]) **2;
    }
    return Math.sqrt(sum);
  }

  function calculateRank(patternVectors, currentVector) {
    const weights = {
      s: 1.5, // user 1, api 0
      t: 0.01, // 1s
      p: 1, // 1% -> 0.01
      tr: 2.5, // up 1, down -1
      sem: 2 // 1% -> 0.01
    }
    let finalScore = [];
    for (const item of patternVectors) {
      let score = 0;
      for (const key in item) {
        if (key != "id" && key != "segmentId") {
          let weight = weights[key] ?? 1;
          let arr = item[key];
          score += weight * l2(arr, currentVector[key]);
        }
      }
      finalScore.push([item.segmentId, score]);
    }
    finalScore.sort((a, b) => a[1] - b[1]);
    return finalScore;
  }

  async function patternDataLoad(results) {
    const ids = results.map((group) => group[0]?.id).filter(Boolean);
    const fetchPromises = ids.map((id) => fetchData(id, false, false));
    await Promise.all(fetchPromises);

    const sessionDataMap = get(storeSessionData);
    patternDataList.set(
      results
        .map((group) => {
          const id = group[0]?.id;
          const sessionData = sessionDataMap.get(id);
          if (sessionData) {
            return {
              ...sessionData,
              segments: group,
            };
          }
          return null;
        })
        .filter(Boolean)
    );
    isSearch = 2; // reset search state; 0: not searching, 1: searching, 2: search done
  }

  function closePatternSearch() {
    showPatternSearch = false;
    selectionMode = false;
    isSearch = 0; // reset search state; 0: not searching, 1: searching, 2: search done

    Object.keys(selectedPatterns).forEach((sessionId) => {
      const chartRef = chartRefs[sessionId + "-barChart"];
      if (chartRef && chartRef.clearSelection) {
        chartRef.clearSelection();
      }
    });

    selectedPatterns = {};
    patternData = [];
    patternDataList.set([]);
    currentResults = {};
  }

  function getTrend(a, b) {
    if (a < b) return 1; // up is 1, down is -1
    if (a > b) return -1;
    return 0;
  }

  function handleSelectionChanged(event) {
    showResultCount.set(5)
    isProgressChecked = true;
    isTimeChecked = true;
    isSourceChecked = true;
    isSemanticChecked = true;
    isValueRangeChecked = true;
    isValueTrendChecked = true;
    isExactSearchSource = false;
    isExactSearchTrend = false;
    semanticTrend = [];
    selectedPatterns = {};
    patternData = [];
    patternDataList.set([]);
    currentResults = {};
    const { sessionId, range, dataRange, data, wholeData, sources } = event.detail;
    writingProgressRange = [
      dataRange.progressRange.min,
      dataRange.progressRange.max,
    ];
    timeRange = [dataRange.timeRange.min, dataRange.timeRange.max];
    sourceRange = sources;
    semanticRange = [dataRange.scRange.min, dataRange.scRange.max];
    semanticData = dataRange.sc.sc;
    for (let i = 1; i < semanticData.length; i++) {
      semanticTrend.push(getTrend(semanticData[i - 1], semanticData[i]));
    }
    currentResults = data

    selectedPatterns[sessionId] = {
      range,
      dataRange,
      data,
      wholeData,
      sources,
      scRange: `${range.sc.min.toFixed(1)} - ${range.sc.max.toFixed(1)}%`,
      progressRange: `${range.progress.min.toFixed(1)} - ${range.progress.max.toFixed(1)}%`,
      count: data.length,
    };
  }

  function handleSelectionCleared(event) {
    const { sessionId } = event.detail;

    if (selectedPatterns[sessionId]) {
      delete selectedPatterns[sessionId];
    }
  }

  function change2bar() {
    showMulti = !showMulti;
    clickSession.set([]);
  }

  function updatePromptFilterStatus() {
    const allSessions = tableData || [];
    const promptGroups = {};

    allSessions.forEach((session) => {
      if (!promptGroups[session.prompt_code]) {
        promptGroups[session.prompt_code] = [];
      }
      promptGroups[session.prompt_code].push(session);
    });

    const statusMap = {};
    Object.entries(promptGroups).forEach(([promptCode, sessions]) => {
      const totalSessions = sessions.length;
      const selectedSessions = sessions.filter((session) =>
        $filterTableData.find(
          (item) => item.session_id === session.session_id && item.selected
        )
      ).length;

      if (selectedSessions === 0) {
        statusMap[promptCode] = "none";
      } else if (selectedSessions === totalSessions) {
        statusMap[promptCode] = "all";
      } else {
        statusMap[promptCode] = "partial";
      }
    });
    promptFilterStatus.set(statusMap);
  }

  async function toggleTag(event) {
    const tag = event.target.value;

    selectedTags.update((selected) => {
      if (event.target.checked) {
        if (!selected.includes(tag)) {
          selected.push(tag);
        }
      } else {
        const index = selected.indexOf(tag);
        if (index !== -1) {
          selected.splice(index, 1);
        }
      }
      return selected;
    });
    filterSessions();
    if (event.target.checked) {
      for (const newSession of $filterTableData) {
        await fetchInitData(newSession.session_id, false, true);
      }
    } else {
      const sessionsToRemove = tableData.filter(
        (item) => item.prompt_code === tag
      );
      for (const sessionToRemove of sessionsToRemove) {
        await fetchInitData(sessionToRemove.session_id, true, true);
      }
    }

    const selectedSessionsMap = get(storeSessionData);
    const selectedSessions = Array.from(selectedSessionsMap.values());
    const selectedTagsList = get(selectedTags);
    if (selectedTagsList.length > 1) {
      const tagSessionCount = selectedSessions.filter((session) =>
        selectedTagsList.some((tag) =>
          tableData.some(
            (item) =>
              item.session_id === session.sessionId && item.prompt_code === tag
          )
        )
      ).length;
      if (tagSessionCount === 1) {
        const allSessionsForTag = tableData.filter((item) =>
          selectedTagsList.includes(item.prompt_code)
        );
        for (const session of allSessionsForTag) {
          await fetchInitData(session.session_id, false, true);
        }
      }
    } else {
      const allSessionsForTag = tableData.filter((item) =>
        selectedTagsList.includes(item.prompt_code)
      );
      for (const session of allSessionsForTag) {
        await fetchInitData(session.session_id, false, true);
      }
    }
    updatePromptFilterStatus();
  }

  function filterSessions() {
    if ($selectedTags.length === 0) {
      filterTableData.set([]);
      storeSessionData.set(new Map());
    } else {
      const filteredData = tableData.filter((session) =>
        $selectedTags.includes(session.prompt_code)
      );
      const sessionArray = Array.from($storeSessionData.values());
      const updatedData = filteredData.map((row) => ({
        ...row,
        selected:
          sessionArray.some((item) => item.sessionId === row.session_id) || true,
      }));

      filterTableData.set(updatedData);
      updatePromptFilterStatus();
    }
  }

  function toggleTableCollapse() {
    isCollapsed = !isCollapsed;
  }

  const toggleFilter = () => {
    showFilter = !showFilter;
  };

  async function fetchInitData(sessionId, isDelete, isPrompt) {
    if (isDelete) {
      initData.update((data) =>
        data.filter((item) => item.sessionId !== sessionId)
      );
      return;
    }

    const similarityData = await fetchSimilarityData(sessionId);
    const llmScore = await fetchLLMScore(sessionId);
    
    if (similarityData) {
      initData.update((sessions) => {
        
        const existingIndex = sessions.findIndex(s => s.sessionId === sessionId);
        
        if (existingIndex !== -1) {
         
          sessions[existingIndex] = {
            ...sessions[existingIndex],
            llmScore: llmScore
          };
        } else {
          sessions.push({
            sessionId,
            similarityData,
            totalSimilarityData: similarityData,
            llmScore: llmScore,
          });
        }
        return [...sessions];
      });
    }

    if (isPrompt) {
      updatePromptFilterStatus();
    }
    console.log("🔍 Final initData after update:", sessions.find(s => s.sessionId === sessionId));
  }

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${base}/fine.json`);
      const data = await response.json();
      sessions = data || [];
      
      if (firstSession) {
        tableData = sessions.map((session) => {
          return {
            session_id: session.session_id,
            prompt_code: session.prompt_code,
            selected: true,
          };
        });
        
        selectedSession = sessions.map(session => session.session_id);
        firstSession = false;
        selectedTags.set(["reincarnation", "bee", "sideeffect", "pig", "obama", "mana", "dad", "mattdamon", "shapeshifter", "isolation"]);
        filterSessions();
        
        $filterTableData = tableData.filter((session) =>
          $selectedTags.includes(session.prompt_code)
        );
        
        filterOptions = Array.from(
          new Set(tableData.map((row) => row.prompt_code))
        );
        
        updatePromptFilterStatus();
        
        for (const session of $filterTableData) {
          const llmScore = await fetchLLMScore(session.session_id);
          console.log("Initial LLM score for", session.session_id, ":", llmScore);
          
        }
      }
    } catch (error) {
      console.error("Error when fetching sessions:", error);
    }
  };
  const fetchData = async (sessionFile, isDelete, isPrompt) => {
    if (!firstSession && isDelete) {
      storeSessionData.update((map) => {
        const newMap = new Map(map);
        newMap.delete(sessionFile);
        return newMap;
      });
      return;
    }
    try {
      const response = await fetch(`${base}/chi2022-coauthor-v1.0/coauthor-json/${sessionFile}.jsonl`);
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }
      const data = await response.json();

      time0 = new Date(data.init_time);
      time100 = new Date(data.end_time);
      time100 = (time100.getTime() - time0.getTime()) / (1000 * 60);
      currentTime = time100;

      const { chartData, textElements, paragraphColor, summaryData } = handleEvents(data, sessionFile);
      const similarityData = await fetchSimilarityData(sessionFile);
      let updatedSession = {
        sessionId: sessionFile,
        time0,
        time100,
        currentTime,
        chartData,
        textElements,
        paragraphColor,
        summaryData,
        similarityData: similarityData || undefined,
        totalSimilarityData: similarityData || undefined,
      };
      storeSessionData.update((sessionMap) => {
        const newMap = new Map(sessionMap);
        const existing = newMap.get(sessionFile);

        if (existing) {
          newMap.set(sessionFile, { ...existing, ...updatedSession });
        } else {
          newMap.set(sessionFile, updatedSession);
        }

        return newMap;
      });
    } catch (error) {
      console.error("Error when reading the data file:", error);
    }

    if (isPrompt) {
      updatePromptFilterStatus();
    }
  };

  const fetchSimilarityData = async (sessionFile) => {
    try {
      const response = await fetch(
        `${base}/chi2022-coauthor-v1.0/similarity_results/${sessionFile}_similarity.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  

  const handleSessionChange = (sessionId) => {
    let isCurrentlySelected = $filterTableData.find(
      (row) => row.session_id == sessionId
    )?.selected;

    filterTableData.set(
      $filterTableData.map((row) => {
        if (row.session_id == sessionId) {
          return { ...row, selected: !row.selected };
        }
        return row;
      })
    );

    if (!isCurrentlySelected) {
      for (let i = 0; i < selectedSession.length; i++) {
        selectedSession[i] = sessionId;
        fetchInitData(sessionId, false, true);
      }
    } else {
      fetchInitData(sessionId, true, true);
    }

    for (let i = 0; i < selectedSession.length; i++) {
      fetchSimilarityData(sessionId).then((similarityData) => {
        if (similarityData) {
          storeSessionData.update((sessionsMap) => {
          selectedSession.forEach((sessionId) => {
            if (sessionsMap.has(sessionId)) {
              const session = sessionsMap.get(sessionId);
              sessionsMap.set(sessionId, {
                ...session,
                similarityData: similarityData,
                totalSimilarityData: similarityData,
              });
            }
          });
          return new Map(sessionsMap);
        });
          initData.update((sessions) => {
            if (!sessions.find((s) => s.sessionId === sessionId)) {
              const newSession = {
                sessionId: sessionId,
                similarityData: similarityData,
                totalSimilarityData: similarityData,
              };
              sessions.push(newSession);
            }
            return [...sessions];
          });
        }
      });
    }

    let nowSelectTag = new Set(
      $filterTableData.filter((f) => f.selected).map((f) => f.prompt_code)
    );
    selectedTags.update((selected) => {
      selected = selected.filter((tag) => nowSelectTag.has(tag));
      return selected;
    });
    updatePromptFilterStatus();
  };

  function handleSelectChange(index) {
    handleSessionChange($filterTableData[index].session_id);
  }

  onMount(async () => {
  document.title = "Ink-Pulse";
  await fetchSessions();
  for (let i = 0; i < selectedSession.length; i++) {
    const sessionId = selectedSession[i];
    
    // 获取相似度数据和LLM分数
    const similarityData = await fetchSimilarityData(sessionId);
    const llmScore = await fetchLLMScore(sessionId);
    console.log("✅ onMount LLM score for", sessionId, ":", llmScore);
    
    initData.update((sessions) => {
      const newSession = {
        sessionId: sessionId,
        similarityData: similarityData,
        totalSimilarityData: similarityData,
        llmScore: llmScore,
      };
      sessions.push(newSession);
      return [...sessions];
    });
  }
});
 
  function handleChartZoom(event) {
    event.preventDefault();
    
    if (!$clickSession || !$clickSession.sessionId) return;
    
    const sessionId = $clickSession.sessionId;
    const currentTransform = zoomTransforms[sessionId] || d3.zoomIdentity;
    
    const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1;
    const newK = Math.max(1, Math.min(5, currentTransform.k * scaleFactor));
    
    const rect = event.currentTarget.getBoundingClientRect();
    const mouseY = event.clientY - rect.top;
    
    const chartHeight = height - margin.top - margin.bottom;
    const centerY = mouseY - margin.top;
    
    const currentCenterY = (centerY - currentTransform.y) / currentTransform.k;
    const newTranslateY = centerY - (currentCenterY * newK);
    
    const maxTranslateY = 0;
    const minTranslateY = -chartHeight * (newK - 1);
    const clampedY = Math.max(minTranslateY, Math.min(newTranslateY, maxTranslateY));
    
    zoomTransforms[sessionId] = d3.zoomIdentity
      .translate(currentTransform.x, clampedY)
      .scale(newK);
    
    zoomTransforms = { ...zoomTransforms };
  }

  function generateColorGrey(index) {
    const colors = ["rgba(220, 220, 220, 0.5)", "rgba(240, 240, 240, 0.3)"];
    return colors[index % colors.length];
  }

  function adjustTime(currentText, chartData) {
    let wholeText = currentText;
    let textLength = wholeText.length;

    let newParagraph = [...wholeText.matchAll(/\n/g)].map(
      (match) => match.index
    );
    let paragraphPercentages = newParagraph.map(
      (pos) => (pos / textLength) * 100
    );
    let mergeParagraph = [0];
    for (let i = 0; i < paragraphPercentages.length; i++) {
      let previous = mergeParagraph[mergeParagraph.length - 1];
      let current = paragraphPercentages[i];
      if (current - previous <= 0.07) {
        mergeParagraph[mergeParagraph.length - 1] = current;
      } else {
        mergeParagraph.push(current);
      }
    }
    const getTimeFromPercentage = (percentage, chartData) => {
      let closest = chartData.reduce((prev, curr) =>
        Math.abs(curr.percentage - percentage) <
        Math.abs(prev.percentage - percentage)
          ? curr
          : prev
      );

      return closest.time;
    };
    let newParagraphTime = mergeParagraph.map((percentage) => ({
      time: getTimeFromPercentage(percentage, chartData),
      pos: Math.round((percentage / 100) * textLength),
    }));

    return newParagraphTime;
  }

  const handleEvents = (data, _) => {
    const initText = data.init_text.join("");
    let currentText = initText;
    let currentColor = [];
    let chartData = [];
    let paragraphColor = [];
    let firstTime = null;
    let indexOfAct = 0;
    const wholeText = data.text[0].slice(0, -1);
    const totalTextLength = wholeText.length;

    let totalInsertions = 0;
    let totalDeletions = 0;
    let totalSuggestions = 0;
    let totalInsertionTime = 0;
    let totalDeletionTime = 0;
    let totalSuggestionTime = 0;
    let totalProcessedCharacters = totalTextLength;
    let currentCharArray = initText.split("");

    const initColor = "#FC8D62";
    currentColor = new Array(currentCharArray.length).fill(initColor);

    let combinedText = data.info.reduce((acc, event) => {
      const { name, text = "", eventSource, event_time, count = 0, pos = 0 } = event;
      const textColor = eventSource === "user" ? "#66C2A5" : "#FC8D62";
      const eventTime = new Date(event_time);

      if (firstTime === null) {
        firstTime = eventTime;
        paragraphTime = [{ time: 0, pos: 0 }];
      }

      const relativeTime = (eventTime.getTime() - firstTime.getTime()) / 60000;
      let percentage;

      if (name === "text-insert") {
        const insertChars = [...text];
        currentCharArray.splice(pos, 0, ...insertChars);
        currentColor.splice(pos, 0, ...insertChars.map(() => textColor));
        currentText = currentCharArray.join("");
        insertChars.forEach((char, i) => {
          acc.splice(pos + i, 0, { text: char, textColor });
        });
        totalInsertions++;
        totalInsertionTime += relativeTime;
      }

      if (name === "text-delete") {
        currentCharArray.splice(pos, count);
        currentColor.splice(pos, count);
        currentText = currentCharArray.join("");
        acc.splice(pos, count);
        totalDeletions++;
        totalDeletionTime += relativeTime;
      }

      if (name === "suggestion-open") {
        totalSuggestions++;
        totalSuggestionTime += relativeTime;
      }

      percentage = (currentCharArray.length / totalTextLength) * 100;

      chartData.push({
        time: relativeTime,
        percentage,
        eventSource,
        color: textColor,
        currentText,
        currentColor: [...currentColor],
        opacity: 1,
        isSuggestionOpen: name === "suggestion-open",
        index: indexOfAct++,
      });

      return acc;
    }, [...initText].map(ch => ({ text: ch, textColor: "#FC8D62" })));

    paragraphTime = adjustTime(currentText, chartData);
    for (let i = 0; i < paragraphTime.length - 1; i++) {
      const { time: startTime } = paragraphTime[i];
      const { time: endTime } = paragraphTime[i + 1];
      const color = generateColorGrey(i);
      paragraphColor.push({
        type: "box",
        xMin: startTime,
        xMax: endTime,
        yMin: -5,
        yMax: 100,
        backgroundColor: color,
        borderWidth: 0,
        zIndex: -10,
        drawTime: "beforeDatasetsDraw",
        value: i + 1,
      });
    }

    if (combinedText.length && combinedText[combinedText.length - 1].text === "\n") {
      combinedText.pop();
      currentCharArray.pop();
      currentColor.pop();
      chartData.pop();
      totalProcessedCharacters--;
      totalInsertions--;
    }

    if (chartData.length) {
      chartData[0].isSuggestionOpen = false;
    }

    return {
      chartData,
      textElements: combinedText,
      paragraphColor,
      summaryData: {
        totalProcessedCharacters,
        totalInsertions,
        totalDeletions,
        totalSuggestions,
      }
    };
  };
  
  function handlePointSelected(e, sessionId) {
    const d = e.detail;
    clickSession.update((currentSession) => {
      if (currentSession.sessionId === sessionId) {
        const updatedSession = {
          ...currentSession,
          textElements: d.currentText.split("").map((char, index) => ({
            text: char,
            textColor: d.currentColor[index],
          })),
          currentTime: d.time,
          chartData: currentSession.chartData.map((point) => ({
            ...point,
            opacity: point.index > d.index ? 0.01 : 1,
          })),
        };

        const similarityData = currentSession.totalSimilarityData;
        let selectedData = [];
        for (let i = 0; i < similarityData.length; i++) {
          const currentItem = similarityData[i];
          if (d.percentage < currentItem.end_progress * 100) {
            selectedData = similarityData.slice(0, i);
            break;
          }
        }
        if (selectedData.length === 0 && similarityData.length > 0) {
          selectedData = similarityData;
        }

        return {
          ...updatedSession,
          similarityData: selectedData,
        };
      }
      return currentSession;
    });
  }
</script>

<div class="App">
  <header class="App-header">
    <nav>
      {#if !showMulti}
      <div
        class={`filter-container ${showFilter ? (isCollapsed ? "filter-container-close" : "") : ""} ${showFilter ? "show" : ""}`}
      >
        {#each filterOptions as option}
          <label class="filter-label">
            <span class="checkbox-wrapper">
              <input
                id="checkbox-n"
                type="checkbox"
                value={option}
                on:change={toggleTag}
                checked={$selectedTags.includes(option)}
                class="filter-checkbox"
              />
              <span class="custom-checkbox">
                {#if $promptFilterStatus[option] === "all"}
                  <span class="checkbox-indicator">✓</span>
                {:else if $promptFilterStatus[option] === "partial"}
                  <span
                    class="checkbox-indicator-alter"
                    style="font-weight: bold; font-size: 24px;">-</span
                  >
                {:else}
                  <span class="checkbox-indicator"></span>
                {/if}
              </span>
            </span>
            {option}
          </label>
        {/each}
      </div>
      {/if}
      <div class="chart-explanation">
        <span class="triangle-text">▼</span> user open the AI suggestion
        <span class="user-line">●</span> User written
        <span class="api-line">●</span> AI writing
      </div>
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded"
        rel="stylesheet"
      />
      {#if showMulti}
        <a
          on:click={change2bar}
          href=" "
          aria-label="Toggle View"
          class="material-symbols-rounded"
        >
          swap_horiz
        </a>
      {/if}
      <button
        class="pattern-search-button"
        class:active={selectionMode}
        on:click={togglePatternSearch}
        aria-label="Pattern Search"
      >
        <span class="search-icon">🔍</span>
        {selectionMode ? "Exit Search" : "Pattern Search"}
      </button>
      <a
        on:click={open2close}
        href=" "
        aria-label="Instruction"
        class="material-symbols--info-outline-rounded"
      ></a>
    </nav>
    {#if showPatternSearch}
      <div class="pattern-search-panel">
        <div class="pattern-panel-header">
          <h3>Pattern Search</h3>
          <button class="close-button" on:click={closePatternSearch}>×</button>
        </div>

        <div class="pattern-panel-content">
          <div class="pattern-instructions">
            <p>
              Select a portion in the chart to identify patterns in writing
              behavior.
            </p>
          </div>

          {#if Object.keys(selectedPatterns).length > 0}
            <div class="pattern-results-summary">
              <h4>Selection Results</h4>
              {#each Object.entries(selectedPatterns) as [sessionId, pattern]}
                <div class="pattern-item">
                  <div class="pattern-header">
                    <h5>Session: {sessionId.slice(0, 4)}</h5>
                    <div class="pattern-buttons">
                      <button
                        class="delete-pattern-button"
                        on:click={() => deletePattern(sessionId)}>Delete</button
                      >
                      <button
                        class="search-pattern-button"
                        on:click={() => searchPattern(sessionId)}>Search</button
                      >
                    </div>
                  </div>
                  <div class="pattern-details">
                    <div>
                      Semantic Change: {pattern.dataRange.scRange.min.toFixed(2)} - {pattern.dataRange.scRange.max.toFixed(2)}
                    </div>
                    <div>
                      Progress Range: {pattern.dataRange.progressRange.min.toFixed(2)}% - {pattern.dataRange.progressRange.max.toFixed(2)}%
                    </div>
                    <div>
                      Counts: {pattern.count}
                    </div>
                  </div>
                  <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <div class="pattern-chart-preview small-preview">
                      <PatternChartPreview
                        {sessionId}
                        data={pattern.data}
                        wholeData={pattern.wholeData}
                        selectedRange={pattern.range}
                        bind:this={chartRefs[sessionId]}
                      />
                    </div>
                    <div style="margin-top: 5px; width: 60%">
                      <div
                        class:dimmed={!isProgressChecked}
                        style="display: flex; align-items: center; font-size: 13px;"
                      >
                        <input type="checkbox" bind:checked={isProgressChecked} />
                        Writing Progress
                        <div style="flex: 1;"></div>
                        <RangeSlider range float
                          class="rangeSlider"
                          min={0}
                          max={100}
                          bind:values={writingProgressRange}
                        />
                      </div>
                      <div
                        class:dimmed={!isTimeChecked}
                        style="display: flex; align-items: center; font-size: 13px;"
                      >
                        <input type="checkbox" bind:checked={isTimeChecked} />
                        Time
                        <div style="flex: 1"></div>
                        <RangeSlider range float
                          class="rangeSlider"
                          min={0}
                          max={$clickSession?.time100}
                          bind:values={timeRange}
                        />
                      </div>
                      <div class:dimmed={!isSourceChecked} style="font-size: 13px;">
                        <input type="checkbox" bind:checked={isSourceChecked} />
                        Source(human/AI)
                        <label class="switch" style="transform: translateY(4px);" bind:this={exactSourceButton}>
                          <input type="checkbox" bind:checked={isExactSearchSource} disabled={!isSourceChecked}>
                          <span class="slider"></span>
                        </label>
                      </div>
                      <div style="font-size: 13px;">
                        <div class:dimmed={!isSemanticChecked}>
                          <input type="checkbox" bind:checked={isSemanticChecked} />
                          Semantic Expansion
                        </div>
                          <div style="margin-left: 20px;">
                            <div class:dimmed={!isValueRangeChecked}>
                              <input
                                type="checkbox"
                                bind:checked={isValueRangeChecked}
                                disabled={!isSemanticChecked}
                              />
                              Value Range
                            </div>
                            <div class:dimmed={!isValueTrendChecked}>
                              <input
                                type="checkbox"
                                bind:checked={isValueTrendChecked}
                                disabled={!isSemanticChecked}
                              />
                              Value Trend
                              <label class="switch" style="transform: translateY(4px);" bind:this={exactTrendButton}>
                                <input type="checkbox" bind:checked={isExactSearchTrend} disabled={!isSemanticChecked || !isValueTrendChecked}>
                                <span class="slider"></span>
                              </label>
                            </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  {#if $patternDataList.length > 0 && isSearch == 2}
                    <div>
                      Search Results
                    </div>
                    {#each $patternDataList as sessionData, index}
                      {#if index < $showResultCount} 
                        <div class="search-result-container">
                          <div style="font-size: 13px; margin-bottom: 4px; margin-left: 8px; position: relative;">
                            <strong>{sessionData.sessionId}</strong>
                            <button class="close-button" style="position: absolute; top:0px; right:0px; background-color: initial;"
                              on:click={() => {
                                removepattern();
                              }}
                            >×</button>
                          </div>
                          <div style="display: flex; align-items: flex-start">
                            <div>
                              <PatternChartPreviewSerach
                              sessionId={sessionData.sessionId}
                              data={sessionData.segments}
                              wholeData={sessionData.similarityData} 
                              />
                            </div>
                            <div>
                              <LineChartPreview
                              bind:this={chartRefs[sessionData.sessionId]}
                              chartData={sessionData.chartData}
                              />
                            </div>
                          </div>
                        </div>
                      {/if}
                    {/each}
                    {#if $showResultCount < $patternDataList.length}
                      <div style="display: flex; justify-content: center; margin-top: 10px;">
                        <button 
                          class="search-pattern-button"
                          style="margin-right: 10px;"
                          on:click={() => {
                              const sliceToSave = $patternDataList.slice(0, $showResultCount);
                              searchPatternSet.update(current => [...current, sliceToSave]);
                            }}>Save NOW Pattern
                        </button>
                        <button class="search-pattern-button" on:click={() => {$showResultCount += 5}}>
                          More Results
                        </button>
                      </div>
                    {:else}
                    <div style="gap: 10px"></div>
                      <button
                        class="search-pattern-button"
                        on:click={() => {
                            const sliceToSave = $patternDataList.slice(0, $showResultCount);
                            searchPatternSet.update(current => [...current, sliceToSave]);
                          }}>Save NOW pattern
                      </button>
                      <div style="text-align: center; margin-top: 10px;">
                        <span class="no-more-results">End of Results</span>
                      </div>
                    {/if}
                  {:else if $patternDataList.length == 0 && isSearch == 2}
                    <div class="no-data-message">
                      No data found matching the search criteria.
                    </div>
                  {:else if isSearch == 1}
                    <div class="loading-message">
                      Searching for patterns...
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {:else if selectionMode}
            <div class="no-patterns-selected">
              <p>No patterns selected.</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}
    <div class="container">
      {#if isOpen}
        <div class="introduction-background">
          <div class="introduction">
            <h2>Welcome to the CoAuthor visualization!</h2>
            <p>
              This platform allows you to explore the <b
                >human-AI collaborative writing process</b
              >
              using the
              <a href="https://coauthor.stanford.edu/" target="_blank"
                >CoAuthor dataset</a
              >. View how writers interacted with GPT-3, analyze AI-generated
              suggestions, and track text evolution in real time.
            </p>
            <p>
              Discover insights into <b>human-AI collaboration</b>
              and have fun!
            </p>
            <button class="start-button" on:click={open2close}
              >Start Exploring</button
            >
          </div>
        </div>
      {/if}
      <div style="margin-top: 70px;" hidden={showMulti}>
        {#if $initData.length > 0}
          {#if selectedCategoryFilter}
            <!-- Filter -->
            <div class="category-filter-section">
              <div class="category-filter-header">
                <h2>
                  <span class="category-icon-large">
                    {getCategoryIcon(selectedCategoryFilter)}
                  </span>
                  {selectedCategoryFilter.toUpperCase()} Sessions
                </h2>
              </div>
              <div class="table-container full-width">
                <table class="sessions-table">
                  <thead>
                    <tr>
                      <th>Activity</th>
                      <th class="sortable-header" on:click={() => handleSort('topic')}>
                        <span>Topic</span>
                        <span class="sort-icon">{getSortIcon('topic')}</span>
                      </th>
                      <th class="sortable-header" on:click={() => handleSort('score')}>
                        <span>Score</span>
                        <span class="sort-icon">{getSortIcon('score')}</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each (selectedCategoryFilter ? filteredByCategory : filteredSessions) as sessionData (sessionData.sessionId + sortColumn + sortDirection)}
                      <tr 
                        class="session-row"
                        on:click={() => handleRowClick(sessionData)}
                      >
                        <td class="activity-cell">
                          <div class="mini-chart">
                            <ZoomoutChart
                              on:containerClick={handleContainerClick}
                              bind:this={chartRefs[sessionData.sessionId]}
                              sessionId={sessionData.sessionId}
                              similarityData={sessionData.similarityData}
                            />
                          </div>
                        </td>
                        <td class="topic-cell">
                          <button
                            class="topic-icon-btn"
                            on:click|stopPropagation={() => handleCategoryIconClick(getPromptCode(sessionData.sessionId))}
                            title="Click to clear filter"
                            type="button"
                          >
                            {getCategoryIcon(getPromptCode(sessionData.sessionId))}
                          </button>
                        </td>
                        <td class="score-cell">
                          <SemanticExpansionCircle 
                            llmJudgeScore={sessionData.llmScore}
                            size={16}
                            sessionId={sessionData.sessionId}
                          />
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>               
            </div>
          {:else}
            <div class="unified-table-container">
              <div class="unified-table-wrapper">
                <table class="unified-sessions-table">
                  <thead>
                    <tr>
                      <!-- 第一组 -->
                      <th>Activity</th>
                      <th class="sortable-header" on:click={() => handleSort('topic')}>
                        <span>Topic</span>
                        <span class="sort-icon">{getSortIcon('topic')}</span>
                      </th>
                      <th class="sortable-header" on:click={() => handleSort('score')}>
                        <span>Score</span>
                        <span class="sort-icon">{getSortIcon('score')}</span>
                      </th>
                      
                      <!-- 第二组 -->
                      <th>Activity</th>
                      <th class="sortable-header" on:click={() => handleSort('topic')}>
                        <span>Topic</span>
                        <span class="sort-icon">{getSortIcon('topic')}</span>
                      </th>
                      <th class="sortable-header" on:click={() => handleSort('score')}>
                        <span>Score</span>
                        <span class="sort-icon">{getSortIcon('score')}</span>
                      </th>
                      
                      <!-- 第三组 -->
                      <th>Activity</th>
                      <th class="sortable-header" on:click={() => handleSort('topic')}>
                        <span>Topic</span>
                        <span class="sort-icon">{getSortIcon('topic')}</span>
                      </th>
                      <th class="sortable-header" on:click={() => handleSort('score')}>
                        <span>Score</span>
                        <span class="sort-icon">{getSortIcon('score')}</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each Array(Math.ceil(Math.max(...getColumnGroups().map(group => group.length)))) as _, rowIndex (rowIndex + sortColumn + sortDirection)}
                      <tr class="unified-session-row">
                        <!-- 第一列数据 -->
                        {#if getColumnGroups()[0] && getColumnGroups()[0][rowIndex]}
                          {@const sessionData = getColumnGroups()[0][rowIndex]}
                          <td class="activity-cell">
                            <div class="mini-chart" on:click={() => handleRowClick(sessionData)}>
                              <ZoomoutChart
                                on:containerClick={handleContainerClick}
                                bind:this={chartRefs[sessionData.sessionId]}
                                sessionId={sessionData.sessionId}
                                similarityData={sessionData.similarityData}
                              />
                            </div>
                          </td>
                          <td class="topic-cell">
                            <button
                              class="topic-icon-btn"
                              on:click|stopPropagation={() => handleCategoryIconClick(getPromptCode(sessionData.sessionId))}
                              title={getPromptCode(sessionData.sessionId)}
                              type="button"
                            >
                              {getCategoryIcon(getPromptCode(sessionData.sessionId))}
                            </button>
                          </td>
                          <td class="score-cell">
                            <SemanticExpansionCircle 
                              llmJudgeScore={sessionData.llmScore}
                              size={16}
                              sessionId={sessionData.sessionId}
                            />
                          </td>
                        {:else}
                          <td class="empty-cell"></td>
                          <td class="empty-cell"></td>
                          <td class="empty-cell"></td>
                        {/if}
                        
                        <!-- 第二列数据 -->
                        {#if getColumnGroups()[1] && getColumnGroups()[1][rowIndex]}
                          {@const sessionData = getColumnGroups()[1][rowIndex]}
                          <td class="activity-cell">
                            <div class="mini-chart" on:click={() => handleRowClick(sessionData)}>
                              <ZoomoutChart
                                on:containerClick={handleContainerClick}
                                bind:this={chartRefs[sessionData.sessionId]}
                                sessionId={sessionData.sessionId}
                                similarityData={sessionData.similarityData}
                              />
                            </div>
                          </td>
                          <td class="topic-cell">
                            <button
                              class="topic-icon-btn"
                              on:click|stopPropagation={() => handleCategoryIconClick(getPromptCode(sessionData.sessionId))}
                              title={getPromptCode(sessionData.sessionId)}
                              type="button"
                            >
                              {getCategoryIcon(getPromptCode(sessionData.sessionId))}
                            </button>
                          </td>
                          <td class="score-cell">
                            <SemanticExpansionCircle 
                              llmJudgeScore={sessionData.llmScore}
                              size={16}
                              sessionId={sessionData.sessionId}
                            />
                          </td>
                        {:else}
                          <td class="empty-cell"></td>
                          <td class="empty-cell"></td>
                          <td class="empty-cell"></td>
                        {/if}
                        
                        <!-- 第三列数据 -->
                        {#if getColumnGroups()[2] && getColumnGroups()[2][rowIndex]}
                          {@const sessionData = getColumnGroups()[2][rowIndex]}
                          <td class="activity-cell">
                            <div class="mini-chart" on:click={() => handleRowClick(sessionData)}>
                              <ZoomoutChart
                                on:containerClick={handleContainerClick}
                                bind:this={chartRefs[sessionData.sessionId]}
                                sessionId={sessionData.sessionId}
                                similarityData={sessionData.similarityData}
                              />
                            </div>
                          </td>
                          <td class="topic-cell">
                            <button
                              class="topic-icon-btn"
                              on:click|stopPropagation={() => handleCategoryIconClick(getPromptCode(sessionData.sessionId))}
                              title={getPromptCode(sessionData.sessionId)}
                              type="button"
                            >
                              {getCategoryIcon(getPromptCode(sessionData.sessionId))}
                            </button>
                          </td>
                          <td class="score-cell">
                            <SemanticExpansionCircle 
                              llmJudgeScore={sessionData.llmScore}
                              size={16}
                              sessionId={sessionData.sessionId}
                            />
                          </td>
                        {:else}
                          <td class="empty-cell"></td>
                          <td class="empty-cell"></td>
                          <td class="empty-cell"></td>
                        {/if}
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          {/if}
        {/if}
      </div>
      {#if showMulti}
        {#if $clickSession}
          <div class="multi-box" style="margin-top: 70px;">
            {#if !loadedMap[$clickSession.sessionId]}
                  <SkeletonLoading />
            {/if}
            <div class:hide={!loadedMap[$clickSession.sessionId]}>
              <div class="display-box">
                <div class="content-box">
                  <div class="session-identifier">
                    <h3>
                      {#if sessions && sessions.find((s) => s.session_id === $clickSession.sessionId)}
                        {sessions.find(
                          (s) => s.session_id === $clickSession.sessionId
                        ).prompt_code} - {$clickSession.sessionId}
                      {:else}
                        Session: {$clickSession.sessionId}
                      {/if}
                    </h3>
                  </div>
                  <div
                    class="session-summary"
                    id="summary-{$clickSession.sessionId}"
                  >
                    <h3>Session Summary</h3>
                    <div class="summary-container">
                      <div class="totalText">
                        {$clickSession.summaryData
                          ? `Total Text: ${$clickSession.summaryData.totalProcessedCharacters} characters`
                          : ""}
                      </div>
                      <div class="totalInsertions">
                        {$clickSession.summaryData
                          ? `Insertions: ${$clickSession.summaryData.totalInsertions}`
                          : ""}
                      </div>
                      <div class="totalDeletions">
                        {$clickSession.summaryData
                          ? `Deletions: ${$clickSession.summaryData.totalDeletions}`
                          : ""}
                      </div>
                      <div class="totalSuggestions">
                        {$clickSession.summaryData
                          ? `Suggestions: ${$clickSession.summaryData.totalSuggestions - 1}`
                          : ""}
                      </div>
                    </div>
                  </div>
                  <div class="" on:wheel={handleChartZoom}>
                    <div class="chart-wrapper">
                      {#if $clickSession.similarityData}
                        <BarChartY
                          sessionId={$clickSession.sessionId}
                          similarityData={$clickSession.similarityData}
                          {yScale}
                          {height}
                          bind:zoomTransform={zoomTransforms[$clickSession.sessionId]}
                          {selectionMode}
                          on:selectionChanged={handleSelectionChanged}
                          on:selectionCleared={handleSelectionCleared}
                          bind:this={chartRefs[$clickSession.sessionId + "-barChart"]}
                          on:chartLoaded={handleChartLoaded}
                        />
                      {/if}
                      <div>
                        <LineChart
                          bind:this={chartRefs[$clickSession.sessionId]}
                          chartData={$clickSession.chartData}
                          paragraphColor={$clickSession.paragraphColor}
                          on:pointSelected={(e) =>
                            handlePointSelected(e, $clickSession.sessionId)}
                          {yScale}
                          {height}
                          bind:zoomTransform={zoomTransforms[$clickSession.sessionId]}
                        />
                      </div>
                    </div>
                    <button
                      on:click={() => resetZoom($clickSession.sessionId)}
                      class="zoom-reset-btn"
                    >
                      Reset Zoom
                    </button>
                  </div>
                </div>
                <div class="content-box">
                  <div class="progress-container">
                    <span
                      >{($clickSession?.currentTime || 0).toFixed(2)} mins</span
                    >
                    <progress
                      value={$clickSession?.currentTime || 0}
                      max={$clickSession?.time100 || 1}
                    ></progress>
                  </div>
                  <div class="scale-container">
                    <div class="scale" id="scale"></div>
                  </div>
                  <div class="text-container">
                    {#if $clickSession.textElements && $clickSession.textElements.length > 0}
                      {#each $clickSession.textElements as element, index}
                        <span
                          class="text-span"
                          style="color: {element.textColor}"
                        >
                          {element.text}
                        </span>
                      {/each}
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/if}
      {/if}
    </div>
    {#if !showMulti}
      <div class="table" class:collapsed={isCollapsed}>
        <table>
          <thead>
            <tr>
              <th
                style="text-transform: uppercase; padding-top: 10px; padding-bottom: 7px"
                >Session ID</th
              >
              <th
                style="display: inline-flex; align-items: center; gap: 4px; text-transform: uppercase; padding-top: 10px; padding-bottom: 7px"
                >Prompt Code
                  <a
                    on:click|preventDefault={toggleFilter}
                    href=" "
                    aria-label="Filter"
                    bind:this={filterButton}
                    class={showFilter
                      ? "material-symbols--filter-alt"
                      : "material-symbols--filter-alt-outline"}
                  >
                  </a>
              </th>
              <th
                style="text-transform: uppercase; padding-top: 10px; padding-bottom: 7px"
                >Selected</th
              >
              <th>
                <a
                  on:click|preventDefault={toggleTableCollapse}
                  href=" "
                  aria-label="Collapse"
                  bind:this={collapseButton}
                  class={isCollapsed
                    ? "material-symbols--stat-1-rounded"
                    : "material-symbols--stat-minus-1-rounded"}
                >
                </a>
              </th>
            </tr>
          </thead>
          <tbody>
            {#each $filterTableData as row, index}
              <tr>
                <td>{row.session_id}</td>
                <td>{row.prompt_code}</td>
                <td style="padding-left: 230px">
                  <input
                    type="checkbox"
                    checked={row.selected}
                    on:change={() => handleSelectChange(index)}
                  />
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </header>
</div>

<style>
  :root {
    color-scheme: light !important;
    --progColor: hsl(6, 100%, 75%);
    --progHeight: 20px;
    --progBackgroundColor: hsl(6, 100%, 90%);
    --range-handle: #86cecb;
    --range-handle-focus: #137a7f;
  }

  .zoom-reset-btn {
    display: block;
    margin: 10px auto;
    padding: 5px 10px;
    background-color: #137a7f;
    color: white;
    border: none;
    cursor: pointer;
    border-radius: 5px;
  }

  .zoom-reset-btn:hover {
    background-color: #86cecb;
  }

  .container {
    width: 100%; 
    margin: 0 auto;
    margin-bottom: 70px;
    display: flex;
    justify-content: center;
    padding: 0 10px;
  }

  .multi-box {
    display: flex;
    flex-direction: column;
    gap: 20px;
    align-items: stretch;
    width: 100%;
    max-width: 1200px;
  }

  .display-box {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    gap: 10px;
    border-radius: 15px;
    padding: 25px;
    box-shadow:
      0px 1px 5px rgba(0, 0, 0, 0.1),
      1px 1px 5px rgba(0, 0, 0, 0.1),
      -1px 1px 5px rgba(0, 0, 0, 0.1);
    font-family: Poppins, sans-serif;
    font-size: 14px;
    white-space: pre-wrap;
    text-align: left;
    width: 100%;
    margin-top: 50px;
  }

  .content-box {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 400px;
    font-family: Poppins, sans-serif;
    font-size: 14px;
    white-space: pre-wrap;
    text-align: left;
    padding: 15px;
  }

  .content-box:first-child {
  flex: 3; 
}


  .text-container {
    flex: 1;
    width: 100%;
    max-height: 100%;
    overflow-y: auto;
    margin-top: 20px;
  }

  .text-span {
    display: inline;
  }

  .progress-container {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: hsl(6, 100%, 90%);
    border-radius: 20px;
    color: white;
    width: fit-content;
    position: relative;
  }

  .progress-container span {
    background-color: transparent;
    position: absolute;
    z-index: 1;
    text-align: center;
    top: 10%;
  }
  
  .grid-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: white;
    border-radius: 8px;
    padding: 15px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  progress {
    width: 600px;
    appearance: none;
  }

  progress::-webkit-progress-value {
    height: var(--progHeight);
    border-radius: 20px;
    background: var(--progColor);
  }

  progress::-webkit-progress-bar {
    height: var(--progHeight);
    border-radius: 20px;
    background: var(--progBackgroundColor);
  }

  progress::-moz-progress-bar {
    height: var(--progHeight);
    border-radius: 20px;
    background: var(--progColor);
  }

  .session-identifier {
    padding: 8px 12px;
    border-radius: 4px;
    margin-bottom: 10px;
  }

  .session-identifier h3 {
    margin: 0;
    font-size: 14px;
    color: #333;
  }

  .summary-container {
    display: flex;
    justify-content: space-between;
  }

  .session-summary {
    font-family: Poppins, sans-serif;
    font-size: 12px;
    line-height: 1.1;
  }

  .session-summary h3 {
    margin-bottom: 2px;
    font-size: 12px;
  }

  .session-summary div {
    margin-bottom: 2px;
  }

  .totalText,
  .totalInsertions,
  .totalDeletions,
  .totalSuggestions {
    display: inline-block;
    white-space: nowrap;
    margin-right: 15px;
  }

  .chart-explanation {
    margin-top: 5px;
    font-family: Poppins, sans-serif;
    font-size: 12px;
    display: flex;
  }

  .triangle-text {
    color: #ffbbcc;
  }

  .user-line {
    color: #66c2a5;
  }

  .api-line {
    color: #fc8d62;
  }

  .triangle-text,
  .user-line,
  .api-line {
    margin-right: 3px;
  }

  .chart-explanation span {
    margin-left: 7px;
  }

  .introduction-background {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999;
  }

  .introduction {
    background: white;
    padding: 20px;
    border-radius: 10px;
    max-width: 500px;
    text-align: center;
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
  }

  .introduction h2 {
    margin-bottom: 10px;
  }

  .start-button {
    margin-top: 15px;
    padding: 10px 20px;
    background: #137a7f;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
  }

  .start-button:hover {
    background: #86cecb;
  }

  nav {
    position: fixed;
    top: 0;
    width: 100%;
    background-color: white;
    padding: 1em 0;
    margin: 0px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    z-index: 2;
    left: 0;
    display: flex;
  }

  nav a {
    color: #333;
    text-decoration: none;
    margin: 0 1em;
    font-weight: 500;
    cursor: pointer;
  }

  .table,
  .collapsed {
    position: fixed;
    bottom: 0;
    width: 100%;
    background-color: white;
    margin: 0px;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
    z-index: 1;
    left: 0;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    transition: height 0.2s ease;
  }

  .table {
    height: 225px;
  }

  .collapsed {
    height: 40px;
  }

  thead {
    position: sticky;
    top: 0;
    background: white;
    z-index: 10;
  }

  .material-symbols--info-outline-rounded {
    display: flex;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M12 17q.425 0 .713-.288T13 16v-4q0-.425-.288-.712T12 11t-.712.288T11 12v4q0 .425.288.713T12 17m0-8q.425 0 .713-.288T13 8t-.288-.712T12 7t-.712.288T11 8t.288.713T12 9m0 13q-2.075 0-3.9-.788t-3.175-2.137T2.788 15.9T2 12t.788-3.9t2.137-3.175T8.1 2.788T12 2t3.9.788t3.175 2.137T21.213 8.1T22 12t-.788 3.9t-2.137 3.175t-3.175 2.138T12 22m0-2q3.35 0 5.675-2.325T20 12t-2.325-5.675T12 4T6.325 6.325T4 12t2.325 5.675T12 20m0-8'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
    margin-left: auto;
    margin-left: 10px;
  }

  .material-symbols--filter-alt-outline {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M11 20q-.425 0-.712-.288T10 19v-6L4.2 5.6q-.375-.5-.112-1.05T5 4h14q.65 0 .913.55T19.8 5.6L14 13v6q0 .425-.288.713T13 20zm1-7.7L16.95 6h-9.9zm0 0'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  .material-symbols--filter-alt {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M11 20q-.425 0-.712-.288T10 19v-6L4.2 5.6q-.375-.5-.112-1.05T5 4h14q.65 0 .913.55T19.8 5.6L14 13v6q0 .425-.288.713T13 20z'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  .filter-container {
    position: absolute;
    top: 195px;
    left: 750px;
    background: white;
    border: 1px solid #ccc;
    padding: 12px;
    display: none;
    box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
    width: 200px;
    text-align: left;
    border-radius: 8px;
    transition: top 0.2s ease;
  }

  .filter-container-close {
    position: absolute;
    top: 370px;
    left: 750px;
    background: white;
    border: 1px solid #ccc;
    padding: 12px;
    display: none;
    box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
    width: 200px;
    text-align: left;
    border-radius: 8px;
    transition: top 0.2s ease;
  }

  .filter-container.show {
    display: block;
  }

  .filter-container label {
    display: block;
    cursor: pointer;
    margin-bottom: 8px;
  }

  .filter-label {
    display: flex;
    align-items: center;
    cursor: pointer;
    margin-bottom: 8px;
    position: relative;
    font-weight: normal;
  }

  .checkbox-wrapper {
    position: relative;
    display: inline-block;
    width: 16px;
    height: 16px;
    margin-right: 8px;
  }

  .filter-checkbox {
    vertical-align: middle;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    width: 16px;
    height: 16px;
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    background-color: white;
    cursor: pointer;
    position: relative;
    margin: 0;
  }

  .custom-checkbox {
    position: absolute;
    top: 0;
    left: 0;
    width: 16px;
    height: 16px;
    pointer-events: none;
  }

  .checkbox-indicator {
    position: absolute;
    left: 50%;
    transform: translate(-50%, 25%);
    color: white;
    font-size: 12px;
    font-weight: bold;
    pointer-events: none;
  }

  .checkbox-indicator-alter {
    position: absolute;
    left: 50%;
    transform: translate(-50%, -20%);
    color: white;
    font-size: 12px;
    font-weight: bold;
    pointer-events: none;
  }

  input[type="checkbox"] {
    vertical-align: middle;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    width: 16px;
    height: 16px;
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    background-color: white;
    cursor: pointer;
    position: relative;
  }

  input[type="checkbox"]:checked {
    background-color: #ffbbcc;
    border-color: #ffbbcc;
  }

  input[type="checkbox"]:checked::before {
    content: "✔";
    font-size: 12px;
    color: white;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: bold;
  }

  #checkbox-n:checked::before {
    content: "";
  }

  .material-symbols--stat-1-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='m12 10.8l-3.9 3.875q-.275.275-.687.288t-.713-.288q-.275-.275-.275-.7t.275-.7l4.6-4.6q.15-.15.325-.213T12 8.4t.375.063t.325.212l4.6 4.6q.275.275.288.688t-.288.712q-.275.275-.7.275t-.7-.275z'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  .material-symbols--stat-minus-1-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M12 14.95q-.2 0-.375-.062t-.325-.213l-4.6-4.6q-.275-.275-.288-.687t.288-.713q.275-.275.7-.275t.7.275L12 12.55l3.9-3.875q.275-.275.688-.288t.712.288q.275.275.275.7t-.275.7l-4.6 4.6q-.15.15-.325.213T12 14.95'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  a:focus,
  a:active {
    color: #86cecb;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  tbody tr {
    border-bottom: 1px solid #e0e0e0;
    display: table-row;
  }

  td {
    padding: 12px 16px;
  }

  .chart-wrapper {
    display: flex;
    align-items: flex-start;
    margin: 15px 0;
  }

  .material-symbols--restart-alt-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M9.825 20.7q-2.575-.725-4.2-2.837T4 13q0-1.425.475-2.713t1.35-2.362q.275-.3.675-.313t.725.313q.275.275.288.675t-.263.75q-.6.775-.925 1.7T6 13q0 2.025 1.188 3.613t3.062 2.162q.325.1.538.375t.212.6q0 .5-.35.788t-.825.162m4.35 0q-.475.125-.825-.175t-.35-.8q0-.3.213-.575t.537-.375q1.875-.6 3.063-2.175T18 13q0-2.5-1.75-4.25T12 7h-.075l.4.4q.275.275.275.7t-.275.7t-.7.275t-.7-.275l-2.1-2.1q-.15-.15-.212-.325T8.55 6t.063-.375t.212-.325l2.1-2.1q.275-.275.7-.275t.7.275t.275.7t-.275.7l-.4.4H12q3.35 0 5.675 2.325T20 13q0 2.725-1.625 4.85t-4.2 2.85'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  .zoomout-chart {
    display: flex;
    margin-left: 3vw;
    margin-right: 3vw;
    height: 30px;
    width: 100%;
    justify-content: center;
  }

  .loading {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999;
  }

  .line-md--loading-twotone-loop {
    display: inline-block;
    width: 96px;
    height: 96px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cg fill='none' stroke='%23000' stroke-linecap='round' stroke-linejoin='round' stroke-width='2'%3E%3Cpath stroke-dasharray='16' stroke-dashoffset='16' d='M12 3c4.97 0 9 4.03 9 9'%3E%3Canimate fill='freeze' attributeName='stroke-dashoffset' dur='0.3s' values='16;0'/%3E%3CanimateTransform attributeName='transform' dur='1.5s' repeatCount='indefinite' type='rotate' values='0 12 12;360 12 12'/%3E%3C/path%3E%3Cpath stroke-dasharray='64' stroke-dashoffset='64' stroke-opacity='0.3' d='M12 3c4.97 0 9 4.03 9 9c0 4.97 -4.03 9 -9 9c-4.97 0 -9 -4.03 -9 -9c0 -4.97 4.03 -9 9 -9Z'%3E%3Canimate fill='freeze' attributeName='stroke-dashoffset' dur='1.2s' values='64;0'/%3E%3C/path%3E%3C/g%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
    z-index: 1000;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }

  .material-symbols--search-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M9.5 16q-2.725 0-4.612-1.888T3 9.5t1.888-4.612T9.5 3t4.613 1.888T16 9.5q0 1.1-.35 2.075T14.7 13.3l5.6 5.6q.275.275.275.7t-.275.7t-.7.275t-.7-.275l-5.6-5.6q-.75.6-1.725.95T9.5 16m0-2q1.875 0 3.188-1.312T14 9.5t-1.312-3.187T9.5 5T6.313 6.313T5 9.5t1.313 3.188T9.5 14'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  .pattern-search-button {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 16px;
    background-color: #137a7f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
    font-weight: 500;
    margin-left: auto;
  }

  .pattern-search-button.active {
    background-color: #ea4335;
  }

  .pattern-search-button:hover {
    opacity: 0.9;
  }

  .search-icon {
    font-size: 16px;
  }

  .pattern-search-panel {
    position: fixed;
    top: 70px;
    right: 20px;
    width: 500px;
    max-height: calc(100vh - 100px);
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.2);
    overflow: auto;
    z-index: 1000;
    display: flex;
    flex-direction: column;
  }

  .pattern-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background-color: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
    position: sticky;
    top: 0;
  }

  .pattern-panel-header h3 {
    margin: 0;
    font-size: 16px;
    color: #202124;
  }

  .pattern-panel-content {
    padding: 16px;
    overflow-y: auto;
  }

  .pattern-instructions {
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid #e0e0e0;
    color: #5f6368;
    font-size: 14px;
  }

  .pattern-results-summary h4 {
    margin: 0 0 12px 0;
    font-size: 15px;
    color: #202124;
  }

  .pattern-item {
    background-color: #f8f9fa;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 12px;
  }

  .pattern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .pattern-header h5 {
    margin: 0;
    font-size: 12px;
    color: #202124;
  }

  .view-pattern-button {
    padding: 4px 10px;
    background-color: #137a7f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }

  .pattern-chart-preview.small-preview {
    width: 150px; 
    height: 120px;
  }

  .delete-pattern-button {
    padding: 4px 10px;
    background-color: #921515;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }

  .search-pattern-button {
    padding: 4px 10px;
    background-color: #137a7f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }

  .pattern-details {
    font-size: 13px;
    color: #5f6368;
    margin-bottom: 10px;
  }

  .pattern-chart-preview {
    height: 120px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    margin-top: 10px;
    background-color: white;
  }

  .close-button {
    background: none;
    border: none;
    font-size: 22px;
    cursor: pointer;
    color: #5f6368;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    transition: background-color 0.2s;
  }

  .close-button:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }

  .no-patterns-selected {
    color: #5f6368;
    font-size: 14px;
    padding: 16px;
    text-align: center;
    background-color: #f8f9fa;
    border-radius: 6px;
  }

  .highlighted-text {
    background-color: #ffeb3b;
    padding: 0 1px;
    border-radius: 2px;
  }

  .hide {
    display: none;
  }

  :global(.rangeSlider) {
    font-size: 4px;
    width: 100px;
  }

 :global(.rangeFloat) {
    font-size: 12px !important;
    opacity: 1 !important;
    background-color: transparent !important;
    color: #99A2A2 !important;
    top: 0 !important;
  }

  .dimmed {
    color: #5f6368;
  }

  .switch {
    position: relative;
    display: inline-block;
    width: 25px;
    height: 14px;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0;
    right: 0; bottom: 0;
    background-color: #ccc;
    transition: 0.2s;
    border-radius: 28px;
  }

  .slider::before {
    position: absolute;
    content: "";
    height: 11px;
    width: 11px;
    left: 1.5px;
    bottom: 1.5px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: #ffbbcc;
  }

  input:checked + .slider::before {
    transform: translateX(11px);
  }

  .search-result-container {
    transition: background-color 0.2s ease;
    border-radius: 8px;
    margin-top: 10px; 
    margin-bottom: 10px;
  }

  .search-result-container:hover {
    background-color: #e0e0e0;
  }

</style>
