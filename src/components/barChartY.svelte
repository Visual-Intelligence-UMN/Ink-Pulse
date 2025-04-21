<script>
  import { onMount, createEventDispatcher } from "svelte";
  import * as d3 from "d3";
  export let sessionId;
  export let similarityData;
  export let width = 150;
  export let height;
  export let yScale;
  export let selectionMode = false;

  let container;
  const dispatch = createEventDispatcher();
  let brush;
  let brushGroup;
  let svg;
  let bars;
  let currentSelection = null;
  export let zoomTransform = d3.zoomIdentity;

  onMount(() => {
    if (similarityData && container) {
      renderChart();
    }
  });

  $: if (similarityData && container && zoomTransform !== d3.zoomIdentity) {
    renderChart();
  }

  $: if (svg && brushGroup) {
    if (selectionMode) {
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

  function renderChart() {
    d3.select(container).selectAll("svg").remove();

    const processedData = similarityData.map((item) => ({
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.residual_vector_norm * 100,
      source: item.source,
      startTime: item.start_time / 60, // Convert to minutes
      endTime: item.end_time / 60, // Convert to minutes
      dissimilarity: item.residual_vector_norm * 100,
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
        `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`
      )
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain([100, 0]).range([0, chartWidth]);
    const newyScale = zoomTransform.rescaleY(yScale.copy());

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
      .attr("y", (d) => newyScale(d.endProgress))
      .attr("x", (d) => xScale(d.residual_vector_norm))
      .attr("width", (d) => xScale(0) - xScale(d.residual_vector_norm))
      .attr(
        "height",
        (d) => newyScale(d.startProgress) - newyScale(d.endProgress)
      )
      .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 1)
      .attr("opacity", 0.5)
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 0.1)
      .attr("clip-path", "url(#clip_bar)");

    brush = d3
      .brush()
      .extent([
        [0, 0],
        [chartWidth, chartHeight],
      ])
      .on("end", brushed);

    brushGroup = svg.append("g").attr("class", "brush");

    if (selectionMode) {
      brushGroup.call(brush);
      brushGroup.style("pointer-events", "all");
    } else {
      brushGroup.style("pointer-events", "none");
    }

    function brushed(event) {
      if (!event.selection) {
        resetBars();
        currentSelection = null;
        dispatch("selectionCleared", { sessionId });
        return;
      }

      currentSelection = event.selection;

      const [[x0, y0], [x1, y1]] = event.selection;

      const scMin = xScale.invert(x1);
      const scMax = xScale.invert(x0);
      const progressMin = yScale.invert(y1);
      const progressMax = yScale.invert(y0);

      const filteredData = processedData.filter((d) => {
        const barX = xScale(d.residual_vector_norm);
        const barY = yScale(d.endProgress);
        const barWidth = xScale(0) - xScale(d.residual_vector_norm);
        const barHeight = yScale(d.startProgress) - yScale(d.endProgress);

        return (
          barX + barWidth >= x0 &&
          barX <= x1 &&
          barY + barHeight >= y0 &&
          barY <= y1
        );
      });

      highlightBars(filteredData);

      dispatch("selectionChanged", {
        range: {
          sc: { min: scMin, max: scMax },
          progress: { min: progressMin, max: progressMax },
        },
        data: filteredData,
        sessionId: sessionId,
      });
    }

    function resetBars() {
      bars.attr("opacity", 0.5).attr("stroke-width", 1);
    }

    function highlightBars(filteredData) {
      bars
        .attr("opacity", (d) => {
          const isSelected = filteredData.some(
            (fd) =>
              fd.startProgress === d.startProgress &&
              fd.endProgress === d.endProgress &&
              fd.residual_vector_norm === d.residual_vector_norm
          );
          return isSelected ? 0.9 : 0.2;
        })
        .attr("stroke-width", (d) => {
          const isSelected = filteredData.some(
            (fd) =>
              fd.startProgress === d.startProgress &&
              fd.endProgress === d.endProgress &&
              fd.residual_vector_norm === d.residual_vector_norm
          );
          return isSelected ? 2 : 0.5;
        });
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
