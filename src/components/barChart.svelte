<script>
  import { onMount } from "svelte";
  import * as d3 from "d3";

  export let sessionId; // The session ID
  export let similarityData; // The data for the chart
  export let width = 250;
  export let height = 200;

  let container;

  onMount(() => {
    if (similarityData && container) {
      renderChart();
    }
  });

  $: if (similarityData && container) {
    renderChart();
  }

  function renderChart() {
    // Clear previous chart if any
    d3.select(container).selectAll("svg").remove();

    const processedData = similarityData.map((item, index) => ({
      sentenceNum: index + 1,
      dissimilarity: item.dissimilarity * 100,
    }));

    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight =
      Math.min(height, processedData.length * 20) - margin.top - margin.bottom;

    const svg = d3
      .select(container)
      .append("svg")
      .attr("width", chartWidth + margin.left + margin.right)
      .attr("height", chartHeight + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain([100, 0]).range([0, chartWidth]);

    const yScale = d3
      .scaleBand()
      .domain(processedData.map((d) => d.sentenceNum).reverse())
      .range([0, chartHeight])
      .padding(0.1);

    // Add X axis
    svg
      .append("g")
      .attr("transform", `translate(0, ${chartHeight})`)
      .call(d3.axisBottom(xScale))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 30)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .text("Semantic Change (%)");

    // Add Y axis
    svg
      .append("g")
      .call(d3.axisLeft(yScale))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -40)
      .attr("x", -chartHeight / 2)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .text("Sentence Number");

    // Add bars
    svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("y", (d) => yScale(d.sentenceNum))
      .attr("x", (d) => xScale(d.dissimilarity))
      .attr("width", (d) => xScale(0) - xScale(d.dissimilarity))
      .attr("height", yScale.bandwidth())
      .attr("fill", "rgba(0, 0, 255, 0.8)")
      .attr("stroke", "rgba(0, 0, 255, 1)")
      .attr("stroke-width", 1);

    // Add title
    svg
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", -5)
      .attr("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "500")
      .text("Semantic Change by Sentence");
  }
</script>

<div
  bind:this={container}
  class="bar-chart-container"
  data-session-id={sessionId}
></div>

<style>
  .bar-chart-container {
    width: 100%;
    height: 100%;
  }
</style>
