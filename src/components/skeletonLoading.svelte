<script>
  function Random() {
      const min = 50;
      const max = 100;
      return `${Math.floor(Math.random() * (max - min + 1)) + min}%`;
  }

  let skeletonWidths = Array.from({ length: 14 }, () => Random());
  
</script>
<div>
  <div class="display-box">
      <div class="content-box">
          <div class="session-identifier">
              <div class="skeleton-line" style="width: 80%;"></div>
          </div>
          <div>
              <div class="skeleton-line" style="width: 30%; margin-top: 20px"></div>
          <div class="summary-container">
              <div class="skeleton-line" style="width: 90%;"></div>
          </div>
          </div>
          <div class="chart-container">
          <div class="chart-wrapper">
              <div class="skeleton-line" style="width: 120px; height: 170px; margin-left: 40px"></div>
              <div class="skeleton-line" style="width: 300px; height: 170px; margin-left: 2px"></div>
          </div>
              <div class="skeleton-line" style="margin: 0 auto; width: 15%; height: 25px"></div>
          </div>
      </div>
      <div class="content-box">
          <div class="progress-container">
              <div class="skeleton-line" style="height: 1.3rem; border-radius: 12px;"></div>
          </div>
          <div class="scale-container">
          <div class="scale" id="scale"></div>
          </div>
          <div class="text-container">
              {#each skeletonWidths as width}
                  <div class="skeleton-line" style="width: {width}; margin-bottom: 8px"></div>
              {/each}
          </div>
      </div>
  </div>
</div>

<style>
.display-box {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    gap: 20px;
    border-radius: 15px;
    padding: 25px;
    box-shadow:
        0px 1px 5px rgba(0, 0, 0, 0.1),
        1px 1px 5px rgba(0, 0, 0, 0.1),
        -1px 1px 5px rgba(0, 0, 0, 0.1);
    font-family: Poppins, sans-serif;
    font-size: 14px;
    white-space: pre-wrap;
    text-align: left;
    width: 100%;
    margin-top: 50px;
}

.content-box {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 400px;
    font-family: Poppins, sans-serif;
    font-size: 14px;
    white-space: pre-wrap;
    text-align: left;
    padding: 15px;
}

.session-identifier {
    padding: 8px 12px;
    border-radius: 4px;
    margin-bottom: 10px;
}

.chart-wrapper {
    display: flex;
    align-items: flex-start;
    margin: 15px 0;
}

.text-container {
    flex: 1;
    width: 100%;
    max-height: 100%;
    overflow-y: auto;
    margin-top: 20px;
}

.skeleton-line {
  height: 1rem;
  background-color: #eee;
  border-radius: 4px;
  animation: shimmer 1.5s infinite linear;
  position: relative;
  overflow: hidden;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton-line::before {
  content: '';
  position: absolute;
  top: 0;
  left: -150%;
  height: 100%;
  width: 150%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  animation: shine 0.6s infinite;
}

@keyframes shine {
  0% {
    left: -150%;
  }
  100% {
    left: 100%;
  }
}
</style>