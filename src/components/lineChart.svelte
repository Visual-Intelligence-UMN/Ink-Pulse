<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import * as d3 from 'd3';
  
    export let chartData: any[] = [];
    export let paragraphColor: any[] = [];
  
    type ChartEvents = {
      pointSelected: { time: number; percentage: number; currentText: string; currentColor: string[] };
    };
    const dispatch = createEventDispatcher<ChartEvents>();
  
    let svgContainer: SVGSVGElement;
    let width = 300;
    let height = 200;
    const margin = { top: 20, right: 30, bottom: 20, left: 40 };
  
    let xScale: any, yScale: any;
    let zoomTransform = d3.zoomIdentity;
  
    let selectedPoint: any = null;
    let hoveredPoint: any = null;

    let zoom: any;

    export function resetZoom() {
        d3.select(svgContainer)
            .transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity);
    }
  
    $: if (chartData.length) {
      initChart();
    }
  
    function initChart() {
      const minTime = d3.min(chartData, d => d.time) ?? 0;
      const maxTime = d3.max(chartData, d => d.time) ?? 10;
      const padding = Math.max(2, (maxTime - minTime) * 0.2);
  
      xScale = d3.scaleLinear()
        .domain([minTime - padding, maxTime + padding])
        .range([0, width - margin.left - margin.right]);
  
      yScale = d3.scaleLinear()
        .domain([0 - padding, 100 + padding])
        .range([height - margin.top - margin.bottom, 0]);
  
      zoom = d3.zoom()
        .scaleExtent([1, 5])
        .translateExtent([[0, 0], [width, height]])
        .on("zoom", (event) => {
          zoomTransform = event.transform;
        });
  
      d3.select(svgContainer).call(zoom);
    }
  
    function handlePointClick(d) {
      selectedPoint = selectedPoint === d ? null : d;
      dispatch('pointSelected', d);
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
  
  <svg bind:this={svgContainer} width={width} height={height}>
    <g transform={`translate(${margin.left},${margin.top})`}>
    <g transform={zoomTransform.toString()}>
      {#each paragraphColor as d}
        <rect
          x={scaledX(d.xMin)}
          width={scaledX(d.xMax) - scaledX(d.xMin)}
          y={scaledY(d.yMax)}
          height={scaledY(d.yMin) - scaledY(d.yMax)}
          fill={d.backgroundColor}
        />
        <text
          x={(scaledX(d.xMin) + scaledX(d.xMax)) / 2}
          y={scaledY(d.yMax) - 5}
          text-anchor="middle"
          font-size="12px"
        >
          {d.value}
        </text>
      {/each}

      {#each chartData as d}
        <circle
          cx={scaledX(d.time)}
          cy={scaledY(d.percentage)}
          r={selectedPoint === d ? 5 : hoveredPoint === d ? 5 : 2}
          fill={d.color}
          on:click={() => handlePointClick(d)}
          on:mouseover={() => hoveredPoint = d}
          on:mouseout={() => hoveredPoint = null}
          style="cursor: pointer;"
        />
      {/each}
  
      {#each chartData.filter(d => d.isSuggestionOpen) as d}
        <path
          d={d3.symbol().type(d3.symbolTriangle).size(40)()}
          fill="#FFBBCC"
          transform={`translate(${scaledX(d.time)},${scaledY(d.percentage + 6)}) rotate(180)`}
        />
      {/each}
    </g>
    </g>
  </svg>
  