<script>
  import { onMount, createEventDispatcher } from "svelte";
  import * as d3 from "d3";
  export let sessionId;
  export let similarityData;
  export let width = 300;
  export let height;
  export let yScale;
  export let xAxisField = "progress"; // 新增：X轴字段
  export let yAxisField = "semantic_change"; // 新增：Y轴字段
  export let selectionMode = false;
  export let readOnly = false;
  export let sharedSelection = null;
  export let xScaleBarChartFactor = 1;
  const uniqueId = Math.random().toString(36).substring(2, 9);

  let container;
  const dispatch = createEventDispatcher();
  let brush;
  let brushGroup;
  let svg;
  let bars;
  let currentSelection = null;
  export let zoomTransform = d3.zoomIdentity;

  let processedData = [];
  let xScale;
  let newyScale;

  // 属性配置池
  const attributeConfig = {
    progress: {
      label: "Writing length",
      getValue: (item) => ((item.start_progress + item.end_progress) / 2) * 100,
      getStart: (item) => item.start_progress * 100,
      getEnd: (item) => item.end_progress * 100,
      hasRange: true,
      domain: [0, 100],
    },
    time: {
      label: "Time (min)",
      getValue: (item) => (item.start_time + item.end_time) / 2 / 60,
      getStart: (item) => item.start_time / 60,
      getEnd: (item) => {
        const startTime = item.start_time / 60;
        const endTime = item.end_time / 60;
        // 如果是AI且时间相同（瞬时操作），添加一个很小的时间跨度（0.05分钟 = 3秒）
        if (item.source === "api" && startTime === endTime) {
          return endTime + 0.05;
        }
        return endTime;
      },
      hasRange: true,
      domain: null, // 动态计算
    },
    semantic_change: {
      label: "Semantic Change",
      getValue: (item) => item.residual_vector_norm,
      hasRange: false,
      domain: [0, 1],
    },
  };

  const colorMap = {
    user: "#66C2A5",
    api: "#FC8D62",
  };

  import colors from "./colors.js";
  const colorPalette = colors(
    "7fc97fbeaed4fdc086ffff99386cb0f0027fbf5b17666666"
  );
  let colorIndex = 0;

  onMount(() => {
    if (similarityData && container) {
      renderChart();
      dispatch("chartLoaded", sessionId);
    }
  });

  $: if (!zoomTransform) {
    zoomTransform = d3.zoomIdentity;
  }

  // 监听轴字段变化，重新渲染
  $: if (xAxisField && yAxisField && similarityData && container) {
    renderChart();
  }

  $: if ((similarityData && container) || zoomTransform !== d3.zoomIdentity) {
    renderChart();
  }

  $: if (svg && brushGroup) {
    if (selectionMode) {
      if (sharedSelection && sharedSelection.selectionSource != "barChart_y") {
        brushGroup.select(".selection").style("display", "none");
      } else {
        brushGroup.select(".selection").style("display", null);
      }

      if (!brushGroup.select(".overlay").node()) {
        brushGroup.call(brush);
      }

      brushGroup.style("pointer-events", "all");

      if (!svg.select(".selection-mode-indicator").size()) {
        svg
          .append("text")
          .attr("class", "selection-mode-indicator")
          .attr("x", width / 2 - 50)
          .attr("y", 10)
          .attr("text-anchor", "middle")
          .style("font-size", "10px")
          .style("fill", "#e74c3c")
          .style("font-weight", "bold");
      }
    } else {
      if (brushGroup && brush) {
        brushGroup.call(brush.move, null);
        brushGroup.selectAll("*").remove();
      }

      brushGroup.style("pointer-events", "none");

      svg.select(".selection-mode-indicator").remove();
    }
  }

  $: if (sharedSelection) {
    sharedSelectionChanged();
  } else {
    // Only run if svg, brushGroup, brush exist
    if (svg && brushGroup && brush) {
      if (bars) {
        bars.attr("opacity", 0.5).attr("stroke-width", 0.1);
      }

      if (currentSelection) {
        brushGroup.call(brush.move, null);
        currentSelection = null;
      }
    }
  }

  function sharedSelectionChanged() {
    // console.log("Shared selection changed:", sharedSelection);
    if (!sharedSelection) return;
    if (!processedData) return;
    if (!bars) return;
    if (!newyScale) return;
    if (!xScale) return;

    const xConfig = attributeConfig[xAxisField];

    function highlightBars(filteredData) {
      const selectedIds = new Set(filteredData.map((d) => d.id));
      bars.attr("opacity", (d) => (selectedIds.has(d.id) ? 0.9 : 0.1));
    }

    // 通用格式：优先使用 xMin/xMax/xField
    let selectionMin, selectionMax;

    if (sharedSelection.xField && sharedSelection.xField === xAxisField) {
      // 新格式：字段匹配
      selectionMin = sharedSelection.xMin;
      selectionMax = sharedSelection.xMax;
    } else if (
      sharedSelection.progressMin !== null &&
      xAxisField === "progress"
    ) {
      // 向后兼容：progressMin/progressMax
      selectionMin = sharedSelection.progressMin;
      selectionMax = sharedSelection.progressMax;
    } else if (sharedSelection.timeMin !== null && xAxisField === "time") {
      // 向后兼容：timeMin/timeMax
      selectionMin = sharedSelection.timeMin;
      selectionMax = sharedSelection.timeMax;
    } else {
      // 字段不匹配，不响应
      bars.attr("opacity", 0.5).attr("stroke-width", 0.1);
      return;
    }

    if (selectionMin === null || selectionMax === null) {
      bars.attr("opacity", 0.5).attr("stroke-width", 0.1);
      return;
    }

    const x0 = xScale(selectionMin);
    const x1 = xScale(selectionMax);

    const filteredData = processedData.filter((d) => {
      if (xConfig.hasRange) {
        // X axis is range type
        const barX = Math.min(xScale(d.xStart), xScale(d.xEnd));
        const barWidth = Math.abs(xScale(d.xStart) - xScale(d.xEnd));
        return barX + barWidth >= x0 && barX <= x1;
      } else {
        // X axis is point value type (semantic_change)
        const barX = xScale(d.xValue);
        return barX >= x0 && barX <= x1;
      }
    });

    if (!filteredData.length) {
      bars.attr("opacity", 0.5).attr("stroke-width", 0.1);
      return;
    }

    const scMin = d3.min(filteredData, (d) => d.residual_vector_norm) ?? 0;
    const scMax = d3.max(filteredData, (d) => d.residual_vector_norm) ?? 0;

    highlightBars(filteredData);

    dispatch("selectionChanged", {
      selection: {
        xMin: selectionMin,
        xMax: selectionMax,
        xField: xAxisField,
        yField: yAxisField,
      },
      range: {
        sc: { min: scMin, max: scMax },
        progress: {
          min:
            xAxisField === "progress"
              ? selectionMin
              : d3.min(filteredData, (d) => d.startProgress),
          max:
            xAxisField === "progress"
              ? selectionMax
              : d3.max(filteredData, (d) => d.endProgress),
        },
      },
      dataRange: {
        scRange: {
          min: d3.min(filteredData, (d) => d.residual_vector_norm),
          max: d3.max(filteredData, (d) => d.residual_vector_norm),
        },
        progressRange: {
          min: d3.min(filteredData, (d) => d.startProgress),
          max: d3.max(filteredData, (d) => d.endProgress),
        },
        timeRange: {
          min: filteredData[0]?.startTime ?? 0,
          max: filteredData[filteredData.length - 1]?.endTime ?? 0,
        },
        sc: {
          sc: filteredData.map((d) => d.residual_vector_norm),
        },
      },
      data: filteredData,
      wholeData: processedData,
      sessionId: sessionId,
      sources: filteredData.map((d) => d.source),
      selectionSource: "barChart_y",
    });
  }

  function renderChart() {
    d3.select(container).selectAll("svg").remove();

    const xConfig = attributeConfig[xAxisField];
    const yConfig = attributeConfig[yAxisField];

    // process the data, calculate all the attribute values
    processedData = similarityData.map((item, i) => {
      const dataPoint = {
        id: i,
        startProgress: item.start_progress * 100,
        endProgress: item.end_progress * 100,
        residual_vector_norm: item.residual_vector_norm,
        source: item.source,
        startTime: item.start_time / 60,
        endTime: item.end_time / 60,
        // 计算当前选择的 X/Y 值
        xValue: xConfig.getValue(item),
        yValue: yConfig.getValue(item),
      };

      // if the x axis is range type, add the range values
      if (xConfig.hasRange) {
        dataPoint.xStart = xConfig.getStart(item);
        dataPoint.xEnd = xConfig.getEnd(item);
      }
      if (yConfig.hasRange) {
        dataPoint.yStart = yConfig.getStart(item);
        dataPoint.yEnd = yConfig.getEnd(item);
      }

      return dataPoint;
    });

    const margin = { top: 20, right: 10, bottom: 35, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    svg = d3
      .select(container)
      .append("svg")
      .style("display", "block")
      .style("vertical-align", "top")
      .attr("width", width)
      .attr("height", chartHeight + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    // dynamically calculate the domain
    let xDomain = xConfig.domain;
    if (!xDomain) {
      // automatically calculate the domain (e.g. time)
      const xValues = processedData.flatMap((d) =>
        xConfig.hasRange ? [d.xStart, d.xEnd] : [d.xValue]
      );
      xDomain = [Math.min(...xValues), Math.max(...xValues)];
    }

    let yDomain = yConfig.domain;
    if (!yDomain) {
      const yValues = processedData.flatMap((d) =>
        yConfig.hasRange ? [d.yStart, d.yEnd] : [d.yValue]
      );
      yDomain = [Math.min(...yValues), Math.max(...yValues)];
    }

    // create scale
    const baseXScale = d3.scaleLinear().domain(xDomain).range([0, chartWidth]);
    xScale = zoomTransform.rescaleX(baseXScale);
    xScaleBarChartFactor = chartWidth / (xDomain[1] - xDomain[0]);

    newyScale = d3.scaleLinear().domain(yDomain).range([chartHeight, 0]);

    svg
      .append("defs")
      .append("clipPath")
      .attr("id", `clip_bar_${uniqueId}`)
      .append("rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", chartWidth)
      .attr("height", chartHeight);

    svg
      .append("g")
      .attr("transform", `translate(0, ${chartHeight})`)
      .call(d3.axisBottom(xScale).ticks(5))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 30)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text(xConfig.label);

    svg
      .append("g")
      .call(d3.axisLeft(newyScale).ticks(5))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -35)
      .attr("x", -chartHeight / 2)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text(yConfig.label);

    // calculate the fixed bar width/height (for point value)
    const fixedBarWidth = chartWidth * 0.02;
    const fixedBarHeight = chartHeight * 0.02;

    bars = svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", (d) => {
        if (xConfig.hasRange) {
          // X axis is range: use the start point
          return Math.min(xScale(d.xStart), xScale(d.xEnd));
        } else {
          // X axis is point value: center
          return xScale(d.xValue) - fixedBarWidth / 2;
        }
      })
      .attr("y", (d) => {
        if (yConfig.hasRange) {
          // Y axis is range: use the end point (larger Y coordinate)
          return Math.min(newyScale(d.yStart), newyScale(d.yEnd));
        } else {
          // Y axis is point value: extend from the point downward
          return newyScale(d.yValue);
        }
      })
      .attr("width", (d) => {
        if (xConfig.hasRange) {
          // X axis is range: width = range span
          return Math.abs(xScale(d.xEnd) - xScale(d.xStart));
        } else {
          // X axis is point value: fixed width
          return fixedBarWidth;
        }
      })
      .attr("height", (d) => {
        if (yConfig.hasRange) {
          // Y axis is range: height = range span
          return Math.abs(newyScale(d.yStart) - newyScale(d.yEnd));
        } else {
          // Y axis is point value: extend from the point downward
          return newyScale(yDomain[0]) - newyScale(d.yValue);
        }
      })
      .attr("fill", (d) => {
        if (d.source === "user") {
          return colorMap.user;
        } else if (d.source === "api") {
          return colorMap.api;
        } else {
          const color = colorPalette[colorIndex % colorPalette.length];
          colorIndex++;
          return color;
        }
      })
      .attr("stroke", (d) => {
        if (d.source === "user") {
          return colorMap.user;
        } else if (d.source === "api") {
          return colorMap.api;
        } else {
          const color = colorPalette[colorIndex % colorPalette.length];
          colorIndex++;
          return color;
        }
      })
      .attr("opacity", 0.5)
      .attr("stroke-width", 0.1)
      .attr("clip-path", `url(#clip_bar_${uniqueId})`);

    brush = d3
      .brushX()
      .extent([
        [0, 0],
        [chartWidth, chartHeight],
      ])
      .on("end", brushed);

    brushGroup = svg.append("g").attr("class", "brush");
    brushGroup.call(brush);

    if (selectionMode && !readOnly) {
      brushGroup.style("pointer-events", "all");
    } else {
      brushGroup.style("pointer-events", "none");
    }

    function brushed(event) {
      if (readOnly) {
        return;
      }

      if (!event.selection) {
        resetBars();
        sharedSelection = null;
        // currentSelection = null;
        // dispatch("selectionCleared", { sessionId });
        return;
      }

      currentSelection = event.selection;
      const [x0, x1] = event.selection;

      const xMin = xScale.invert(x0);
      const xMax = xScale.invert(x1);

      // general format: contains field information
      sharedSelection = {
        xMin,
        xMax,
        xField: xAxisField,
        yField: yAxisField,
        selectionSource: "barChart_y",
        // backward compatibility: if the x axis is progress, keep the old field
        progressMin: xAxisField === "progress" ? xMin : null,
        progressMax: xAxisField === "progress" ? xMax : null,
        timeMin: xAxisField === "time" ? xMin : null,
        timeMax: xAxisField === "time" ? xMax : null,
      };
    }

    function resetBars() {
      bars.attr("opacity", 0.5).attr("stroke-width", 0.1);
    }

    if (!selectionMode) {
      svg.select(".brush-instructions").remove();
    }
  }

  export function clearSelection() {
    if (brushGroup && brush) {
      brushGroup.call(brush.move, null);
      currentSelection = null;
    }
  }

  export function restoreSelection() {
    if (brushGroup && brush && currentSelection) {
      brushGroup.call(brush.move, currentSelection);
    }
  }
</script>

<div bind:this={container} data-session-id={sessionId}></div>

<style>
  div {
    position: relative;
  }

  :global(.brush .selection) {
    stroke: #000;
    stroke-opacity: 0.3;
    fill: #000;
    fill-opacity: 0.1;
  }
</style>
