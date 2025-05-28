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

  let chartRefs = {};
  function resetZoom(sessionId) {
    chartRefs[sessionId]?.resetZoom();
  }

  let filterButton;
  let collapseButton;
  let selectionMode = false;
  let selectedPatterns = {};
  let showPatternResults = false;
  let showPatternSearch = false;

  onMount(() => {
    if (filterButton) {
      tippy(filterButton, {
        content: "Click to filter based on prompt type",
        placement: "top",
      });
    }
    if (collapseButton) {
      tippy(collapseButton, {
        content: "Click to collapse/expand table view",
        placement: "top",
      });
    }
  });

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
  let selectedSession = [
    "e4611bd31b794677b02c52d5700b2e38",
    "233f1efcf0274acba92f46bf2f8766d2",
  ];
  let sessions = [];
  let time0 = null; // process bar's start time
  let time100 = null; // process bar's end time
  let endTime = null; // last paragraph time
  let isOpen = false;
  let showFilter = false;
  export const selectedTags = writable([]);
  let filterOptions = [];
  let showMulti = false;
  export const storeSessionData = writable([]);
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
  let patternDataList = [];
  export const initData = writable([]);

  async function handleContainerClick(event) {
    const sessionId = event.detail.sessionId;
    await fetchData(sessionId, false, true);
    try {
      const allSessions = get(storeSessionData);
      const data = allSessions.find((item) => item.sessionId === sessionId);
      if (data) {
        clickSession.set(data);
      }
    } catch (error) {
      console.error("Failed to fetch session data:", error);
    }
    showMulti = !showMulti;
  }

  let loadedMap = {
    e4611bd31b794677b02c52d5700b2e38: false,
    "233f1efcf0274acba92f46bf2f8766d2": false,
  };
  function syncLoadedMap(currentMap, sessionList) {
    const newMap = { ...currentMap };
    for (const s of sessionList) {
      if (!(s.sessionId in newMap)) {
        newMap[s.sessionId] = false;
      }
    }
    return newMap;
  }
  $: loadedMap = syncLoadedMap(loadedMap, $storeSessionData);
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
    const newSelectedPatterns = { ...selectedPatterns };
    delete newSelectedPatterns[sessionId];
    patternData = [];

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
      if (values[i] > values[i - 1]) pattern.push("up");
      else if (values[i] < values[i - 1]) pattern.push("down");
      else pattern.push("flat");
    }
    return pattern;
  }

  function matchesTrend(values, expectedTrend) {
    const actual = getTrendPattern(values);
    return actual.every((v, i) => v === expectedTrend[i]);
  }

  function findSegments(data, checks, minCount) {
    const segments = [];
    const sourceChecked = checks.source[0];
    const sourceOrder = checks.source[1];
    const trendChecked = checks.trend[0];
    const expectedTrend = checks.trend[1];
    const useSourceMatch =
      sourceChecked && Array.isArray(sourceOrder) && sourceOrder.length > 0;

    if (useSourceMatch) {
      const windowSize = sourceOrder.length;
      for (let i = 0; i <= data.length - windowSize; i++) {
        const window = data.slice(i, i + windowSize);
        const sources = window.map((d) => d.source);
        const allValid = window.every((d) => isDataValid(d, checks));
        if (!allValid) continue;
        if (sources.every((src, idx) => src === sourceOrder[idx])) {
          if (
            trendChecked &&
            expectedTrend &&
            expectedTrend.length === window.length - 1
          ) {
            const values = window.map((d) => d.residual_vector_norm);
            if (!matchesTrend(values, expectedTrend)) continue;
          }
          segments.push([...window]);
          i += windowSize - 1;
        }
      }
    } else {
      let currentSegment = [];
      for (const item of data) {
        if (isDataValid(item, checks)) {
          currentSegment.push(item);
        } else {
          if (currentSegment.length >= minCount) {
            if (
              trendChecked &&
              expectedTrend &&
              expectedTrend.length === currentSegment.length - 1
            ) {
              const values = currentSegment.map((d) => d.residual_vector_norm);
              if (matchesTrend(values, expectedTrend)) {
                segments.push([...currentSegment]);
              }
            } else if (!trendChecked) {
              segments.push([...currentSegment]);
            }
          }
          currentSegment = [];
        }
      }
      if (currentSegment.length >= minCount) {
        if (
          trendChecked &&
          expectedTrend &&
          expectedTrend.length === currentSegment.length - 1
        ) {
          const values = currentSegment.map((d) => d.residual_vector_norm);
          if (matchesTrend(values, expectedTrend)) {
            segments.push([...currentSegment]);
          }
        } else if (!trendChecked) {
          segments.push([...currentSegment]);
        }
      }
    }
    return segments;
  }

  function buildVectorFromSegment(segment, checks) {
    console.log("gayu segment", segment);
    console.log("gayu checks", checks);
    const vector = {
      x: [],
    };

    if (checks.source[0]) vector.s = [];
    if (checks.time[0]) vector.t = [];
    if (checks.progress[0]) vector.p = [];
    if (checks.trend[0]) vector.tr = [];
    if (checks.semantic[0]) vector.sem = [];

    for (let i = 0; i < segment.length; i++) {
      const item = segment[i];

      vector.x.push(item.x ?? 0);

      if (checks.source[0]) {
        const source = item.source?.toLowerCase();
        vector.s.push(source === "user" ? "H" : "A");
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
        const trendArray = checks.trend[1] || [];
        vector.tr.push(trendArray[i] ?? null);
      }
      if (checks.semantic[0]) {
        const semanticArray = checks.semantic[1] || [];
        vector.sem.push(semanticArray[i] ?? null);
      }
    }

    return vector;
  }

  async function searchPattern(sessionId) {
    const sessionData = selectedPatterns[sessionId];
    const count = sessionData.count;
    let results = [];
    let patternVectors = []; // ⬅️ NEW: store vectors
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
        const dataResponse = await fetch(
          `${base}/chi2022-coauthor-v1.0/similarity_results/${fileName}`
        );
        const data = await dataResponse.json();
        const segments = findSegments(data, checks, count);
        const extractedFileName = fileName
          .split(".")[0]
          .replace(/_similarity$/, "");

        const taggedSegments = segments.map((segment) =>
          segment.map((item) => ({ ...item, id: extractedFileName }))
        );

        for (const segment of taggedSegments) {
          const vector = buildVectorFromSegment(segment, checks);
          patternVectors.push(vector);
        }

        results.push(...taggedSegments);
      }

      patternData = results;
      patternDataLoad(results.slice(0, 3));

      // You can do something with patternVectors if needed
      console.log("Pattern Vectors:", patternVectors); // ⬅️ check output here
    } catch (error) {
      console.error("Search failed", error);
    }
  }

  async function patternDataLoad(results) {
    const ids = results.map((group) => group[0]?.id).filter(Boolean);
    const fetchPromises = ids.map((id) => fetchData(id, false, false));
    await Promise.all(fetchPromises);
    const sessionDataList = get(storeSessionData);
    patternDataList = results
      .map((group) => {
        const id = group[0]?.id;
        const sessionData = sessionDataList.find((s) => s.sessionId === id);
        if (sessionData) {
          return {
            ...sessionData,
            segments: group,
          };
        }
        return null;
      })
      .filter(Boolean);
  }

  function closePatternSearch() {
    showPatternSearch = false;
    selectionMode = false;

    Object.keys(selectedPatterns).forEach((sessionId) => {
      const chartRef = chartRefs[sessionId + "-barChart"];
      if (chartRef && chartRef.clearSelection) {
        chartRef.clearSelection();
      }
      resetTextHighlighting(sessionId);
    });

    selectedPatterns = {};
  }

  function getTrend(a, b) {
    if (a < b) return "up";
    if (a > b) return "down";
    return "flat";
  }

  function handleSelectionChanged(event) {
    const { sessionId, range, dataRange, data, sources } = event.detail;
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

    selectedPatterns[sessionId] = {
      range,
      dataRange,
      data,
      sources,
      scRange: `${range.sc.min.toFixed(1)} - ${range.sc.max.toFixed(1)}%`,
      progressRange: `${range.progress.min.toFixed(1)} - ${range.progress.max.toFixed(1)}%`,
      count: data.length,
    };

    highlightTextSegments(sessionId, data);
  }

  function handleSelectionCleared(event) {
    const { sessionId } = event.detail;

    if (selectedPatterns[sessionId]) {
      delete selectedPatterns[sessionId];
    }

    resetTextHighlighting(sessionId);
  }

  function scrollToSession(sessionId) {
    const sessionElement = document.getElementById(`summary-${sessionId}`);
    if (sessionElement) {
      sessionElement.scrollIntoView({ behavior: "smooth", block: "center" });

      sessionElement.classList.add("highlight-flash");
      setTimeout(() => {
        sessionElement.classList.remove("highlight-flash");
      }, 2000);
    }
  }

  function highlightTextSegments(sessionId, selectedData) {
    const sessionData = $storeSessionData.find(
      (s) => s.sessionId === sessionId
    );
    if (!sessionData || !sessionData.textElements) return;

    const textContainer = document.querySelector(`.text-container`);
    if (!textContainer) return;

    const textElements = textContainer.querySelectorAll(".text-span");

    textElements.forEach((el) => {
      el.classList.remove("highlighted-text");
    });

    const progressRanges = selectedData.map((d) => ({
      start: d.startProgress,
      end: d.endProgress,
    }));

    sessionData.textElements.forEach((element, index) => {
      if (!element) return;

      const elementProgress = element.progress * 100;
      if (!elementProgress) return;

      const isInSelectedRange = progressRanges.some(
        (range) =>
          elementProgress >= range.start && elementProgress <= range.end
      );

      if (isInSelectedRange && textElements[index]) {
        textElements[index].classList.add("highlighted-text");
      }
    });
  }

  function resetTextHighlighting(sessionId) {
    const textElements = document.querySelectorAll(".text-span");
    textElements.forEach((element) => {
      element.classList.remove("highlighted-text");
    });
  }

  function change2bar() {
    showMulti = !showMulti;

    setTimeout(() => {
      $storeSessionData.forEach((sessionData) => {
        if (sessionData.summaryData) {
          updateSessionSummary(
            sessionData.sessionId,
            sessionData.summaryData.totalProcessedCharacters,
            sessionData.summaryData.totalInsertions,
            sessionData.summaryData.totalDeletions,
            sessionData.summaryData.totalSuggestions
          );
        }
      });
    }, 0);
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
        // storeSessionData.update((sessionData) => {
        //   if (
        //     !sessionData.some(
        //       (session) => session.sessionId === newSession.session_id
        //     )
        //   ) {
        //     sessionData.push({
        //       sessionId: newSession.session_id,
        //     });
        //   }
        //   return sessionData;
        // });
        // await fetchData(newSession.session_id, false, true);
        await fetchInitData(newSession.session_id, false, true);
        // const similarityData = await fetchSimilarityData(newSession.session_id);
        // if (similarityData) {
        //   initData.update((sessions) => {
        //     if (!sessions.find(s => s.sessionId === newSession.session_id)) {
        //       sessions.push({
        //         sessionId: newSession.session_id,
        //         similarityData: similarityData,
        //         totalSimilarityData: similarityData,
        //       });
        //     }
        //     return [...sessions];
        //   });
        // }
      }
    } else {
      // storeSessionData.update((sessionData) => {
      //   return sessionData.filter(
      //     (session) =>
      //       !tableData.some(
      //         (item) =>
      //           item.prompt_code === tag &&
      //           item.session_id === session.sessionId
      //       )
      //   );
      // });
      const sessionsToRemove = tableData.filter(
        (item) => item.prompt_code === tag
      );
      for (const sessionToRemove of sessionsToRemove) {
        // await fetchData(sessionToRemove.session_id, true, true);
        await fetchInitData(sessionToRemove.session_id, true, true);
      }
    }

    const selectedSessions = get(storeSessionData);
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
          // await fetchData(session.session_id, false, true);
          await fetchInitData(session.session_id, false, true);
        }
      }
    } else {
      const allSessionsForTag = tableData.filter((item) =>
        selectedTagsList.includes(item.prompt_code)
      );
      for (const session of allSessionsForTag) {
        // await fetchData(session.session_id, false,true);
        await fetchInitData(session.session_id, false, true);
      }
    }
    updatePromptFilterStatus();
  }

  function filterSessions() {
    if ($selectedTags.length === 0) {
      filterTableData.set([]);
      storeSessionData.set([]);
    } else {
      const filteredData = tableData.filter((session) =>
        $selectedTags.includes(session.prompt_code)
      );
      const updatedData = filteredData.map((row) => ({
        ...row,
        selected:
          $storeSessionData.some((item) => item.sessionId == row.session_id) ||
          true,
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
    if (similarityData) {
      initData.update((sessions) => {
        if (!sessions.find((s) => s.sessionId === sessionId)) {
          sessions.push({
            sessionId,
            similarityData,
            totalSimilarityData: similarityData,
          });
        }
        return [...sessions];
      });
    }

    if (isPrompt) {
      updatePromptFilterStatus();
    }
  }

  const fetchData = async (sessionFile, isDelete, isPrompt) => {
    if (!firstSession && isDelete) {
      storeSessionData.update((data) => {
        return data.filter((item) => item.sessionId !== sessionFile);
      });
      return;
    }

    try {
      const response = await fetch(
        `${base}/chi2022-coauthor-v1.0/coauthor-json/${sessionFile}.jsonl`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }

      const data = await response.json();

      time0 = new Date(data.init_time);
      time100 = new Date(data.end_time);
      time100 = (time100 - time0) / (1000 * 60);
      currentTime = time100;

      dataDict = data;
      let sessionData = {
        sessionId: sessionFile,
        time0,
        time100,
        currentTime,
        chartData: [],
      };

      storeSessionData.update((sessions) => {
        let sessionIndex = sessions.findIndex(
          (s) => s.sessionId === sessionFile
        );
        if (sessionIndex !== -1) {
          sessions[sessionIndex] = {
            ...sessions[sessionIndex],
            time0,
            time100,
            currentTime,
            chartData: [],
          };
        } else {
          sessions.push(sessionData);
        }
        return [...sessions];
      });

      const { chartData, textElements, paragraphColor } = handleEvents(
        data,
        sessionFile
      );
      storeSessionData.update((sessions) => {
        let sessionIndex = sessions.findIndex(
          (s) => s.sessionId === sessionFile
        );
        if (sessionIndex !== -1) {
          sessions[sessionIndex].chartData = chartData;
          sessions[sessionIndex].textElements = textElements;
          sessions[sessionIndex].paragraphColor = paragraphColor;
        }
        return [...sessions];
      });

      const similarityData = await fetchSimilarityData(sessionFile);
      if (similarityData) {
        storeSessionData.update((sessions) => {
          let sessionIndex = sessions.findIndex(
            (s) => s.sessionId === sessionFile
          );
          if (sessionIndex !== -1) {
            sessions[sessionIndex].similarityData = similarityData;
            sessions[sessionIndex].totalSimilarityData = similarityData;
          }
          return [...sessions];
        });
      }
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
            selected:
              session.session_id === "e4611bd31b794677b02c52d5700b2e38" ||
              session.session_id === "233f1efcf0274acba92f46bf2f8766d2"
                ? true
                : false,
          };
        });
        firstSession = false;
        selectedTags.set(["reincarnation", "bee"]);
        filterSessions();
        $filterTableData = tableData.filter((session) =>
          $selectedTags.includes(session.prompt_code)
        );
        filterOptions = Array.from(
          new Set(tableData.map((row) => row.prompt_code))
        );
        updatePromptFilterStatus();
      }
    } catch (error) {
      console.error("Error when fetching sessions:", error);
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
        // fetchData(sessionId, false, true);
        fetchInitData(sessionId, false, true);
      }
    } else {
      // storeSessionData.update((data) => {
      //   return data.filter((item) => item.session_id !== sessionId);
      // });
      // fetchData(sessionId, true, true);
      fetchInitData(sessionId, true, true);
    }

    for (let i = 0; i < selectedSession.length; i++) {
      fetchSimilarityData(sessionId).then((similarityData) => {
        if (similarityData) {
          storeSessionData.update((sessions) => {
            let sessionIndex = sessions.findIndex(
              (s) => s.sessionId === selectedSession[i]
            );
            if (sessionIndex !== -1) {
              sessions[sessionIndex].similarityData = similarityData;
              sessions[sessionIndex].totalSimilarityData = similarityData;
            }
            return [...sessions];
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

  onMount(() => {
    document.title = "Ink-Pulse";
    fetchSessions();
    for (let i = 0; i < selectedSession.length; i++) {
      // fetchData(selectedSession[i], true, true);
      // fetchSimilarityData(selectedSession[i]).then((data) => {
      //   if (data) {
      //     storeSessionData.update((sessions) => {
      //       let sessionIndex = sessions.findIndex(
      //         (s) => s.sessionId === selectedSession[i]
      //       );
      //       if (sessionIndex !== -1) {
      //         sessions[sessionIndex].similarityData = data;
      //         sessions[sessionIndex].totalSimilarityData = data;
      //       }
      //       return [...sessions];
      //     });
      //   }
      // });
      fetchSimilarityData(selectedSession[i]).then((data) => {
        initData.update((sessions) => {
          const newSession = {
            sessionId: selectedSession[i],
            similarityData: data,
            totalSimilarityData: data,
          };
          sessions.push(newSession);
          return [...sessions];
        });
      });
    }
  });

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

  const handleEvents = (data, sessionId) => {
    let initText = data.init_text.join("");
    let currentText = initText;
    let currentColor = [];
    let wholeText = data.text[0];
    wholeText = wholeText.slice(0, -1);
    chartData = [];
    paragraphColor = [];
    let firstTime = null;
    let indexOfAct = 0;

    let totalInsertions = 0;
    let totalDeletions = 0;
    let totalSuggestions = 0;
    let totalInsertionTime = 0;
    let totalDeletionTime = 0;
    let totalSuggestionTime = 0;
    let totalProcessedCharacters = data.text[0].length;

    let combinedText = data.info.reduce((acc, event) => {
      if (acc.length === 0) {
        for (let i = 0; i < initText.length; i++) {
          // init text's color should be the same as api insert
          acc.push({ text: initText[i], textColor: "#FC8D62" });
          currentColor.push("#FC8D62");
        }
      }
      const { name, text, eventSource, event_time, count, pos } = event;
      const textColor = eventSource === "user" ? "#66C2A5" : "#FC8D62"; // api and user insert color setting
      const eventTime = new Date(event_time);
      if (firstTime === null) {
        firstTime = eventTime;
        paragraphTime.push({ time: 0, pos: 0 });
      }
      const relativeTime = (eventTime - firstTime) / (1000 * 60); // convert time into easy format

      if (name === "text-insert") {
        // check whether insert a sentence or a character, divede into characters if it is a sentence
        if (pos === currentText.length) {
          // inset chracter/sentence at the end of the text
          currentText += text;
          for (let i = 0; i < text.length; i++) {
            acc.push({ text: text[i], textColor: textColor });
            currentColor.push(textColor);
          }
        } else {
          currentText =
            currentText.slice(0, pos) + text + currentText.slice(pos);
          for (let i = 0; i < text.length; i++) {
            acc.splice(pos + i, 0, {
              text: text[i],
              textColor: textColor,
            });
            currentColor.splice(pos + i, 0, textColor);
          }
        }
      } else if (name === "text-delete") {
        // also check delete number
        currentText =
          currentText.slice(0, pos) + currentText.slice(pos + count);
        let remainingCount = count;
        let index = pos;
        while (remainingCount > 0 && index < acc.length) {
          if (acc[index].text.length <= remainingCount) {
            remainingCount -= acc[index].text.length;
            acc.splice(index, 1);
            currentColor.splice(index, 1);
          } else {
            acc[index].text = acc[index].text.slice(remainingCount);
            currentColor[index] = currentColor[index].slice(remainingCount);
            remainingCount = 0;
          }
        }
      }

      const percentage = (currentText.length / wholeText.length) * 100;
      endTime = relativeTime;

      if (name === "suggestion-open") {
        // use isSuggestionOpen to filter specific data
        chartData.push({
          time: relativeTime,
          percentage: percentage,
          eventSource,
          color: textColor,
          currentText,
          currentColor: [...currentColor],
          opacity: 1,
          isSuggestionOpen: true,
          index: indexOfAct,
        });
      } else {
        chartData.push({
          time: relativeTime,
          percentage: percentage,
          eventSource,
          color: textColor,
          currentText,
          currentColor: [...currentColor],
          opacity: 1,
          index: indexOfAct,
        });
      }
      indexOfAct += 1;

      if (name === "text-insert") {
        totalInsertions++;
        totalInsertionTime += relativeTime;
      } else if (name === "text-delete") {
        totalDeletions++;
        totalDeletionTime += relativeTime;
      } else if (name === "suggestion-open") {
        totalSuggestions++;
        totalSuggestionTime += relativeTime;
      }

      return acc;
    }, []);

    paragraphTime = adjustTime(currentText, chartData);

    for (let i = 0; i < paragraphTime.length - 1; i++) {
      const startTime = paragraphTime[i].time;
      const endTime = paragraphTime[i + 1].time;
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

    combinedText = combinedText.slice(0, -1); // delete last "\n"
    textElements = combinedText;
    chartData = chartData.slice(0, -1); // delete last "\n"
    chartData[0].isSuggestionOpen = false; // change the init api insert into false so not show in the chart
    // calculateSessionAnalytics(data, sessionId);
    storeSessionData.update((sessions) => {
      const idx = sessions.findIndex((s) => s.sessionId === sessionId);
      if (idx !== -1) {
        sessions[idx].summaryData = {
          totalProcessedCharacters,
          totalInsertions,
          totalDeletions,
          totalSuggestions,
        };
      }
      return [...sessions];
    });

    updateSessionSummary(
      sessionId,
      totalProcessedCharacters,
      totalInsertions,
      totalDeletions,
      totalSuggestions
    );

    return {
      chartData,
      textElements,
      paragraphColor,
    };
  };

  const updateSessionSummary = (
    sessionId,
    totalProcessedCharacters,
    totalInsertions,
    totalDeletions,
    totalSuggestions
  ) => {
    const sessionSummaryContainer = document.getElementById(
      `summary-${sessionId}`
    );

    if (!sessionSummaryContainer) {
      console.error(`Summary container for session ${sessionId} not found`);
      return;
    }

    sessionSummaryContainer.querySelector(".totalText").textContent =
      `Total Text: ${totalProcessedCharacters} characters`;
    sessionSummaryContainer.querySelector(".totalInsertions").textContent =
      `Insertions: ${totalInsertions}`;
    sessionSummaryContainer.querySelector(".totalDeletions").textContent =
      `Deletions: ${totalDeletions}`;
    sessionSummaryContainer.querySelector(".totalSuggestions").textContent =
      `Suggestions: ${totalSuggestions - 1}`;
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
      <div class="chart-explanation">
        <span class="triangle-text">▼</span> user open the AI suggestion
        <span class="user-line">●</span> User written
        <span class="api-line">●</span> AI writing
      </div>
      <a
        on:click={change2bar}
        href=" "
        aria-label="Change2Bar"
        class="material-symbols--restart-alt-rounded"
      ></a>
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
                    <h5>Session: {sessionId}</h5>
                    <div class="pattern-buttons">
                      <button
                        class="view-pattern-button"
                        on:click={() => scrollToSession(sessionId)}>View</button
                      >
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
                  <div class="pattern-chart-preview small-preview">
                    <PatternChartPreview
                      {sessionId}
                      data={pattern.data}
                      selectedRange={pattern.range}
                      bind:this={chartRefs[sessionId]}
                    />
                  </div>
                  <div
                    class:dimmed={!isProgressChecked}
                    style="display: flex; align-items: center; font-size: 13px;"
                  >
                    <input type="checkbox" bind:checked={isProgressChecked} />
                    Writing Progress
                    <div style="flex: 1;"></div>
                    <RangeSlider
                      class="rangeSlider"
                      min={0}
                      max={100}
                      bind:values={writingProgressRange}
                    />
                    <div
                      style="font-size: 12px; margin-top: 4px; text-align: right;"
                    >
                      Selected: {writingProgressRange[0]}% – {writingProgressRange[1]}%
                    </div>
                  </div>
                  <div
                    class:dimmed={!isTimeChecked}
                    style="display: flex; align-items: center; font-size: 13px;"
                  >
                    <input type="checkbox" bind:checked={isTimeChecked} />
                    Time
                    <div style="flex: 1;"></div>
                    <RangeSlider
                      class="rangeSlider"
                      min={0}
                      max={$clickSession?.time100}
                      bind:values={timeRange}
                    />
                    <div
                      style="font-size: 12px; margin-top: 4px; text-align: right;"
                    >
                      Selected: {timeRange[0]} – {timeRange[1]}
                    </div>
                  </div>
                  <div class:dimmed={!isSourceChecked} style="font-size: 13px;">
                    <input type="checkbox" bind:checked={isSourceChecked} />
                    Source(human/AI)
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
                      </div>
                    </div>
                  </div>
                  {#if patternDataList.length > 0}
                    {#each patternDataList as sessionData}
                      <div class="chart-container">
                        <div style="font-size: 13px; margin-bottom: 4px;">
                          <strong>{sessionData.sessionId}</strong>
                        </div>
                        <div class="chart-wrapper">
                          <PatternChartPreviewSerach
                            sessionId={sessionData.sessionId}
                            data={sessionData.segments}
                          />
                          <!-- <div>
                              <LineChart
                                bind:this={chartRefs[sessionData.sessionId]}
                                chartData={sessionData.chartData}
                                paragraphColor={sessionData.paragraphColor}
                                on:pointSelected={(e) => handlePointSelected(e, sessionData.sessionId)}
                                {yScale}
                                {height}
                                bind:zoomTransform={zoomTransforms[sessionData.sessionId]}
                              />
                            </div> -->
                        </div>
                      </div>
                    {/each}
                  {:else}
                    <div class="no-data-message">
                      No data found matching the search criteria.
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
      {#if !showMulti}
        <div style="margin-top: 100px;">
          {#if $initData.length > 0}
            {#each $initData as sessionData (sessionData.sessionId)}
              <div class="zoomout-chart">
                <ZoomoutChart
                  on:containerClick={handleContainerClick}
                  bind:this={chartRefs[sessionData.sessionId]}
                  sessionId={sessionData.sessionId}
                  sessionTopic={sessions.find(
                    (s) => s.session_id === sessionData.sessionId
                  ).prompt_code}
                  similarityData={sessionData.similarityData}
                />
              </div>
            {/each}
          {/if}
        </div>
      {/if}
      {#if showMulti}
        {#if $clickSession}
          <div class="multi-box">
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
                <div class="chart-container">
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
                        on:selectionChanged={handleSelectionChanged}
                        on:selectionCleared={handleSelectionCleared}
                        bind:this={
                          chartRefs[$clickSession.sessionId + "-barChart"]
                        }
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
                        bind:zoomTransform={
                          zoomTransforms[$clickSession.sessionId]
                        }
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
    max-width: 1200px;
    margin: 0 auto;
    margin-top: 70px;
    margin-bottom: 70px;
  }

  .multi-box {
    display: flex;
    flex-direction: column;
    gap: 20px;
    align-items: stretch;
    width: 100%;
  }

  .display-box {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    gap: 20px;
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
    left: 930px;
    background: white;
    border: 1px solid #ccc;
    padding: 12px;
    display: none;
    box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
    width: 200px;
    text-align: left;
    border-radius: 8px;
  }

  .filter-container-close {
    position: absolute;
    top: 370px;
    left: 930px;
    background: white;
    border: 1px solid #ccc;
    padding: 12px;
    display: none;
    box-shadow: 0 3px 5px rgba(0, 0, 0, 0.1);
    width: 200px;
    text-align: left;
    border-radius: 8px;
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
    background-color: #86cecb;
    border-color: #86cecb;
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
    margin-left: 300px;
    height: 30px;
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
    width: 380px;
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
    font-size: 14px;
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
    width: 60%;
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

  .dimmed {
    color: #5f6368;
  }
</style>
