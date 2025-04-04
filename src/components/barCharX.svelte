<script>
    import { onMount } from "svelte";
    import * as d3 from "d3";
  
    export let sessionId;
    export let similarityData;
    export let width = 150;
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
        // sentenceNum: index + 1,
        startProgress: item.start_progress * 100,
        endProgress: item.end_progress * 100,
        dissimilarity: item.dissimilarity * 100,
        source: item.source,
        startTime: item.start_time / 60,
        endTime: item.end_time / 60,
      }));
  
      const margin = { top: 20, right: 0, bottom: 40, left: 50 };
      const chartWidth = width - margin.left - margin.right;
      const chartHeight = height - margin.top - margin.bottom;
  
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
      const yScale = d3.scaleLinear().domain([100, 0]).range([0, chartHeight]);
  
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
        .call(d3.axisLeft(yScale).ticks(5))
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", -35)
        .attr("x", -chartHeight / 2)
        .attr("fill", "black")
        .attr("text-anchor", "middle")
        .style("font-size", "10px")
        .text("Progress");
  
      svg
        .selectAll(".bar")
        .data(processedData)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("y", (d) => yScale(d.endProgress))
        .attr("x", (d) => xScale(d.dissimilarity))
        .attr("width", (d) => xScale(0) - xScale(d.dissimilarity))
        .attr("height", (d) => yScale(d.startProgress) - yScale(d.endProgress))
        .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
        .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
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
  
    // function filterTicks(ticks) {
    //   if (ticks.length <= 20) return ticks;
  
    //   const step = Math.ceil(ticks.length / 10);
    //   return ticks.filter((_, i) => i % step === 0);
    // }
  </script>
  
  <div
    bind:this={container}
    class="bar-chart-container"
    data-session-id={sessionId}
  ></div>
  
  <style>
    .bar-chart-container {
      margin-bottom: 0;
      margin-right: 0;
    }
  </style>
  