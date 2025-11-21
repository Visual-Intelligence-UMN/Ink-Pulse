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
  import { getCategoryIcon as getCategoryIconBase } from "../components/topicIcons.js";
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
    exportSinglePattern,
    triggerImport,
    loadPattern,
  } from "../components/cache.js";
  import RankWorker from "../workers/rankWorker.js?worker";
  import WeightPanel from "../components/weightPanel.svelte";
  import Papa from "papaparse";

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
    init_text: "", // Initial text
    init_time: "", // Start time
    json: [], // all operation
    text: "", // final text
    action: [], // insert, delete and suggestion-open operation
    end_time: "",
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

  // Search functionality
  let searchQuery = "";
  let searchResults = [];
  let showSearchResults = false;

  // Export functionality
  let showExportMenu = false;
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
  $: if (isValueTrendChecked) {
    isExactSearchTrend = true;
  }
  $: if (isSourceChecked) {
    isExactSearchSource = true;
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
  let showSavedMessage = false;
  async function openSavePanel() {
    isSave = false;
    await tick();
    nameInput = "";
    colorInput = "#66ccff";
    isSave = true;
  }

  function handleSave(event) {
    const { name, color } = event.detail;

    // Top-N rows we're saving from the visible results
    const allPatternData = get(patternDataList).slice(0, get(showResultCount));

    // Group rows by sessionId so we can accumulate counts per session
    const sessionsById = new Map();

    const getOrInitSession = (row) => {
      if (!sessionsById.has(row.sessionId)) {
        const sim = Array.isArray(row.similarityData) ? row.similarityData : [];
        // ✅ Only save essential fields to reduce file size
        // Keep similarityData for chart rendering, but remove large arrays like chartData
        sessionsById.set(row.sessionId, {
          sessionId: row.sessionId,
          similarityData: sim, // Keep for chart display (small: ~5KB per session)
          pattern_indices: Array(sim.length).fill(0),
          llmScore: sim?.[0]?.score ?? 0,
          // Removed: chartData (~586KB), time0, time100, segments, etc.
        });
      }
      return sessionsById.get(row.sessionId);
    };

    const findIndex = (sim, time, field) =>
      sim.findIndex((x) => x?.[field] === time);

    // For each pattern occurrence (row), mark its segments into that session's counters
    for (const row of allPatternData) {
      const session = getOrInitSession(row);
      const sim = Array.isArray(row.similarityData) ? row.similarityData : [];
      const segs = Array.isArray(row.segments) ? row.segments : [];

      for (const seg of segs) {
        const startIdx = findIndex(sim, seg?.start_time, "start_time");
        const endIdx = findIndex(sim, seg?.end_time, "end_time");
        if (startIdx === -1 || endIdx === -1) continue;

        const a = Math.min(startIdx, endIdx);
        const b = Math.max(startIdx, endIdx);
        for (let i = a; i <= b; i++) {
          session.pattern_indices[i] += 1; // increment covered indices
        }
      }
    }

    // Final list of sessions (unique by sessionId), with accumulated pattern_indices
    const processedSlice = Array.from(sessionsById.values());

    const itemToSave = {
      id: `pattern_${Date.now()}`,
      name,
      color,
      dataset: selectedDataset,
      pattern: processedSlice,
      metadata: {
        createdAt: Date.now(),
        totalSessions: processedSlice.length, // unique sessions
        originalMatches: allPatternData.length, // raw rows
      },
      searchDetail,
      // scoreSummary,
      // percentageData,
      // percentageSummaryData: processedSlice,
      // lengthData,
      // lengthSummaryData: processedSlice,
      // overallSemScoreData,
      // overallSemScoreSummaryData: processedSlice,
    };

    // Commit & refresh UI
    searchPatternSet.update((cur) => [...cur, itemToSave]);
    isSave = false;

    tick().then(() => {
      initData.update((data) => [...data]); // poke reactivity
    });

    showSavedMessage = true;
    setTimeout(() => {
      showSavedMessage = false;
    }, 1000);
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

  function getCategoryIcon(promptCode) {
    return getCategoryIconBase(promptCode, selectedDataset);
  }

  // Functions about tables
  function handleRowClick(sessionData) {
    handleContainerClick({ detail: { sessionId: sessionData.sessionId } });
  }
  // TOPIC ICONS
  let sortColumn = "";
  let sortDirection = "none";

  function handleSort(column) {
    if (column === "topic" && selectedCategoryFilter) {
      return;
    }

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
    if (column === "topic" && selectedCategoryFilter) {
      return "";
    }

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
  // const fetchLLMScore = async (sessionFile) => {
  //   const url = `${base}/dataset/${selectedDataset}/eval_results/${sessionFile}.json`;
  //   try {
  //     const response = await fetch(url);
  //     if (!response.ok) {
  //       console.error("Response not ok:", response.status, response.statusText);
  //       throw new Error(`Failed to fetch LLM score: ${response.status}`);
  //     }

  //     const data = await response.json();
  //     const totalScore = data[0] || 0;
  //     return totalScore;
  //   } catch (error) {
  //     console.error("Error when reading LLM score file:", error);
  //     return null;
  //   }
  // };
  const fetchCSVData = async () => {
    try {

      const response = await fetch(
        `${base}/dataset/${selectedDataset}/fine.csv`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch CSV data");
      }

      const text = await response.text();
      const parsedData = Papa.parse(text, { header: true }).data;

      return parsedData;
    } catch (error) {
      console.error("Error fetching or parsing CSV:", error);
      return [];
    }
  };

  const fetchFeatureData = (data) => {
    return data.map((item) => {
      const filteredItem = Object.fromEntries(
        Object.entries(item).filter(([key]) => key !== "prompt_code")
      );
      return filteredItem;
    });
  };

  const fetchLLMScore = async (sessionId, data) => {
    const item = data.find((item) => item.session_id === sessionId);
    return item ? item.judge_score : null;
  };

  function getColumnGroups() {
    let sessions = getDisplaySessions();
    // Topic
    if (sortColumn === "topic" && sortDirection !== "none") {
      sessions = [...sessions].sort((a, b) => {
        const aCode = getPromptCode(a.session_id);
        const bCode = getPromptCode(b.session_id);

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

  // Topic page, sort filteredByCategory data
  $: sortedFilteredByCategory = (() => {
    if (!selectedCategoryFilter || !filteredByCategory.length) {
      return filteredByCategory;
    }

    let sorted = [...filteredByCategory];

    // Score sort
    if (sortColumn === "score" && sortDirection !== "none") {
      sorted = sorted.sort((a, b) => {
        const aScore = a.llmScore || 0;
        const bScore = b.llmScore || 0;
        if (sortDirection === "asc") {
          return aScore - bScore;
        } else {
          return bScore - aScore;
        }
      });
    }

    // Pattern sort
    if (sortColumn === "pattern" && sortDirection !== "none") {
      sorted = sorted.sort((a, b) => {
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

    return sorted;
  })();

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

  function deriveTimeRangeFromProgress(progressRange, data) {
    if (!progressRange || !data || !data.length) {
      return null;
    }

    const getClosestTime = (targetPercentage) => {
      let closestPoint = data[0];
      let smallestDelta = Infinity;

      for (const point of data) {
        const percentage = Number(point?.percentage ?? point?.progress ?? 0);
        const delta = Math.abs(percentage - targetPercentage);
        if (delta < smallestDelta) {
          smallestDelta = delta;
          closestPoint = point;
        }
      }

      return Number(closestPoint?.time ?? 0);
    };

    const start = getClosestTime(progressRange.min);
    const end = getClosestTime(progressRange.max);

    return {
      min: Math.min(start, end),
      max: Math.max(start, end),
    };
  }

  function findSegments(data, checks, minCount) {
    // console.log("=== findSegments Debug ===");
    // console.log("data.length:", data.length);
    // console.log("checks:", checks);
    // console.log("minCount:", minCount);

    const segments = [];
    const isSourceCheckRequired =
      isExactSearchSource && checks.source && checks.source[0];
    const isTrendCheckRequired =
      isExactSearchTrend && checks.trend && checks.trend[0] && minCount > 1;
    const isProgressCheckRequired =
      isExactSearchProgress && checks.progress && checks.progress[0];
    const isTimeCheckRequired =
      isExactSearchTime && checks.time && checks.time[0];

    // console.log("Check requirements:", {
    //   isSourceCheckRequired,
    //   isTrendCheckRequired,
    //   isProgressCheckRequired,
    //   isTimeCheckRequired,
    // });

    for (let i = 1; i <= data.length - minCount; i++) {
      const window = data.slice(i, i + minCount);

      // Safety check
      if (!window || window.length === 0 || !window[0]) {
        // console.log("Invalid window at index", i, "window:", window);
        continue;
      }

      if (checks.progress && checks.progress[0]) {
        const [min, max] = checks.progress[1];
        const deltaTarget = max - min;
        const relax = deltaTarget * 0.1;

        // Check if required properties exist
        if (
          typeof window[0].start_progress !== "number" ||
          typeof window[window.length - 1].end_progress !== "number"
        ) {
          // console.log("Missing progress data in window:", window[0]);
          continue;
        }

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
        let [minTime, maxTime] = checks.time[1];
        // console.log("Time check - original range:", minTime, maxTime);

        // Check if required time properties exist
        if (
          typeof window[0].start_time !== "number" ||
          typeof window[window.length - 1].end_time !== "number"
        ) {
          // console.log("Missing time data in window:", window[0]);
          continue;
        }

        maxTime = maxTime * 60;
        minTime = minTime * 60;
        const deltaTarget = maxTime - minTime;
        const relax = deltaTarget * 0.3;
        const startTime = window[0].start_time;
        const endTime = window[window.length - 1].end_time;
        const deltaTime = endTime - startTime;
        // console.log("Time check - converted range:", minTime, maxTime);
        // console.log(
        //   "Window time range:",
        //   startTime,
        //   endTime,
        //   "delta:",
        //   deltaTime
        // );
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
    const count =
      sessionData.count || Math.max(1, sessionData.data?.length || 1);

    // console.log("=== Search Pattern Debug ===");
    // console.log("sessionData:", sessionData);
    // console.log("sessionData.count:", sessionData.count);
    // console.log("sessionData.data length:", sessionData.data?.length);
    // console.log("isTimeChecked:", isTimeChecked);
    // console.log("timeRange:", timeRange);
    // console.log("isProgressChecked:", isProgressChecked);
    // console.log("writingProgressRange:", writingProgressRange);

    searchDetail = {
      sessionId,
      data: sessionData.data,
      dataRange: sessionData.dataRange,
      count,
      wholeData: sessionData.wholeData,
      range: sessionData.range,
      selectionSource: sessionData.selectionSource ?? null,
      flag: {
        isProgressChecked,
        isTimeChecked,
        isSourceChecked,
        isSemanticChecked,
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

    // console.log("checks:", checks);

    try {
      // const fileListResponse = await fetch(
      //   `${base}/dataset/${selectedDataset}/session_name.json`
      // );
      // const fileList = await fileListResponse.json();
      const fileList = CSVData.map((item) => item.session_id);

      for (const fileName of fileList) {
        // const fileId = fileName.split(".")[0].replace(/_similarity$/, "");
        // if (fileId === sessionId) {
        //   continue;
        // }

        const dataResponse = await fetch(
          `${base}/dataset/${selectedDataset}/segment_results/${fileName}.json`
        );
        const data = await dataResponse.json();

        if (Array.isArray(data.chartData)) {
          data.chartData = data.chartData.map(
            ({ currentText, ...rest }) => rest
          );
        }
        delete data.paragraphColor;
        delete data.textElements;

        // console.log("Processing file:", fileName);
        // console.log("Data structure keys:", Object.keys(data));
        // console.log("Data.chartData length:", data.chartData?.length);
        // console.log("Data is array?", Array.isArray(data));
        // console.log("Data length:", data.length);
        // if (Array.isArray(data) && data.length > 0) {
        //   console.log("Sample data item:", data[0]);
        // } else if (data.chartData && data.chartData.length > 0) {
        //   console.log("Sample chartData item:", data.chartData[0]);
        // }

        // Use the correct data structure
        const dataToProcess = Array.isArray(data)
          ? data
          : data.chartData || data.totalSimilarityData || [];

        // console.log("Data to process length:", dataToProcess.length);
        // console.log("Count:", count);

        const segments = findSegments(dataToProcess, checks, count);
        const extractedFileName = fileName;

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

  let fetchProgress = 0;

  function computeHighlightRangesFromSegments(segments) {
    if (!Array.isArray(segments) || segments.length === 0) {
      return { time: null, progress: null, windows: [] };
    }

    const toMinutes = (secondsValue, minutesValue, fallbackValue) => {
      if (Number.isFinite(secondsValue)) {
        return secondsValue / 60;
      }
      if (Number.isFinite(minutesValue)) {
        return minutesValue;
      }
      if (Number.isFinite(fallbackValue)) {
        return fallbackValue;
      }
      return null;
    };

    const toPercentage = (primaryValue, fallbackValue) => {
      if (Number.isFinite(primaryValue)) {
        const base =
          Math.abs(primaryValue) <= 1.0001 ? primaryValue * 100 : primaryValue;
        return base;
      }
      if (Number.isFinite(fallbackValue)) {
        const base =
          Math.abs(fallbackValue) <= 1.0001
            ? fallbackValue * 100
            : fallbackValue;
        return base;
      }
      return null;
    };

    const allTimes = [];
    const allProgresses = [];

    segments.forEach((item) => {
      const startTimeSeconds = Number(item.start_time);
      const endTimeSeconds = Number(item.end_time);
      const startTimeMinutes = Number(item.startTime ?? item.startTimeMinutes);
      const endTimeMinutes = Number(item.endTime ?? item.endTimeMinutes);
      const singleTime = Number(item.time);

      const startTime = toMinutes(
        startTimeSeconds,
        startTimeMinutes,
        singleTime
      );
      const endTime = toMinutes(endTimeSeconds, endTimeMinutes, singleTime);

      if (startTime !== null) {
        allTimes.push(startTime);
      }
      if (endTime !== null) {
        allTimes.push(endTime);
      }

      const startProgress = toPercentage(
        Number(item.start_progress ?? item.startProgress ?? item.progressStart),
        Number(item.percentage)
      );
      const endProgress = toPercentage(
        Number(item.end_progress ?? item.endProgress ?? item.progressEnd),
        Number(item.percentage)
      );

      if (startProgress !== null) {
        allProgresses.push(startProgress);
      }
      if (endProgress !== null) {
        allProgresses.push(endProgress);
      }
    });

    let timeRange = null;
    if (allTimes.length) {
      const minTime = Math.min(...allTimes);
      const maxTime = Math.max(...allTimes);
      if (Number.isFinite(minTime) && Number.isFinite(maxTime)) {
        timeRange = {
          min: Math.min(minTime, maxTime),
          max: Math.max(minTime, maxTime),
        };
      }
    }

    let progressRange = null;
    if (allProgresses.length) {
      const rawMin = Math.min(...allProgresses);
      const rawMax = Math.max(...allProgresses);
      if (Number.isFinite(rawMin) && Number.isFinite(rawMax)) {
        const clampedMin = Math.min(Math.max(rawMin, 0), 100);
        const clampedMax = Math.min(Math.max(rawMax, clampedMin), 100);
        progressRange = {
          min: clampedMin,
          max: clampedMax,
        };
      }
    }

    const windows =
      timeRange || progressRange
        ? [
            {
              time: timeRange,
              progress: progressRange,
            },
          ]
        : [];

    const mode =
      timeRange && progressRange
        ? "both"
        : timeRange
          ? "time"
          : progressRange
            ? "progress"
            : null;

    const selectionContext =
      mode === "time"
        ? {
            selectionSource: "lineChart_x",
            timeMin: timeRange?.min ?? null,
            timeMax: timeRange?.max ?? null,
            progressMin: progressRange?.min ?? null,
            progressMax: progressRange?.max ?? null,
          }
        : mode === "progress"
          ? {
              selectionSource: "lineChart_y",
              timeMin: timeRange?.min ?? null,
              timeMax: timeRange?.max ?? null,
              progressMin: progressRange?.min ?? null,
              progressMax: progressRange?.max ?? null,
            }
          : mode === "both"
            ? {
                selectionSource: "lineChart_y",
                timeMin: timeRange?.min ?? null,
                timeMax: timeRange?.max ?? null,
                progressMin: progressRange?.min ?? null,
                progressMax: progressRange?.max ?? null,
              }
            : {
                selectionSource: null,
                timeMin: timeRange?.min ?? null,
                timeMax: timeRange?.max ?? null,
                progressMin: progressRange?.min ?? null,
                progressMax: progressRange?.max ?? null,
              };

    return {
      time: timeRange,
      progress: progressRange,
      windows,
      mode,
      selectionContext,
    };
  }

  async function patternDataLoad(results) {
    const ids = results.map((group) => group[0]?.id).filter(Boolean);
    const BATCH_SIZE = 100;
    for (let i = 0; i < ids.length; i += BATCH_SIZE) {
      // console.log("processing", i, "out of", ids.length);
      fetchProgress =
        Math.round((i / ids.length) * 100) > 100
          ? 100
          : Math.round((i / ids.length) * 100);
      const chunk = ids.slice(i, i + BATCH_SIZE);
      await Promise.allSettled(chunk.map((id) => fetchDataSummary(id)));
    }

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
          const highlightRanges = computeHighlightRangesFromSegments(group);
          const fallbackMode = resolveHighlightModeFromSource(
            searchDetail?.selectionSource ?? null
          );
          const highlightMode = fallbackMode ?? highlightRanges.mode ?? null;
          const selectionContext = highlightRanges.selectionContext ?? {
            selectionSource:
              highlightMode === "time"
                ? "lineChart_x"
                : highlightMode === "progress"
                  ? "lineChart_y"
                  : null,
            timeMin: highlightRanges.time?.min ?? null,
            timeMax: highlightRanges.time?.max ?? null,
            progressMin: highlightRanges.progress?.min ?? null,
            progressMax: highlightRanges.progress?.max ?? null,
          };
          return {
            ...newSessionData,
            chartData: Array.isArray(newSessionData.chartData)
              ? newSessionData.chartData
              : [],
            segments: group,
            segmentId: group[0]?.segmentId,
            highlightRanges: {
              ...highlightRanges,
              mode: highlightMode,
              selectionContext,
            },
          };
        })
        .filter(Boolean)
    );
    isSearch = 2; // reset search state; 0: not searching, 1: searching, 2: search done
    fetchProgress = 0;
  }

  function closePatternSearch() {
    showPatternSearch = false;
    selectionMode = false;
  }

  let selectionSrc = null;

  function resolveHighlightModeFromSource(source) {
    if (source === "lineChart_x") return "time";
    if (source === "lineChart_y" || source === "barChart_y") return "progress";
    return null;
  }

  function handleSelectionChanged(event) {
    showResultCount.set(5);
    if (sharedSelection) {
      selectionSrc = sharedSelection.selectionSource;
    }

    if (sharedSelection && sharedSelection.selectionSource === "lineChart_x") {
      // console.log("Setting lineChart_x options");
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
      // console.log(
      //   "After setting lineChart_x - isProgressChecked:",
      //   isProgressChecked,
      //   "isTimeChecked:",
      //   isTimeChecked,
      //   "isSourceChecked:",
      //   isSourceChecked
      // );
    } else if (
      sharedSelection &&
      sharedSelection.selectionSource === "lineChart_y"
    ) {
      // console.log("Setting lineChart_y options");
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
      // console.log("Setting barChart_y options");
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
      // console.log("Setting default options");
      isProgressChecked = false;
      isTimeChecked = false;
      isSourceChecked = true;
      isExactSearchSource = true;
      isSemanticChecked = true;
      isValueRangeChecked = true;
      isValueTrendChecked = true;
      isExactSearchTrend = true;
    }

    // if (sharedSelection && sharedSelection.selectionSource === "barChart_y") {
    //   isExactSearchSource = true;/
    //   isExactSearchTrend = true;
    // } else {
    //   isExactSearchSource = false;
    //   isExactSearchTrend = false;
    // }
    semanticTrend = [];
    selectedPatterns = {};
    patternData = [];
    patternDataList.set([]);
    currentResults = {};
    const {
      sessionId: rawSessionId,
      range,
      dataRange,
      data,
      wholeData,
      sources,
    } = event.detail;

    const resolvedSessionId =
      rawSessionId ??
      sharedSelection?.sessionId ??
      $clickSession?.sessionId ??
      lastSession?.sessionId;

    if (!resolvedSessionId) {
      return;
    }

    const sessionStore = get(storeSessionData);
    const sessionSummaryStore = get(storeSessionSummaryData);
    const sessionRecord =
      sessionStore.get(resolvedSessionId) ??
      sessionSummaryStore.get(resolvedSessionId) ??
      {};

    const similaritySeries = Array.isArray(sessionRecord.totalSimilarityData)
      ? sessionRecord.totalSimilarityData
      : Array.isArray(sessionRecord.similarityData)
        ? sessionRecord.similarityData
        : [];

    const chartSeries =
      Array.isArray(wholeData) && wholeData.length
        ? wholeData
        : Array.isArray(sessionRecord.chartData)
          ? sessionRecord.chartData
          : [];

    const selectionSource =
      sharedSelection?.selectionSource ??
      selectionSrc ??
      event.detail.selectionSource ??
      null;

    const baseRange = range
      ? {
          sc: {
            min: range?.sc?.min ?? 0,
            max: range?.sc?.max ?? 0,
          },
          progress: {
            min: range?.progress?.min ?? 0,
            max: range?.progress?.max ?? 0,
          },
        }
      : {
          sc: { min: 0, max: 0 },
          progress: { min: 0, max: 0 },
        };

    let effectiveRange = baseRange;

    const baseDataRange = dataRange
      ? {
          scRange: {
            min: dataRange?.scRange?.min ?? 0,
            max: dataRange?.scRange?.max ?? 0,
          },
          progressRange: {
            min: dataRange?.progressRange?.min ?? 0,
            max: dataRange?.progressRange?.max ?? 0,
          },
          timeRange: {
            min: dataRange?.timeRange?.min ?? 0,
            max: dataRange?.timeRange?.max ?? 0,
          },
          sc: { sc: [...(dataRange?.sc?.sc ?? [])] },
        }
      : {
          scRange: { min: 0, max: 0 },
          progressRange: { min: 0, max: 0 },
          timeRange: { min: 0, max: 0 },
          sc: { sc: [] },
        };

    let effectiveDataRange = baseDataRange;

    let effectiveData =
      data && data.length ? data.map((item) => ({ ...item })) : [];

    let effectiveSources = sources && sources.length ? [...sources] : [];

    let scValues = [...effectiveDataRange.sc.sc];

    if (!effectiveData.length && similaritySeries.length) {
      effectiveData = similaritySeries.map((item) => ({ ...item }));
      scValues = effectiveData
        .map((point) => Number(point?.residual_vector_norm ?? 0))
        .filter((value) => Number.isFinite(value));
    }

    if (selectionSource === "lineChart_x" && similaritySeries.length) {
      const timeMinRaw =
        sharedSelection?.timeMin ?? effectiveDataRange.timeRange.min ?? 0;
      const timeMaxRaw =
        sharedSelection?.timeMax ??
        effectiveDataRange.timeRange.max ??
        timeMinRaw;
      const timeMin = Math.min(timeMinRaw, timeMaxRaw);
      const timeMax = Math.max(timeMinRaw, timeMaxRaw);

      const filteredSimilarity = similaritySeries.filter((segment) => {
        const startSeconds = Number(
          segment?.start_time ?? segment?.startTime ?? 0
        );
        const endSeconds = Number(
          segment?.end_time ??
            segment?.endTime ??
            segment?.last_event_time ??
            segment?.start_time ??
            startSeconds
        );
        const startMinutes = startSeconds / 60;
        const endMinutes = endSeconds / 60;
        const segStart = Math.min(startMinutes, endMinutes);
        const segEnd = Math.max(startMinutes, endMinutes);
        return segEnd >= timeMin && segStart <= timeMax;
      });

      if (filteredSimilarity.length) {
        effectiveData = filteredSimilarity.map((segment) => ({ ...segment }));

        scValues = filteredSimilarity
          .map((segment) => Number(segment?.residual_vector_norm ?? 0))
          .filter((value) => Number.isFinite(value));

        if (scValues.length) {
          effectiveRange = {
            ...effectiveRange,
            sc: {
              min: Math.min(...scValues),
              max: Math.max(...scValues),
            },
          };
        } else {
          effectiveRange = {
            ...effectiveRange,
            sc: { min: 0, max: 0 },
          };
        }

        const progressValues = filteredSimilarity
          .flatMap((segment) => [
            Number(segment?.start_progress ?? 0) * 100,
            Number(segment?.end_progress ?? 0) * 100,
          ])
          .filter((value) => Number.isFinite(value));

        if (progressValues.length) {
          effectiveRange = {
            ...effectiveRange,
            progress: {
              min: Math.min(...progressValues),
              max: Math.max(...progressValues),
            },
          };
        }

        effectiveSources = filteredSimilarity.map(
          (segment) => segment?.source ?? "user"
        );

        effectiveDataRange = {
          ...effectiveDataRange,
          scRange: { ...effectiveRange.sc },
          progressRange: { ...effectiveRange.progress },
          timeRange: { min: timeMin, max: timeMax },
          sc: { sc: scValues },
        };
      } else {
        effectiveDataRange = {
          ...effectiveDataRange,
          timeRange: { min: timeMin, max: timeMax },
        };
      }
    } else {
      if (!scValues.length) {
        scValues = effectiveData
          .map((point) => Number(point?.residual_vector_norm ?? 0))
          .filter((value) => Number.isFinite(value));
      }
      if (scValues.length) {
        effectiveRange = {
          ...effectiveRange,
          sc: {
            min: Math.min(...scValues),
            max: Math.max(...scValues),
          },
        };
        effectiveDataRange.scRange = { ...effectiveRange.sc };
        effectiveDataRange.sc = { sc: scValues };
      }
    }

    if (!effectiveSources.length) {
      effectiveSources = effectiveData.map((point) => point?.source ?? "user");
    }

    writingProgressRange = [
      effectiveDataRange.progressRange.min ?? 0,
      effectiveDataRange.progressRange.max ?? 0,
    ];

    // Use time range in dataRange, no different bewteen Time and Progress mode
    timeRange = [
      effectiveDataRange.timeRange.min ?? 0,
      effectiveDataRange.timeRange.max ?? 0,
    ];
    sourceRange = effectiveSources;
    semanticRange = [
      effectiveDataRange.scRange.min ?? 0,
      effectiveDataRange.scRange.max ?? 0,
    ];
    semanticData = scValues;
    semanticTrend = getTrendPattern(semanticData);
    currentResults = effectiveData;
    lastSession = $clickSession ?? sessionRecord;

    let highlightTimeRange = null;
    if (selectionSource === "lineChart_x") {
      highlightTimeRange = { min: timeRange[0], max: timeRange[1] };
    } else if (
      sharedSelection &&
      sharedSelection.timeMin !== undefined &&
      sharedSelection.timeMax !== undefined
    ) {
      highlightTimeRange = {
        min: Math.min(sharedSelection.timeMin, sharedSelection.timeMax),
        max: Math.max(sharedSelection.timeMin, sharedSelection.timeMax),
      };
    } else if (
      effectiveRange?.progress &&
      Number.isFinite(effectiveRange.progress.min) &&
      Number.isFinite(effectiveRange.progress.max) &&
      Array.isArray(chartSeries) &&
      chartSeries.length > 0
    ) {
      const derivedRange = deriveTimeRangeFromProgress(
        effectiveRange.progress,
        chartSeries
      );

      if (
        derivedRange &&
        derivedRange.min !== undefined &&
        derivedRange.max !== undefined
      ) {
        highlightTimeRange = derivedRange;
      }
    }

    const selectionHighlightWindows = [];
    const selectionHighlightMode =
      resolveHighlightModeFromSource(selectionSource);
    const highlightInfo = computeHighlightRangesFromSegments(effectiveData);
    const highlightMode = selectionHighlightMode ?? highlightInfo.mode ?? null;

    const selectionContext = {
      selectionSource,
      timeMin: null,
      timeMax: null,
      progressMin: Number.isFinite(effectiveRange.progress.min)
        ? effectiveRange.progress.min
        : null,
      progressMax: Number.isFinite(effectiveRange.progress.max)
        ? effectiveRange.progress.max
        : null,
    };

    if (
      (highlightMode === "progress" || highlightMode === "both") &&
      Number.isFinite(effectiveRange.progress.min) &&
      Number.isFinite(effectiveRange.progress.max)
    ) {
      selectionHighlightWindows.push({
        progress: {
          min: effectiveRange.progress.min,
          max: effectiveRange.progress.max,
        },
      });
    }

    const resolvedSelectedTimeRangeCandidate =
      highlightTimeRange ??
      (highlightMode === "time" || highlightMode === "both"
        ? {
            min: timeRange[0],
            max: timeRange[1],
          }
        : null);

    if (
      (highlightMode === "time" || highlightMode === "both") &&
      resolvedSelectedTimeRangeCandidate &&
      Number.isFinite(resolvedSelectedTimeRangeCandidate.min) &&
      Number.isFinite(resolvedSelectedTimeRangeCandidate.max)
    ) {
      selectionContext.timeMin = resolvedSelectedTimeRangeCandidate.min;
      selectionContext.timeMax = resolvedSelectedTimeRangeCandidate.max;
      selectionHighlightWindows.push({
        time: {
          min: resolvedSelectedTimeRangeCandidate.min,
          max: resolvedSelectedTimeRangeCandidate.max,
        },
      });
    }

    const resolvedSelectedTimeRange =
      highlightTimeRange ?? highlightInfo.time ?? null;

    const resolvedHighlightWindows =
      selectionHighlightWindows.length > 0
        ? selectionHighlightWindows
        : (highlightInfo.windows ?? []);
    const resolvedSelectionContext =
      selectionContext.timeMin !== null ||
      selectionContext.timeMax !== null ||
      selectionContext.progressMin !== null ||
      selectionContext.progressMax !== null
        ? selectionContext
        : (highlightInfo.selectionContext ?? {
            selectionSource,
            timeMin: highlightInfo.time?.min ?? null,
            timeMax: highlightInfo.time?.max ?? null,
            progressMin: highlightInfo.progress?.min ?? null,
            progressMax: highlightInfo.progress?.max ?? null,
          });

    const updatedPattern = {
      range: effectiveRange,
      dataRange: effectiveDataRange,
      data: effectiveData,
      wholeData: chartSeries,
      sources: effectiveSources,
      scRange: `${effectiveRange.sc.min.toFixed(1)} - ${effectiveRange.sc.max.toFixed(1)}%`,
      progressRange: `${effectiveRange.progress.min.toFixed(1)} - ${effectiveRange.progress.max.toFixed(1)}%`,
      count: effectiveData.length,
      // Save selected time range, used for highlight in time mode
      selectedTimeRange: resolvedSelectedTimeRange,
      highlightWindows: resolvedHighlightWindows,
      highlightMode,
      selectionSource,
      selectionContext: resolvedSelectionContext,
    };

    selectedPatterns = {
      ...selectedPatterns,
      [resolvedSessionId]: updatedPattern,
    };
  }

  function handleSelectionCleared(event) {
    const resolvedSessionId =
      event.detail.sessionId ??
      sharedSelection?.sessionId ??
      $clickSession?.sessionId ??
      lastSession?.sessionId;

    if (resolvedSessionId && selectedPatterns[resolvedSessionId]) {
      const { [resolvedSessionId]: _, ...rest } = selectedPatterns;
      selectedPatterns = rest;
    }
  }

  function change2bar() {
    showMulti = !showMulti;
    clickSession.set([]);
  }

  function change2main() {
    showMulti = false;
    clickSession.set([]);
  }

  function backToLanding() {
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
  }

  // const fetchLengthData = async () => {
  //   try {
  //     const response = await fetch(
  //       `${base}/dataset/${selectedDataset}/length.json`
  //     );
  //     if (!response.ok) {
  //       throw new Error(`Failed to fetch summary data: ${response.status}`);
  //     }

  //     const data = await response.json();
  //     return data;
  //   } catch (error) {
  //     console.error("Error when reading the data file:", error);
  //     return null;
  //   }
  // };

  // const fetchOverallSemScoreData = async () => {
  //   try {
  //     const response = await fetch(
  //       `${base}/dataset/${selectedDataset}/overall_sem_score.json`
  //     );
  //     if (!response.ok) {
  //       throw new Error(`Failed to fetch summary data: ${response.status}`);
  //     }

  //     const data = await response.json();
  //     return data;
  //   } catch (error) {
  //     console.error("Error when reading the data file:", error);
  //     return null;
  //   }
  // };

  // const fetchPercentageData = async () => {
  //   try {
  //     const response = await fetch(
  //       `${base}/dataset/${selectedDataset}/percentage.json`
  //     );
  //     if (!response.ok) {
  //       throw new Error(`Failed to fetch summary data: ${response.status}`);
  //     }

  //     const data = await response.json();
  //     return data;
  //   } catch (error) {
  //     console.error("Error when reading the data file:", error);
  //     return null;
  //   }
  // };

  // const fetchScoreSummaryData = async () => {
  //   try {
  //     const response = await fetch(
  //       `${base}/dataset/${selectedDataset}/score_summary.json`
  //     );
  //     if (!response.ok) {
  //       throw new Error(`Failed to fetch summary data: ${response.status}`);
  //     }

  //     const data = await response.json();
  //     return data;
  //   } catch (error) {
  //     console.error("Error when reading the data file:", error);
  //     return null;
  //   }
  // };

  async function fetchInitData(sessionId, isDelete) {
    if (isDelete) {
      initData.update((data) =>
        data.filter((item) => item.sessionId !== sessionId)
      );
      return;
    }
    const similarityData = await fetchSimilarityData(sessionId);
    const llmScore = await fetchLLMScore(sessionId, CSVData);

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
        `${base}/import_dataset/${selectedDataset}.csv`
      );
      if (!response.ok) {
        throw new Error("Failed to fetch CSV data");
      }
      const text = await response.text();
      const parsedData = Papa.parse(text, { header: true }).data;
      sessions = parsedData.map((session) => ({
        session_id: session.session_id,
        prompt_code: session.prompt_code,
      }));

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
        `${base}/dataset/${selectedDataset}/json/${sessionFile}.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }

      const data = await response.json();
      const time0 = new Date(data.init_time);
      const time100 = new Date(data.end_time);
      const currentTime = (time100.getTime() - time0.getTime()) / (1000 * 60); // in minutes
      const similarityData = await fetchSimilarityData(sessionFile);
      const chartData = handleEventsSummary(data, similarityData);
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
        `${base}/dataset/${selectedDataset}/json/${sessionFile}.json`
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
        handleEvents(data);
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
        `${base}/dataset/${selectedDataset}/segment_results/${sessionFile}.json`
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

  let isLoadOverallData = false;
  let CSVData = [];
  let featureData = [];
  onMount(async () => {
    document.title = "Ink-Pulse";
    const res = await fetch(`${base}/dataset_name.json`);
    datasets = await res.json();
    const params = new URLSearchParams(window.location.search);
    const datasetParam = params.get("dataset");
    if (datasetParam && datasets.includes(datasetParam)) {
      selectedDataset = datasetParam;
    }
    CSVData = (await fetchCSVData()).filter(
      (item) => item.session_id && item.session_id.trim() !== ""
    );
    featureData = await fetchFeatureData(CSVData);

    if (isLoadOverallData == false) {
      const prefix = selectedDataset.slice(0, 2);
      const itemToSave = {
        id: `pattern_0`,
        name: `Others-${prefix}`,
        dataset: selectedDataset,
        pattern: [],
        metadata: {},
        featuredata: featureData,
      };
      searchPatternSet.update((current) => {
        const index = current.findIndex(
          (p) => p.id === "pattern_0" && p.dataset === selectedDataset
        );

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
      const llmScore = await fetchLLMScore(sessionId, CSVData);

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

  const handleEventsSummary = (data, similarityData) => {
    const chartData = [];
    let firstTime = null;
    let index = 0;
    const totalTextLength = data.text[0].slice(0, -1).length;
    let currentCharCount = data.init_text.length;

    data.action.forEach((event, idx) => {
      const { name, event_time, eventSource, text = "", count = 0 } = event;

      const textColor = eventSource === "user" ? "#66C2A5" : "#FC8D62";
      const eventTime = new Date(event_time);
      if (!firstTime) firstTime = eventTime;
      const relativeTime = (eventTime.getTime() - firstTime.getTime()) / 60000;

      let percentage;
      if (name === "text-insert") {
        const insertChars = [...text];
        insertChars.forEach(() => {
          currentCharCount++;
          percentage = (currentCharCount / totalTextLength) * 100;
          chartData.push({
            time: relativeTime,
            percentage,
            eventSource,
            color: textColor,
            isSuggestionOpen: false,
            isSuggestionAccept: false,
            index: index++,
          });
        });
      } else if (name === "text-delete") {
        const deleteCount = text.length || count;
        currentCharCount -= deleteCount;
        percentage = (currentCharCount / totalTextLength) * 100;
        chartData.push({
          time: relativeTime,
          percentage,
          eventSource,
          color: textColor,
          isSuggestionOpen: false,
          isSuggestionAccept: false,
          index: index++,
        });
      } else {
        percentage = (currentCharCount / totalTextLength) * 100;
        let isSuggestionAccept = false;
        if (name === "suggestion-open" && data.action[idx + 1]) {
          const nextEvent = data.action[idx + 1];
          if (
            nextEvent.eventSource === "api" &&
            nextEvent.name === "text-insert"
          ) {
            isSuggestionAccept = true;
          }
        }

        chartData.push({
          time: relativeTime,
          percentage,
          eventSource,
          color: textColor,
          isSuggestionOpen: name === "suggestion-open",
          isSuggestionAccept,
          index: index++,
        });
      }
    });
    return chartData;
  };

  const handleEvents = (data) => {
    const initText = data.init_text;
    let currentCharArray = initText.split("");
    let currentColor = new Array(currentCharArray.length).fill("#FC8D62");
    let chartData = [];
    let paragraphColor = [];
    let firstTime = null;
    let indexOfAct = 0;
    const wholeText = data.text.slice(0, -1);
    const totalTextLength = wholeText.length;
    let totalInsertions = 0;
    let totalDeletions = 0;
    let totalSuggestions = 0;
    let totalProcessedCharacters = totalTextLength;
    const sortedEvents = [...data.action].sort((a, b) => a.id - b.id);

    let combinedText = [...initText].map((ch) => ({
      text: ch,
      textColor: "#FC8D62",
    }));
    sortedEvents.forEach((event, idx) => {
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
            isSuggestionAccept: false,
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

      let isSuggestionAccept = false;
      if (name === "suggestion-open" && sortedEvents[idx + 1]) {
        const nextEvent = sortedEvents[idx + 1];
        if (
          nextEvent.eventSource === "api" &&
          nextEvent.name === "text-insert"
        ) {
          isSuggestionAccept = true;
        }
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
        isSuggestionAccept,
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

    totalSuggestions = chartData.filter((d) => d.isSuggestionOpen).length;

    let i = 0; // code about making $text$ grey
    while (i < combinedText.length) {
      if (combinedText[i].text === "$") {
        let start = i;
        let end = -1;

        for (let j = i + 1; j < combinedText.length; j++) {
          if (combinedText[j].text === "$") {
            end = j;
            break;
          }
        }

        if (end !== -1 && end > start) {
          for (let k = start; k <= end; k++) {
            combinedText[k].textColor = "#cccccc";
          }
          i = end + 1;
        } else {
          i++;
        }
      } else {
        i++;
      }
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
    // console.log("Right clicked on pattern from table:", pattern.name);
  }

  $: showPatternColumn = $searchPatternSet && $searchPatternSet.length > 0;
  let maxVisible = 8;
  function handleShowMorePatterns() {
    maxVisible = $searchPatternSet.length;
    // console.log(`Total patterns: ${$searchPatternSet.length}`);
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
    // console.log("displaySessions:", getDisplaySessions());
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

  function scrollToTop() {
    const panel = document.querySelector(".pattern-panel-content");
    if (panel) panel.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Search functionality
  function handleSearch() {
    if (!searchQuery.trim()) {
      searchResults = [];
      showSearchResults = false;
      return;
    }

    // Search through all sessions in initData
    const query = searchQuery.toLowerCase().trim();
    searchResults = $initData
      .filter(
        (session) =>
          session.sessionId && session.sessionId.toLowerCase().includes(query)
      )
      .slice(0, 10); // Limit to 10 results

    showSearchResults = searchResults.length > 0;
  }

  function handleSearchInput(event) {
    searchQuery = event.target.value;
    handleSearch();
  }

  function selectSearchResult(sessionId) {
    // Navigate to the session detail
    handleContainerClick({ detail: { sessionId } });

    // Clear search
    searchQuery = "";
    searchResults = [];
    showSearchResults = false;
  }

  function handleSearchKeydown(event) {
    if (event.key === "Enter") {
      if (searchResults.length > 0) {
        selectSearchResult(searchResults[0].sessionId);
      }
    } else if (event.key === "Escape") {
      searchQuery = "";
      searchResults = [];
      showSearchResults = false;
    }
  }

  // Close search results when clicking outside
  function handleDocumentClick(event) {
    const searchContainer = document.querySelector(".search-container");
    if (searchContainer && !searchContainer.contains(event.target)) {
      showSearchResults = false;
    }

    // Close export menu when clicking outside
    const exportContainer = document.querySelector(".export-dropdown");
    if (exportContainer && !exportContainer.contains(event.target)) {
      showExportMenu = false;
    }
  }

  // Export functions
  function toggleExportMenu() {
    showExportMenu = !showExportMenu;
    if (showExportMenu) {
      console.log("=== Export Menu Debug ===");
      console.log("searchPatternSet:", $searchPatternSet);
      console.log("selectedDataset:", selectedDataset);
      console.log(
        "all patterns:",
        $searchPatternSet.filter((p) => p.id !== "pattern_0")
      );
      console.log(
        "filtered patterns:",
        $searchPatternSet.filter(
          (p) => p.dataset === selectedDataset && p.id !== "pattern_0"
        )
      );
    }
  }

  async function handleExportAll() {
    showExportMenu = false;
    await exportDB();
  }

  async function handleExportSingle(patternId) {
    showExportMenu = false;
    await exportSinglePattern(patternId);
  }

  let showButton = false;
  async function updateVisibility() {
    await tick();
    const panel = document.querySelector(".pattern-panel-content");
    if (panel) {
      showButton = panel.scrollHeight > panel.clientHeight;
    }
  }

  onMount(() => {
    updateVisibility();
    window.addEventListener("resize", updateVisibility);

    // Add document click listener for search
    document.addEventListener("click", handleDocumentClick);

    return () => {
      window.removeEventListener("resize", updateVisibility);
      document.removeEventListener("click", handleDocumentClick);
    };
  });

  function handleNavigation() {
    if (currentView === "pattern-detail") {
      handleBackFromDetail();
    } else if (selectedCategoryFilter) {
      backToLanding();
    } else if (showMulti) {
      change2bar();
    }
  }
</script>

<div class="App">
  <header class="App-header">
    <nav style="display: flex; align-items: center;">
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo" style="zoom: 150%;">
            <img
              src="{base}/favicon.png"
              alt="InkPulse Logo"
              class="ink-icon"
              style="width: 40px; height: auto; cursor: pointer;"
              on:click={handleNavigation}
            />

            <span
              class="brand-name"
              style="cursor: pointer;"
              on:click={handleNavigation}>InkPulse</span
            >
          </div>
        </div>
      </div>
      <div
        class="chart-explanation"
        style="font-size: 13px; align-items: center; display: flex;"
      >
        &nbsp;&nbsp;&nbsp;&nbsp;
        <span class="triangle-text-accept">▼</span> Accept AI suggestion &nbsp;
        <span class="triangle-text-reject">▼</span> Reject AI suggestion &nbsp;
        <span class="user-line">●</span> User &nbsp;
        <span class="api-line">●</span> AI
      </div>

      <!-- Search Box -->
      <div
        class="search-container"
        style="position: relative; margin-left: 20px;"
      >
        <input
          type="text"
          placeholder="Search Session ID..."
          bind:value={searchQuery}
          on:input={handleSearchInput}
          on:keydown={handleSearchKeydown}
          class="search-input"
          style="
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 13px;
            width: 200px;
            outline: none;
          "
        />

        {#if showSearchResults && searchResults.length > 0}
          <div
            class="search-results"
            style="
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 6px 6px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
          "
          >
            {#each searchResults as session}
              <div
                class="search-result-item"
                on:click={() => selectSearchResult(session.sessionId)}
                style="
                  padding: 8px 12px;
                  cursor: pointer;
                  border-bottom: 1px solid #eee;
                  font-size: 13px;
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                "
              >
                <span style="font-weight: 500;">{session.sessionId}</span>
                {#if session.llmScore}
                  <span style="color: #666; font-size: 12px;"
                    >Score: {session.llmScore}</span
                  >
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        {#if showSearchResults && searchResults.length === 0 && searchQuery.trim()}
          <div
            class="search-results"
            style="
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 6px 6px;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            padding: 12px;
            text-align: center;
            color: #666;
            font-size: 13px;
          "
          >
            No sessions found
          </div>
        {/if}
      </div>
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded"
        rel="stylesheet"
      />
      {#if currentView === "pattern-detail"}
        <a
          on:click={handleBackFromDetail}
          href=" "
          aria-label="Back from Pattern Detail"
          class="humbleicons--arrow-go-back"
        ></a>
      {:else if showMulti}
        <a
          on:click={change2bar}
          href=" "
          aria-label="Toggle View"
          class="humbleicons--arrow-go-back"
        ></a>
      {:else if selectedCategoryFilter}
        <a
          on:click={backToLanding}
          href=" "
          aria-label="Back to Landing"
          class="humbleicons--arrow-go-back"
        ></a>
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
          {#if Object.keys(selectedPatterns).length > 0}
            <button class="scroll-to-top" on:click={scrollToTop}>↑</button>
          {/if}
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
                <div class="export-dropdown">
                  <button
                    class="search-pattern-button"
                    on:click={toggleExportMenu}
                    aria-label="Download patterns"
                    title="Download saved patterns"
                  >
                    Download ▼
                  </button>

                  {#if showExportMenu}
                    <div class="export-menu">
                      <button
                        class="export-option"
                        on:click={handleExportAll}
                        title="Export all patterns as separate files"
                      >
                        📁 Export All (Separate Files)
                      </button>

                      <div class="export-divider">Individual Patterns:</div>

                      {#each $searchPatternSet.filter((p) => p.dataset === selectedDataset && p.id !== "pattern_0") as pattern}
                        <button
                          class="export-option pattern-export"
                          on:click={() => handleExportSingle(pattern.id)}
                          title="Export {pattern.name}"
                        >
                          <span
                            class="pattern-color"
                            style="background-color: {pattern.color}"
                          ></span>
                          {pattern.name}
                        </button>
                      {:else}
                        <div class="export-no-patterns">
                          No patterns found for dataset: {selectedDataset}
                          <br />
                          <small>Available patterns in other datasets:</small>
                          {#each $searchPatternSet.filter((p) => p.id !== "pattern_0") as pattern}
                            <small class="other-dataset-pattern">
                              • {pattern.name} ({pattern.dataset})
                            </small>
                          {:else}
                            <small>No saved patterns yet</small>
                          {/each}
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
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
                  dataset={selectedDataset}
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
                      <button
                        class="weight-button"
                        on:click={setWeight}
                        title="Adjust Weight"
                      >
                        🔧
                      </button>
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
                  {#if selectionSrc == "lineChart_y"}
                    <div
                      style="display: flex; flex-wrap: wrap; gap: 0; width: 100%; align-items: flex-start;"
                    >
                      <div
                        style="
                          display: flex;
                          gap: 0;
                          width: 100%;
                          align-items: flex-start;
                          border: 1px solid #e0e0e0;
                          border-radius: 4px;
                          background-color: white;
                        "
                      >
                        <!-- Pattern chart -->
                        <div
                          style="flex: 1 1 50%; margin-top: 10px; padding: 0;"
                        >
                          <div style="margin: 0; padding: 0;">
                            <PatternChartPreview
                              {sessionId}
                              data={pattern.data}
                              wholeData={pattern.wholeData}
                              selectedRange={pattern.range}
                              bind:this={chartRefs[sessionId]}
                              margin_right={0}
                            />
                          </div>
                        </div>

                        <!-- Line chart -->
                        <div
                          style="flex: 1 1 50%; margin-top: 7px; padding: 0; margin-left: 0;"
                        >
                          <div
                            style="
                              position: relative;
                              height: 160px;
                              overflow: hidden;
                              transform-origin: top left;
                              margin-left: 0;
                            "
                          >
                            <LineChartPreview
                              bind:this={chartRefs[sessionId]}
                              chartData={$clickSession.chartData}
                              selectedTimeRange={pattern.selectedTimeRange ??
                                deriveTimeRangeFromProgress(
                                  pattern.range?.progress,
                                  pattern.wholeData
                                ) ??
                                null}
                              selectedProgressRange={pattern.range?.progress ??
                                null}
                              highlightWindows={pattern.highlightWindows ?? []}
                              highlightMode={pattern.highlightMode ?? null}
                              selectionContext={pattern.selectionContext ??
                                null}
                            />
                          </div>
                        </div>
                      </div>

                      <div
                        style="
                          display: grid;
                          grid-template-columns: 1fr 1fr;
                          column-gap: 20px;
                          width: 100%;
                          margin-top: 8px;
                          align-items: start;
                        "
                      >
                        <div style="font-size: 13px;">
                          <div
                            class:dimmed={!isProgressChecked}
                            style="font-size: 13px; display: flex; align-items: center; gap: 8px;"
                          >
                            <input
                              type="checkbox"
                              bind:checked={isProgressChecked}
                            />
                            <span>Writing Progress</span>
                            <label
                              class="switch"
                              style="transform: translateY(4px); margin-left: auto;"
                              bind:this={exactProgressButton}
                            >
                              <input
                                type="checkbox"
                                bind:checked={isExactSearchProgress}
                                disabled={!isProgressChecked}
                              />
                              <span class="slider">
                                <span
                                  class="switch-text {isExactSearchProgress
                                    ? 'exact'
                                    : 'duration'}"
                                >
                                  {isExactSearchProgress ? "Exact" : "Duration"}
                                </span>
                              </span>
                            </label>
                          </div>

                          <div
                            class:dimmed={!isTimeChecked}
                            style="font-size: 13px; display: flex; align-items: center; gap: 8px;"
                          >
                            <input
                              type="checkbox"
                              bind:checked={isTimeChecked}
                            />
                            <span>Time</span>
                            <label
                              class="switch"
                              style="transform: translateY(4px); margin-left: auto;"
                              bind:this={exactTimeButton}
                            >
                              <input
                                type="checkbox"
                                bind:checked={isExactSearchTime}
                                disabled={!isTimeChecked}
                              />
                              <span class="slider">
                                <span
                                  class="switch-text {isExactSearchTime
                                    ? 'exact'
                                    : 'duration'}"
                                >
                                  {isExactSearchTime ? "Exact" : "Duration"}
                                </span>
                              </span>
                            </label>
                          </div>

                          <div
                            class:dimmed={!isSourceChecked}
                            style="font-size: 13px; display: flex; align-items: center; gap: 8px; white-space: nowrap;"
                          >
                            <input
                              type="checkbox"
                              bind:checked={isSourceChecked}
                            />
                            <span>Source (human/AI)</span>
                            <label
                              class="switch"
                              style="transform: translateY(4px); margin-left: auto;"
                              bind:this={exactSourceButton}
                            >
                              <input
                                type="checkbox"
                                bind:checked={isExactSearchSource}
                                disabled={!isSourceChecked}
                              />
                            </label>
                          </div>
                        </div>

                        <div style="font-size: 13px;">
                          <div
                            class:dimmed={!isSemanticChecked}
                            style="display: flex; align-items: center; gap: 8px; white-space: nowrap; font-weight: 600; padding: 2px 4px; border-radius: 4px;"
                          >
                            <input
                              type="checkbox"
                              bind:checked={isSemanticChecked}
                            />
                            <span>Semantic Expansion</span>
                          </div>

                          <div
                            style="
                              margin: 0;
                              padding: 0px 10px;
                              border-left: 3px solid #dcdcdc;
                              background: rgba(0,0,0,0.03);
                              border-radius: 4px;
                            "
                          >
                            <div
                              class:dimmed={!isValueRangeChecked}
                              style="display: flex; align-items: center; gap: 8px; white-space: nowrap;"
                            >
                              <input
                                type="checkbox"
                                bind:checked={isValueRangeChecked}
                                disabled={!isSemanticChecked}
                              />
                              <span>Value Range</span>
                            </div>

                            <div
                              class:dimmed={!isValueTrendChecked}
                              style="display: flex; align-items: center; gap: 8px; white-space: nowrap;"
                            >
                              <input
                                type="checkbox"
                                bind:checked={isValueTrendChecked}
                                disabled={!isSemanticChecked}
                              />
                              <span>Value Trend</span>
                              <label
                                class="switch"
                                style="transform: translateY(4px); margin-left: auto;"
                                bind:this={exactTrendButton}
                              >
                                <input
                                  type="checkbox"
                                  bind:checked={isExactSearchTrend}
                                  disabled={!isSemanticChecked ||
                                    !isValueTrendChecked}
                                />
                              </label>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  {:else}
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                      {#if selectionSrc == "lineChart_x"}
                        <!-- Time mode: Show LineChart with time selection highlight -->
                        <div
                          class="pattern-chart-preview small-preview"
                          style="height: 160px; width: fit-content; max-width: 100%;"
                        >
                          <LineChartPreview
                            bind:this={chartRefs[sessionId]}
                            chartData={(() => {
                              // Make sure charts always display
                              let data = $clickSession?.chartData;

                              // If current data cannot use
                              if (
                                !data ||
                                !Array.isArray(data) ||
                                data.length === 0
                              ) {
                                data = pattern.wholeData;
                              }

                              // Empty array
                              if (!data || !Array.isArray(data)) {
                                data = [];
                              }

                              return data;
                            })()}
                            selectedTimeRange={pattern.selectedTimeRange}
                            selectedProgressRange={pattern.range?.progress ??
                              null}
                            highlightWindows={pattern.highlightWindows ?? []}
                            highlightMode={pattern.highlightMode ?? null}
                            selectionContext={pattern.selectionContext ?? null}
                          />
                        </div>
                        <div
                          style="
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            column-gap: 20px;
                            width: 100%;
                            margin-top: 8px;
                            align-items: start;
                          "
                        >
                          <div style="font-size: 13px;">
                            <div
                              class:dimmed={!isProgressChecked}
                              style="font-size: 13px; display: flex; align-items: center; gap: 8px;"
                            >
                              <input
                                type="checkbox"
                                bind:checked={isProgressChecked}
                              />
                              <span>Writing Progress</span>
                              <label
                                class="switch"
                                style="transform: translateY(4px); margin-left: auto;"
                                bind:this={exactProgressButton}
                              >
                                <input
                                  type="checkbox"
                                  bind:checked={isExactSearchProgress}
                                  disabled={!isProgressChecked}
                                />
                                <span class="slider">
                                  <span
                                    class="switch-text {isExactSearchProgress
                                      ? 'exact'
                                      : 'duration'}"
                                  >
                                    {isExactSearchProgress
                                      ? "Exact"
                                      : "Duration"}
                                  </span>
                                </span>
                              </label>
                            </div>

                            <div
                              class:dimmed={!isTimeChecked}
                              style="font-size: 13px; display: flex; align-items: center; gap: 8px;"
                            >
                              <input
                                type="checkbox"
                                bind:checked={isTimeChecked}
                              />
                              <span>Time</span>
                              <label
                                class="switch"
                                style="transform: translateY(4px); margin-left: auto;"
                                bind:this={exactTimeButton}
                              >
                                <input
                                  type="checkbox"
                                  bind:checked={isExactSearchTime}
                                  disabled={!isTimeChecked}
                                />
                                <span class="slider">
                                  <span
                                    class="switch-text {isExactSearchTime
                                      ? 'exact'
                                      : 'duration'}"
                                  >
                                    {isExactSearchTime ? "Exact" : "Duration"}
                                  </span>
                                </span>
                              </label>
                            </div>

                            <div
                              class:dimmed={!isSourceChecked}
                              style="font-size: 13px; display: flex; align-items: center; gap: 8px; white-space: nowrap;"
                            >
                              <input
                                type="checkbox"
                                bind:checked={isSourceChecked}
                              />
                              <span>Source (human/AI)</span>
                              <label
                                class="switch"
                                style="transform: translateY(4px); margin-left: auto;"
                                bind:this={exactSourceButton}
                              >
                                <input
                                  type="checkbox"
                                  bind:checked={isExactSearchSource}
                                  disabled={!isSourceChecked}
                                />
                              </label>
                            </div>
                          </div>

                          <div style="font-size: 13px;">
                            <div
                              class:dimmed={!isSemanticChecked}
                              style="display: flex; align-items: center; gap: 8px; white-space: nowrap; font-weight: 600; padding: 2px 4px; border-radius: 4px;"
                            >
                              <input
                                type="checkbox"
                                bind:checked={isSemanticChecked}
                              />
                              <span>Semantic Expansion</span>
                            </div>

                            <div
                              style="
                                margin: 0;
                                padding: 0px 10px;
                                border-left: 3px solid #dcdcdc;
                                background: rgba(0,0,0,0.03);
                                border-radius: 4px;
                              "
                            >
                              <div
                                class:dimmed={!isValueRangeChecked}
                                style="display: flex; align-items: center; gap: 8px; white-space: nowrap;"
                              >
                                <input
                                  type="checkbox"
                                  bind:checked={isValueRangeChecked}
                                  disabled={!isSemanticChecked}
                                />
                                <span>Value Range</span>
                              </div>

                              <div
                                class:dimmed={!isValueTrendChecked}
                                style="display: flex; align-items: center; gap: 8px; white-space: nowrap;"
                              >
                                <input
                                  type="checkbox"
                                  bind:checked={isValueTrendChecked}
                                  disabled={!isSemanticChecked}
                                />
                                <span>Value Trend</span>
                                <label
                                  class="switch"
                                  style="transform: translateY(4px); margin-left: auto;"
                                  bind:this={exactTrendButton}
                                >
                                  <input
                                    type="checkbox"
                                    bind:checked={isExactSearchTrend}
                                    disabled={!isSemanticChecked ||
                                      !isValueTrendChecked}
                                  />
                                </label>
                              </div>
                            </div>
                          </div>
                        </div>
                      {:else}
                        <!-- Progress/Bar modes: Show PatternChartPreview -->
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
                                <span
                                  class="switch-text {isExactSearchProgress
                                    ? 'exact'
                                    : 'duration'}"
                                >
                                  {isExactSearchProgress ? "Exact" : "Duration"}
                                </span>
                              </span>
                            </label>
                          </div>
                          <div
                            class:dimmed={!isTimeChecked}
                            style="font-size: 13px;"
                          >
                            <input
                              type="checkbox"
                              bind:checked={isTimeChecked}
                            />
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
                                <span
                                  class="switch-text {isExactSearchTime
                                    ? 'exact'
                                    : 'duration'}"
                                >
                                  {isExactSearchTime ? "Exact" : "Duration"}
                                </span>
                              </span>
                            </label>
                          </div>
                          <div
                            class:dimmed={!isSourceChecked}
                            style="font-size: 13px;"
                          >
                            <input
                              type="checkbox"
                              bind:checked={isSourceChecked}
                            />
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
                              <!-- <span class="slider">
                                <span class="switch-text">
                                  {isExactSearchSource ? "Exact" : "Proximity"}
                                </span>
                              </span> -->
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
                                  <!-- <span class="slider">
                                    <span class="switch-text">
                                      {isExactSearchTrend ? "Exact" : "Proximity"}
                                    </span>
                                  </span> -->
                                </label>
                              </div>
                            </div>
                          </div>
                        </div>
                      {/if}
                    </div>
                  {/if}
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
                                selectedTimeRange={sessionData.highlightRanges
                                  ?.time ?? null}
                                selectedProgressRange={sessionData
                                  .highlightRanges?.progress ?? null}
                                highlightWindows={sessionData.highlightRanges
                                  ?.windows ?? []}
                                highlightMode={sessionData.highlightRanges
                                  ?.mode ??
                                  resolveHighlightModeFromSource(
                                    searchDetail?.selectionSource ?? null
                                  )}
                                selectionContext={sessionData.highlightRanges
                                  ?.selectionContext ?? null}
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
                    <div
                      style="
                        display: flex;
                        align-items: center;
                        gap: 40px;
                        margin-top: 10px;
                        width: 100%;
                      "
                    >
                      <div class="loading-message" style="margin: 0;">
                        Searching for patterns...
                      </div>
                      {#if fetchProgress > 0}
                        <div
                          class="progress-container"
                          style="margin-top: 5px;"
                        >
                          <span style="font-size: 12px; top: 0%"
                            >{fetchProgress} %</span
                          >
                          <progress
                            value={fetchProgress}
                            max={100}
                            style="
                              width: 180px;
                              height: 15px;
                              border-radius: 15px;
                              --progHeight: 15px;
                            "
                          ></progress>
                        </div>
                      {/if}
                    </div>
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
    {#if showSavedMessage}
      <div class="saved-message">Saved successfully</div>
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
            <p>
              Want to use your own dataset?
              <a href=" " on:click={openDatasetHelp}> Check here!</a>
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
            {selectedDataset}
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
                      {@html getCategoryIconBase(
                        selectedCategoryFilter,
                        selectedDataset
                      )}
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
                          class:disabled={selectedCategoryFilter}
                          on:click={() => handleSort("topic")}
                          style="min-width: 70px;"
                        >
                          <span
                            style="cursor: {selectedCategoryFilter
                              ? 'default'
                              : 'pointer'};">Topic</span
                          >
                          <span
                            class="sort-icon"
                            style="cursor: {selectedCategoryFilter
                              ? 'default'
                              : 'pointer'};"
                            >{getSortIcon("topic")}
                          </span>
                        </th>
                        <th
                          class="sortable-header"
                          on:click={() => handleSort("score")}
                          style="min-width: 90px;"
                        >
                          <span style="cursor: pointer;">Score</span>
                          <span class="sort-icon" style="cursor: pointer;"
                            >{getSortIcon("score")}</span
                          >
                        </th>
                        {#if showPatternColumn}
                          <th
                            class="sortable-header"
                            on:click={() => handleSort("pattern")}
                            style="min-width: 100px;"
                          >
                            <span style="cursor: pointer;">Pattern</span>
                            <span class="sort-icon" style="cursor: pointer;"
                              >{getSortIcon("pattern")}</span
                            >
                          </th>
                        {/if}
                        <th>Activity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each selectedCategoryFilter ? sortedFilteredByCategory : filteredSessions as sessionData}
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
                            <span style="cursor: pointer;">Topic</span>
                            <span class="sort-icon" style="cursor: pointer;"
                              >{getSortIcon("topic")}</span
                            >
                          </th>
                          <th
                            class="sortable-header"
                            on:click={() => handleSort("score")}
                            style="min-width: 90px;"
                          >
                            <span style="cursor: pointer;">Score</span>
                            <span class="sort-icon" style="cursor: pointer;"
                              >{getSortIcon("score")}</span
                            >
                          </th>
                          {#if showPatternColumn}
                            <th
                              class="sortable-header"
                              on:click={() => handleSort("pattern")}
                              style="min-width: 100px;"
                            >
                              <span style="cursor: pointer;">Pattern</span>
                              <span class="sort-icon" style="cursor: pointer;"
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
                            ? `Suggestions: ${$clickSession.summaryData.totalSuggestions}`
                            : ""}
                        </div>
                      </div>
                    </div>
                    <div class="chart-container">
                      <div class="chart-wrapper" on:wheel={handleChartZoom}>
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
                            similarityData={$clickSession.similarityData}
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
                  <div class="content-box" style="height:65vh">
                    <div class="progress-container" style="width: 100%;">
                      <span style="width: 100%;"
                        >{($clickSession?.currentTime || 0).toFixed(2)} mins</span
                      >
                      <progress
                        style="width: 100%;"
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

  /* Search Box Styles */
  .search-input {
    transition: all 0.2s ease;
  }

  .search-input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1) !important;
  }

  .search-result-item:hover {
    background-color: #f8f9fa !important;
  }

  .search-result-item:last-child {
    border-bottom: none !important;
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

  .chart-container {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: visible;
  }

  .chart-wrapper {
    display: flex;
    align-items: flex-start;
    padding-right: 35px;
    transform: scale(1.25);
    transform-origin: center top;
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

  /* Large topic icon styling with dynamic colors */
  .category-icon-large :global(.topic-letters) {
    font-family:
      "Inter",
      "SF Pro Display",
      "Segoe UI",
      "Roboto",
      -apple-system,
      sans-serif;
    font-weight: 800;
    font-size: 24px;
    letter-spacing: 1px;

    /* Fallback color */
    color: var(--topic-color-primary, #667eea);

    /* Dynamic gradient text effect */
    background: linear-gradient(
      135deg,
      var(--topic-color-primary, #667eea) 0%,
      var(--topic-color-secondary, #764ba2) 100%
    );
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    /* Enhanced typography */
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;

    /* Enhanced shadow for large size using dynamic color */
    filter: drop-shadow(
      0 2px 6px
        color-mix(in srgb, var(--topic-color-primary, #667eea) 35%, transparent)
    );

    display: inline-block;
    transform: translateZ(0);
  }

  /* Export dropdown styles */
  .export-dropdown {
    position: relative;
    display: inline-block;
  }

  .export-menu {
    position: absolute;
    top: 100%;
    left: 0; /* 改为左对齐，避免超出屏幕 */
    background: white;
    border: 2px solid #007acc;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    z-index: 9999;
    min-width: 300px;
    max-width: 400px;
    margin-top: 8px;
    max-height: 400px;
    overflow-y: auto;
    background-color: #ffffff;
  }

  .export-option {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 16px 20px;
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s ease;
    border-radius: 0;
    color: #333;
  }

  .export-option:first-child {
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
  }

  .export-option:last-child {
    border-bottom-left-radius: 8px;
    border-bottom-right-radius: 8px;
  }

  .export-option:hover {
    background-color: #f5f5f5;
  }

  .export-divider {
    padding: 12px 20px;
    font-size: 12px;
    font-weight: 700;
    color: #666;
    background-color: #f9f9f9;
    border-top: 1px solid #eee;
    border-bottom: 1px solid #eee;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .pattern-export {
    font-size: 12px;
  }

  .pattern-color {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    display: inline-block;
    flex-shrink: 0;
    border: 1px solid rgba(0, 0, 0, 0.1);
  }

  .export-no-patterns {
    padding: 16px;
    color: #666;
    font-size: 12px;
    text-align: left;
    font-style: italic;
    border-top: 1px solid #eee;
  }

  .export-no-patterns small {
    color: #999;
    font-size: 10px;
    display: block;
    margin-top: 4px;
  }

  .other-dataset-pattern {
    display: block;
    margin-left: 8px;
    margin-top: 2px;
    color: #777;
  }

  .sortable-header.disabled {
    opacity: 0.6;
    pointer-events: none;
  }

  .sortable-header.disabled span {
    color: #999 !important;
  }
</style>
