<script lang="ts">
  import { createEventDispatcher, afterUpdate } from "svelte";
  import * as d3 from "d3";

  export let chartData: any[] = [];
  export let paragraphColor: any[] = [];
  
  type ChartEvents = {
    pointSelected: {
      time: number;
      percentage: number;
      currentText: string;
      currentColor: string[];
    };
  };
  const dispatch = createEventDispatcher<ChartEvents>();

  let svgContainer: SVGSVGElement;
  let width = 400;
  export let height;
  const margin = { top: 20, right: 30, bottom: 40, left: 40 };

  let xScale: any;
  export let yScale;
  let zoomTransform = d3.zoomIdentity;

  let selectedPoint: any = null;
  let hoveredPoint: any = null;

  let zoom: any = null;
  let xAxisG: SVGGElement;
  let yAxisG: SVGGElement;

  export function resetZoom() {
    d3.select(svgContainer)
      .transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity);
  }

  $: if (chartData.length) {
    initChart();
  }

  $: if (xAxisG && yAxisG) {
    updateAxes();
  }
  
  afterUpdate(() => {
    if (svgContainer && zoom) {
      d3.select(svgContainer).call(zoom);
    }
  });


  function updateAxes() {
    if (!xScale || !yScale) return;

    const xAxis = d3.axisBottom(zoomTransform.rescaleX(xScale)).ticks(5);
    const yAxis = d3.axisLeft(zoomTransform.rescaleY(yScale)).ticks(5);

    d3.select(xAxisG).call(xAxis);
    d3.select(yAxisG).call(yAxis);
  }

  function initChart() {
    const minTime = 0;
    const maxTime = d3.max(chartData, (d) => d.time);
    // const Padding = Math.max(2, (maxTime - minTime) * 0.2);
    const padding = 0;

    xScale = d3
      .scaleLinear()
      .domain([minTime, maxTime + padding])
      .range([0, width - margin.left - margin.right]);

    yScale = d3
      .scaleLinear()
      .domain([0 - padding, 100 + padding])
      .range([height - margin.top - margin.bottom, 0]);

    zoom = d3
      .zoom()
      .scaleExtent([1, 5])
      .translateExtent([
        [0, 0],
        [width, height],
      ])
      .on("zoom", (event) => {
        zoomTransform = event.transform;
        updateAxes();
      });

    d3.select(svgContainer).call(zoom);
    updateAxes();
  }

  function handlePointClick(d) {
    selectedPoint = selectedPoint === d ? null : d;
    dispatch("pointSelected", d);
  }

  function scaledX(val) {
    if (!xScale) return 0;
    return zoomTransform.rescaleX(xScale)(val);
  }

  function scaledY(val) {
    if (!yScale) return 0;
    return zoomTransform.rescaleY(yScale)(val);
  }
</script>

<svg bind:this={svgContainer} {width} {height}>
  <defs>
    <clipPath id="clip">
      <rect
        x="0"
        y="0"
        width={width - margin.left - margin.right}
        height={height - margin.top - margin.bottom}
      />
    </clipPath>
    <clipPath id="clip-text">
      <rect
        x="-5"
        y="-20"
        width={width - margin.left - margin.right}
        height={height - margin.top - margin.bottom}
      />
    </clipPath>
  </defs>

  <g transform={`translate(${margin.left},${margin.top})`}>
    <g clip-path="url(#clip)">
      <g transform={zoomTransform.toString()}>
        {#each paragraphColor as d}
          <rect
            x={scaledX(d.xMin)}
            width={scaledX(d.xMax) - scaledX(d.xMin)}
            y={scaledY(d.yMax)}
            height={scaledY(d.yMin) - scaledY(d.yMax)}
            fill={d.backgroundColor}
          />
        {/each}

        {#each chartData as d}
          <circle
            cx={scaledX(d.time)}
            cy={scaledY(d.percentage)}
            r={selectedPoint === d ? 5 : hoveredPoint === d ? 5 : 2}
            fill={d.color}
            on:click={() => handlePointClick(d)}
            on:mouseover={() => (hoveredPoint = d)}
            on:mouseout={() => (hoveredPoint = null)}
            style="cursor: pointer;"
          />
        {/each}

        {#each chartData.filter((d) => d.isSuggestionOpen) as d}
          <path
            d={d3.symbol().type(d3.symbolTriangle).size(40)()}
            fill="#FFBBCC"
            transform={`translate(${scaledX(d.time)},${scaledY(d.percentage + 6)}) rotate(180)`}
          />
        {/each}
      </g>
    </g>

    <g clip-path="url(#clip-text)">
      {#if paragraphColor.length < 10}
        {#each paragraphColor as d}
          <text
            x={zoomTransform.applyX((scaledX(d.xMin) + scaledX(d.xMax)) / 2)}
            y={-3}
            text-anchor="middle"
            font-size="12px"
          >
            {d.value}
          </text>
        {/each}
      {/if}
      {#if paragraphColor.length > 10}
        {#each paragraphColor as d, index}
          {#if index === 0 || index % 4 === 0}
            <text
              x={zoomTransform.applyX((scaledX(d.xMin) + scaledX(d.xMax)) / 2)}
              y={-3}
              text-anchor="middle"
              font-size="12px"
            >
              {d.value}
            </text>
          {/if}
        {/each}
      {/if}
    </g>

    <g
      class="x-axis"
      transform={`translate(0, ${height - margin.top - margin.bottom})`}
      bind:this={xAxisG}
    ></g>
    <g class="y-axis" bind:this={yAxisG}></g>
  </g>
</svg>
