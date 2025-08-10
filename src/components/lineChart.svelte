<script lang="ts">
  import { createEventDispatcher, afterUpdate, onMount} from "svelte";
  import * as d3 from "d3";

  export let chartData: any[] = [];
  export let paragraphColor: any[] = [];
  export let selectionMode: boolean = false;
  export let sharedSelection

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
  let brush: any = null;
  onMount(() => {
    brush = d3
      .brushY()
      .extent([
        [0, 0],
      [chartWidth, chartHeight],
    ])
    .extent([[0, 0], [chartWidth, chartHeight]])
    .on('start brush end', (event: any) => {
      if (event.sourceEvent) event.sourceEvent.stopPropagation();
    })
    .on("end", brushedY);
    brushGroup = d3.select(svgContainer).append("g").attr("class", "brush");
    brushGroup.call(brush);
  })

  $: {
    if (brushGroup && brush) {
      if (!selectionMode) {
        brushGroup.call(brush.move, null);
        brushGroup.select(".overlay").style("pointer-events", "none");
      }
      else {
        brushGroup.select(".overlay").style("pointer-events", "all");
        if (sharedSelection && sharedSelection.selectionSource != "lineChart_y") {
          brushGroup.select(".selection").style("display", "none");
        }
        else {
          brushGroup.select(".selection").style("display", null);
        }
      }
    }
  }

function getCircleOpacity(d) {
  if (!selectionMode) {
    // original logic
    return selectedPoint === d || hoveredPoint === d ? 1 : d.opacity;
  }

  if (!sharedSelection || !sharedSelection.progressMin || !sharedSelection.progressMax) {
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
      return;
    }

    const [y0, y1] = event.selection || [];
    const progressMin = yScale.invert(y1);
    const progressMax = yScale.invert(y0);
    sharedSelection = { progressMin, progressMax, selectionSource: "lineChart_y" };
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
        Math.min(centerX, maxTranslateX),
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
          Math.min(transform.y, maxTranslateY),
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
            fill="#FFBBCC"
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
