<script>
  import { onMount, onDestroy } from "svelte";
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
  import ConfirmDialog from "../components/ConfirmDialog.svelte";
  import EditPatternDialog from "../components/EditPatternDialog.svelte";
  import {
    searchPatternSet,
    exportDB,
    triggerImport,
    loadPattern,
  } from "../components/cache.js";
  import RankWorker from "../workers/rankWorker.js?worker";
  import WeightPanel from "../components/weightPanel.svelte";

  let chartRefs = {};
  let filterButton;
  let collapseButton;
  let selectionMode = false;
  let selectedPatterns = {};
  let showPatternSearch = false;
  let exactSourceButton;
  let exactTrendButton;
  let searchDetail = null;
  let sharedSelection;
  let exactProgressButton;
  let exactTimeButton;

  let lastSharedSelection = null;
  $: if (sharedSelection) {
    // console.log("selectedPatterns", selectedPatterns);
    // console.log("sharedSelection", sharedSelection);
    if (sharedSelection !== lastSharedSelection) {
      isSearch = 0; // reset search state; 0: not searching, 1: searching, 2: search done
      lastSharedSelection = sharedSelection;
    }
  }

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
  // $: exactSourceButton && initTippy(exactSourceButton, "Open/Close exact search");
  // $: exactTrendButton && initTippy(exactTrendButton, "Open/Close exact search");
  // $: exactProgressButton &&
  //   initTippy(exactProgressButton, "Open/Close exact search");
  // $: exactTimeButton && initTippy(exactTimeButton, "Open/Close exact search");

  onMount(() => {
    loadPattern("patterns/load");
  });

  let dataDict = {
    init_text: [], // Initial text
    init_time: [], // Start time
    json: [], // all operation
    text: [], // final text
    info: [], // insert, delete and suggestion-open operation
    end_time: [],
  };
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
  export const selectedTags = writable([]);
  let filterOptions = [];
  let showMulti = false;
  export const storeSessionData = writable(new Map());
  export const storeSessionSummaryData = writable(new Map());
  let tableData = [];
  let firstSession = true;
  export const filterTableData = writable([]);
  // store to track filter states
  const promptFilterStatus = writable({});
  const margin = { top: 20, right: 0, bottom: 30, left: 50 };
  const height = 200;
  let yScale = d3
    .scaleLinear()
    .domain([0, 100])
    .range([height - margin.top - margin.bottom, 0]);
  let yScaleFactor = (height - margin.top - margin.bottom) / 100;
  let xScaleBarChartFactor;
  let xScaleLineChartFactor;

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
  let currentView = "landing";
  let selectedPatternForDetail = null;
  let activePatternId = null;

  // Loading state for pattern import
  let isImporting = false;

  // Confirm dialog state
  let showDeleteConfirm = false;
  let patternToDelete = null;

  // Edit pattern dialog state
  let showEditDialog = false;
  let patternToEdit = null;
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
  let lastSession = null;
  let datasets = [];
  let selectedDataset = "creative";

  export const patternDataList = writable([]);
  export const initData = writable([]);
  let currentResults = {};
  let isSearch = 0; // 0: not searching, 1: searching, 2: search done
  let searchCount = 5; // count of search results
  export const showResultCount = writable(searchCount); // count of results to show in the UI

  let isExactSearchSource = true;
  let isExactSearchTrend = true;
  let isExactSearchProgress = false;
  let isExactSearchTime = false;
  $: if (!isSemanticChecked || !isValueTrendChecked) {
    isExactSearchTrend = false;
  }
  $: if (!isSourceChecked) {
    isExactSearchSource = false;
  }
  $: if (!isProgressChecked) {
    isExactSearchProgress = false;
  }
  $: if (!isTimeChecked) {
    isExactSearchTime = false;
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
    const deduplicatedData = allPatternData.filter((session) => {
      if (seenSessionIds.has(session.sessionId)) {
        return false;
      }
      seenSessionIds.add(session.sessionId);
      return true;
    });

    const processedSlice = deduplicatedData.map((session) => ({
      ...session,
      llmScore: session.similarityData[0].score || 0,
    }));

    const itemToSave = {
      id: `pattern_${Date.now()}`,
      name,
      color,
      pattern: processedSlice,
      metadata: {
        createdAt: Date.now(),
        totalSessions: processedSlice.length,
        originalMatches: allPatternData.length,
      },
      searchDetail,
    };

    searchPatternSet.update((current) => [...current, itemToSave]);
    isSave = false;

    tick().then(() => {
      initData.update((data) => [...data]);
    });
  }

  function handleClose() {
    isSave = false;
  }

  function handleWeightsClose() {
    isWeights = false;
  }

  function handleWeightsSave(event) {
    weights.set(event.detail.weights);
    isWeights = false;
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
    if (column === "pattern") {
      // Special logic for pattern sorting: toggle between sorted and original order
      if (sortColumn === "pattern") {
        // If already sorting by pattern, revert to original order
        sortColumn = null;
        sortDirection = "none";
      } else {
        // First click: sort by pattern (show sessions with patterns first)
        sortColumn = "pattern";
        sortDirection = "asc";
      }
    } else {
      // Original logic for other columns
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
  }

  function getSortIcon(column) {
    if (column === "pattern") {
      // Special icon for pattern column
      if (sortColumn === "pattern") {
        return "✓"; // Show checkmark when patterns are sorted to front
      } else {
        return "🔄"; // Show refresh icon when not sorted
      }
    } else {
      // Original logic for other columns
      if (sortColumn !== column || sortDirection === "none") {
        return "↕️";
      }
      return sortDirection === "asc" ? "↑" : "↓";
    }
  }

  // FETCH SCORES
  const fetchLLMScore = async (sessionFile) => {
    const url = `${base}/dataset/${selectedDataset}/eval_results/${sessionFile}.json`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        console.error("Response not ok:", response.status, response.statusText);
        throw new Error(`Failed to fetch LLM score: ${response.status}`);
      }

      const data = await response.json();
      const totalScore = data[0] || 0;
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
    // Pattern
    if (sortColumn === "pattern" && sortDirection !== "none") {
      sessions = [...sessions].sort((a, b) => {
        const aHasPattern = hasPattern(a.sessionId);
        const bHasPattern = hasPattern(b.sessionId);

        if (sortDirection === "asc") {
          // Show sessions with patterns first
          if (aHasPattern && !bHasPattern) return -1;
          if (!aHasPattern && bHasPattern) return 1;
          return 0;
        } else {
          // Show sessions without patterns first
          if (aHasPattern && !bHasPattern) return 1;
          if (!aHasPattern && bHasPattern) return -1;
          return 0;
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
        selected: true,
      }));
      filterTableData.set(originalUpdatedData);
    } else {
      selectedCategoryFilter = category;

      filteredByCategory = $initData.filter((sessionData) => {
        const sessionInfo = sessions.find(
          (s) => s.session_id === sessionData.sessionId
        );
        return sessionInfo && sessionInfo.prompt_code === category;
      });

      const categoryTableRows = tableData.filter(
        (row) => row.prompt_code === category
      );
      filterTableData.set(
        categoryTableRows.map((row) => ({
          ...row,
          selected: true,
        }))
      );

      categoryTableRows.forEach((row) => {
        fetchInitData(row.session_id, false);
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

  function hasPattern(sessionId) {
    if (!$searchPatternSet || $searchPatternSet.length === 0) return false;

    return $searchPatternSet.some((pattern) => {
      if (!pattern.pattern || pattern.pattern.length === 0) return false;
      return pattern.pattern.some((session) => session.sessionId === sessionId);
    });
  }

  async function handleContainerClick(event) {
    const sessionId = event.detail.sessionId;
    loadedMap = {
      ...loadedMap,
      [sessionId]: false,
    };
    showMulti = true;
    try {
      await fetchData(sessionId, false);
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
    if (!showPatternSearch) {
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
    const isSourceCheckRequired =
      isExactSearchSource && checks.source && checks.source[1];
    const isTrendCheckRequired =
      isExactSearchTrend && checks.trend && checks.trend[1] && minCount > 1;
    const isProgressCheckRequired =
      isExactSearchProgress && checks.progress && checks.progress[1];
    const isTimeCheckRequired =
      isExactSearchTime && checks.time && checks.time[1];

    for (let i = 1; i <= data.length - minCount; i++) {
      const window = data.slice(i, i + minCount);
      if (checks.progress && checks.progress[0]) {
        const [min, max] = checks.progress[1];
        const deltaTarget = max - min;
        const relax = deltaTarget * 0.1;
        const start = window[0].start_progress * 100;
        const end = window[window.length - 1].end_progress * 100;
        const delta = end - start;
        const relaxedStartMin = min - relax;
        const relaxedStartMax = min + relax;
        const relaxedEndMin = max - relax;
        const relaxedEndMax = max + relax;
        const relaxedDeltaMin = deltaTarget - relax;
        const relaxedDeltaMax = deltaTarget + relax;
        if (isProgressCheckRequired) {
          if (
            start < relaxedStartMin ||
            start > relaxedStartMax ||
            end < relaxedEndMin ||
            end > relaxedEndMax ||
            delta < relaxedDeltaMin ||
            delta > relaxedDeltaMax
          ) {
            continue;
          }
        } else {
          if (delta < relaxedDeltaMin || delta > relaxedDeltaMax) continue;
        }
      }

      if (checks.time && checks.time[0]) {
        const [minTime, maxTime] = checks.time[1];
        const deltaTarget = maxTime - minTime;
        const relax = deltaTarget * 0.1;
        const startTime = window[0].start_time;
        const endTime = window[window.length - 1].end_time;
        const deltaTime = endTime - startTime;
        const relaxedStartMin = minTime - relax;
        const relaxedStartMax = minTime + relax;
        const relaxedEndMin = maxTime - relax;
        const relaxedEndMax = maxTime + relax;
        const relaxedDeltaMin = deltaTarget - relax;
        const relaxedDeltaMax = deltaTarget + relax;
        if (isTimeCheckRequired) {
          if (
            startTime < relaxedStartMin ||
            startTime > relaxedStartMax ||
            endTime < relaxedEndMin ||
            endTime > relaxedEndMax ||
            deltaTime < relaxedDeltaMin ||
            deltaTime > relaxedDeltaMax
          ) {
            continue;
          }
        } else {
          if (deltaTime < relaxedDeltaMin || deltaTime > relaxedDeltaMax)
            continue;
        }
      }

      if (isSourceCheckRequired) {
        const expectedSources = checks.source[1];
        if (expectedSources.length !== minCount) continue;

        const actualSources = window.map((item) => item.source);
        if (!expectedSources.every((src, idx) => src === actualSources[idx]))
          continue;
      }

      if (checks.semantic && checks.semantic[0]) {
        const [minScore, maxScore] = checks.semantic[1];
        const relax = (maxScore - minScore) * 0.1;
        const relaxedMin = minScore - relax;
        const relaxedMax = maxScore + relax;
        const allScores = window.map((item) => item.residual_vector_norm);
        const isScoreValid = allScores.every(
          (score) => score >= relaxedMin && score <= relaxedMax
        );
        if (!isScoreValid) continue;
      }

      if (isTrendCheckRequired) {
        const values = window.map((item) => item.residual_vector_norm);
        if (!matchesTrend(values, checks.trend[1])) continue;
      }
      segments.push(window);
    }
    return segments;
  }

  function buildVectorForCurrentSegment(currentResults, checks) {
    const currentVector = {};
    if (checks.source[0]) currentVector.s = [];
    if (checks.time[0]) currentVector.t = []; // n min
    if (checks.progress[0]) currentVector.p = []; // n
    if (checks.trend[0]) currentVector.tr = [];
    if (checks.semantic[0]) currentVector.sem = [];
    for (let i = 0; i < currentResults.length; i++) {
      const currentItem = currentResults[i];
      if (checks.source[0]) {
        currentVector.s.push(checks.source[1][i] === "user" ? 1 : 0);
      }

      if (checks.time[0]) {
        currentVector.t.push(
          currentItem.endTime * 60 - currentItem.startTime * 60
        );
      }

      if (checks.progress[0]) {
        currentVector.p.push(
          currentItem.endProgress - currentItem.startProgress
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
    if (checks.time[0]) vector.t = []; // n s
    if (checks.progress[0]) vector.p = []; // 0.n
    if (checks.trend[0]) vector.tr = [];
    if (checks.semantic[0]) vector.sem = [];

    for (let i = 0; i < segment.length; i++) {
      const item = segment[i];

      if (checks.source[0]) {
        const source = item.source?.toLowerCase();
        vector.s.push(source === "user" ? 1 : 0); // user is 1, api is 0
      }
      if (checks.time[0]) {
        const tStart = item.start_time;
        const tEnd = item.end_time;
        vector.t.push(tEnd - tStart);
      }
      if (checks.progress[0]) {
        const y1 = item.start_progress * 100;
        const y2 = item.end_progress * 100;
        vector.p.push(y2 - y1);
      }
      if (checks.semantic[0]) {
        vector.sem.push(item.residual_vector_norm);
      }
    }
    if (checks.trend[0]) {
      const values = segment.map((d) => d.residual_vector_norm);
      vector.tr = getTrendPattern(values);
    }
    return vector;
  }

  async function searchPattern(sessionId) {
    isSearch = 1; // 0: not searching, 1: searching, 2: search done
    const sessionData = selectedPatterns[sessionId];
    const count = sessionData.count;
    searchDetail = {
      sessionId,
      data: sessionData.data,
      dataRange: sessionData.dataRange,
      count,
      wholeData: sessionData.wholeData,
      range: sessionData.range,
      flag: {
        isProgressChecked,
        isTimeChecked,
        isSourceChecked,
        isValueRangeChecked,
        isValueTrendChecked,
        isExactSearchSource,
        isExactSearchTrend,
        isExactSearchProgress,
        isExactSearchTime,
      },
    };
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
      const fileListResponse = await fetch(
        `${base}/dataset/${selectedDataset}/session_name.json`
      );
      const fileList = await fileListResponse.json();
      console.log("File list length:", fileList.length);

      for (const fileName of fileList) {
        // const fileId = fileName.split(".")[0].replace(/_similarity$/, "");
        // if (fileId === sessionId) {
        //   continue;
        // }
        const dataResponse = await fetch(
          `${base}/dataset/${selectedDataset}/similarity_results/${fileName}`
        );
        const data = await dataResponse.json();
        if (Array.isArray(data.chartData)) {
          data.chartData = data.chartData.map(
            ({ currentText, ...rest }) => rest
          );
        }
        delete data.paragraphColor;
        delete data.textElements;

        const segments = findSegments(data, checks, count);
        const extractedFileName = fileName
          .split(".")[0]
          .replace(/_similarity$/, "");

        const taggedSegments = segments.map((segment, index) =>
          segment.map((item) => ({
            ...item,
            id: extractedFileName,
            segmentId: `${extractedFileName}_${index}`,
          }))
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
        checks
      );
      patternData = results;
      const finalScore = await calculateRankAuto(patternVectors, currentVector);
      const idToData = Object.fromEntries(
        patternData.map((d) => [d[0].segmentId, d])
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
      const d = arr1[i] - arr2[i];
      sum += d * d;
    }
    return sum;
  }

  let isWeights = false;
  function setWeight() {
    isWeights = !isWeights;
  }
  let weights = writable({
    s: 1.5, // user 1, api 0
    t: 0.2, // 1s
    p: 1, // 1% -> 0.01
    tr: 2.5, // up 1, down -1
    sem: 2, // 1% -> 0.01
  });
  let initialWeights = get(weights);

  $: if (xScaleBarChartFactor || xScaleLineChartFactor) {
    // console.log("yScaleFactor:", yScaleFactor);
    // console.log("xScaleBarChartFactor:", xScaleBarChartFactor);
    // console.log("xScaleLineChartFactor:", xScaleLineChartFactor);

    initialWeights.p = Math.round((yScaleFactor + Number.EPSILON) * 100) / 100;
    initialWeights.sem =
      Math.round((xScaleBarChartFactor + Number.EPSILON) * 100) / 100;
    initialWeights.t =
      Math.round((xScaleLineChartFactor + Number.EPSILON) * 1e2) / 1e2;

    // console.log("Initial Weights:", initialWeights);
  }

  $: if (zoomTransforms && $clickSession?.sessionId && initialWeights) {
    const scale = zoomTransforms[$clickSession.sessionId]?.k ?? 1;

    weights.update((w) => {
      const updated = {
        ...w,
        t: Math.round((initialWeights.t * scale + Number.EPSILON) * 1e2) / 1e2,
        p: Math.round((initialWeights.p * scale + Number.EPSILON) * 100) / 100,
        sem: initialWeights.sem,
      };
      return updated;
    });
  }

  export async function calculateRankAuto(
    patternVectors,
    currentVector,
    threadCount = 4,
    threshold = 100
  ) {
    if (patternVectors.length <= threshold) {
      return calculateRank(patternVectors, currentVector);
    } else {
      return calculateRankWorkers(patternVectors, currentVector, threadCount);
    }
  }

  function calculateRank(patternVectors, currentVector) {
    let finalScore = [];
    const weightValues = get(weights);
    for (const item of patternVectors) {
      let score = 0;
      for (const key in item) {
        if (key != "id" && key != "segmentId") {
          let weight = weightValues[key] ?? 1;
          let arr = item[key];
          score += weight * l2(arr, currentVector[key]);
        }
      }
      finalScore.push([item.segmentId, score]);
    }
    finalScore.sort((a, b) => a[1] - b[1]);
    return finalScore;
  }

  async function calculateRankWorkers(
    patternVectors,
    currentVector,
    threadCount = 4
  ) {
    const chunkSize = Math.ceil(patternVectors.length / threadCount);
    let completed = 0;
    const weightValues = get(weights);
    const allResults = [];

    return new Promise((resolve, reject) => {
      for (let i = 0; i < threadCount; i++) {
        const chunk = patternVectors.slice(i * chunkSize, (i + 1) * chunkSize);
        if (chunk.length === 0) {
          completed++;
          continue;
        }
        const worker = new RankWorker();
        worker.postMessage({
          patternVectors: chunk,
          currentVector,
          weights: weightValues,
        });
        worker.onmessage = (e) => {
          allResults.push(...e.data);
          completed++;
          worker.terminate();
          if (completed === threadCount) {
            allResults.sort((a, b) => a[1] - b[1]);
            resolve(allResults);
          }
        };
        worker.onerror = (err) => {
          reject(err);
        };
      }
    });
  }

  async function patternDataLoad(results) {
    const ids = results.map((group) => group[0]?.id).filter(Boolean);
    const fetchPromises = ids.map((id) => fetchDataSummary(id));
    await Promise.all(fetchPromises);

    const sessionDataMap = get(storeSessionSummaryData);
    patternDataList.set(
      results
        .map((group) => {
          const id = group[0]?.id;
          const sessionData = sessionDataMap.get(id);
          if (!sessionData) return null;
          const newSessionData = { ...sessionData };
          delete newSessionData.paragraphColor;
          delete newSessionData.summaryData;
          delete newSessionData.textElements;

          if (Array.isArray(newSessionData.chartData)) {
            newSessionData.chartData = newSessionData.chartData.map((item) => {
              const newItem = { ...item };
              delete newItem.currentText;
              delete newItem.currentColor;
              return newItem;
            });
          }
          return {
            ...newSessionData,
            segments: group,
            segmentId: group[0]?.segmentId,
          };
        })
        .filter(Boolean)
    );
    isSearch = 2; // reset search state; 0: not searching, 1: searching, 2: search done
  }

  function closePatternSearch() {
    showPatternSearch = false;
    selectionMode = false;
  }

  function handleSelectionChanged(event) {
    showResultCount.set(5);

    // console.log("handleSelectionChanged called with:", event.detail);
    // console.log("sharedSelection:", sharedSelection);

    if (sharedSelection && sharedSelection.selectionSource === "lineChart_x") {
      console.log("Setting lineChart_x options");
      isProgressChecked = true;
      isTimeChecked = true;
      isSourceChecked = false;
      isSemanticChecked = false;
      isValueRangeChecked = false;
      isValueTrendChecked = false;
      isExactSearchTime = true;
      isExactSearchProgress = true;
      isExactSearchSource = false;
      isExactSearchTrend = false;
      console.log(
        "After setting lineChart_x - isProgressChecked:",
        isProgressChecked,
        "isTimeChecked:",
        isTimeChecked,
        "isSourceChecked:",
        isSourceChecked
      );
    } else if (
      sharedSelection &&
      sharedSelection.selectionSource === "lineChart_y"
    ) {
      console.log("Setting lineChart_y options");
      isProgressChecked = true;
      isTimeChecked = true;
      isSourceChecked = true;
      isSemanticChecked = true;
      isValueRangeChecked = true;
      isValueTrendChecked = true;
      isExactSearchProgress = true;
      isExactSearchTime = true;
      isExactSearchSource = true;
      isExactSearchTrend = true;
    } else if (
      sharedSelection &&
      sharedSelection.selectionSource === "barChart_y"
    ) {
      console.log("Setting barChart_y options");
      isProgressChecked = true;
      isTimeChecked = false;
      isSourceChecked = true;
      isSemanticChecked = true;
      isValueRangeChecked = true;
      isValueTrendChecked = true;
      isExactSearchProgress = true;
      isExactSearchSource = true;
      isExactSearchTrend = true;
    } else {
      console.log("Setting default options");
      isProgressChecked = false;
      isTimeChecked = false;
      isSourceChecked = true;
      isSemanticChecked = true;
      isValueRangeChecked = true;
      isValueTrendChecked = true;
    }

    if (sharedSelection && sharedSelection.selectionSource === "barChart_y") {
      isExactSearchSource = true;
      isExactSearchTrend = true;
    } else {
      isExactSearchSource = false;
      isExactSearchTrend = false;
    }
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
    timeRange = [dataRange.timeRange, dataRange.timeRange.max];
    sourceRange = sources;
    semanticRange = [dataRange.scRange.min, dataRange.scRange.max];
    semanticData = dataRange.sc.sc;
    semanticTrend = getTrendPattern(semanticData);
    currentResults = data;
    lastSession = $clickSession;

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

  const fetchLengthData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/length.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  const fetchOverallSemScoreSummaryData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/overall_sem_score_summary.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  const fetchOverallSemScoreData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/overall_sem_score.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  const fetchLengthSummaryData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/length_summary.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  const fetchPercentageSummaryData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/percentage_summary.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  const fetchPercentageData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/percentage.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  const fetchScoreSummaryData = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/score_summary.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch summary data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  async function fetchInitData(sessionId, isDelete) {
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
        const existingIndex = sessions.findIndex(
          (s) => s.sessionId === sessionId
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
  }

  const fetchSessions = async () => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/fine.json`
      );
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
          "cat",
        ]);

        $filterTableData = tableData.filter((session) =>
          $selectedTags.includes(session.prompt_code)
        );

        filterOptions = Array.from(
          new Set(tableData.map((row) => row.prompt_code))
        );
      }
    } catch (error) {
      console.error("Error when fetching sessions:", error);
    }
  };

  const fetchDataSummary = async (sessionFile) => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/coauthor-json/${sessionFile}.jsonl`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }

      const data = await response.json();
      const time0 = new Date(data.init_time);
      const time100 = new Date(data.end_time);
      const currentTime = (time100.getTime() - time0.getTime()) / (1000 * 60); // in minutes
      const chartData = handleEventsSummary(data);
      const similarityData = await fetchSimilarityData(sessionFile);
      let updatedSession = {
        sessionId: sessionFile,
        time0,
        time100: currentTime,
        currentTime,
        chartData,
        similarityData: similarityData || undefined,
        totalSimilarityData: similarityData || undefined,
      };

      storeSessionSummaryData.update((sessionMap) => {
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
      console.error("Error when reading the data file (summary only):", error);
    }
  };

  const fetchData = async (sessionFile, isDelete) => {
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
        `${base}/dataset/${selectedDataset}/coauthor-json/${sessionFile}.jsonl`
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
  };

  const fetchSimilarityData = async (sessionFile) => {
    try {
      const response = await fetch(
        `${base}/dataset/${selectedDataset}/similarity_results/${sessionFile}_similarity.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }

      const data = (await response.json()) || [];
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
      return null;
    }
  };

  let scoreSummary = [];
  let percentageData = [];
  let percentageSummaryData = [];
  let lengthData = [];
  let lengthSummaryData = [];
  let overallSemScoreData = [];
  let overallSemScoreSummaryData = [];
  let isLoadOverallData = false;
  onMount(async () => {
    document.title = "Ink-Pulse";
    const res = await fetch(`${base}/dataset_name.json`);
    datasets = await res.json();
    const params = new URLSearchParams(window.location.search);
    const datasetParam = params.get("dataset");
    if (datasetParam && datasets.includes(datasetParam)) {
      selectedDataset = datasetParam;
    }
    scoreSummary = await fetchScoreSummaryData();
    percentageData = await fetchPercentageData();
    percentageSummaryData = await fetchPercentageSummaryData();
    lengthData = await fetchLengthData();
    lengthSummaryData = await fetchLengthSummaryData();
    overallSemScoreData = await fetchOverallSemScoreData();
    overallSemScoreSummaryData = await fetchOverallSemScoreSummaryData();
    if (isLoadOverallData == false) {
      const itemToSave = {
        id: `pattern_0`,
        name: "Overall",
        pattern: [],
        metadata: {},
        scoreSummary,
        percentageSummaryData,
        lengthSummaryData,
        overallSemScoreData,
        overallSemScoreSummaryData,
      };
      searchPatternSet.update((current) => {
        const index = current.findIndex((p) => p.id === "pattern_0");
        if (index >= 0) {
          const copy = [...current];
          copy[index] = itemToSave;
          return copy;
        } else {
          return [...current, itemToSave];
        }
      });
      isLoadOverallData = true;
    }

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
      Math.min(newTranslateY, maxTranslateY)
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

  const handleEventsSummary = (data) => {
    const chartData = [];
    let firstTime = null;
    let index = 0;
    const totalTextLength = data.text[0].slice(0, -1).length;
    let currentCharCount = data.init_text.join("").length;

    data.info.forEach((event) => {
      const { name, event_time, eventSource, text = "", count = 0 } = event;

      const textColor = eventSource === "user" ? "#66C2A5" : "#FC8D62";
      const eventTime = new Date(event_time);
      if (!firstTime) firstTime = eventTime;
      const relativeTime = (eventTime.getTime() - firstTime.getTime()) / 60000;

      if (name === "text-insert") {
        const insertChars = [...text];
        insertChars.forEach(() => {
          currentCharCount++;
          const percentage = (currentCharCount / totalTextLength) * 100;
          chartData.push({
            time: relativeTime,
            percentage,
            eventSource,
            color: textColor,
            isSuggestionOpen: false,
            index: index++,
          });
        });
      } else if (name === "text-delete") {
        const deleteCount = text.length || count;
        currentCharCount -= deleteCount;
        const percentage = (currentCharCount / totalTextLength) * 100;
        chartData.push({
          time: relativeTime,
          percentage,
          eventSource,
          color: textColor,
          isSuggestionOpen: false,
          index: index++,
        });
      } else {
        const percentage = (currentCharCount / totalTextLength) * 100;
        chartData.push({
          time: relativeTime,
          percentage,
          eventSource,
          color: textColor,
          isSuggestionOpen: name === "suggestion-open",
          index: index++,
        });
      }
    });

    return chartData;
  };

  const handleEvents = (data, _) => {
    const initText = data.init_text.join("");
    let currentCharArray = initText.split("");
    let currentColor = new Array(currentCharArray.length).fill("#FC8D62");
    let chartData = [];
    let paragraphColor = [];
    let firstTime = null;
    let indexOfAct = 0;
    const wholeText = data.text[0].slice(0, -1);
    const totalTextLength = wholeText.length;
    let totalInsertions = 0;
    let totalDeletions = 0;
    let totalSuggestions = 0;
    let totalProcessedCharacters = totalTextLength;
    const sortedEvents = [...data.info].sort((a, b) => a.id - b.id);
    let combinedText = [...initText].map((ch) => ({
      text: ch,
      textColor: "#FC8D62",
    }));
    sortedEvents.forEach((event) => {
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

      const relativeTime = (eventTime.getTime() - firstTime.getTime()) / 60000;

      if (name === "text-insert") {
        const insertChars = [...text];
        const insertPos = Math.min(pos, currentCharArray.length);

        insertChars.forEach((ch, i) => {
          currentCharArray.splice(insertPos + i, 0, ch);
          currentColor.splice(insertPos + i, 0, textColor);
          combinedText.splice(insertPos + i, 0, { text: ch, textColor });

          const percentage = (currentCharArray.length / totalTextLength) * 100;

          chartData.push({
            time: relativeTime,
            percentage,
            eventSource,
            color: textColor,
            currentText: currentCharArray.join(""),
            currentColor: [...currentColor],
            opacity: 1,
            isSuggestionOpen: name === "suggestion-open",
            index: indexOfAct++,
          });

          totalInsertions++;
        });
      }
      if (name === "text-delete") {
        const deleteCount = text.length || count;
        currentCharArray.splice(pos, deleteCount);
        currentColor.splice(pos, deleteCount);
        combinedText.splice(pos, deleteCount);
        totalDeletions++;
        totalProcessedCharacters -= deleteCount;
      }

      if (name === "suggestion-open") {
        totalSuggestions++;
      }

      const percentage = (currentCharArray.length / totalTextLength) * 100;

      chartData.push({
        time: relativeTime,
        percentage,
        eventSource,
        color: textColor,
        currentText: currentCharArray.join(""),
        currentColor: [...currentColor],
        opacity: 1,
        isSuggestionOpen: name === "suggestion-open",
        index: indexOfAct++,
      });
    });

    paragraphTime = adjustTime(currentCharArray.join(""), chartData);
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
      if (currentSession.sessionId !== sessionId) return currentSession;
      const textElements = d.currentText.split("").map((char, index) => ({
        text: char,
        textColor: d.currentColor?.[index] ?? "#000",
      }));
      const chartData = currentSession.chartData.map((point) => ({
        ...point,
        opacity: point.index > d.index ? 0.01 : 1,
      }));
      const similarityData = currentSession.totalSimilarityData;
      const endIndex = similarityData.findIndex(
        (item) => d.percentage < item.end_progress * 100
      );
      const selectedData =
        endIndex === -1 ? similarityData : similarityData.slice(0, endIndex);

      return {
        ...currentSession,
        textElements,
        currentTime: d.time,
        chartData,
        similarityData: selectedData,
      };
    });
  }

  function handlePatternClick(event) {
    const { pattern } = event.detail;

    selectedPatternForDetail = pattern;
    activePatternId = pattern.id;
    currentView = "pattern-detail";
  }

  function handlePatternContextMenu(event) {
    const { pattern } = event.detail;
    console.log("Right clicked on pattern from table:", pattern.name);
  }

  $: showPatternColumn = $searchPatternSet && $searchPatternSet.length > 0;
  let maxVisible = 8;
  function handleShowMorePatterns() {
    maxVisible = $searchPatternSet.length;
    console.log(`Total patterns: ${$searchPatternSet.length}`);
  }

  function handleBackFromDetail() {
    currentView = "landing";
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
    patternToEdit = pattern;
    showEditDialog = true;
  }

  function handleEditSave(event) {
    const { pattern, newName } = event.detail;
    searchPatternSet.update((patterns) =>
      patterns.map((p) => (p.id === pattern.id ? { ...p, name: newName } : p))
    );
    if (
      selectedPatternForDetail &&
      selectedPatternForDetail.id === pattern.id
    ) {
      selectedPatternForDetail = {
        ...selectedPatternForDetail,
        name: newName,
      };
    }
    showEditDialog = false;
    patternToEdit = null;
  }

  function handleEditCancel() {
    showEditDialog = false;
    patternToEdit = null;
  }

  function handleDeletePattern(event) {
    const { pattern } = event.detail;
    patternToDelete = pattern;
    showDeleteConfirm = true;
  }

  function confirmDeletePattern() {
    if (patternToDelete) {
      searchPatternSet.update((patterns) =>
        patterns.filter((p) => p.id !== patternToDelete.id)
      );
      if (currentView === "pattern-detail") {
        handleBackFromDetail();
      }
      patternToDelete = null;
    }
    showDeleteConfirm = false;
  }

  function cancelDeletePattern() {
    patternToDelete = null;
    showDeleteConfirm = false;
  }

  function handlePatternDetailRowClick(event) {
    const { sessionData } = event.detail;
    handleContainerClick({ detail: { sessionId: sessionData.sessionId } });
    handleBackFromDetail();
  }

  function handleDatasetChange(event) {
    const value = event.target.value;

    // Handle help option
    if (value === "__help__") {
      // Reset to current dataset
      event.target.value = selectedDataset;
      // Open help dialog or navigate to documentation
      openDatasetHelp();
      return;
    }

    selectedDataset = value;
    window.location.href = `${window.location.pathname}?dataset=${selectedDataset}`;
  }

  function openDatasetHelp() {
    // Open GitHub README section about dataset import
    window.open(
      "https://github.com/Visual-Intelligence-UMN/Ink-Pulse/blob/main/README.md#how-to-import-your-own-dataset",
      "_blank"
    );
  }

  // --- Virtual table configuration ---
  export let vtRowHeight = 65; // height of each row in px
  export let vtHeaderHeight = 120; // header height in px
  export let vtOverscan = 2; // number of extra rows rendered above/below

  // --- Data for the table (replace with your dataset) ---
  export let vtData = [];

  // --- Internal state ---
  let vtScrollY = 0; // current vertical scroll offset of window
  let vtViewportH = 0; // current viewport height

  // --- Derived values (recomputed automatically when deps change) ---
  $: if (
    $initData ||
    sortColumn ||
    sortDirection ||
    !selectedCategoryFilter ||
    !selectedPatternForDetail
  ) {
    const colgrp = getColumnGroups();
    if (!(colgrp.length === 0 || colgrp[0].length === 0)) {
      vtData = colgrp;
    }
  }
  $: vtTotalRows = Math.max(...vtData.map((group) => group.length)); // total number of rows
  $: vtRowsInView = Math.max(
    1,
    Math.ceil((vtViewportH - vtHeaderHeight) / vtRowHeight)
  );
  $: vtVisibleCnt = vtRowsInView + vtOverscan * 2; // rows to render including overscan
  $: vtStartIndex = Math.max(
    0,
    Math.floor(vtScrollY / vtRowHeight) - vtOverscan
  );
  $: vtEndIndex = Math.min(vtTotalRows, vtStartIndex + vtVisibleCnt); // slice end index
  $: vtVisibleRows = vtData.map((col) => col.slice(vtStartIndex, vtEndIndex)); // actual rows rendered
  $: vtOverlayY =
    vtHeaderHeight -
    (vtScrollY < vtRowHeight * vtOverscan
      ? vtScrollY
      : (vtScrollY % vtRowHeight) + vtRowHeight * vtOverscan); // overlay vertical offset

  // --- Lifecycle hooks ---
  onMount(() => {
    function vtOnScroll() {
      vtScrollY = window.scrollY || 0;
    }
    function vtOnResize() {
      vtViewportH = window.innerHeight || 0;
    }

    vtOnResize();
    vtOnScroll();

    // setInterval(() => {
    //   console.log("displaySessions:", getDisplaySessions());
    //   console.log("columnGroups:", getColumnGroups());
    //   console.log("vtData:", vtData);
    //   console.log("filteredByCategory:", filteredByCategory);
    //   console.log("-----------------------");
    //   console.log("-----------------------");
    // }, 2000);

    window.addEventListener("scroll", vtOnScroll, { passive: true });
    window.addEventListener("resize", vtOnResize);

    onDestroy(() => {
      window.removeEventListener("scroll", vtOnScroll);
      window.removeEventListener("resize", vtOnResize);
    });
  });
</script>

<div class="App">
  <header class="App-header">
    <nav>
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo" style="zoom: 150%;">
            <img
              src="{base}/favicon.png"
              alt="InkPulse Logo"
              class="ink-icon"
            />
            <span class="brand-name">InkPulse</span>
          </div>
        </div>
      </div>
      <div class="chart-explanation" style="font-size: 13px; align-items: center; display: flex;">
        &nbsp;&nbsp;&nbsp;&nbsp;
        <span class="triangle-text">▼</span> User open the AI suggestion &nbsp;
        <span class="user-line">●</span> User written &nbsp;
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
      <div style="flex: 1;"></div>
      <div style="display: flex; gap: 0.5em; align-items: center;">
        <div style="margin-right: 30px;">
          <label for="dataset-select" style="font-size: 14px;">Dataset:</label>
          <select
            id="dataset-select"
            bind:value={selectedDataset}
            on:change={handleDatasetChange}
            style="width: min-content;"
          >
            {#each datasets as dataset}
              <option value={dataset}>{dataset}</option>
            {/each}
            <option disabled>────────────</option>
            <option value="__help__">How to Add Your Dataset</option>
          </select>
        </div>
        <button
          class="pattern-search-button"
          class:active={showPatternSearch}
          on:click={togglePatternSearch}
          aria-label="Pattern Search"
        >
          <span class="search-icon">🔍</span>
          {showPatternSearch ? "Exit Search" : "Pattern Search"}
        </button>
        <a
          on:click={open2close}
          href=" "
          aria-label="Instruction"
          class="material-symbols--info-outline-rounded"
        ></a>
      </div>
    </nav>
    <div class:hidden={!showPatternSearch}>
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

          <div class="patterns-header">
            <h4 class="patterns-title">Manage Patterns</h4>
            <div
              class="patterns-actions"
              role="toolbar"
              aria-label="Pattern actions"
            >
              <button
                class="search-pattern-button"
                class:loading={isImporting}
                on:click={async () => {
                  isImporting = true;
                  try {
                    await triggerImport();
                  } finally {
                    isImporting = false;
                  }
                }}
                aria-label="Upload patterns"
                title="Upload patterns"
                disabled={isImporting}
              >
                {#if isImporting}
                  <span class="loading-spinner"></span>
                  Loading...
                {:else}
                  Upload
                {/if}
              </button>

              {#if $searchPatternSet && $searchPatternSet.length > 1}
                <button
                  class="search-pattern-button"
                  on:click={exportDB}
                  aria-label="Download patterns"
                  title="Download saved patterns"
                >
                  Download
                </button>
              {/if}
            </div>
          </div>

          {#if $searchPatternSet && $searchPatternSet.length > 1}
            <div class="saved-patterns-section" style="margin-top: 20px;">
              <h4>Saved Patterns</h4>
              <div class="saved-patterns-list">
                <SavedPatternsBar
                  patterns={$searchPatternSet}
                  {activePatternId}
                  on:pattern-click={handlePatternClick}
                  on:pattern-contextmenu={handlePatternContextMenu}
                  on:show-more-patterns={handleShowMorePatterns}
                  {maxVisible}
                />
              </div>
            </div>
          {:else}
            <div class="saved-patterns-section">
              <h4>Saved Patterns</h4>
              <div class="no-patterns-message">
                <p>
                  No saved patterns yet. Start by selecting a portion in the
                  chart and saving your first pattern!
                </p>
              </div>
            </div>
          {/if}

          {#if Object.keys(selectedPatterns).length > 0}
            <div class="pattern-results-summary" style="margin-top: 20px;">
              <h4>Selection Results</h4>
              {#each Object.entries(selectedPatterns) as [sessionId, pattern]}
                <div class="pattern-item">
                  <div class="pattern-header">
                    <h5>Session: {sessionId.slice(0, 4)}</h5>
                    <div class="pattern-buttons">
                      <button class="weight-button" on:click={setWeight}
                        >Weight</button
                      >
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
                        2
                      )} - {pattern.dataRange.scRange.max.toFixed(2)}
                    </div>
                    <div>
                      Progress Range: {pattern.dataRange.progressRange.min.toFixed(
                        2
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
                        style="font-size: 13px;"
                      >
                        <input
                          type="checkbox"
                          bind:checked={isProgressChecked}
                        />
                        Writing Progress
                        <label
                          class="switch"
                          style="transform: translateY(4px);"
                          bind:this={exactProgressButton}
                        >
                          <input
                            type="checkbox"
                            bind:checked={isExactSearchProgress}
                            disabled={!isProgressChecked}
                          />
                          <span class="slider">
                            <span class="switch-text">
                              {isExactSearchProgress ? "Exact" : "Proximity"}
                            </span>
                          </span>
                        </label>
                      </div>
                      <div
                        class:dimmed={!isTimeChecked}
                        style="font-size: 13px;"
                      >
                        <input type="checkbox" bind:checked={isTimeChecked} />
                        Time
                        <label
                          class="switch"
                          style="transform: translateY(4px);"
                          bind:this={exactTimeButton}
                        >
                          <input
                            type="checkbox"
                            bind:checked={isExactSearchTime}
                            disabled={!isTimeChecked}
                          />
                          <span class="slider">
                            <span class="switch-text">
                              {isExactSearchTime ? "Exact" : "Proximity"}
                            </span>
                          </span>
                        </label>
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
                          <span class="slider">
                            <span class="switch-text">
                              {isExactSearchSource ? "Exact" : "Proximity"}
                            </span>
                          </span>
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
                              <span class="slider">
                                <span class="switch-text">
                                  {isExactSearchTrend ? "Exact" : "Proximity"}
                                </span>
                              </span>
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
                              on:click={() =>
                                removepattern(sessionData.segmentId)}>×</button
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
                          >Save NOW Pattern
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
          {:else}
            <div class="no-patterns-selected">
              <p>No patterns selected.</p>
            </div>
          {/if}
        </div>
      </div>
    </div>
    {#if isSave}
      <SavePanel
        name={nameInput}
        color={colorInput}
        on:save={handleSave}
        on:close={handleClose}
      />
    {/if}
    {#if isWeights}
      <WeightPanel
        {weights}
        on:save={handleWeightsSave}
        on:close={handleWeightsClose}
      />
    {/if}
    <div
      class="container"
      style="margin-bottom: {showMulti ? '30px' : '70px'}; width: {showMulti
        ? ''
        : '100%'};"
    >
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
              Discover insights into <b>human-AI collaboration</b> and have fun!
            </p>
            <button class="start-button" on:click={open2close}
              >Start Exploring</button
            >
          </div>
        </div>
      {/if}

      {#if currentView === "pattern-detail" && selectedPatternForDetail}
        <div style="margin-top: 70px;">
          <PatternDetailView
            pattern={selectedPatternForDetail}
            searchPatternSet={$searchPatternSet}
            {sessions}
            {chartRefs}
            {percentageData}
            {lengthData}
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
                        <th
                          class="sortable-header"
                          on:click={() => handleSort("topic")}
                          style="min-width: 70px;"
                        >
                          <span>Topic</span>
                          <span class="sort-icon">{getSortIcon("topic")}</span>
                        </th>
                        <th
                          class="sortable-header"
                          on:click={() => handleSort("score")}
                          style="min-width: 90px;"
                        >
                          <span>Score</span>
                          <span class="sort-icon">{getSortIcon("score")}</span>
                        </th>
                        {#if showPatternColumn}
                          <th
                            class="sortable-header"
                            on:click={() => handleSort("pattern")}
                            style="min-width: 100px;"
                          >
                            <span>Pattern</span>
                            <span class="sort-icon"
                              >{getSortIcon("pattern")}</span
                            >
                          </th>
                        {/if}
                        <th>Activity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each selectedCategoryFilter ? filteredByCategory : filteredSessions as sessionData}
                        <tr
                          class="session-row"
                          on:click={() => handleRowClick(sessionData)}
                        >
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
                          <th
                            class="sortable-header"
                            on:click={() => handleSort("topic")}
                            style="min-width: 70px;"
                          >
                            <span>Topic</span>
                            <span class="sort-icon">{getSortIcon("topic")}</span
                            >
                          </th>
                          <th
                            class="sortable-header"
                            on:click={() => handleSort("score")}
                            style="min-width: 90px;"
                          >
                            <span>Score</span>
                            <span class="sort-icon">{getSortIcon("score")}</span
                            >
                          </th>
                          {#if showPatternColumn}
                            <th
                              class="sortable-header"
                              on:click={() => handleSort("pattern")}
                              style="min-width: 100px;"
                            >
                              <span>Pattern</span>
                              <span class="sort-icon"
                                >{getSortIcon("pattern")}</span
                              >
                            </th>
                          {/if}
                          <th>Activity</th>
                          {#if colIndex < 2}
                            <th class="spacer" style="width: 8vw;"></th>
                          {/if}
                        {/each}
                      </tr>
                    </thead>
                    <tbody
                      aria-hidden="true"
                      style="
                        visibility:hidden;
                        pointer-events:none;
                      "
                    >
                      {#if vtVisibleRows && vtVisibleRows.length}
                        <tr
                          class="unified-session-row"
                          style="height:0; padding:0; border:0;"
                        >
                          {#each vtVisibleRows as group, colIndex}
                            <SessionCell
                              sessionData={group[0]}
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
                              noRightBorder={true}
                            />
                          {/each}
                        </tr>
                      {/if}
                    </tbody>
                  </table>

                  <!-- Spacer to push rows below sticky header -->
                  <div
                    style="
                      height:{vtHeaderHeight}px;
                      margin-top:-1px;
                    "
                  ></div>

                  <!-- Tall pad to create correct scrollbar height -->
                  <div style="height:{vtTotalRows * vtRowHeight}px;"></div>

                  <!-- Fixed overlay that actually renders only visible rows -->
                  <div
                    style="
                      position:fixed;
                      left:0;
                      right:0;
                      top:0;
                      z-index:2;
                      pointer-events:auto;
                      transform: translateY({vtOverlayY}px);
                      --vt-row-h:{vtRowHeight}px;

                      display: flex;
                      justify-content: center;
                    "
                  >
                    <table class="unified-sessions-table">
                      <thead
                        aria-hidden="true"
                        style="visibility:hidden; height:0; overflow:hidden; pointer-events:none;"
                      >
                        <tr>
                          {#each Array(3) as _, colIndex}
                            <th style="min-width:70px;"></th>
                            <th style="min-width:90px;"></th>
                            {#if showPatternColumn}
                              <th style="min-width:100px;"></th>
                            {/if}
                            <th></th>
                            {#if colIndex < 2}
                              <th class="spacer" style="width:8vw;"></th>
                            {/if}
                          {/each}
                        </tr>
                      </thead>
                      <tbody>
                        {#each Array(Math.ceil(Math.max(...vtVisibleRows.map((group) => group.length)))) as _, rowIndex (rowIndex + sortColumn + sortDirection)}
                          <tr
                            class="unified-session-row"
                            style="height: {vtRowHeight}px;"
                          >
                            {#each vtVisibleRows as group, colIndex}
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
              </div>
            {/if}
          {/if}
        </div>

        {#if showMulti}
          {#if $clickSession}
            <div style="margin-top: 70px;">
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
                            bind:zoomTransform={
                              zoomTransforms[$clickSession.sessionId]
                            }
                            {selectionMode}
                            bind:sharedSelection
                            on:selectionChanged={handleSelectionChanged}
                            on:selectionCleared={handleSelectionCleared}
                            bind:this={
                              chartRefs[$clickSession.sessionId + "-barChart"]
                            }
                            on:chartLoaded={handleChartLoaded}
                            bind:xScaleBarChartFactor
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
                            bind:zoomTransform={
                              zoomTransforms[$clickSession.sessionId]
                            }
                            {selectionMode}
                            bind:sharedSelection
                            on:selectionChanged={handleSelectionChanged}
                            on:selectionCleared={handleSelectionCleared}
                            bind:xScaleLineChartFactor
                          />
                        </div>
                      </div>
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
                        {#each $clickSession.textElements as element, _}
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
      {/if}
    </div>
  </header>
</div>

<!-- Confirm Dialog -->
<ConfirmDialog
  show={showDeleteConfirm}
  title="Delete Pattern"
  message={patternToDelete
    ? `Are you sure you want to delete pattern "${patternToDelete.name}"? This action cannot be undone.`
    : ""}
  confirmText="Delete"
  cancelText="Cancel"
  variant="danger"
  on:confirm={confirmDeletePattern}
  on:cancel={cancelDeletePattern}
/>

<!-- Edit Pattern Dialog -->
<EditPatternDialog
  show={showEditDialog}
  pattern={patternToEdit}
  on:save={handleEditSave}
  on:cancel={handleEditCancel}
/>

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
    /* width: 100%; */
    margin: 0 5px;
    display: flex;
    justify-content: center;
    padding: 0 10px;
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
    margin-top: 40px;
    box-sizing: border-box;
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

  .brand-section {
    display: flex;
    align-items: flex-start;
    margin-left: 10px;
    margin-top: -5px;
  }

  .brand-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .brand-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }

  .ink-icon {
    width: 28px;
    height: 28px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
    border-radius: 4px;
  }

  .brand-name {
    font-size: 16px;
    font-weight: 700;
    color: #2563eb;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .chart-explanation {
    font-size: 11px;
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
    padding: 0.5em 0;
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
    font-size: 14px;
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
    width: 62px;
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

  .hidden {
    display: none;
  }

  .pattern-actions {
    display: flex;
    gap: 12px;
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #e0e0e0;
  }

  .pattern-action-button {
    flex: 1;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }

  .save-button {
    background-color: #10b981;
    color: white;
  }

  .save-button:hover {
    background-color: #059669;
    transform: translateY(-1px);
  }

  .load-button {
    background-color: #3b82f6;
    color: white;
  }

  .load-button:hover {
    background-color: #2563eb;
    transform: translateY(-1px);
  }

  .no-patterns-message {
    padding: 20px;
    text-align: center;
    color: #6b7280;
    font-size: 14px;
    background-color: #f9fafb;
    border-radius: 8px;
    margin-bottom: 10px;
  }

  /* Loading state styles */
  .search-pattern-button.loading {
    opacity: 0.7;
    cursor: not-allowed;
    position: relative;
  }

  .loading-spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-right: 8px;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .search-pattern-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
</style>
