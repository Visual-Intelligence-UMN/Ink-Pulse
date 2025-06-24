<script>
    import { onMount } from "svelte";
    import * as d3 from "d3";

    export let sessionId;
    export let data;
    export let wholeData;

    let container;
    let prevData;
    let height = 125;
    let width = 150;

    onMount(() => {
        if (data && container) {
            renderChart();
            prevData = JSON.parse(JSON.stringify(data));
        }
    });

    function renderChart() {
        d3.select(container).selectAll("svg").remove();

        const wholeProcessedData = wholeData.map((d) => ({
            startProgress: d.start_progress * 100,
            endProgress: d.end_progress * 100,
            residual_vector_norm: d.residual_vector_norm,
            source: d.source,
        }));

        const processedData = data.map((d) => ({
            startProgress: d.start_progress * 100,
            endProgress: d.end_progress * 100,
            residual_vector_norm: d.residual_vector_norm,
            source: d.source,
        }));

        const margin = { top: 10, right: 5, bottom: 25, left: 40 };
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
                `0 0 ${chartWidth + margin.left + margin.right} ${chartHeight + margin.top + margin.bottom}`
            )
            .append("g")
            .attr("transform", `translate(${margin.left}, ${margin.top})`);

        const xScale = d3.scaleLinear().domain([1, 0]).range([0, chartWidth]);
        const yScale = d3.scaleLinear().domain([100, 0]).range([0, chartHeight]);

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
            .text("Semantic Change (%)");

        svg
            .append("g")
            .call(d3.axisLeft(yScale).ticks(5))
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -25)
            .attr("x", -chartHeight / 2)
            .attr("fill", "black")
            .attr("text-anchor", "middle")
            .style("font-size", "8px")
            .text("Progress (%)");


        svg
            .selectAll(".bar-whole")
            .data(wholeProcessedData)
            .enter()
            .append("rect")
            .attr("class", "bar-whole")
            .attr("y", (d) =>
                yScale(d.startProgress) < yScale(d.endProgress)
                    ? yScale(d.startProgress)
                    : yScale(d.endProgress)
            )
            .attr("x", (d) => xScale(d.residual_vector_norm))
            .attr("width", (d) => xScale(0) - xScale(d.residual_vector_norm))
            .attr("height", (d) =>
                Math.abs(yScale(d.startProgress) - yScale(d.endProgress))
            )
            .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
            .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
            .attr("stroke-width", 0.1)
            .attr("opacity", 0.2);

        svg
            .selectAll(".bar")
            .data(processedData)
            .enter()
            .append("rect")
            .attr("class", "bar")
            .attr("y", (d) =>
                yScale(d.startProgress) < yScale(d.endProgress)
                    ? yScale(d.startProgress)
                    : yScale(d.endProgress)
            )
            .attr("x", (d) => xScale(d.residual_vector_norm))
            .attr("width", (d) => xScale(0) - xScale(d.residual_vector_norm))
            .attr("height", (d) =>
                Math.abs(yScale(d.startProgress) - yScale(d.endProgress))
            )
            .attr("fill", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
            .attr("stroke", (d) => (d.source === "user" ? "#66C2A5" : "#FC8D62"))
            .attr("stroke-width", 0.1)
            .attr("opacity", 0.9);
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
    min-height: 150px;
    position: relative;
}
</style>