<script>
  import { onMount, afterUpdate } from "svelte";
  import * as d3 from "d3";

  export let sessionId;
  export let data;
  export let selectedRange;

  let container;
  let prevSelectedRange;
  let prevData;

  onMount(() => {
    if (data && container) {
      renderChart();
    }
  });

  afterUpdate(() => {
    if (
      data &&
      container &&
      (JSON.stringify(prevSelectedRange) !== JSON.stringify(selectedRange) ||
        JSON.stringify(prevData) !== JSON.stringify(data))
    ) {
      renderChart();
      prevSelectedRange = JSON.parse(JSON.stringify(selectedRange));
      prevData = JSON.parse(JSON.stringify(data));
    }
  });

  function renderChart() {
    d3.select(container).selectAll("svg").remove();

    const processedData = data.map((d) => ({
      startProgress: d.startProgress,
      endProgress: d.endProgress,
      residual_vector_norm: d.dissimilarity || d.residual_vector_norm,
      source: d.source,
      startTime: d.startTime,
      endTime: d.endTime,
    }));

    const margin = { top: 10, right: 5, bottom: 25, left: 40 };
    const chartWidth = container.clientWidth - margin.left - margin.right;
    const chartHeight = container.clientHeight - margin.top - margin.bottom;

    const svg = d3
      .select(container)
      .append("svg")
      .style("display", "block")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr(
        "viewBox",
        `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`
      )
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain([100, 0]).range([0, chartWidth]);
    const newyScale = d3.scaleLinear().domain([0, 100]).range([chartHeight, 0]);

    svg
      .append("defs")
      .append("clipPath")
      .attr("id", `clip_bar_preview_${sessionId}`)
      .append("rect")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", chartWidth)
      .attr("height", chartHeight);

    svg
      .append("g")
      .attr("transform", `translate(0, ${chartHeight})`)
      .call(d3.axisBottom(xScale).ticks(3))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 20)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "8px")
      .text("Semantic Change (%)");

    svg
      .append("g")
      .call(d3.axisLeft(newyScale).ticks(3))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -25)
      .attr("x", -chartHeight / 2)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "8px")
      .text("Progress(%)");

    const bars = svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("y", (d) => newyScale(d.endProgress))
      .attr("x", (d) => xScale(d.residual_vector_norm))
      .attr("width", (d) => xScale(0) - xScale(d.residual_vector_norm))
      .attr("height", (d) => newyScale(d.startProgress) - newyScale(d.endProgress))
      .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 0.5)
      .attr("opacity", 0.5)
      .attr("clip-path", `url(#clip_bar_preview_${sessionId})`);

    if (selectedRange) {
      const { sc, progress } = selectedRange;

      svg
        .append("rect")
        .attr("class", "selection-rect")
        .attr("x", xScale(sc.max))
        .attr("y", newyScale(progress.max))
        .attr("width", xScale(sc.min) - xScale(sc.max))
        .attr("height", newyScale(progress.min) - newyScale(progress.max))
        .attr("fill", "none")
        .attr("stroke", "#000")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,3")
        .attr("pointer-events", "none");

      bars
        .attr("opacity", (d) => {
          const isSelected =
            d.residual_vector_norm >= sc.min &&
            d.residual_vector_norm <= sc.max &&
            ((d.startProgress >= progress.min &&
              d.startProgress <= progress.max) ||
              (d.endProgress >= progress.min &&
                d.endProgress <= progress.max) ||
              (d.startProgress <= progress.min &&
                d.endProgress >= progress.max));

          return isSelected ? 0.9 : 0.2;
        })
        .attr("stroke-width", (d) => {
          const isSelected =
            d.residual_vector_norm >= sc.min &&
            d.residual_vector_norm <= sc.max &&
            ((d.startProgress >= progress.min &&
              d.startProgress <= progress.max) ||
              (d.endProgress >= progress.min &&
                d.endProgress <= progress.max) ||
              (d.startProgress <= progress.min &&
                d.endProgress >= progress.max));

          return isSelected ? 2 : 0.5;
        });
    }
  }
</script>

<div
  bind:this={container}
  class="chart-preview-container"
  data-session-id={sessionId}
></div>

<style>
  .chart-preview-container {
    width: 100%;
    height: 100%;
    position: relative;
  }
</style>
