<script>
  import { onMount } from "svelte";
  import * as d3 from "d3";

  export let sessionId;
  export let similarityData;
  export let width = 200;
  export let height = 150;

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
    d3.select(container).selectAll("svg").remove();

    const processedData = similarityData.map((item, index) => ({
      sentenceNum: index + 1,
      dissimilarity: item.dissimilarity * 100,
    }));

    const margin = { top: 10, right: 30, bottom: 30, left: 50 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight =
      Math.min(height, processedData.length * 15) - margin.top - margin.bottom;

    const svg = d3
      .select(container)
      .append("svg")
      .attr("width", "100%")
      .attr("height", chartHeight + margin.top + margin.bottom)
      .attr(
        "viewBox",
        `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`
      )
      .attr("preserveAspectRatio", "xMidYMid meet")
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain([100, 0]).range([0, chartWidth]);

    const yScale = d3
      .scaleBand()
      .domain(processedData.map((d) => d.sentenceNum).reverse())
      .range([0, chartHeight])
      .padding(0.1);

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
      .call(
        d3
          .axisLeft(yScale)
          .tickSize(0)
          .tickValues(
            filterTicks(processedData.map((d) => d.sentenceNum).reverse())
          )
      )
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -35)
      .attr("x", -chartHeight / 2)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text("Sentence Number");

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

    // svg
    //   .append("text")
    //   .attr("x", chartWidth / 2)
    //   .attr("y", -2)
    //   .attr("text-anchor", "middle")
    //   .style("font-size", "12px")
    //   .style("font-weight", "500")
    //   .text("Semantic Change by Sentence");
  }

  function filterTicks(ticks) {
    if (ticks.length <= 20) return ticks;

    const step = Math.ceil(ticks.length / 10);
    return ticks.filter((_, i) => i % step === 0);
  }
</script>

<div
  bind:this={container}
  class="bar-chart-container"
  data-session-id={sessionId}
></div>

<style>
  .bar-chart-container {
    width: 50%;
    height: 100%;
    margin-bottom: 0;
    margin-right: 0;
  }
</style>
