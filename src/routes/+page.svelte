<script>
  import { onMount } from "svelte";
  import {
    Chart,
    TimeScale,
    LineController,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarController,
    BarElement,
  } from "chart.js";
  import { Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell } from 'flowbite-svelte';
  import "chartjs-adapter-date-fns";
  import annotationPlugin from "chartjs-plugin-annotation";
  import { writable } from "svelte/store";
  import { tick } from "svelte";
  import { base } from "$app/paths";
  import tippy from "tippy.js";
  import "tippy.js/dist/tippy.css";
  import 'flowbite/dist/flowbite.min.css';

  Chart.register(
    TimeScale,
    LineController,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    CategoryScale,
    BarController,
    LinearScale,
    annotationPlugin,
    BarElement
  );

  let zoomPlugin;
  let filterButton;
  let multiSessionButton;
  let collapseButton;

  onMount(() => {
    if (filterButton) {
      tippy(filterButton, {
        content: "Click to filter based on prompt type",
        placement: "top",
      });
    }
    if (multiSessionButton) {
      tippy(multiSessionButton, {
        content: "Click to enable/disable multi session view",
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

  onMount(async () => {
    const module = await import("chartjs-plugin-zoom");
    zoomPlugin = module.default;
    Chart.register(zoomPlugin);
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
  let selectedSession = "0c7bfadbd8db49b4b793e2a46e581759";
  let sessions = [];
  let chart = null;
  let time0 = null; // process bar's start time
  let time100 = null; // process bar's end time
  let endTime = null; // last paragraph time
  let isOpen = false;
  let showFilter = false;
  let tags = [
    "shapeshifter",
    "reincarnation",
    "mana",
    "obama",
    "pig",
    "mattdamon",
    "dad",
    "isolation",
    "bee",
    "sideeffect",
  ];
  let selectedTags = new Set(tags);
  let filterOptions = [
    "shapeshifter",
    "reincarnation",
    "mana",
    "obama",
    "pig",
    "mattdamon",
    "dad",
    "isolation",
    "bee",
    "sideeffect",
  ];
  let isAllSelected = true;
  let showMulti = false;
  export const storeSessionData = writable([]);
  let tableData = [];
  let firstSession = true;
  let filterTableData = [];
  let isCollapsed = false;

  function open2close() {
    isOpen = !isOpen;
  }

  function toggleTag(event) {
    const tag = event.target.value;
    if (event.target.checked) {
      selectedTags.add(tag);
    } else {
      selectedTags.delete(tag);
    }
    isAllSelected = selectedTags.size === tags.length;
    filterSessions();
  }

  function filterSessions() {
    filterTableData = tableData.filter(
      (session) =>
        selectedTags.size === 0 || selectedTags.has(session.prompt_code)
    );
  }

  function toggleSelectAll() {

    if (selectedTags.size !== 0) {
      selectedTags.clear();
      selectedTags = new Set([...selectedTags]);
    } else {
      filterOptions.forEach(option => {
        selectedTags.add(option);
      });
      selectedTags = new Set([...selectedTags]);
    }
  }

  function toggleTableCollapse() {
    isCollapsed = !isCollapsed;
  }

  function resetDisplay() {
    storeSessionData.set([]);
    filterTableData = tableData.map(session => {
      return {
        session_id: session.session_id,
        prompt_code: session.prompt_code,
        selected: false
      };
    });
  }

  const toggleFilter = () => {
    showFilter = !showFilter;
  };

  const toggleMulti = () => {
    // when change the display destory all
    resetDisplay();
    showMulti = !showMulti;
  };

  const fetchData = async (sessionFile, isDelete) => {
    if (!firstSession && isDelete) {
      storeSessionData.update(data => {
        return data.filter(item => item.sessionId !== sessionFile);
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

      const progressElement = document.querySelector("progress");
      if (progressElement) {
        // at first let the max time = end time, the init time = end time
        progressElement.max = time100;
        progressElement.value = currentTime;
      }

      if (!showMulti) {
        dataDict = data;
        let sessionData = {
          sessionId: sessionFile,
          time0,
          time100,
          currentTime,
          chartData: [],
        };
        storeSessionData.set([sessionData]);
        await tick(); // wait for storeSessionData update

        const { chartData, textElements } = handleEvents(data, sessionFile);
        storeSessionData.update((sessions) => {
          let sessionIndex = sessions.findIndex(
            (s) => s.sessionId === sessionFile
          );
          if (sessionIndex !== -1) {
            sessions[sessionIndex].chartData = chartData;
            sessions[sessionIndex].textElements = textElements;
          }
          return [...sessions];
        });
        await tick();
        renderChart(sessionFile); // Ensure this function is correctly updating and re-rendering the chart
      }
      if (showMulti) {
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

        await tick();
        const { chartData, textElements } = handleEvents(data, sessionFile);
        storeSessionData.update((sessions) => {
          let sessionIndex = sessions.findIndex(
            (s) => s.sessionId === sessionFile
          );
          if (sessionIndex !== -1) {
            sessions[sessionIndex].chartData = chartData;
            sessions[sessionIndex].textElements = textElements;
          }
          return [...sessions];
        });

        await tick();
        renderChart(sessionFile);
      }
    } catch (error) {
      console.error("Error when reading the data file:", error);
    }
  };

  const fetchSimilarityData = async (sessionFile) => {
    try {
      const response = await fetch(
        `${base}/similarity_results/${sessionFile}_similarity.json`
      );
      if (!response.ok) {
        throw new Error(`Failed to fetch session data: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error when reading the data file:", error);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${base}/fine.json`);
      const data = await response.json();
      sessions = data || [];
      if (firstSession) {
        tableData = sessions.map(session => {
          return {
            session_id: session.session_id,
            prompt_code: session.prompt_code,
            selected: session.session_id === "0c7bfadbd8db49b4b793e2a46e581759" ? true : false
          };
        });
        firstSession = false;
        filterTableData = tableData;
      }
      // fetchSessions()
    } catch (error) {
      console.error("Error when fetching sessions:", error);
    }
  };

  const handleSessionChange = (sessionId) => {
    let isCurrentlySelected = filterTableData.find(row => row.session_id == sessionId)?.selected;

    if (!showMulti) {
      if (isCurrentlySelected) {
        selectedSession = null;
        filterTableData = filterTableData.map(row => ({ ...row, selected: false }));
        storeSessionData.update(data => {
          return data.filter(item => item.session_id !== sessionId);
        });
        fetchData(sessionId, true);
      } else {
        selectedSession = sessionId;
        filterTableData = filterTableData.map(row => ({
          ...row,
          selected: row.session_id == selectedSession
        }));
        fetchData(sessionId, false);
      }
    } else {
      filterTableData = filterTableData.map(row => {
        if (row.session_id == sessionId) {
          return { ...row, selected: !row.selected };
        }
        return row;
      });

      if (!isCurrentlySelected) {
        selectedSession = sessionId;
        fetchData(sessionId, false);
      } else {
        storeSessionData.update(data => {
          return data.filter(item => item.session_id !== sessionId);
        });
        fetchData(sessionId, true);
      }
    }

    paragraphTime = [];
    paragraphColor = [];
      
    // fetchSimilarityData(selectedSession).then((data) => {
    //   renderSimilarityChart(selectedSession, data);
    // });
  };

  function handleSelectChange(index) {
    handleSessionChange(sessions[index].session_id);
  }

  onMount(() => {
    document.title = "Ink-Pulse";
    fetchSessions();
    if (selectedSession) {
      fetchData(selectedSession, true);
    }
    // fetchSimilarityData(selectedSession).then((data) => {
    //   renderSimilarityChart(selectedSession, data);
    // });
  });

  function generateColor(index) {
    const colors = [
      "rgba(211, 179, 255, 0.2)",
      "rgba(255, 183, 77, 0.2)",
      "rgba(179, 217, 255, 0.2)",
      "rgba(179, 255, 179, 0.2)",
      "rgba(255, 217, 179, 0.2)",
    ];
    return colors[index % colors.length];
  }

  function generateColorGrey(index) {
    const colors = ["rgba(220, 220, 220, 0.3)", "rgba(240, 240, 240, 0.3)"];
    return colors[index % colors.length];
  }

  function adjustTime(paragraphTime, currentText, chartData) {
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
    let firstTime = null;
    let preEvent = null;

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
          currentColor,
          isSuggestionOpen: true,
        });
      } else {
        chartData.push({
          time: relativeTime,
          percentage: percentage,
          eventSource,
          color: textColor,
          currentText,
          currentColor,
        });
      }
      preEvent = event;

      return acc;
    }, []);

    paragraphTime = adjustTime(paragraphTime, currentText, chartData);

    const customLabelPlugin = {
      id: "customLabel",
      afterDatasetsDraw(chart) {
        const ctx = chart.ctx;

        paragraphColor.forEach((box) => {
          const { xMin, xMax, yMin, yMax, value } = box;

          if (
            value &&
            xMin !== undefined &&
            xMax !== undefined &&
            yMin !== undefined &&
            yMax !== undefined
          ) {
            const xPosition =
              (chart.scales["x"].getPixelForValue(xMin) +
                chart.scales["x"].getPixelForValue(xMax)) /
              2;

            const yPosition = chart.scales["y"].getPixelForValue(yMax) - 5;

            ctx.fillStyle = "black";
            ctx.font = "12px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "bottom";

            ctx.fillText(value, xPosition, yPosition);
          }
        });
      },
    };
    Chart.register(customLabelPlugin);

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
    calculateSessionAnalytics(data, sessionId);

    return {
      chartData,
      textElements,
    };
  };

  const calculateSessionAnalytics = (data, sessionId) => {
    let totalInsertions = 0;
    let totalDeletions = 0;
    let totalSuggestions = 0;
    let totalInsertionTime = 0;
    let totalDeletionTime = 0;
    let totalSuggestionTime = 0;
    let totalProcessedCharacters = data.text[0].length;

    data.info.forEach((event) => {
      const { name, event_time } = event;
      const eventTime = new Date(event_time);
      const relativeTime =
        (eventTime - new Date(data.info[0].event_time)) / (1000 * 60); // in minutes

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
    });

    updateSessionSummary(
      sessionId,
      totalProcessedCharacters,
      totalInsertions,
      totalDeletions,
      totalSuggestions
    );
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
    if (!sessionSummaryContainer) return;

    sessionSummaryContainer.querySelector(".totalText").textContent =
      `Total Text: ${totalProcessedCharacters} characters`;
    sessionSummaryContainer.querySelector(".totalInsertions").textContent =
      `Insertions: ${totalInsertions}`;
    sessionSummaryContainer.querySelector(".totalDeletions").textContent =
      `Deletions: ${totalDeletions}`;
    sessionSummaryContainer.querySelector(".totalSuggestions").textContent =
      `Suggestions: ${totalSuggestions - 1}`;
  };

  function resetZoom() {
    if (chart) {
      chart.resetZoom();
    }
  }

  const renderChart = (sessionId) => {
    if (!showMulti) {
      if (chart) {
        chart.destroy();
      }
    }
    storeSessionData.update((sessions) => {
      let sessionIndex = sessions.findIndex((s) => s.sessionId == sessionId);
      if (sessionIndex === -1) return sessions; // check whether empty

      let session = sessions[sessionIndex];

      const lineChart = document
        .getElementById(`chart-${sessionId}`)
        .getContext("2d");
      const processedData = session.chartData.map((data, index) => {
        if (
          index > 0 &&
          session.chartData[index - 1].percentage === data.percentage
        ) {
          return { x: data.time, y: null };
        }
        if (
          index > 0 &&
          session.chartData[index - 1].eventSource === "api" &&
          session.chartData[index].eventSource === "user"
        ) {
          return { x: data.time, y: null };
        }
        if (
          index > 0 &&
          session.chartData[index - 1].eventSource === "user" &&
          session.chartData[index].eventSource === "user" &&
          session.chartData[index].time - session.chartData[index - 1].time >
            0.3
        ) {
          return { x: data.time, y: null };
        }

        return { x: data.time, y: data.percentage };
      });

      let selectPoint = null;
      chart = new Chart(lineChart, {
        type: "line",
        data: {
          labels: session.chartData.map((data) => data.time.toFixed(2)),
          datasets: [
            {
              label: "process",
              data: processedData,
              borderColor: session.chartData.map((data) => data.color),
              backgroundColor: "transparent",
              segment: {
                borderColor: (lineChart) =>
                  session.chartData[lineChart.p1DataIndex].color,
              },
              tension: 0.1,
            },
          ],
        },
        options: {
          interaction: {
            mode: "nearest",
            intersect: true,
          },
          onClick: (event, chartElements) => {
            if (chartElements.length > 0) {
              const index = chartElements[0].index;
              if (selectPoint !== index) {
                selectPoint = index;
                chart.update();
              }
            }
          },
          plugins: {
            legend: {
              display: false,
            },
            zoom: {
              pan: {
                enabled: true,
                mode: "xy",
              },
              zoom: {
                wheel: {
                  enabled: true, // Enable zooming with mouse wheel
                },
                pinch: {
                  enabled: true, // Enable zooming with pinch gestures
                },
                mode: "xy",
              },
              limits: {
                x: {
                  min: "original",
                  max: 100,
                  minRange: 20,
                },
                y: {
                  min: 0,
                  max: 100,
                  minRange: 20,
                },
              },
            },
            tooltip: {
              enabled: true,
              mode: "nearest",
              intersect: true,
              callbacks: {
                title: (tooltipItems) => {
                  const data = session.chartData[tooltipItems[0].dataIndex];
                  return `Time: ${data.time.toFixed(2)} mins`;
                },
                label: (tooltipItem) => {
                  const data = session.chartData[tooltipItem.dataIndex];
                  const eventType =
                    data.eventSource === "user" ? "User" : "API";
                  return `Progress: ${data.percentage.toFixed(2)}% | Event: ${data.eventSource}`;
                },
              },
            },
            annotation: {
              annotations: [
                ...paragraphColor,
                ...session.chartData
                  .filter((data) => data.isSuggestionOpen)
                  .map((data) => ({
                    type: "point",
                    pointStyle: "triangle",
                    rotation: 180,
                    xMax: data.time,
                    xMin: data.time,
                    yMin: data.percentage + 1,
                    yMax: data.percentage + 5,
                    borderColor: "#FFB6B3",
                    borderWidth: 1,
                    radius: 3,
                    backgroundColor: "#FFB6B3",
                    interactive: true,
                  })),
              ],
            },
          },
          elements: {
            point: {
              radius: (context) => {
                if (selectPoint !== null && context.dataIndex === selectPoint) {
                  return 8;
                }
                return 1;
              },
              hoverRadius: 8,
              hoverBackgroundColor: "rgba(255, 99, 132, 0.8)",
              hoverBorderColor: "rgba(255, 99, 132, 1)",
            },
          },
          scales: {
            x: {
              type: "linear",
              title: {
                display: true,
                text: "Time (mins)",
              },
              ticks: {
                stepSize: 1,
              },
              grid: {
                display: false,
              },
            },
            y: {
              min: 0,
              max: 100,
              offset: true,
              title: {
                display: true,
                text: "Process(%)",
              },
              ticks: {
                stepSize: 10,
              },
              grid: {
                display: false,
              },
            },
          },
        },
      });
      lineChart.canvas.addEventListener("click", (event) => {
        const points = chart.getElementsAtEventForMode(
          event,
          "nearest",
          { intersect: true },
          true
        );
        if (points.length > 0) {
          const point = points[0];
          const data = session.chartData[point.index];

          textElements = data.currentText.split("").map((char, index) => ({
            text: char,
            textColor: data.currentColor[index],
          }));
          currentTime = data.time;
          storeSessionData.update((sessions) => {
            let sessionIndex = sessions.findIndex(
              (s) => s.sessionId === sessionId
            );
            if (sessionIndex !== -1) {
              sessions[sessionIndex].textElements = data.currentText
                .split("")
                .map((char, index) => ({
                  text: char,
                  textColor: data.currentColor[index],
                }));
              sessions[sessionIndex].currentTime = data.time;
            }
            return [...sessions];
          });
        }
      });
      return sessions;
    });
  };
</script>

<div class="App">
  <header class="App-header">
    <nav>
      <div class="filter-container {showFilter ? 'show' : ''}">
        <a
          on:click={toggleSelectAll}
          href=" "
          aria-label="toggle-btn"
          class="material-symbols--refresh-rounded"
        >
          {isAllSelected ? "Clear All" : "Select All"}
        </a>
        {#each filterOptions as option}
          <label>
            <input
              type="checkbox"
              value={option}
              on:change={toggleTag}
              checked={selectedTags.has(option)}
            />
            {option}
          </label>
          <br />
        {/each}
      </div>
      <!-- <div class="dropdown-container">
        <b>Select Session: &nbsp;</b>
        <select bind:value={selectedSession} on:change={handleSessionChange}>
          {#each filterTableData.length > 0 ? filterTableData : sessions as session}
            <option value={session.session_id}>
              {session.prompt_code} - {session.session_id}
            </option>
          {/each}
        </select>
      </div> -->
      <div>
        <a
          bind:this={multiSessionButton}
          on:click={toggleMulti}
          href=" "
          aria-label="multiple-session"
          class={showMulti
            ? "material-symbols--stack-rounded"
            : "material-symbols--stack-off-rounded"}
        >
        </a>
      </div>
      <div class="chart-explanation">
          <span class="triangle-text">▼</span> user open the AI suggestion
          <span class="user-line">●</span> User written
          <span class="api-line">●</span> AI writing
      </div>
      <a
        on:click={open2close}
        href=" "
        aria-label="Instruction"
        class="material-symbols--info-outline-rounded"
      ></a>
    </nav>
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
      {#if !showMulti && $storeSessionData.length > 0}
        <div class="display-box">
          <div class="content-box">
              <div
                class="session-summary"
                id="summary-{$storeSessionData[0].sessionId}"
              >
                <h3>Session Summary</h3>
                <div class="summary-container">
                  <div class="totalText"></div>
                  <div class="totalInsertions"></div>
                  <div class="totalDeletions"></div>
                  <div class="totalSuggestions"></div>
                </div>
              </div>
            <div class="chart-container">
              <canvas id="chart-{$storeSessionData[0].sessionId}"></canvas>
            </div>
            <!--<div class="chart-container">
              <canvas id="similarity-chart-{$storeSessionData[0].sessionId}"
              ></canvas>
            </div> -->

            <button on:click={resetZoom} class="zoom-reset-btn"
              >Reset Zoom</button
            >
          </div>
          <div class="content-box">
            <div class="progress-container">
              <span
                >{($storeSessionData[0]?.currentTime || 0).toFixed(2)} mins</span
              >
              <progress
                value={$storeSessionData[0]?.currentTime || 0}
                max={$storeSessionData[0]?.time100 || 1}
              ></progress>
            </div>
            <div class="scale-container">
              <div class="scale" id="scale"></div>
            </div>
            <div class="text-container">
              {#if $storeSessionData[0].textElements && $storeSessionData[0].textElements.length > 0}
                {#if $storeSessionData[0].textElements[0].text !== "\n"}
                  <span
                    class="text-span"
                    style="color: black; font-weight: normal;"
                  >
                    1.
                  </span>
                {/if}
                {#each $storeSessionData[0].textElements as element, index}
                  {#if element.text === "\n" && index + 1 < $storeSessionData[0].textElements.length}
                    <br />
                    {#if index + 1 < $storeSessionData[0].textElements.length && $storeSessionData[0].textElements[index + 1].text === "\n"}{:else if index > 0 && $storeSessionData[0].textElements[index - 1].text === "\n"}
                      <span
                        class="text-span"
                        style="color: black; font-weight: normal;"
                      >
                        {(() => {
                          let count =
                            $storeSessionData[0].textElements[0].text !== "\n"
                              ? 1
                              : 0;
                          for (let i = 0; i < index; i++) {
                            if (
                              $storeSessionData[0].textElements[i].text ===
                                "\n" &&
                              i > 0 &&
                              $storeSessionData[0].textElements[i - 1].text ===
                                "\n"
                            ) {
                              count++;
                            }
                          }
                          return count + 1;
                        })()}.
                      </span>
                    {/if}
                  {:else}
                    <span class="text-span" style="color: {element.textColor}">
                      {element.text}
                    </span>
                  {/if}
                {/each}
              {/if}
            </div>
          </div>
        </div>
      {/if}

      {#if showMulti && $storeSessionData.length > 0}
        <div class="multi-box">
          {#each $storeSessionData as sessionData (sessionData.sessionId)}
            <div class="display-box">
              <div class="content-box">
                <div class="session-identifier">
                  <h3>
                    {#if sessions && sessions.find((s) => s.session_id === sessionData.sessionId)}
                      {sessions.find(
                        (s) => s.session_id === sessionData.sessionId
                      ).prompt_code} - {sessionData.sessionId}
                    {:else}
                      Session: {sessionData.sessionId}
                    {/if}
                  </h3>
                </div>
                <div
                  class="session-summary"
                  id="summary-{$storeSessionData[0].sessionId}"
                >
                  <h3>Session Summary</h3>
                  <div class="summary-container">
                    <div class="totalText"></div>
                    <div class="totalInsertions"></div>
                    <div class="totalDeletions"></div>
                    <div class="totalSuggestions"></div>
                  </div>
                </div>
                <div class="chart-container">
                  <canvas id="chart-{sessionData.sessionId}"></canvas>
                </div>
                <button on:click={resetZoom} class="zoom-reset-btn"
                  >Reset Zoom</button
                >
              </div>
              <div class="content-box">
                <div class="progress-container">
                  <span>{(sessionData?.currentTime || 0).toFixed(2)} mins</span>
                  <progress
                    value={sessionData?.currentTime || 0}
                    max={sessionData?.time100 || 1}
                  ></progress>
                </div>
                <div class="scale-container">
                  <div class="scale" id="scale"></div>
                </div>
                <div class="text-container">
                  {#if sessionData.textElements && sessionData.textElements.length > 0}
                    {#if sessionData.textElements[0].text !== "\n"}
                      <span
                        class="text-span"
                        style="color: black; font-weight: normal;"
                      >
                        1.
                      </span>
                    {/if}
                    {#each sessionData.textElements as element, index}
                      {#if element.text === "\n" && index + 1 < sessionData.textElements.length}
                        <br />
                        {#if index + 1 < sessionData.textElements.length && sessionData.textElements[index + 1].text === "\n"}{:else if index > 0 && sessionData.textElements[index - 1].text === "\n"}
                          <span
                            class="text-span"
                            style="color: black; font-weight: normal;"
                          >
                            {(() => {
                              let count =
                                sessionData.textElements[0].text !== "\n"
                                  ? 1
                                  : 0;
                              for (let i = 0; i < index; i++) {
                                if (
                                  sessionData.textElements[i].text === "\n" &&
                                  i > 0 &&
                                  sessionData.textElements[i - 1].text === "\n"
                                ) {
                                  count++;
                                }
                              }
                              return count + 1;
                            })()}.
                          </span>
                        {/if}
                      {:else}
                        <span
                          class="text-span"
                          style="color: {element.textColor}"
                        >
                          {element.text}
                        </span>
                      {/if}
                    {/each}
                  {/if}
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    <div class="table" class:collapsed={isCollapsed}>
    <Table>
      <TableHead>
        <TableHeadCell>Session ID</TableHeadCell>
        <TableHeadCell>Prompt Code</TableHeadCell>
        <TableHeadCell>Selected</TableHeadCell>
        <TableBodyCell>
          <a
            bind:this={filterButton}
            on:click={toggleFilter}
            href=" "
            aria-label="Filter"
            class={showFilter
              ? "material-symbols--filter-alt"
              : "material-symbols--filter-alt-outline"}
          >
          </a>
        </TableBodyCell>
        <TableBodyCell>
          <a
            bind:this={collapseButton}
            on:click={toggleTableCollapse}
            href=" "
            aria-label="collapse"
            class={isCollapsed
            ? "material-symbols--stat-1-rounded"
            : "material-symbols--stat-minus-1-rounded"}
          >
          </a>
        </TableBodyCell>
      </TableHead>
      <TableBody tableBodyClass="divide-y">
        {#each filterTableData as row, index (row.session_id)}
          <TableBodyRow>
            <TableBodyCell>{row.session_id}</TableBodyCell>
            <TableBodyCell>{row.prompt_code}</TableBodyCell>
            <TableBodyCell>
              <input
                type="checkbox" 
                checked={row.selected} 
                on:change={() => handleSelectChange(index)} 
              />
            </TableBodyCell>
          </TableBodyRow>
        {/each}
      </TableBody>
    </Table>
  </div>
  </header>
</div>

<style>
  .App-header {
    text-align: center;
  }

  .App {
    margin: 0px;
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
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
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
    border: 1px solid lightgray;
    border-radius: 15px;
    padding: 25px;
    box-shadow:
      0px 2px 5px rgba(0, 0, 0, 0.2),
      2px 2px 5px rgba(0, 0, 0, 0.2),
      -2px 2px 5px rgba(0, 0, 0, 0.2);
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

  .chart-container {
    width: 100%;
    margin-top: 20px;
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

  :root {
    --progColor: hsl(6, 100%, 75%);
    --progHeight: 20px;
    --progBackgroundColor: hsl(6, 100%, 90%);
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

  /* .dropdown-container {
    align-self: flex-start;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-left: 20px;
  } */

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

  .totalText, .totalInsertions, .totalDeletions, .totalSuggestions {
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
    color: hsl(6, 100%, 75%);
  }

  .user-line {
    color: #66c2a5;
  }

  .api-line {
    color: #fc8d62;
  }

  .triangle-text, .user-line, .api-line {
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
    background: rgba(0, 0, 0, 0.6);
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
    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
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

  .table {
    position: fixed;
    bottom: 0;
    width: 100%;
    height: 200px;
    background-color: white;
    padding: 1em 0;
    margin: 0px;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
    z-index: 1;
    left: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    overflow-y: auto;
  }

  .collapsed {
    position: fixed;
    bottom: 0;
    width: 100%;
    height: 80px;
    background-color: white;
    padding: 1em 0;
    margin: 0px;
    box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
    z-index: 1;
    left: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    overflow-y: auto;
  }

  .material-symbols--info-outline-rounded {
    display: inline-block;
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
    top: 70px;
    left: 30px;
    background: white;
    border: 1px solid #ccc;
    padding: 12px;
    display: none;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
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
  }

  .material-symbols--refresh-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M12 20q-3.35 0-5.675-2.325T4 12t2.325-5.675T12 4q1.725 0 3.3.712T18 6.75V5q0-.425.288-.712T19 4t.713.288T20 5v5q0 .425-.288.713T19 11h-5q-.425 0-.712-.288T13 10t.288-.712T14 9h3.2q-.8-1.4-2.187-2.2T12 6Q9.5 6 7.75 7.75T6 12t1.75 4.25T12 18q1.7 0 3.113-.862t2.187-2.313q.2-.35.563-.487t.737-.013q.4.125.575.525t-.025.75q-1.025 2-2.925 3.2T12 20'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
    margin-left: auto;
  }

  input[type="checkbox"] {
    vertical-align: middle;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(0, 0, 0, 0.2);
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
    font-size: 12px;
    color: white;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: bold;
  }

  .material-symbols--stack-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M4 16q-.825 0-1.412-.587T2 14V4q0-.825.588-1.412T4 2h10q.825 0 1.413.588T16 4v1q0 .425-.288.713T15 6t-.712-.288T14 5V4H4v10h1q.425 0 .713.288T6 15t-.288.713T5 16zm6 6q-.825 0-1.412-.587T8 20V10q0-.825.588-1.412T10 8h10q.825 0 1.413.588T22 10v10q0 .825-.587 1.413T20 22z'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
  }

  .material-symbols--stack-off-rounded {
    display: inline-block;
    width: 24px;
    height: 24px;
    --svg: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23000' d='M22 19.15L10.85 8H20q.825 0 1.413.588T22 10zM6.85 4l-2-2H14q.825 0 1.413.588T16 4v2h-2V4zM10 22q-.85 0-1.425-.575T8 20v-9.15l-4-4V14h2v2H4q-.85 0-1.425-.575T2 14V4.85l-.725-.725q-.3-.3-.288-.712T1.3 2.7t.713-.3t.712.3L21.3 21.3q.3.3.3.7t-.3.7t-.712.3t-.713-.3l-.725-.7z'/%3E%3C/svg%3E");
    background-color: currentColor;
    -webkit-mask-image: var(--svg);
    mask-image: var(--svg);
    -webkit-mask-repeat: no-repeat;
    mask-repeat: no-repeat;
    -webkit-mask-size: 100% 100%;
    mask-size: 100% 100%;
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

  a:focus, a:active {
    color: #86cecb;
  }
</style>
