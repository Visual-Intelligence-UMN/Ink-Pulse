<script>
  import { onMount} from "svelte";
  import * as d3 from "d3";
  export let sessionId;
  export let similarityData;
  export let width = 150;
  export let height;
  export let yScale;

  let container;
  export let zoomTransform = d3.zoomIdentity;

  onMount(() => {
    if (similarityData && container) {
      renderChart();
    }
  });

  $: if (similarityData && container && zoomTransform !== d3.zoomIdentity) {
    renderChart();
  }

  function renderChart() {
    d3.select(container).selectAll("svg").remove();

    const processedData = similarityData.map((item, index) => ({
      startProgress: item.start_progress * 100,
      endProgress: item.end_progress * 100,
      residual_vector_norm: item.residual_vector_norm * 100,
      source: item.source,
    }));

    const margin = { top: 20, right: 0, bottom: 30, left: 50 };
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
        `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`
      )
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain([100, 0]).range([0, chartWidth]);
    const newyScale = zoomTransform.rescaleY(yScale.copy());

    svg.append("defs")
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

    svg
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
      .attr("stroke-width", 1)
      .attr("opacity", 0.5)
      .attr("stroke", d => d.source === "user" ? "#66C2A5" : "#FC8D62")
      .attr("stroke-width", 0.1)
      .attr("clip-path", "url(#clip_bar)");
  }
</script>

<div
  bind:this={container}
  data-session-id={sessionId}
></div>
