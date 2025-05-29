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

'''