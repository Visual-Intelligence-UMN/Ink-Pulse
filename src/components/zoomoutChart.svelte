<script lang="ts">
  import { onMount } from "svelte";
  import * as d3 from "d3";
  export let similarityData;
  export let width = 50;
  let height = 150;
  export let yScale;

  let container;
  let svg;
  let bars;

  export let sessionId;
  export let sessionTopic;

  onMount(() => {
    if (similarityData && container) {
      renderChart();
    }
  });

  $: if (similarityData && container) {
    renderChart();
  }

  function renderChart() {
    d3.select(container).selectAll("svg").remove();

    const processedData = similarityData.map((item) => ({
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.norm_vector,
      source: item.source,
      max_norm_vector: item.max_norm_vector,
    }));
    const max_norm_vector = processedData[0].max_norm_vector
    const min_norm_vector = d3.min(processedData, d => d.residual_vector_norm);
    const opacityScale = d3.scaleLinear()
      .domain([min_norm_vector, max_norm_vector])
      .range([0.2, 1]);

    const margin = { top: 0, right: 0, bottom: 0, left: 0 };
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

    const xScale = d3.scaleLinear().domain([max_norm_vector, 0]).range([0, chartWidth]);
    const newyScale = yScale.copy();

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
      // .call(d3.axisBottom(xScale).ticks(3))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 25)
      // .attr("fill", "black")
      // .attr("text-anchor", "middle")
      // .style("font-size", "10px")
      // .text("Semantic Change (%)");

    svg
      .append("g")
      // .call(d3.axisLeft(newyScale).ticks(3))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -35)
      .attr("x", -chartHeight / 2)
      // .attr("fill", "black")
      // .attr("text-anchor", "middle")
      // .style("font-size", "10px")
      // .text("Progress(%)");

    bars = svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("y", (d) => newyScale(d.endProgress))
      .attr("x", (_, i) => {
        const firstElement = i === 0 ? 0 : max_norm_vector / 2;
        return xScale(firstElement);
      })
      .attr("width", (_, i) => {
        const firstElement = i === 0 ? 0 : max_norm_vector;
        return xScale(0) - xScale(firstElement);
      })
      .attr(
        "height",
        (d) => newyScale(d.startProgress) - newyScale(d.endProgress)
      )
      .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("opacity", (d) => opacityScale(d.residual_vector_norm))
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 0.1)
      .attr("clip-path", "url(#clip_bar)");
  }
</script>
    
<div class="chart-container">
  <div class="session-label">
    {sessionTopic} - {sessionId}
  </div>
  <div bind:this={container} data-session-id={sessionId} style="transform: rotate(90deg)"></div>
</div>

<style>
  .session-label {
    width: 400px;
    font-size: 12px;
    font-family: "Poppins", sans-serif;
    margin-top: 35px;
  }

  .chart-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 4px;
  }
</style>