<script>
  import { onMount, createEventDispatcher } from "svelte";
  import * as d3 from "d3";
  export let sessionId;
  export let similarityData;
  export let width = 150;
  export let height;
  export let yScale;
  export let selectionMode = false;
  export let sharedSelection = null;

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
      }
      else {
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
    console.log("Shared selection changed:", sharedSelection);
    if (!sharedSelection) return;
    if (!processedData) return;
    if (!bars) return;
    if (!newyScale) return;
    if (!xScale) return;

    function highlightBars(filteredData) {
      if (!sharedSelection || !sharedSelection.progressMin || !sharedSelection.progressMax) return;

      const selectedIds = new Set(filteredData.map((d) => d.id));
      bars.attr("opacity", (d) => (selectedIds.has(d.id) ? 0.9 : 0.1));
    }
    const { progressMin, progressMax } = sharedSelection;
    const y0 = newyScale(progressMax);
    const y1 = newyScale(progressMin);

    const filteredData = processedData.filter((d) => {
      const barY = newyScale(d.endProgress);
      const barHeight = newyScale(d.startProgress) - newyScale(d.endProgress);
      return barY + barHeight >= y0 && barY <= y1;
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
          min: filteredData[0].startTime,
          max: filteredData[filteredData.length - 1].endTime,
        },
        sc: {
          sc: filteredData.map((d) => d.residual_vector_norm),
        },
      },
      data: filteredData,
      wholeData: processedData,
      sessionId: sessionId,
      sources: filteredData.map((d) => d.source),
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
      .attr("width", "100%")
      .attr("height", chartHeight + margin.top + margin.bottom)
      .attr(
        "viewBox",
        `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`,
      )
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    xScale = d3.scaleLinear().domain([1, 0]).range([0, chartWidth]);
    newyScale = zoomTransform.rescaleY(yScale.copy());

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
      .call(d3.axisBottom(xScale).ticks(0))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 25)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text("Semantic Change (%)");

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
      .text("Progress(%)");

    bars = svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("y", (d) =>
        newyScale(d.startProgress) < newyScale(d.endProgress)
          ? newyScale(d.startProgress)
          : newyScale(d.endProgress),
      )
      .attr("x", (d) => xScale(d.residual_vector_norm))
      .attr("width", (d) => xScale(0) - xScale(d.residual_vector_norm))
      .attr("height", (d) =>
        Math.abs(newyScale(d.startProgress) - newyScale(d.endProgress)),
      )
      .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("opacity", 0.5)
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 0.1)
      .attr("clip-path", "url(#clip_bar)");

    brush = d3
      .brushY()
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
      const [y0, y1] = event.selection;

      const progressMin = newyScale.invert(y1);
      const progressMax = newyScale.invert(y0);

      sharedSelection = { progressMin, progressMax, selectionSource: "barChart_y" };
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