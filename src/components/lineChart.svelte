<script lang="ts">
  import { createEventDispatcher, afterUpdate, onMount } from "svelte";
  import * as d3 from "d3";

  export let chartData: any[] = [];
  export let paragraphColor: any[] = [];
  export let selectionMode: boolean = false;
  export let sharedSelection;
  export let xScaleLineChartFactor: number;

  type ChartEvents = {
    pointSelected: {
      time: number;
      percentage: number;
      currentText: string;
      currentColor: string[];
    };
    selectionChanged: {
      range: {
        sc: { min: number; max: number };
        progress: { min: number; max: number };
      };
      dataRange: {
        scRange: { min: number; max: number };
        progressRange: { min: number; max: number };
        timeRange: { min: number; max: number };
        sc: { sc: number[] };
      };
      data: any[];
      wholeData: any[];
      sessionId: string | null;
      sources: string[];
    };
    selectionCleared: {
      sessionId: string | null;
    };
  };
  const dispatch = createEventDispatcher<ChartEvents>();

  let svgContainer: SVGSVGElement;
  let width = 300;
  export let height;
  const margin = { top: 20, right: 0, bottom: 30, left: 0 };

  let xScale: any;
  export let yScale;
  export let zoomTransform = d3.zoomIdentity;
  let ZoomTransformIsInteral = d3.zoomIdentity;

  let selectedPoint: any = null;
  let hoveredPoint: any = null;

  let zoom: any = null;
  let xAxisG: SVGGElement;
  let yAxisG: SVGGElement;

  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;
  let brushGroup: any = null;
  let brushY: any = null;
  let brushX: any = null;
  let brushIsX: boolean = false;

  $: if (brushGroup && brushX && brushY) {
    if (brushIsX) {
      brushGroup.call(brushY.move, null);
      brushGroup.call(brushX);
    } else {
      brushGroup.call(brushX.move, null);
      brushGroup.call(brushY);
    }
  }

  onMount(() => {
    brushY = d3
      .brushY()
      .extent([
        [0, 0],
        [chartWidth, chartHeight],
      ])
      .on("start brush end", (event: any) => {
        if (event.sourceEvent) event.sourceEvent.stopPropagation();
      })
      .on("end", brushedY);

    brushX = d3
      .brushX()
      .extent([
        [0, 0],
        [chartWidth, chartHeight],
      ])
      .on("start brush end", (event: any) => {
        if (event.sourceEvent) event.sourceEvent.stopPropagation();
      })
      .on("end", brushedX);

    const plot = d3
      .select(svgContainer)
      .select("g")
      .select('g[clip-path="url(#clip)"]');

    brushGroup = plot.append("g").attr("class", "brush");
    brushGroup.call(brushX);
  });

  $: {
    if (brushGroup && brushX && brushY) {
      if (!selectionMode) {
        brushGroup.call(brushX.move, null);
        brushGroup.call(brushY.move, null);
        brushGroup.select(".overlay").style("pointer-events", "none");
      } else {
        brushGroup.select(".overlay").style("pointer-events", "all");
        if (
          sharedSelection &&
          sharedSelection.selectionSource != "lineChart_y" &&
          sharedSelection.selectionSource != "lineChart_x"
        ) {
          brushGroup.select(".selection").style("display", "none");
        } else {
          brushGroup.select(".selection").style("display", null);
        }
      }
    }
  }

  $: if(brushGroup && zoomTransform) {
    brushGroup.select(".selection").style("display", "none");
  }

  function getCircleOpacity(d) {
    if (!selectionMode) {
      // original logic
      return selectedPoint === d || hoveredPoint === d ? 1 : d.opacity;
    }

    if (
      !sharedSelection ||
      !sharedSelection.progressMin ||
      !sharedSelection.progressMax
    ) {
      // selectionMode active but no brush yet
      return 1;
    }

    const { progressMin, progressMax } = sharedSelection;
    const inRange = d.percentage >= progressMin && d.percentage <= progressMax;
    return inRange ? 1 : 0.01;
  }

  function brushedY(event) {
    if (!event.selection) {
      sharedSelection = null;
      dispatch("selectionCleared", { sessionId: null });
      return;
    }

    const zy = zoomTransform.rescaleY(yScale);

    const [y0, y1] = event.selection;
    const progressMin = zy.invert(y1);
    const progressMax = zy.invert(y0);
    sharedSelection = {
      progressMin,
      progressMax,
      selectionSource: "lineChart_y",
    };

    dispatch("selectionChanged", {
      range: {
        sc: { min: 0, max: 1 },
        progress: { min: progressMin, max: progressMax },
      },
      dataRange: {
        scRange: { min: 0, max: 1 },
        progressRange: { min: progressMin, max: progressMax },
        timeRange: { min: 0, max: d3.max(chartData, (d) => d.time) },
        sc: { sc: [] },
      },
      data: chartData.filter(
        (p) => p.percentage >= progressMin && p.percentage <= progressMax
      ),
      wholeData: chartData,
      sessionId: null,
      sources: [],
    });
  }

  function brushedX(event) {
    if (!event.selection) {
      sharedSelection = null;
      dispatch("selectionCleared", { sessionId: null });
      return;
    }

    const zx = zoomTransform.rescaleX(xScale);

    const [x0, x1] = event.selection;
    const t0 = zx.invert(x0);
    const t1 = zx.invert(x1);

    // Filter points that are inside the selected time range
    const insidePoints = chartData.filter((p) => p.time >= t0 && p.time <= t1);

    if (!insidePoints.length) {
      // No points inside selection — clear or fallback
      sharedSelection = null;
      return;
    }

    // First and last points inside the selection
    const left = insidePoints[0];
    const right = insidePoints[insidePoints.length - 1];

    // Map to their percentage/progress
    const progressMin = Math.min(left.percentage, right.percentage);
    const progressMax = Math.max(left.percentage, right.percentage);

    sharedSelection = {
      progressMin,
      progressMax,
      selectionSource: "lineChart_x",
    };

    dispatch("selectionChanged", {
      range: {
        sc: { min: 0, max: 1 },
        progress: { min: progressMin, max: progressMax },
      },
      dataRange: {
        scRange: { min: 0, max: 1 },
        progressRange: { min: progressMin, max: progressMax },
        timeRange: { min: t0, max: t1 },
        sc: { sc: [] },
      },
      data: insidePoints,
      wholeData: chartData,
      sessionId: null,
      sources: [],
    });
  }

  export function resetZoom() {
    d3.select(svgContainer)
      .transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity);
  }

  $: if (chartData.length) {
    updateAxes();
    initChart();
  }

  $: if (xAxisG && yAxisG) {
    updateAxes();
  }

  // $: if (zoom) {
  //   console.log("zoomTransform:", zoomTransform);
  // }

  // helper code for handling zooming from outside the component
  // When getting a zoomTransform from outside the component with only y and k values,
  // x value is calculated based on the data points that have closest y value to the zoomTransform.y.

  $: if (zoomTransform && ZoomTransformIsInteral.k !== zoomTransform.k) {
    // console.log("zooming:", zoomTransform);

    if (ZoomTransformIsInteral.k !== zoomTransform.k) {
      let centerY =
        (zoomTransform.y - ZoomTransformIsInteral.y) /
        (ZoomTransformIsInteral.k - zoomTransform.k);
      let { x, y } = findPointAtY(centerY);
      let centerX =
        x * (ZoomTransformIsInteral.k - zoomTransform.k) +
        ZoomTransformIsInteral.x;
      const maxTranslateX = 0;
      const minTranslateX =
        -(width - margin.left - margin.right) * (zoomTransform.k - 1);
      const clampedY = Math.max(
        minTranslateX,
        Math.min(centerX, maxTranslateX)
      );
      zoomTransform.x = clampedY;
      ZoomTransformIsInteral = zoomTransform;
      d3.select(svgContainer).call(zoom.transform, zoomTransform);
      updateAxes();
    }
  }

  afterUpdate(() => {
    if (svgContainer && zoom) {
      d3.select(svgContainer).call(zoom);
    }
  });

  function findPointAtY(yCoordinate: number) {
    let closestPoint = null;
    let minDistance = Infinity;

    for (const d of chartData) {
      const scaledYValue = scaledY(d.percentage);
      const distance = Math.abs(scaledYValue - yCoordinate);

      if (distance < minDistance) {
        minDistance = distance;
        closestPoint = d;
      }
    }

    if (closestPoint) {
      const x = scaledX(closestPoint.time);
      const y = scaledY(closestPoint.percentage);
      return { x, y };
    }

    return null;
  }

  function updateAxes() {
    if (!xScale || !yScale) return;

    const xAxis = d3.axisBottom(zoomTransform.rescaleX(xScale)).ticks(5);
    const yAxis = d3.axisRight(zoomTransform.rescaleY(yScale)).ticks(5);

    d3.select(xAxisG).call(xAxis);
    d3.select(yAxisG).call(yAxis);

    const ticks = d3.select(xAxisG).selectAll(".tick text");
    ticks
      .filter((_, i) => i === 0)
      .attr("text-anchor", "start")
      .attr("dx", "0.01em");
  }

  function initChart() {
    const minTime = 0;
    const maxTime = d3.max(chartData, (d) => d.time);

    xScale = d3
      .scaleLinear()
      .domain([minTime, maxTime])
      .range([0, width - margin.left - margin.right]);

    xScaleLineChartFactor = (width - margin.left - margin.right) / ((maxTime - minTime) * 60);

    zoom = d3
      .zoom()
      .scaleExtent([1, 5])
      .translateExtent([
        [0, 0],
        [width, height],
      ])
      .on("zoom", (event) => {
        let transform = event.transform;
        const maxTranslateY = 0;
        const minTranslateY =
          -(height - margin.top - margin.bottom) * (transform.k - 1);
        const clampedY = Math.max(
          minTranslateY,
          Math.min(transform.y, maxTranslateY)
        );
        zoomTransform = d3.zoomIdentity
          .translate(transform.x, clampedY)
          .scale(transform.k);
        ZoomTransformIsInteral = zoomTransform;
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
    return xScale ? xScale(val) : 0;
  }

  function scaledY(val) {
    return yScale ? yScale(val) : 0;
  }
</script>

<svg bind:this={svgContainer} {width} {height} style="vertical-align: top">
  <defs>
    <clipPath id="clip">
      <rect
        x="0"
        y="0"
        width={width - margin.left - margin.right}
        height={height - margin.top - margin.bottom}
      />
    </clipPath>
    <!-- <clipPath id="clip-text">
      <rect
        x="-5"
        y="-20"
        width={width - margin.left - margin.right}
        height={height - margin.top - margin.bottom}
      />
    </clipPath> -->
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
      </g>

      <g>
        {#each chartData.filter((d) => !d.isSuggestionOpen) as d (d.index)}
          <circle
            cx={zoomTransform.applyX(scaledX(d.time))}
            cy={zoomTransform.applyY(scaledY(d.percentage))}
            r={selectedPoint?.index === d.index
              ? 5
              : hoveredPoint?.index === d.index
                ? 5
                : 2}
            fill={d.color}
            opacity={getCircleOpacity(d)}
            on:click={() => handlePointClick(d)}
            on:mouseover={() => (hoveredPoint = d)}
            on:mouseout={() => (hoveredPoint = null)}
            style="cursor: pointer;"
          />
        {/each}

        {#each chartData.filter((d) => d.isSuggestionOpen) as d}
          <path
            d={d3.symbol().type(d3.symbolTriangle).size(40)()}
            fill="#ffffff"
            stroke="#aaaaaa"
            stroke-width="1"
            opacity={d.opacity + 0.29}
            transform={`translate(${zoomTransform.applyX(scaledX(d.time))},${zoomTransform.applyY(scaledY(d.percentage + 6 / zoomTransform.k))}) rotate(180)`}
          />
        {/each}
      </g>
    </g>

    <!-- <g clip-path="url(#clip-text)">
      {#if paragraphColor.length < 10}
        {#each paragraphColor as d, index}
          <text
            x={zoomTransform.applyX((scaledX(d.xMin) + scaledX(d.xMax)) / 2) + (index === 0 ? 3 : 0)}
            y={-5}
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
              x={zoomTransform.applyX((scaledX(d.xMin) + scaledX(d.xMax)) / 2) + (index === 0 ? 3 : 0)}
              y={-3}
              text-anchor="middle"
              font-size="12px"
            >
              {d.value}
            </text>
          {/if}
        {/each}
      {/if}
    </g> -->

    <g
      class="x-axis"
      transform={`translate(0, ${height - margin.top - margin.bottom})`}
      bind:this={xAxisG}
    ></g>
    <text
      x={width / 2}
      y={height - margin.top - 5}
      text-anchor="middle"
      font-size="10px"
      fill="black"
    >
      Time (min)
    </text>
    <g class="y-axis" bind:this={yAxisG} style="display: none"></g>
  </g>
</svg>

{#if selectionMode}
  <div
    class="brush-toggle"
    style={`width:${width}px; margin-top: 20px; translate: -15px`}
  >
    <span class="label" class:active={!brushIsX}>Progress</span>
    <label class="switch" aria-label="Toggle brush axis">
      <input type="checkbox" bind:checked={brushIsX} />
      <span class="slider"></span>
    </label>
    <span class="label" class:active={brushIsX}>Time</span>
  </div>
{/if}

<style>
  .brush-toggle {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin: 10px auto 0;
  }

  .brush-toggle .label {
    font-size: 15px;
    color: #555;
    user-select: none;
  }

  .switch {
    position: relative;
    display: inline-block;
    width: 48px;
    height: 26px;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  input:checked + .slider {
    background-color: #ffbbcc;
  }

  input:checked + .slider::before {
    transform: translateX(22px); /* 48 - 22 - 2*2 = 22 */
  }

  .slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: #ffbbcc;
    transition: 0.2s;
    border-radius: 30px;
  }

  .slider::before {
    position: absolute;
    content: "";
    height: 22px;
    width: 22px;
    left: 2px;
    bottom: 2px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  }

  .brush-toggle .label {
    font-size: 15px;
    color: #777;
    user-select: none;
    font-weight: normal;
  }

  .brush-toggle .label.active {
    color: black;
    font-weight: bold;
  }
</style>
