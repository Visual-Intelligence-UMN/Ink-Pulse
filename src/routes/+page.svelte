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
  import * as d3 from "d3";
  import PatternChartPreview from "../components/patternChartPreview.svelte";
  import PatternChartPreviewSerach from "../components/patternChartPreviewSerach.svelte";
  import SkeletonLoading from "../components/skeletonLoading.svelte";
  import { getCategoryIcon } from "../components/topicIcons.js";
  import "../components/styles.css";
  import LineChartPreview from "../components/lineChartPreview.svelte";
  import SessionCell from "../components/sessionCell.svelte";
  import SavePanel from "../components/savePanel.svelte";
  import PatternDetailView from "../components/PatternDetailView.svelte";
  import SavedPatternsBar from "../components/SavedPatternsBar.svelte";
  import { searchPatternSet } from '../components/cache.js';

  let chartRefs = {};
  let filterButton;
  let collapseButton;
  let selectionMode = false;
  let selectedPatterns = {};
  let showPatternSearch = false;
  let exactSourceButton;
  let exactTrendButton;

  function initTippy(el, content) {
    if (!el._tippy) {
      tippy(el, {
        content,
        placement: "top",
      });
    }
  }
  $: filterButton && initTippy(filterButton, "Filter based on prompt type");
  $: collapseButton && initTippy(collapseButton, "Collapse/Expand table view");
  $: exactSourceButton &&
    initTippy(exactSourceButton, "Open/Close exact search");
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
  let currentView = 'landing'; 
  let selectedPatternForDetail = null;
  let activePatternId = null;
  let isProgressChecked = false;
  let isTimeChecked = false;
  let isSourceChecked = true;
  let isSemanticChecked = true;
  let isValueRangeChecked = true;
  let isValueTrendChecked = true;
  $: if (!isSemanticChecked) {
    isValueRangeChecked = false;
    isValueTrendChecked = false;
  }
  export const patternDataList = writable([]);
  export const initData = writable([]);
  let currentResults = {};
  let isSearch = 0; // 0: not searching, 1: searching, 2: search done
  let searchCount = 5; // count of search results
  export const showResultCount = writable(searchCount); // count of results to show in the UI

  let isExactSearchSource = true;
  let isExactSearchTrend = true;
  $: if (!isSemanticChecked || !isValueTrendChecked) {
    isExactSearchTrend = false;
  }
  $: if (!isSourceChecked) {
    isExactSearchSource = false;
  }

  export const displaySessions = writable([]);
  $: {
    let newDisplaySessions = [];
    if (selectedCategoryFilter && filteredSessions.length >= 0) {
      newDisplaySessions = filteredSessions;
    } else if (!groupingMode) {
      newDisplaySessions = $initData;
    } else if (Object.keys(groupedSessions).length > 0) {
      newDisplaySessions = Object.values(groupedSessions).flat();
    } else if (sortedSessions.length > 0) {
      newDisplaySessions = sortedSessions;
    } else {
      newDisplaySessions = $initData;
    }

    displaySessions.set(newDisplaySessions);
  }


  const removepattern = (segmentId) => {
    patternDataList.update((patternList) =>
      patternList.filter((pattern) => pattern.segmentId !== segmentId)
    );
    showResultCount.update((count) => count - 1);
  };

  let isSave = false;
  let nameInput = "";
  let colorInput = "#66ccff";
  async function openSavePanel() {
    isSave = false;
    await tick();
    nameInput = "";
    colorInput = "#66ccff";
    isSave = true;
  }

  function handleSave(event) {
    const { name, color } = event.detail;
    const allPatternData = get(patternDataList).slice(0, get(showResultCount));
    const seenSessionIds = new Set();
    const deduplicatedData = allPatternData.filter(session => {
      if (seenSessionIds.has(session.sessionId)) {
        return false;
      }
      seenSessionIds.add(session.sessionId);
      return true;
    });
    
    const processedSlice = deduplicatedData.map(session => ({
      ...session,
      llmScore: session.similarityData[0].score || 0
    }));
    
    const itemToSave = {
      id: `pattern_${Date.now()}`,
      name,
      color,
      pattern: processedSlice,
      metadata: {
        createdAt: Date.now(),
        totalSessions: processedSlice.length,
        originalMatches: allPatternData.length
      }
    };
    
    searchPatternSet.update((current) => [...current, itemToSave]);
    isSave = false;

    tick().then(() => {
      // Method1:  update showPatternColumn
      //const currentPatterns = get(searchPatternSet);
      //showPatternColumn = currentPatterns && currentPatterns.length > 0;
      // Method2: refresh patternDataList
      initData.update(data => [...data]);
      // Mathod3: update patternDataList
      //displaySessions.update(sessions => [...sessions]);
    });
  }

  function handleClose() {
    isSave = false;
  }

  function getPromptCode(sessionId) {
    const found = sessions.find((s) => s.session_id === sessionId);
    return found?.prompt_code ?? "";
  }

  // Functions about tables
  function handleRowClick(sessionData) {
    handleContainerClick({ detail: { sessionId: sessionData.sessionId } });
  }
  // TOPIC ICONS
  let sortColumn = "";
  let sortDirection = "none";

  function handleSort(column) {
    if (sortColumn === column) {
      if (sortDirection === "none") {
        sortDirection = "asc";
      } else if (sortDirection === "asc") {
        sortDirection = "desc";
      } else {
        sortDirection = "none";
      }
    } else {
      sortColumn = column;
      sortDirection = "asc";
    }
  }

  function getSortIcon(column) {
    if (sortColumn !== column || sortDirection === "none") {
      return "↕️";
    }
    return sortDirection === "asc" ? "↑" : "↓";
  }
  // FETCH SCORES
  const fetchLLMScore = async (sessionFile) => {
    const url = `${base}/chi2022-coauthor-v1.0/eval_results/${sessionFile}.json`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        console.error("Response not ok:", response.status, response.statusText);
        throw new Error(`Failed to fetch LLM score: ${response.status}`);
      }

      const data = await response.json();
      const totalScore = data[0];
      return totalScore;
    } catch (error) {
      console.error("Error when reading LLM score file:", error);
      return null;
    }
  };

  function getColumnGroups() {
    let sessions = getDisplaySessions();
    // Topic
    if (sortColumn === "topic" && sortDirection !== "none") {
      sessions = [...sessions].sort((a, b) => {
        const aCode = getPromptCode(a.sessionId);
        const bCode = getPromptCode(b.sessionId);

        if (sortDirection === "asc") {
          return aCode.localeCompare(bCode);
        } else {
          return bCode.localeCompare(aCode);
        }
      });
    }
    // Score
    if (sortColumn === "score" && sortDirection !== "none") {
      sessions = [...sessions].sort((a, b) => {
        const aScore = a.llmScore || 0;
        const bScore = b.llmScore || 0;
        if (sortDirection === "asc") {
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

  $: if (sortColumn || sortDirection) {
  }

  // function calculateAccumulatedSemanticScore(data) {
  //   if (!data || data.length === 0) return 0;

  //   const totalScore = data.reduce((sum, item) => {
  //     return sum + (item.residual_vector_norm || 0);
  //   }, 0);

  //   return totalScore;
  // }

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
    $initData.forEach((sessionData) => {
      const sessionInfo = sessions.find(
        (s) => s.session_id === sessionData.sessionId,
      );
      if (sessionInfo) {
        const key = sessionInfo[attribute] || "unknown";
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
    return $initData.filter((sessionData) => {
      const sessionInfo = sessions.find(
        (s) => s.session_id === sessionData.sessionId,
      );
      return sessionInfo && sessionInfo.prompt_code === category;
    });
  }

  function rankSessionsByAttribute(attribute, sessionsData) {
    const sessionsCopy = [...sessionsData];

    switch (attribute) {
      case "prompt_code":
        return sessionsCopy.sort((a, b) => {
          const aCode = getPromptCode(a.sessionId);
          const bCode = getPromptCode(b.sessionId);
          return aCode.localeCompare(bCode);
        });

      case "writing_time":
        return sessionsCopy.sort((a, b) => {
          const aTime = a.time100 || 0;
          const bTime = b.time100 || 0;
          return bTime - aTime;
        });

      case "text_length":
        return sessionsCopy.sort((a, b) => {
          const aLength = a.summaryData?.totalProcessedCharacters || 0;
          const bLength = b.summaryData?.totalProcessedCharacters || 0;
          return bLength - aLength;
        });

      case "suggestions_count":
        return sessionsCopy.sort((a, b) => {
          const aSuggestions = a.summaryData?.totalSuggestions || 0;
          const bSuggestions = b.summaryData?.totalSuggestions || 0;
          return bSuggestions - aSuggestions;
        });

      default:
        return sessionsCopy;
    }
  }

  // function handleIconClick(attribute, mode = "group", specificValue = null) {
  //   if (selectedCategoryFilter === specificValue && specificValue) {
  //     groupingMode = false;
  //     selectedGroupAttribute = null;
  //     selectedCategoryFilter = null;
  //     groupedSessions = {};
  //     sortedSessions = [];
  //     filteredSessions = [];
  //     return;
  //   }

  //   if (specificValue) {
  //     groupingMode = true;
  //     selectedGroupAttribute = attribute;
  //     selectedCategoryFilter = specificValue;

  //     filteredSessions = filterSessionsByCategory(specificValue);
  //     groupedSessions = {};
  //     sortedSessions = [];
  //     return;
  //   }

  //   if (
  //     groupingMode &&
  //     selectedGroupAttribute === attribute &&
  //     !selectedCategoryFilter
  //   ) {
  //     groupingMode = false;
  //     selectedGroupAttribute = null;
  //     selectedCategoryFilter = null;
  //     groupedSessions = {};
  //     sortedSessions = [];
  //     filteredSessions = [];
  //   } else {
  //     groupingMode = true;
  //     selectedGroupAttribute = attribute;
  //     selectedCategoryFilter = null;

  //     if (mode === "group") {
  //       groupedSessions = groupSessionsByAttribute(attribute);
  //       sortedSessions = [];
  //       filteredSessions = [];
  //     } else if (mode === "rank") {
  //       sortedSessions = rankSessionsByAttribute(attribute, $initData);
  //       groupedSessions = {};
  //       filteredSessions = [];
  //     }
  //   }
  // }

  let filteredByCategory = [];
  function handleCategoryIconClick(category) {
    if (selectedCategoryFilter === category) {
      selectedCategoryFilter = null;
      filteredByCategory = [];

      const originalFilteredData = tableData.filter((session) =>
        $selectedTags.includes(session.prompt_code),
      );
      const originalUpdatedData = originalFilteredData.map((row) => ({
        ...row,
        selected: true,
      }));
      filterTableData.set(originalUpdatedData);
    } else {
      selectedCategoryFilter = category;

      filteredByCategory = $initData.filter((sessionData) => {
        const sessionInfo = sessions.find(
          (s) => s.session_id === sessionData.sessionId,
        );
        return sessionInfo && sessionInfo.prompt_code === category;
      });

      const categoryTableRows = tableData.filter(
        (row) => row.prompt_code === category,
      );
      filterTableData.set(
        categoryTableRows.map((row) => ({
          ...row,
          selected: true,
        })),
      );

      categoryTableRows.forEach((row) => {
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

  // function isIconActive(promptCode) {
  //   return selectedCategoryFilter === promptCode;
  // }

  // function getGridItemClass(sessionId) {
  //   if (!groupingMode) return "";

  //   const sessionInfo = sessions.find((s) => s.session_id === sessionId);
  //   if (!sessionInfo) return "";

  //   const attributeValue = sessionInfo[selectedGroupAttribute];
  //   return `grouped-${attributeValue}`;
  // }

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

  function isDataValid(item, checks, minCount) {
    const fieldMap = {
      progress: (d) => d.end_progress * 100,
      time: (d) => d.end_time / 60,
      semantic: (d) => d.residual_vector_norm,
    };

    const relaxRatioMap = {
      progress: 0.3,
    };

    for (const [key, [checked, range]] of Object.entries(checks)) {
      if (!checked || !(key in fieldMap)) continue;
      const value = fieldMap[key](item);
      if (value == null || isNaN(value)) return false;

      if (minCount === 1) {
        if (key === "semantic") {
          const relaxedMin = range[0] - 0.05;
          const relaxedMax = range[1] + 0.05;
          if (value < relaxedMin || value > relaxedMax) return false;
        } else {
          const relaxRatio = relaxRatioMap[key] ?? 0.2;
          const delta = (range[1] - range[0]) * relaxRatio;
          const relaxedMin = range[0] - delta;
          const relaxedMax = range[1] + delta;
          if (value < relaxedMin || value > relaxedMax) return false;
        }
      } else {
        if (value < range[0] || value > range[1]) return false;
      }
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
      const allValid = window.every((item) => isDataValid(item, checks, minCount));
      if (!allValid) continue;
      if (isExactSearchSource && checks.source && checks.source[1]) {
        const expectedSources = checks.source[1];
        if (expectedSources.length !== minCount) continue;

        const actualSources = window.map((item) => item.source);
        const matches = actualSources.every(
          (src, idx) => src === expectedSources[idx],
        );
        if (!matches) continue;
      }
      if (isExactSearchTrend && checks.trend && checks.trend[1] && minCount > 1) {
        const values = window.map((item) => item.residual_vector_norm);
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
        currentVector.t.push(
          currentItem.endTime * 60 - currentItem.startTime * 60,
        );
      }

      if (checks.progress[0]) {
        currentVector.p.push(
          currentItem.endProgress / 100 - currentItem.startProgress / 100,
        );
      }

      if (checks.semantic[0]) {
        currentVector.sem.push(currentItem.residual_vector_norm);
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
      if (checks.semantic[0]) {
        vector.sem.push(item.residual_vector_norm ?? null);
      }
    }
    if (checks.trend[0]) {
      const values = segment.map(d => d.residual_vector_norm ?? 0);
      vector.tr = getTrendPattern(values);
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
        // const fileId = fileName.split(".")[0].replace(/_similarity$/, "");
        // if (fileId === sessionId) {
        //   continue;
        // }
        const dataResponse = await fetch(
          `${base}/chi2022-coauthor-v1.0/similarity_results/${fileName}`,
        );
        const data = await dataResponse.json();
        const segments = findSegments(data, checks, count);
        const extractedFileName = fileName
          .split(".")[0]
          .replace(/_similarity$/, "");

        const taggedSegments = segments.map((segment, index) =>
          segment.map((item) => ({
            ...item,
            id: extractedFileName,
            segmentId: `${extractedFileName}_${index}`,
          })),
        );

        for (const segment of taggedSegments) {
          const vector = buildVectorFromSegment(segment, checks);
          vector.id = segment[0]?.id ?? null;
          vector.segmentId = segment[0]?.segmentId ?? null;
          patternVectors.push(vector);
        }

        results.push(...taggedSegments);
      }
      const currentVector = buildVectorForCurrentSegment(
        currentResults,
        checks,
      );

      patternData = results;
      const finalScore = calculateRank(patternVectors, currentVector);
      const idToData = Object.fromEntries(
        patternData.map((d) => [d[0].segmentId, d]),
      );
      const fullData = finalScore.map(([segmentId]) => idToData[segmentId]);
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
      sum += (arr1[i] - arr2[i]) ** 2;
    }
    return Math.sqrt(sum);
  }

  function calculateRank(patternVectors, currentVector) {
    const weights = {
      s: 1.5, // user 1, api 0
      t: 0.01, // 1s
      p: 1, // 1% -> 0.01
      tr: 2.5, // up 1, down -1
      sem: 2, // 1% -> 0.01
    };
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
          if (!sessionData) return null;
          const cleanSessionData = { ...sessionData };
          if (Array.isArray(cleanSessionData.chartData)) {
            cleanSessionData.chartData = cleanSessionData.chartData.map(({ currentText, ...rest }) => rest);
          }
          delete cleanSessionData.paragraphColor;
          delete cleanSessionData.textElements;

          return {
            ...cleanSessionData,
            segments: group,
            segmentId: group[0]?.segmentId,
          };
        })
        .filter(Boolean),
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

  function handleSelectionChanged(event) {
    showResultCount.set(5);
    isProgressChecked = false;
    isTimeChecked = false;
    isSourceChecked = true;
    isSemanticChecked = true;
    isValueRangeChecked = true;
    isValueTrendChecked = true;
    isExactSearchSource = true;
    isExactSearchTrend = true;
    semanticTrend = [];
    selectedPatterns = {};
    patternData = [];
    patternDataList.set([]);
    currentResults = {};
    const { sessionId, range, dataRange, data, wholeData, sources } =
      event.detail;
    writingProgressRange = [
      dataRange.progressRange.min,
      dataRange.progressRange.max,
    ];
    timeRange = [dataRange.timeRange.min, dataRange.timeRange.max];
    sourceRange = sources;
    semanticRange = [dataRange.scRange.min, dataRange.scRange.max];
    semanticData = dataRange.sc.sc;
    semanticTrend = getTrendPattern(semanticData);
    currentResults = data;

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
          (item) => item.session_id === session.session_id && item.selected,
        ),
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
        (item) => item.prompt_code === tag,
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
              item.session_id === session.sessionId && item.prompt_code === tag,
          ),
        ),
      ).length;
      if (tagSessionCount === 1) {
        const allSessionsForTag = tableData.filter((item) =>
          selectedTagsList.includes(item.prompt_code),
        );
        for (const session of allSessionsForTag) {
          await fetchInitData(session.session_id, false, true);
        }
      }
    } else {
      const allSessionsForTag = tableData.filter((item) =>
        selectedTagsList.includes(item.prompt_code),
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
        $selectedTags.includes(session.prompt_code),
      );
      const sessionArray = Array.from($storeSessionData.values());
      const updatedData = filteredData.map((row) => ({
        ...row,
        selected:
          sessionArray.some((item) => item.sessionId === row.session_id) ||
          true,
      }));

      filterTableData.set(updatedData);
      updatePromptFilterStatus();
    }
  }

  async function fetchInitData(sessionId, isDelete, isPrompt) {
    if (isDelete) {
      initData.update((data) =>
        data.filter((item) => item.sessionId !== sessionId),
      );
      return;
    }
    const similarityData = await fetchSimilarityData(sessionId);
    const llmScore = await fetchLLMScore(sessionId);

    if (similarityData) {
      initData.update((sessions) => {
        const existingIndex = sessions.findIndex(
          (s) => s.sessionId === sessionId,
        );

        if (existingIndex !== -1) {
          sessions[existingIndex] = {
            ...sessions[existingIndex],
            llmScore: llmScore,
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

        selectedSession = sessions.map((session) => session.session_id);
        firstSession = false;
        selectedTags.set([
          "reincarnation",
          "bee",
          "sideeffect",
          "pig",
          "obama",
          "mana",
          "dad",
          "mattdamon",
          "shapeshifter",
          "isolation",
        ]);
        filterSessions();

        $filterTableData = tableData.filter((session) =>
          $selectedTags.includes(session.prompt_code),
        );

        filterOptions = Array.from(
          new Set(tableData.map((row) => row.prompt_code)),
        );

        updatePromptFilterStatus();
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
      const response = await fetch(
        `${base}/chi2022-coauthor-v1.0/coauthor-json/${sessionFile}.jsonl`,
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }
      const data = await response.json();

      time0 = new Date(data.init_time);
      time100 = new Date(data.end_time);
      time100 = (time100.getTime() - time0.getTime()) / (1000 * 60);
      currentTime = time100;

      const { chartData, textElements, paragraphColor, summaryData } =
        handleEvents(data, sessionFile);
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
        `${base}/chi2022-coauthor-v1.0/similarity_results/${sessionFile}_similarity.json`,
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

  onMount(async () => {
    document.title = "Ink-Pulse";
    await fetchSessions();
    for (let i = 0; i < selectedSession.length; i++) {
      const sessionId = selectedSession[i];
      const similarityData = await fetchSimilarityData(sessionId);
      const llmScore = await fetchLLMScore(sessionId);

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
    const newTranslateY = centerY - currentCenterY * newK;

    const maxTranslateY = 0;
    const minTranslateY = -chartHeight * (newK - 1);
    const clampedY = Math.max(
      minTranslateY,
      Math.min(newTranslateY, maxTranslateY),
    );

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
      (match) => match.index,
    );
    let paragraphPercentages = newParagraph.map(
      (pos) => (pos / textLength) * 100,
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
          : prev,
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

    let combinedText = data.info.reduce(
      (acc, event) => {
        const {
          name,
          text = "",
          eventSource,
          event_time,
          count = 0,
          pos = 0,
        } = event;
        const textColor = eventSource === "user" ? "#66C2A5" : "#FC8D62";
        const eventTime = new Date(event_time);

        if (firstTime === null) {
          firstTime = eventTime;
          paragraphTime = [{ time: 0, pos: 0 }];
        }

        const relativeTime =
          (eventTime.getTime() - firstTime.getTime()) / 60000;
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
      },
      [...initText].map((ch) => ({ text: ch, textColor: "#FC8D62" })),
    );

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

    if (
      combinedText.length &&
      combinedText[combinedText.length - 1].text === "\n"
    ) {
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
      },
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

  function handlePatternClick(event) {
    const { pattern } = event.detail;
    
    selectedPatternForDetail = pattern;
    activePatternId = pattern.id;
    currentView = 'pattern-detail';
  }

  function handlePatternContextMenu(event) {
    const { pattern } = event.detail;
    console.log('Right clicked on pattern from table:', pattern.name);

  }

  $: showPatternColumn = $searchPatternSet && $searchPatternSet.length > 0;

  function handleShowMorePatterns() {
    console.log(`Total patterns: ${$searchPatternSet.length}`);
  }

  function handleBackFromDetail() {
    currentView = 'landing';
    selectedPatternForDetail = null;
    activePatternId = null;
  }

  function handleApplyPattern(event) {
    const { pattern } = event.detail;
    if (!selectionMode) {
      selectionMode = true;
      showPatternSearch = true;
    }
    handleBackFromDetail();
  }

  function handleEditPattern(event) {
    const { pattern } = event.detail;
    const newName = prompt(`Edit pattern name:`, pattern.name);
    if (newName && newName.trim() && newName !== pattern.name) {
      searchPatternSet.update((patterns) => 
        patterns.map(p => 
          p.id === pattern.id 
            ? { ...p, name: newName.trim() }
            : p
        )
      );
      if (selectedPatternForDetail && selectedPatternForDetail.id === pattern.id) {
        selectedPatternForDetail = { ...selectedPatternForDetail, name: newName.trim() };
      }
    }
  }

  function handleDeletePattern(event) {
    const { pattern } = event.detail;
    if (confirm(`Are you sure you want to delete pattern "${pattern.name}"?`)) {
      searchPatternSet.update((patterns) => 
        patterns.filter(p => p.id !== pattern.id)
      );
      if (currentView === 'pattern-detail') {
        handleBackFromDetail();
      }
    }
  }

  function handlePatternDetailRowClick(event) {
    const { sessionData } = event.detail;
    handleContainerClick({ detail: { sessionId: sessionData.sessionId } });
    handleBackFromDetail();
  }
</script>

<div class="App">
  <header class="App-header">
    <nav>
      <div class="chart-explanation">
        <span class="triangle-text">▼</span> user open the AI suggestion
        <span class="user-line">●</span> User written
        <span class="api-line">●</span> AI writing
      </div>
      {#if !showMulti}
        <SavedPatternsBar 
          patterns={$searchPatternSet}
          {activePatternId}
          on:pattern-click={handlePatternClick}
          on:pattern-contextmenu={handlePatternContextMenu}
          on:show-more-patterns={handleShowMorePatterns}
        />
      {/if}
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
                        class="search-pattern-button"
                        on:click={() => searchPattern(sessionId)}>Search</button
                      >
                      <button
                        class="delete-pattern-button"
                        on:click={() => deletePattern(sessionId)}>Delete</button
                      >
                    </div>
                  </div>
                  <div class="pattern-details">
                    <div>
                      Semantic Change: {pattern.dataRange.scRange.min.toFixed(
                        2,
                      )} - {pattern.dataRange.scRange.max.toFixed(2)}
                    </div>
                    <div>
                      Progress Range: {pattern.dataRange.progressRange.min.toFixed(
                        2,
                      )}% - {pattern.dataRange.progressRange.max.toFixed(2)}%
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
                        <input
                          type="checkbox"
                          bind:checked={isProgressChecked}
                        />
                        Writing Progress
                        <div style="flex: 1;"></div>
                        <RangeSlider
                          range
                          float
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
                        <RangeSlider
                          range
                          float
                          class="rangeSlider"
                          min={0}
                          max={$clickSession?.time100}
                          bind:values={timeRange}
                        />
                      </div>
                      <div
                        class:dimmed={!isSourceChecked}
                        style="font-size: 13px;"
                      >
                        <input type="checkbox" bind:checked={isSourceChecked} />
                        Source(human/AI)
                        <label
                          class="switch"
                          style="transform: translateY(4px);"
                          bind:this={exactSourceButton}
                        >
                          <input
                            type="checkbox"
                            bind:checked={isExactSearchSource}
                            disabled={!isSourceChecked}
                          />
                          <span class="slider"></span>
                        </label>
                      </div>
                      <div style="font-size: 13px;">
                        <div class:dimmed={!isSemanticChecked}>
                          <input
                            type="checkbox"
                            bind:checked={isSemanticChecked}
                          />
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
                            <label
                              class="switch"
                              style="transform: translateY(4px);"
                              bind:this={exactTrendButton}
                            >
                              <input
                                type="checkbox"
                                bind:checked={isExactSearchTrend}
                                disabled={!isSemanticChecked ||
                                  !isValueTrendChecked}
                              />
                              <span class="slider"></span>
                            </label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  {#if $patternDataList.length > 0 && isSearch == 2}
                    <div>Search Results</div>
                    {#each $patternDataList as sessionData, index (sessionData.segmentId)}
                      {#if index < $showResultCount}
                        <div class="search-result-container">
                          <div
                            style="font-size: 13px; margin-bottom: 4px; margin-left: 8px; position: relative;"
                          >
                            <strong>{sessionData.sessionId}</strong>
                            <button
                              class="close-button"
                              style="position: absolute; top:0px; right:0px; background-color: initial;"
                              on:click={() => removepattern(sessionData.segmentId)}>×</button
                            >
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
                      <div
                        style="display: flex; justify-content: center; margin-top: 10px;"
                      >
                        <button
                          class="search-pattern-button"
                          style="margin-right: 10px;"
                          on:click={openSavePanel}
                          >Save NOW Pattern
                        </button>
                        <button
                          class="search-pattern-button"
                          on:click={() => {
                            $showResultCount += 5;
                          }}
                        >
                          More Results
                        </button>
                      </div>
                    {:else}
                      <div style="text-align: center;">
                        <button
                          class="search-pattern-button"
                          on:click={openSavePanel}
                          >Save NOW pattern
                        </button>
                      </div>
                      <div style="text-align: center; margin-top: 10px;">
                        <span class="no-more-results">End of Results</span>
                      </div>
                    {/if}
                  {:else if $patternDataList.length == 0 && isSearch == 2}
                    <div class="no-data-message">
                      No data found matching the search criteria.
                    </div>
                  {:else if isSearch == 1}
                    <div class="loading-message">Searching for patterns...</div>
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
    {#if isSave}
      <SavePanel
        name={nameInput}
        color={colorInput}
        on:save={handleSave}
        on:close={handleClose}
      />
    {/if}
    <div class="container">
       <!-- <div style="position: fixed; top: 100px; right: 10px; background: red; color: white; padding: 10px; z-index: 9999;">
    DEBUG INFO:<br>
    currentView: {currentView}<br>
    selectedPatternForDetail: {selectedPatternForDetail ? selectedPatternForDetail.name : 'null'}<br>
    showMulti: {showMulti}
  </div> -->
      {#if isOpen}
        <div class="introduction-background">
          <div class="introduction">
            <h2>Welcome to the CoAuthor visualization!</h2>
            <p>
              This platform allows you to explore the <b>human-AI collaborative writing process</b>
              using the <a href="https://coauthor.stanford.edu/" target="_blank">CoAuthor dataset</a>. 
              View how writers interacted with GPT-3, analyze AI-generated suggestions, and track text evolution in real time.
            </p>
            <p>Discover insights into <b>human-AI collaboration</b> and have fun!</p>
            <button class="start-button" on:click={open2close}>Start Exploring</button>
          </div>
        </div>
      {/if}
      
      {#if currentView === 'pattern-detail' && selectedPatternForDetail}
        <div style="margin-top: 70px;">
          <PatternDetailView 
            pattern={selectedPatternForDetail}
            {sessions}
            {chartRefs}
            on:back={handleBackFromDetail}
            on:apply-pattern={handleApplyPattern}
            on:edit-pattern={handleEditPattern}
            on:delete-pattern={handleDeletePattern}
            on:row-click={handlePatternDetailRowClick}
          />
        </div>
       {:else}

      <div style="margin-top: 70px;" hidden={showMulti}>
        {#if $initData.length > 0}
          {#if selectedCategoryFilter}
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
                      <th class="sortable-header" on:click={() => handleSort("topic")}>
                        <span>Topic</span>
                        <span class="sort-icon">{getSortIcon("topic")}</span>
                      </th>
                      <th class="sortable-header" on:click={() => handleSort("score")}>
                        <span>Score</span>
                        <span class="sort-icon">{getSortIcon("score")}</span>
                      </th>
                      {#if showPatternColumn}
                        <th>Pattern</th>
                      {/if}
                      <th>Activity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each selectedCategoryFilter ? filteredByCategory : filteredSessions as sessionData (sessionData.sessionId)}
                    <tr class="session-row" on:click={() => handleRowClick(sessionData)}>
                        <SessionCell
                          {sessionData}
                          {chartRefs}
                          onRowClick={handleRowClick}
                          onCategoryIconClick={handleCategoryIconClick}
                          {getPromptCode}
                          {getCategoryIcon}
                          showPatterns={showPatternColumn}
                          patterns={$searchPatternSet}
                          {activePatternId}
                          on:pattern-click={handlePatternClick}
                          on:pattern-contextmenu={handlePatternContextMenu}
                        />
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
                      {#each Array(3) as _, colIndex}
                        <th class="sortable-header" on:click={() => handleSort("topic")} style="min-width: 80px;">
                          <span>Topic</span>
                          <span class="sort-icon">{getSortIcon("topic")}</span>
                        </th>
                        <th class="sortable-header" on:click={() => handleSort("score")} style="min-width: 80px;">
                          <span>Score</span>
                          <span class="sort-icon">{getSortIcon("score")}</span>
                        </th>
                        {#if showPatternColumn}
                          <th>Pattern</th>
                        {/if}
                        <th>Activity</th>
                        {#if colIndex < 2}
                          <th class="spacer" style="width: 8vw;"></th>
                        {/if}
                      {/each}
                    </tr>
                  </thead>
                  <tbody>
                    {#each Array(Math.ceil(Math.max(...getColumnGroups().map((group) => group.length)))) as _, rowIndex (rowIndex + sortColumn + sortDirection)}
                      <tr class="unified-session-row">
                        {#each getColumnGroups() as group, colIndex}
                          <SessionCell
                            sessionData={group[rowIndex]}
                            {chartRefs}
                            onRowClick={handleRowClick}
                            onCategoryIconClick={handleCategoryIconClick}
                            {getPromptCode}
                            {getCategoryIcon}
                            {colIndex}
                            showPatterns={showPatternColumn}
                            patterns={$searchPatternSet}
                            {activePatternId}
                            on:pattern-click={handlePatternClick}
                            on:pattern-contextmenu={handlePatternContextMenu}
                          />
                        {/each}
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
                        {sessions.find((s) => s.session_id === $clickSession.sessionId).prompt_code} - {$clickSession.sessionId}
                      {:else}
                        Session: {$clickSession.sessionId}
                      {/if}
                    </h3>
                  </div>
                  <div class="session-summary" id="summary-{$clickSession.sessionId}">
                    <h3>Session Summary</h3>
                    <div class="summary-container">
                      <div class="totalText">
                        {$clickSession.summaryData ? `Total Text: ${$clickSession.summaryData.totalProcessedCharacters} characters` : ""}
                      </div>
                      <div class="totalInsertions">
                        {$clickSession.summaryData ? `Insertions: ${$clickSession.summaryData.totalInsertions}` : ""}
                      </div>
                      <div class="totalDeletions">
                        {$clickSession.summaryData ? `Deletions: ${$clickSession.summaryData.totalDeletions}` : ""}
                      </div>
                      <div class="totalSuggestions">
                        {$clickSession.summaryData ? `Suggestions: ${$clickSession.summaryData.totalSuggestions - 1}` : ""}
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
                          on:pointSelected={(e) => handlePointSelected(e, $clickSession.sessionId)}
                          {yScale}
                          {height}
                            bind:zoomTransform={zoomTransforms[$clickSession.sessionId]}
                        />
                      </div>
                    </div>
            
                  </div>
                </div>
                <div class="content-box">
                  <div class="progress-container">
                    <span>{($clickSession?.currentTime || 0).toFixed(2)} mins</span>
                    <progress value={$clickSession?.currentTime || 0} max={$clickSession?.time100 || 1}></progress>
                  </div>
                  <div class="scale-container">
                    <div class="scale" id="scale"></div>
                  </div>
                  <div class="text-container">
                    {#if $clickSession.textElements && $clickSession.textElements.length > 0}
                      {#each $clickSession.textElements as element, index}
                        <span class="text-span" style="color: {element.textColor}">
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
      {/if}
    </div>
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

  .App {
    overflow-x: hidden;
  }

  * {
    font-family: "Poppins", sans-serif;
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
    font-size: 12px;
    display: flex;
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

  nav {
    position: fixed;
    top: 0;
    width: 100%;
    background-color: white;
    padding: 1em 0;
    margin: 0px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    z-index: 600;
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

  thead {
    position: sticky;
    top: 0;
    background: white;
    z-index: 10;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  tbody tr {
    border-bottom: 1px solid #e0e0e0;
    display: table-row;
  }

  .chart-wrapper {
    display: flex;
    align-items: flex-start;
    margin: 15px 0;
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
    z-index: 500;
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

  .pattern-chart-preview.small-preview {
    width: 150px;
    height: 120px;
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

  .no-patterns-selected {
    color: #5f6368;
    font-size: 14px;
    padding: 16px;
    text-align: center;
    background-color: #f8f9fa;
    border-radius: 6px;
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
    color: #99a2a2 !important;
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

  .search-result-container {
    transition: background-color 0.2s ease;
    border-radius: 8px;
    margin-top: 10px;
    margin-bottom: 10px;
  }

  .search-result-container:hover {
    background-color: #e0e0e0;
  }

  .unified-sessions-table {
    width: 80vw;
  }

</style>
