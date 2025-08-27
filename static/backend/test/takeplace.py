'''
function findSegments(data, checks, minCount) {
    const segments = [];
    // const sourceChecked = checks.source[0];
    // const sourceOrder = checks.source[1];
    // const trendChecked = checks.trend[0];
    // const expectedTrend = checks.trend[1];
    // const useSourceMatch =
    //   sourceChecked && Array.isArray(sourceOrder) && sourceOrder.length > 0;

    // if (useSourceMatch) {
    //   const windowSize = sourceOrder.length;
    //   for (let i = 0; i <= data.length - windowSize; i++) {
    //     const window = data.slice(i, i + windowSize);
    //     const sources = window.map((d) => d.source);
    //     const allValid = window.every((d) => isDataValid(d, checks));
    //     if (!allValid) continue;
    //     if (sources.every((src, idx) => src === sourceOrder[idx])) {
    //       if (
    //         trendChecked &&
    //         expectedTrend &&
    //         expectedTrend.length === window.length - 1
    //       ) {
    //         const values = window.map((d) => d.residual_vector_norm);
    //         if (!matchesTrend(values, expectedTrend)) continue;
    //       }
    //       segments.push([...window]);
    //       i += windowSize - 1;
    //     }
    //   }
    // } else {
      let currentSegment = [];
      for (const item of data) {
        if (isDataValid(item, checks)) {
          currentSegment.push(item);
        } else {
          if (currentSegment.length >= minCount) {
          //   if (
          //     trendChecked &&
          //     expectedTrend &&
          //     expectedTrend.length === currentSegment.length - 1
          //   ) {
          //     const values = currentSegment.map((d) => d.residual_vector_norm);
          //     if (matchesTrend(values, expectedTrend)) {
          //       segments.push([...currentSegment]);
          //     }
          //   } else if (!trendChecked) {
              segments.push([...currentSegment]);
          //   }
          // }
          currentSegment = [];
        }
      }
      if (currentSegment.length >= minCount) {
      //   if (
      //     trendChecked &&
      //     expectedTrend &&
      //     expectedTrend.length === currentSegment.length - 1
      //   ) {
      //     const values = currentSegment.map((d) => d.residual_vector_norm);
      //     if (matchesTrend(values, expectedTrend)) {
      //       segments.push([...currentSegment]);
      //     }
      //   } else if (!trendChecked) {
          segments.push([...currentSegment]);
      //   }
      }
    }
    return segments;
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

  function matchesTrend(values, expectedTrend) {
    const actual = getTrendPattern(values);
    return actual.every((v, i) => v === expectedTrend[i]);
  }

  function getTrendPattern(values) {
    const pattern = [];
    for (let i = 1; i < values.length; i++) {
      if (values[i] > values[i - 1]) pattern.push(1); // up is 1, down is 0
      else if (values[i] < values[i - 1]) pattern.push(0);
    }
    return pattern;
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

            function resetTextHighlighting(sessionId) {
    const textElements = document.querySelectorAll(".text-span");
    textElements.forEach((element) => {
      element.classList.remove("highlighted-text");
    });
  }

  // *Table* related
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

    <!-- <button on:click={() => resetZoom($clickSession.sessionId)} class="zoom-reset-btn">
                      Reset Zoom
    </button> -->

    function resetZoom(sessionId) {
    chartRefs[sessionId]?.resetZoom();
  }

    function toggleTableCollapse() {
    isCollapsed = !isCollapsed;
  }

  const toggleFilter = () => {
    showFilter = !showFilter;
  };

  function handleSelectChange(index) {
    handleSessionChange($filterTableData[index].session_id);
  }

  const handleSessionChange = (sessionId) => {
    let isCurrentlySelected = $filterTableData.find(
      (row) => row.session_id == sessionId,
    )?.selected;

    filterTableData.set(
      $filterTableData.map((row) => {
        if (row.session_id == sessionId) {
          return { ...row, selected: !row.selected };
        }
        return row;
      }),
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
      $filterTableData.filter((f) => f.selected).map((f) => f.prompt_code),
    );
    selectedTags.update((selected) => {
      selected = selected.filter((tag) => nowSelectTag.has(tag));
      return selected;
    });
    updatePromptFilterStatus();
  };

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

      .grid-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: white;
    border-radius: 8px;
    padding: 15px;
    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease;
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

  td {
    padding: 12px 16px;
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

    function isDataValid(item, checks, minCount) {
    // const fieldMap = {
    //   progress: (d) => (d.end_progress - d.start_progress) * 100,
    //   time: (d) => (d.end_time - d.start_time) / 60,
    //   semantic: (d) => d.residual_vector_norm,
    // };

    // const relaxRatioMap = {
    //   progress: 0.1,
    //   time: 0.1,
    // };

    // for (const [key, [checked, range]] of Object.entries(checks)) {
    //   if (!checked || !(key in fieldMap)) continue;
    //   const value = fieldMap[key](item);
    //   if (value == null || isNaN(value)) return false;

    //   if (minCount === 1) {
    //     if (key === "semantic") {
    //       const relaxedMin = range[0] - 0.05;
    //       const relaxedMax = range[1] + 0.05;
    //       if (value < relaxedMin || value > relaxedMax) return false;
    //     } else {
    //       const relaxRatio = relaxRatioMap[key] ?? 0;
    //       const delta = (range[1] - range[0]) * relaxRatio;
    //       const relaxedMin = range[0] - delta;
    //       const relaxedMax = range[1] + delta;
    //       if (value < relaxedMin || value > relaxedMax) return false;
    //     }
    //   }
    // }
    return true;
  }

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

'''