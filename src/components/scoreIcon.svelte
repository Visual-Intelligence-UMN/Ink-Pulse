<script>
  import { onMount } from "svelte";

  export let llmJudgeScore = null;
  export let size = 20;
  export let showTooltip = true;
  export let sessionId = "";

  let circleElement;
  let tooltip = null;

  const SCORE_THRESHOLDS = {
    excellent: 8,
    good: 6,
    average: 4,
    poor: 0,
  };

  $: qualityScore = llmJudgeScore || 0;
  $: scoreLevel = getScoreLevel(qualityScore);
  $: progressPercentage = normalizeScoreToPercentage(qualityScore);
  $: strokeColor = getColorByScoreLevel(scoreLevel);

  function getScoreLevel(score) {
    if (score >= SCORE_THRESHOLDS.excellent) return "excellent";
    if (score >= SCORE_THRESHOLDS.good) return "good";
    if (score >= SCORE_THRESHOLDS.average) return "average";
    return "poor";
  }

  function normalizeScoreToPercentage(score) {
    return Math.max(5, (score / 10) * 100);
  }

  function getColorByScoreLevel(level) {
    const colors = {
      excellent: "#2E7D32", // green
      good: "#1976D2", // blue
      average: "#F57C00", // orange
      poor: "#D32F2F", // red
    };
    return colors[level] || colors.poor;
  }

  function getScoreLevelText(level) {
    const texts = {
      excellent: "Excellent",
      good: "Good",
      average: "Average",
      poor: "Poor",
    };
    return texts[level] || "Unknown";
  }

  function handleMouseEnter(event) {
    if (!showTooltip) return;

    // 创建tooltip
    tooltip = document.createElement("div");
    tooltip.className = "semantic-tooltip";

    const levelText = getScoreLevelText(scoreLevel);

    tooltip.innerHTML = `
      <div class="tooltip-title">Writing Quality Score</div>
      <div class="tooltip-content">
        <div>Type: LLM Judge Score</div>
        <div>Score: ${qualityScore.toFixed(0)}/10</div>
        <div>Level: ${levelText}</div>
        <div>Session: ${sessionId.slice(0, 6)}...</div>
      </div>
    `;

    document.body.appendChild(tooltip);

    const rect = circleElement.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft =
      window.pageXOffset || document.documentElement.scrollLeft;

    const tooltipRect = tooltip.getBoundingClientRect();
    const tooltipWidth = tooltipRect.width;
    const tooltipHeight = tooltipRect.height;

    const elementCenterX = rect.left + rect.width / 2;
    const elementCenterY = rect.top + rect.height / 2;

    let tooltipLeft = elementCenterX - tooltipWidth / 2;
    let tooltipTop = elementCenterY - tooltipHeight - 10;

    if (tooltipLeft < 10) tooltipLeft = 10;
    if (tooltipLeft + tooltipWidth > window.innerWidth - 10) {
      tooltipLeft = window.innerWidth - tooltipWidth - 10;
    }

    if (tooltipTop < 10) {
      tooltipTop = elementCenterY + rect.height / 2 + 10;
    }

    tooltip.style.left = `${tooltipLeft}px`;
    tooltip.style.top = `${tooltipTop}px`;
    tooltip.style.position = "fixed";
  }

  function handleMouseLeave() {
    if (tooltip) {
      document.body.removeChild(tooltip);
      tooltip = null;
    }
  }

  onMount(() => {
    return () => {
      if (tooltip) {
        document.body.removeChild(tooltip);
      }
    };
  });

  $: radius = (size - 6) / 2;
  $: circumference = 2 * Math.PI * radius;
  $: strokeDasharray = circumference;
  $: strokeDashoffset =
    circumference - (progressPercentage / 100) * circumference;
  $: fontSize = size * 0.5;

  $: displayText = `${Math.round(qualityScore)}`;

  $: textColor = getTextColor(scoreLevel);
  $: textShadow = getTextShadow(scoreLevel);

  function getTextColor(level) {
    return "#000000";
  }

  function getTextShadow(level) {
    switch (level) {
      case "excellent":
        return "1px 1px 2px rgba(0, 0, 0, 0.7)";
      case "good":
        return "1px 1px 2px rgba(0, 0, 0, 0.7)";
      case "average":
        return "1px 1px 2px rgba(255, 255, 255, 0.8)";
      case "poor":
        return "1px 1px 2px rgba(0, 0, 0, 0.7)";
      default:
        return "none";
    }
  }
</script>

<div
  class="semantic-circle-container"
  bind:this={circleElement}
  on:mouseenter={handleMouseEnter}
  on:mouseleave={handleMouseLeave}
  style="width: {size}px; height: {size}px;"
>
  <svg width={size} height={size} class="semantic-circle">
    <circle
      cx={size / 2}
      cy={size / 2}
      r={radius}
      fill="none"
      stroke="#E8E8E8"
      stroke-width="3"
    />

    <circle
      cx={size / 2}
      cy={size / 2}
      r={radius}
      fill="none"
      stroke={strokeColor}
      stroke-width="3"
      stroke-linecap="round"
      stroke-dasharray={strokeDasharray}
      stroke-dashoffset={strokeDashoffset}
      transform="rotate(-90 {size / 2} {size / 2})"
      class="progress-circle"
    />
  </svg>

  <!-- <div
    class="score-text"
    style="font-size: {fontSize}px; color: {textColor}; text-shadow: {textShadow};"
  > -->

  <div class="score-text" style="font-size: {fontSize}px; color: 	#4f4f4f; ">
    {displayText}
  </div>
</div>

<style>
  .semantic-circle-container {
    display: inline-block;
    cursor: pointer;
    margin-left: 6px;
    vertical-align: middle;
    position: relative;
    transition: transform 0.2s ease;
  }

  .semantic-circle-container:hover {
    transform: scale(1.05);
  }

  .semantic-circle {
    position: absolute;
    top: 0;
    left: 0;
  }

  .progress-circle {
    transition:
      stroke-dashoffset 0.8s ease-in-out,
      stroke 0.3s ease;
  }

  .score-text {
    position: absolute;
    top: 46.5%;
    left: 49.5%;
    transform: translate(-50%, -50%);
    font-weight: 800;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      sans-serif;
    line-height: 1;
    pointer-events: none;
    text-align: center;
  }

  /* Tooltip样式 */
  :global(.semantic-tooltip) {
    position: fixed; /* 改为fixed定位 */
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.3;
    pointer-events: none;
    z-index: 10000;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    /* 移除transform，因为我们现在直接计算位置 */
  }

  :global(.semantic-tooltip::after) {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: rgba(0, 0, 0, 0.9);
  }

  :global(.tooltip-title) {
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 11px;
    opacity: 0.8;
  }

  :global(.tooltip-content div) {
    margin: 1px 0;
  }
</style>
