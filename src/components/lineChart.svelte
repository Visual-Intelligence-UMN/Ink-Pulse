<script lang="ts">
  import { createEventDispatcher, afterUpdate, onMount } from "svelte";
  import * as d3 from "d3";

  export let chartData: any[] = [];
  export let paragraphColor: any[] = [];
  export let selectionMode: boolean = false;
  export let sharedSelection;
  export let xScaleLineChartFactor: number;
  export let similarityData: any[] = [];
  export let xAxisField = "time"; // 新增：X轴字段
  export let yAxisField = "progress"; // 新增：Y轴字段

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
      selectionSource: string | null;
    };
    selectionCleared: {
      sessionId: string | null;
    };
  };
  const dispatch = createEventDispatcher<ChartEvents>();

  let svgContainer: SVGSVGElement;
  let width = 300;
  export let height;
  const margin = { top: 20, right: 50, bottom: 30, left: 0 };

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
  export let brushIsX: boolean = false;

  // 属性配置池（细粒度数据）
  const attributeConfig: any = {
    time: {
      label: "Time (min)",
      getValue: (item: any) => item.time,
      domain: null, // 动态计算
    },
    progress: {
      label: "Writing Length",
      getValue: (item: any) => item.percentage,
      domain: [0, 100],
    },
  };

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

  $: if (brushGroup && zoomTransform) {
    brushGroup.select(".selection").style("display", "none");
  }

  function getCircleOpacity(d) {
    if (!selectionMode) {
      // original logic
      return selectedPoint === d || hoveredPoint === d ? 1 : d.opacity;
    }

    if (!sharedSelection) {
      // selectionMode active but no brush yet
      return 1;
    }

    // 通用格式：检查字段匹配
    if (
      sharedSelection.xMin !== undefined &&
      sharedSelection.xMax !== undefined &&
      sharedSelection.xField
    ) {
      // X 方向选择
      if (sharedSelection.xField === xAxisField) {
        const xVal = getXValue(d);
        const inRange =
          xVal >= sharedSelection.xMin && xVal <= sharedSelection.xMax;
        return inRange ? 1 : 0.01;
      }
    }

    if (
      sharedSelection.yMin !== undefined &&
      sharedSelection.yMax !== undefined &&
      sharedSelection.yField
    ) {
      // Y 方向选择
      if (sharedSelection.yField === yAxisField) {
        const yVal = getYValue(d);
        const inRange =
          yVal >= sharedSelection.yMin && yVal <= sharedSelection.yMax;
        return inRange ? 1 : 0.01;
      }
    }

    // 向后兼容：time-based selection
    if (
      sharedSelection.selectionSource === "lineChart_x" &&
      sharedSelection.timeMin !== undefined &&
      sharedSelection.timeMax !== undefined
    ) {
      const { timeMin, timeMax } = sharedSelection;
      const inTimeRange = d.time >= timeMin && d.time <= timeMax;
      return inTimeRange ? 1 : 0.01;
    }

    // 向后兼容：progress-based selection
    if (
      sharedSelection.progressMin !== undefined &&
      sharedSelection.progressMax !== undefined
    ) {
      const { progressMin, progressMax } = sharedSelection;
      const inProgressRange =
        d.percentage >= progressMin && d.percentage <= progressMax;
      return inProgressRange ? 1 : 0.01;
    }

    return 1;
  }

  function brushedY(event) {
    if (!event.selection) {
      sharedSelection = null;
      dispatch("selectionCleared", { sessionId: null });
      return;
    }

    const [y0, y1] = event.selection;
    const zx = zoomTransform.rescaleX(xScale);
    const zy = zoomTransform.rescaleY(yScale);

    const x0 = 0;
    const x1 = chartWidth;

    const insidePoints = chartData.filter((d) => {
      const px = zx(getXValue(d));
      const py = zy(getYValue(d));
      return px >= x0 && px <= x1 && py >= y0 && py <= y1;
    });

    if (!insidePoints.length) {
      sharedSelection = null;
      dispatch("selectionCleared", { sessionId: null });
      return;
    }

    const matchedPoints = insidePoints
      .map((d) => {
        const matchedSim = similarityData.find(
          (s) =>
            s.start_progress * 100 <= d.percentage &&
            s.end_progress * 100 >= d.percentage,
        );

        if (!matchedSim) return null;

        return {
          ...d,
          residual_vector_norm: matchedSim.residual_vector_norm,
        };
      })
      .filter((d) => d !== null);

    const yMin = d3.min(insidePoints, (d) => getYValue(d));
    const yMax = d3.max(insidePoints, (d) => getYValue(d));
    const scValues = matchedPoints.map((d) => d.residual_vector_norm || 0);
    const scMin = d3.min(scValues) || 0;
    const scMax = d3.max(scValues) || 1;
    const sources = insidePoints.map((d) => d.source || "user");
    const tMin = d3.min(insidePoints, (d) => d.time);
    const tMax = d3.max(insidePoints, (d) => d.time);

    sharedSelection = {
      yMin,
      yMax,
      yField: yAxisField,
      xField: xAxisField,
      selectionSource: "lineChart_y",
      // 向后兼容
      progressMin: yAxisField === "progress" ? yMin : null,
      progressMax: yAxisField === "progress" ? yMax : null,
      timeMin: yAxisField === "time" ? yMin : null,
      timeMax: yAxisField === "time" ? yMax : null,
    };

    // dispatch("selectionChanged", {
    //   range: {
    //     sc: { min: scMin, max: scMax },
    //     progress: { min: progressMin, max: progressMax },
    //   },
    //   dataRange: {
    //     scRange: { min: scMin, max: scMax },
    //     progressRange: { min: progressMin, max: progressMax },
    //     timeRange: { min: tMin, max: tMax },
    //     sc: { sc: scValues },
    //   },
    //   data: insidePoints,
    //   wholeData: chartData,
    //   sessionId: null,
    //   sources: sources,
    //   selectionSource: "lineChart_y",
    // });
  }

  function brushedX(event) {
    if (!event.selection) {
      sharedSelection = null;
      dispatch("selectionCleared", { sessionId: null });
      return;
    }

    const [x0, x1] = event.selection;
    const zx = zoomTransform.rescaleX(xScale);

    const xMin = zx.invert(x0);
    const xMax = zx.invert(x1);
    const insidePoints = chartData.filter((d) => {
      const xVal = getXValue(d);
      return xVal >= xMin && xVal <= xMax;
    });

    if (!insidePoints.length) {
      sharedSelection = null;
      dispatch("selectionCleared", { sessionId: null });
      return;
    }

    const matchedPoints = insidePoints
      .map((d) => {
        const matchedSim = similarityData.find(
          (s) =>
            s.start_progress * 100 <= d.percentage &&
            s.end_progress * 100 >= d.percentage,
        );

        if (!matchedSim) return null;

        return {
          ...d,
          residual_vector_norm: matchedSim.residual_vector_norm,
        };
      })
      .filter((d) => d !== null);

    const scValues = matchedPoints.map((d) => d.residual_vector_norm || 0);
    const scMin = d3.min(scValues) || 0;
    const scMax = d3.max(scValues) || 1;

    const progressMin = d3.min(insidePoints, (d) => d.percentage);
    const progressMax = d3.max(insidePoints, (d) => d.percentage);
    const sources = insidePoints.map((d) => d.source || "user");
    const timeMin = d3.min(insidePoints, (d) => d.time);
    const timeMax = d3.max(insidePoints, (d) => d.time);

    sharedSelection = {
      xMin,
      xMax,
      xField: xAxisField,
      yField: yAxisField,
      selectionSource: "lineChart_x",
      // 向后兼容
      progressMin: xAxisField === "progress" ? xMin : progressMin,
      progressMax: xAxisField === "progress" ? xMax : progressMax,
      timeMin: xAxisField === "time" ? xMin : timeMin,
      timeMax: xAxisField === "time" ? xMax : timeMax,
    };

    // dispatch("selectionChanged", {
    //   range: {
    //     sc: { min: scMin, max: scMax },
    //     progress: { min: progressMin, max: progressMax },
    //   },
    //   dataRange: {
    //     scRange: { min: scMin, max: scMax },
    //     progressRange: { min: progressMin, max: progressMax },
    //     timeRange: { min: timeMin, max: timeMax },
    //     sc: { sc: scValues },
    //   },
    //   data: insidePoints,
    //   wholeData: chartData,
    //   sessionId: null,
    //   sources: sources,
    //   selectionSource: "lineChart_x",
    // });
  }

  export function resetZoom() {
    d3.select(svgContainer)
      .transition()
      .duration(750)
      .call(zoom.transform, d3.zoomIdentity);
  }

  // 监听轴字段变化，重新初始化图表
  $: if (xAxisField && yAxisField && chartData.length) {
    initChart();
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
    const xConfig = attributeConfig[xAxisField];
    const yConfig = attributeConfig[yAxisField];

    // 动态计算 X 轴 domain
    let xDomain = xConfig.domain;
    if (!xDomain) {
      const xValues = chartData.map((d) => xConfig.getValue(d));
      const minX = Math.min(...xValues);
      const maxX = Math.max(...xValues);
      xDomain = [minX, maxX];
    }

    // 动态计算 Y 轴 domain
    let yDomain = yConfig.domain;
    if (!yDomain) {
      const yValues = chartData.map((d) => yConfig.getValue(d));
      const minY = Math.min(...yValues);
      const maxY = Math.max(...yValues);
      yDomain = [minY, maxY];
    }

    xScale = d3
      .scaleLinear()
      .domain(xDomain)
      .range([0, width - margin.left - margin.right]);

    xScaleLineChartFactor =
      (width - margin.left - margin.right) /
      ((xDomain[1] - xDomain[0]) * (xAxisField === "time" ? 60 : 1));

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

  // 动态获取点的 X/Y 值
  function getXValue(d: any) {
    return attributeConfig[xAxisField]?.getValue(d) ?? 0;
  }

  function getYValue(d: any) {
    return attributeConfig[yAxisField]?.getValue(d) ?? 0;
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
  </defs>

  <g transform={`translate(${margin.left},${margin.top})`}>
    <g clip-path="url(#clip)">
      {#each paragraphColor as d}
        <rect
          x={zoomTransform.applyX(scaledX(d.xMin))}
          width={zoomTransform.k * (scaledX(d.xMax) - scaledX(d.xMin))}
          y={zoomTransform.applyY(scaledY(d.yMax))}
          height={zoomTransform.k * (scaledY(d.yMin) - scaledY(d.yMax))}
          fill={d.backgroundColor}
        />
      {/each}

      <g>
        {#each chartData.filter((d) => !d.isSuggestionOpen) as d (d.index)}
          <circle
            cx={zoomTransform.applyX(scaledX(getXValue(d)))}
            cy={zoomTransform.applyY(scaledY(getYValue(d)))}
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
            fill={d.isSuggestionAccept ? "#ffffff" : "#cccccc"}
            stroke="#aaaaaa"
            stroke-width="1"
            opacity={d.opacity + 0.29}
            transform={`translate(${zoomTransform.applyX(scaledX(getXValue(d)))},${zoomTransform.applyY(scaledY(getYValue(d) + 6 / zoomTransform.k))}) rotate(180)`}
          />
        {/each}
      </g>
    </g>

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
      {attributeConfig[xAxisField]?.label ?? "X"}
    </text>
    <g class="y-axis" bind:this={yAxisG} transform="translate({chartWidth}, 0)"
    ></g>
    <text
      transform="rotate(-90)"
      x={-chartHeight / 2}
      y={width - 10}
      text-anchor="middle"
      font-size="10px"
      fill="black"
    >
      {attributeConfig[yAxisField]?.label ?? "Y"}
    </text>
  </g>
</svg>

<style>
</style>
