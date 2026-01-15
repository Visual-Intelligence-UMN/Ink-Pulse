<script>
  import { onMount, createEventDispatcher } from "svelte";
  import * as d3 from "d3";
  export let sessionId;
  export let similarityData;
  export let width = 300;
  export let height;
  export let yScale;
  export let selectionMode = false;
  export let sharedSelection = null;
  export let xScaleBarChartFactor = 1;

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

    function highlightBars(filteredData) {
      if (
        !sharedSelection ||
        !sharedSelection.progressMin ||
        !sharedSelection.progressMax
      )
        return;

      const selectedIds = new Set(filteredData.map((d) => d.id));
      bars.attr("opacity", (d) => (selectedIds.has(d.id) ? 0.9 : 0.1));
    }
    const { progressMin, progressMax } = sharedSelection;
    const x0 = xScale(progressMin);
    const x1 = xScale(progressMax);

    const filteredData = processedData.filter((d) => {
      const barX =
        xScale(d.startProgress) < xScale(d.endProgress)
          ? xScale(d.startProgress)
          : xScale(d.endProgress);
      const barWidth = Math.abs(
        xScale(d.startProgress) - xScale(d.endProgress)
      );
      return barX + barWidth >= x0 && barX <= x1;
    });
    const scMin = d3.min(filteredData, (d) => d.residual_vector_norm) ?? 0;
    const scMax = d3.max(filteredData, (d) => d.residual_vector_norm) ?? 0;

    highlightBars(filteredData);

    dispatch("selectionChanged", {
      range: {
        sc: { min: scMin, max: scMax },
        progress: { min: progressMin, max: progressMax },
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

    processedData = similarityData.map((item, i) => ({
      id: i,
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.residual_vector_norm,
      source: item.source,
      startTime: item.start_time / 60,
      endTime: item.end_time / 60,
    }));

    const margin = { top: 20, right: 0, bottom: 30, left: 50 };
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

    // X axis is Writing length (0-100), with zoom support
    const baseXScale = d3.scaleLinear().domain([0, 100]).range([0, chartWidth]);
    xScale = zoomTransform.rescaleX(baseXScale);
    xScaleBarChartFactor = chartWidth / 100;

    // Y axis is Semantic Change (0-1)
    newyScale = d3.scaleLinear().domain([0, 1]).range([chartHeight, 0]);

    svg
      .append("defs")
      .append("clipPath")
      .attr("id", "clip_bar")
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
      .attr("y", 25)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text("Writing length");

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
      .text("Semantic Change");

    bars = svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", (d) =>
        xScale(d.startProgress) < xScale(d.endProgress)
          ? xScale(d.startProgress)
          : xScale(d.endProgress)
      )
      .attr("y", (d) => newyScale(d.residual_vector_norm))
      .attr("width", (d) =>
        Math.abs(xScale(d.startProgress) - xScale(d.endProgress))
      )
      .attr("height", (d) => newyScale(0) - newyScale(d.residual_vector_norm))
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
      .attr("clip-path", "url(#clip_bar)");

    brush = d3
      .brushX()
      .extent([
        [0, 0],
        [chartWidth, chartHeight],
      ])
      .on("end", brushed);

    brushGroup = svg.append("g").attr("class", "brush");
    brushGroup.call(brush);

    if (selectionMode) {
      brushGroup.style("pointer-events", "all");
    } else {
      brushGroup.style("pointer-events", "none");
    }

    function brushed(event) {
      if (!event.selection) {
        resetBars();
        sharedSelection = null;
        // currentSelection = null;
        // dispatch("selectionCleared", { sessionId });
        return;
      }

      currentSelection = event.selection;
      const [x0, x1] = event.selection;

      const progressMin = xScale.invert(x0);
      const progressMax = xScale.invert(x1);

      sharedSelection = {
        progressMin,
        progressMax,
        selectionSource: "barChart_y",
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
