<script>
  import { onMount, afterUpdate } from "svelte";
  import * as d3 from "d3";

  export let sessionId;
  export let data;
  export let wholeData;
  export let selectedRange;
  export let margin_right = 5;

  let container;
  let prevSelectedRange;
  let prevData;
  let width = 150;
  let height = 120;

  const colorMap = {
  user: "#66C2A5",
  api: "#FC8D62",
  };

  import colors from "./colors.js";
  const colorPalette = colors("7fc97fbeaed4fdc086ffff99386cb0f0027fbf5b17666666");
  let colorIndex = 0;

  onMount(() => {
    if (data && container) {
      renderChart();
    }
  });

  function isRangeChanged(a, b) {
    if (!a || !b) return true;
    return (
      a.sc?.min !== b.sc?.min ||
      a.sc?.max !== b.sc?.max ||
      a.progress?.min !== b.progress?.min ||
      a.progress?.max !== b.progress?.max
    );
  }

  afterUpdate(() => {
    if (
      data &&
      container &&
      (isRangeChanged(prevSelectedRange, selectedRange) || prevData !== data)
    ) {
      renderChart();
      prevSelectedRange = { ...selectedRange };
      prevData = data;
    }
  });

  function renderChart() {
    d3.select(container).selectAll("svg").remove();

    const wholeProcessedData = wholeData.map((d) => ({
      startProgress: d.startProgress,
      endProgress: d.endProgress,
      residual_vector_norm: d.residual_vector_norm,
      source: d.source,
    }));

    const processedData = data.map((d) => ({
      startProgress: d.startProgress,
      endProgress: d.endProgress,
      residual_vector_norm: d.residual_vector_norm,
      source: d.source,
    }));

    const margin = { top: 10, right: margin_right, bottom: 25, left: 40 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    const svg = d3
      .select(container)
      .append("svg")
      .style("display", "block")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr(
        "viewBox",
        `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`,
      )
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain([1, 0]).range([0, chartWidth]);
    const newyScale = d3.scaleLinear().domain([100, 0]).range([0, chartHeight]);

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
      .call(d3.axisBottom(xScale).ticks(0))
      .append("text")
      .attr("x", chartWidth / 2)
      .attr("y", 20)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "8px")
      .text("Semantic Change");

    svg
      .append("g")
      .call(d3.axisLeft(newyScale).ticks(5))
      .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -25)
      .attr("x", -chartHeight / 2)
      .attr("fill", "black")
      .attr("text-anchor", "middle")
      .style("font-size", "8px")
      .text("Writing length");

    svg
      .selectAll(".bar-whole")
      .data(wholeProcessedData)
      .enter()
      .append("rect")
      .attr("class", "bar-whole")
      .attr("y", (d) =>
        newyScale(d.startProgress) < newyScale(d.endProgress)
          ? newyScale(d.startProgress)
          : newyScale(d.endProgress),
      )
      .attr("x", (d) => xScale(d.residual_vector_norm))
      .attr("width", (d) => {
        const x1 = xScale(d.residual_vector_norm);
        const x2 = xScale(0);
        return isNaN(x1) || isNaN(x2) ? 0 : (x2 - x1);
      })
      .attr("height", (d) => {
        const y1 = newyScale(d.startProgress);
        const y2 = newyScale(d.endProgress);
        return isNaN(y1) || isNaN(y2) ? 0 : Math.abs(y1 - y2);
      })

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
      .attr("stroke-width", 0.1)
      .attr("opacity", 0.2)
      .attr("clip-path", `url(#clip_bar_preview_${sessionId})`);

    const bars = svg
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
      .attr("width", (d) => {
        const x1 = xScale(d.residual_vector_norm);
        const x2 = xScale(0);
        return isNaN(x1) || isNaN(x2) ? 0 : (x2 - x1);
      })
      .attr("height", (d) => {
        const y1 = newyScale(d.startProgress);
        const y2 = newyScale(d.endProgress);
        return isNaN(y1) || isNaN(y2) ? 0 : Math.abs(y1 - y2);
      })
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
      .attr("stroke-width", 0.1)
      .attr("opacity", 0.9)
      .attr("clip-path", `url(#clip_bar_preview_${sessionId})`);

    if (selectedRange) {
      const { sc, progress } = selectedRange;

      svg
        .append("rect")
        .attr("class", "selection-rect")
        .attr("x", xScale(1))
        .attr("y", newyScale(progress.max))
        .attr("width", xScale(0) - xScale(1))
        .attr("height", newyScale(progress.min) - newyScale(progress.max))
        .attr("fill", "none")
        .attr("stroke", "#000")
        .attr("stroke-width", 0.1)
        .attr("stroke-dasharray", "3,3")
        .attr("pointer-events", "none");

      bars.attr("opacity", (d) => {
        const barMinX = Math.min(d.residual_vector_norm, 0);
        const barMaxX = Math.max(d.residual_vector_norm, 0);

        const xOverlap = !(barMaxX < sc.min || barMinX > sc.max);

        const barStart = d.startProgress;
        const barEnd = d.endProgress;

        const yOverlap =
          (barStart >= progress.min && barStart <= progress.max) ||
          (barEnd >= progress.min && barEnd <= progress.max) ||
          (barStart <= progress.min && barEnd >= progress.max);

        const isSelected = xOverlap && yOverlap;

        return isSelected ? 0.9 : 0.1;
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
    position: relative;
  }
</style>