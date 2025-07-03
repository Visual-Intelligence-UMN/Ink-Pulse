<script>
  import { onMount } from "svelte";
  import * as d3 from "d3";

  export let sessionId;
  export let similarityData;
  export let width = 300;
  export let height = 100;

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
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.residual_vector_norm * 100,
      source: item.source,
      startTime: item.start_time / 60,
      endTime: item.end_time / 60,
      lastEventTime: item.last_event_time / 60,
    }));

    const margin = { top: 0, right: 0, bottom: 40, left: 0 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const svg = d3
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
      .attr("preserveAspectRatio", "xMidYMid meet")
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);
    const xScale = d3
      .scaleLinear()
      .domain([0, processedData[0].lastEventTime])
      .range([0, chartWidth]);
    const yScale = d3.scaleLinear().domain([0, 100]).range([0, chartHeight]);

    svg
      .append("g")
      .attr("transform", `translate(0, 0)`)
      .call(d3.axisTop(xScale).ticks(5))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 25)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text("Time");

    svg
      .append("g")
      .call(d3.axisLeft(yScale).ticks(5))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -35)
      .attr("x", -chartHeight / 2)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "10px")
      .text("SC (%)");

    svg
      .selectAll(".bar")
      .data(processedData)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("y", (d) => yScale(0))
      .attr("x", (d) => xScale(d.startTime))
      .attr("width", (d) => {
        const width = xScale(d.endTime) - xScale(d.startTime);
        return width > 0 ? width : 1;
      })
      .attr("height", (d) => yScale(d.residual_vector_norm))
      .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 1)
      .attr("opacity", 0.5)
      .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
      .attr("stroke-width", 0.1);
  }
</script>

<div bind:this={container} data-session-id={sessionId}></div>
