<script>
    import { onMount } from "svelte";
    import {
        Chart,
        TimeScale,
        LineController,
        LineElement,
        PointElement,
        Title,
        Tooltip,
        Legend,
        CategoryScale,
        LinearScale,
    } from "chart.js";
    import "chartjs-adapter-date-fns";
    import annotationPlugin from "chartjs-plugin-annotation";

    import { base } from "$app/paths";

    Chart.register(
        TimeScale,
        LineController,
        LineElement,
        PointElement,
        Title,
        Tooltip,
        Legend,
        CategoryScale,
        LinearScale,
        annotationPlugin,
    );

    let dataDict = {
        init_text: [], // Initial text
        init_time: [], // Start time
        json: [], // all operation
        text: [], // final text
        info: [], // insert, delete and suggestion-open operation
        end_time: [],
    };
    let textElements = []; // text data
    let chartData = []; // chart data
    let currentTime = 0;
    let paragraphTime = [];
    let paragraphColor = [];
    let selectedSession = "0c7bfadbd8db49b4b793e2a46e581759";
    let sessions = [];
    let chart = null;
    let time0 = null; // process bar's start time
    let time100 = null; // process bar's end time
    let endTime = null; // last paragraph time
    let isOpen = false;

    function open2close(){
        isOpen = !isOpen;
    }

    const fetchData = async (sessionFile) => {
        try {
            const response = await fetch(
                `${base}/chi2022-coauthor-v1.0/coauthor-json/${sessionFile}.jsonl`,
            );
            if (!response.ok) {
                throw new Error(
                    `Failed to fetch session data: ${response.status}`,
                );
            }

            const data = await response.json();

            time0 = new Date(data.init_time);
            time100 = new Date(data.end_time);
            time100 = (time100 - time0) / (1000 * 60);
            currentTime = time100;

            const progressElement = document.querySelector("progress");
            if (progressElement) {
                // at first let the max time = end time, the init time = end time
                progressElement.max = time100;
                progressElement.value = currentTime;
            }

            dataDict = data;
            handleEvents(data);
        } catch (error) {
            console.error("Error when reading the data file:", error);
        }
    };

    const fetchSessions = async () => {
        try {
            const response = await fetch(`${base}/fine.json`);
            const data = await response.json();
            sessions = data || [];
        } catch (error) {
            console.error("Error when fetching sessions:", error);
        }
    };

    const handleSessionChange = (event) => {
        selectedSession = event.target.value;
        paragraphTime = [];
        paragraphColor = [];
        fetchData(selectedSession).then(() => {
            renderChart();
        });
    };

    onMount(() => {
        fetchSessions();
        if (selectedSession) {
            fetchData(selectedSession);
        }
    });

    function generateColor(index) {
        const colors = [
            "rgba(211, 179, 255, 0.2)",
            "rgba(255, 183, 77, 0.2)",
            "rgba(179, 217, 255, 0.2)",
            "rgba(179, 255, 179, 0.2)",
            "rgba(255, 217, 179, 0.2)",
        ];
        return colors[index % colors.length];
    }

    // function generateColorGrey(index) {
    //   const colors = [
    //     "rgba(200, 200, 200, 0.3)",
    //     "rgba(220, 220, 220, 0.3)",
    //     "rgba(240, 240, 240, 0.3)",
    //     "rgba(210, 210, 210, 0.3)",
    //     "rgba(230, 230, 230, 0.3)",
    //   ];
    //   return colors[index % colors.length];
    // }

    function adjustTime(paragraphTime) {
        // if api insert contain multiple /n, only remain one
        for (let i = 0; i < paragraphTime.length - 1; i++) {
            const current = paragraphTime[i];
            const next = paragraphTime[i + 1];
            if (current.time === next.time && next.pos === current.pos + 1) {
                paragraphTime[i] = {
                    time: current.time,
                    pos: current.pos,
                };
                paragraphTime.splice(i + 1, 1);
                i--;
            }
        }
        return paragraphTime;
    }

    const handleEvents = (data) => {
        let initText = data.init_text.join("");
        let currentText = initText;
        let currentColor = [];
        let wholeText = data.text[0];
        wholeText = wholeText.slice(0, -1);
        chartData = [];
        let firstTime = null;
        let preEvent = null;

        let combinedText = data.info.reduce((acc, event) => {
            if (acc.length === 0) {
                for (let i = 0; i < initText.length; i++) {
                    // init text's color should be the same as api insert
                    acc.push({ text: initText[i], textColor: "#FC8D62" });
                    currentColor.push("#FC8D62");
                }
            }
            const { name, text, eventSource, event_time, count, pos } = event;
            const textColor = eventSource === "user" ? "#66C2A5" : "#FC8D62"; // api and user insert color setting
            const eventTime = new Date(event_time);
            if (firstTime === null) {
                firstTime = eventTime;
                paragraphTime.push({ time: 0, pos: 0 });
            }
            const relativeTime = (eventTime - firstTime) / (1000 * 60); // convert time into easy format

            if (name === "text-insert") {
                // check whether insert a sentence or a character, divede into characters if it is a sentence
                if (pos === currentText.length) {
                    // inset chracter/sentence at the end of the text
                    currentText += text;
                    for (let i = 0; i < text.length; i++) {
                        acc.push({ text: text[i], textColor: textColor });
                        currentColor.push(textColor);
                        if (text.includes("\n") && preEvent.name === "suggestion-open" && eventSource === "api") {
                            paragraphTime.push({
                                time: (new Date(preEvent.event_time) - firstTime) / (1000 * 60),
                                pos: pos + i,
                            });
                        }
                        if (text[i] === "\n" && eventSource === "user") {
                            paragraphTime.push({
                                time: relativeTime,
                                pos: pos + i,
                                text: text[i],
                            });
                        }
                    }
                } else {
                    // insert chracter/sentence at the middle of the text
                    currentText =
                        currentText.slice(0, pos) +
                        text +
                        currentText.slice(pos);
                    for (let i = 0; i < text.length; i++) {
                        acc.splice(pos + i, 0, {
                            text: text[i],
                            textColor: textColor,
                        });
                        currentColor.splice(pos + i, 0, textColor);
                        if (text[i] === "\n") {
                            paragraphTime.push({
                                time: relativeTime,
                                pos: pos + i,
                            });
                        }
                    }
                }
            } else if (name === "text-delete") {
                // also check delete number
                currentText =
                    currentText.slice(0, pos) + currentText.slice(pos + count);
                let remainingCount = count;
                let index = pos;
                while (remainingCount > 0 && index < acc.length) {
                    if (acc[index].text.length <= remainingCount) {
                        remainingCount -= acc[index].text.length;
                        acc.splice(index, 1);
                        currentColor.splice(index, 1);
                        if (acc[index].text === "\n") {
                            paragraphTime.splice(index, 1);
                        }
                    } else {
                        acc[index].text = acc[index].text.slice(remainingCount);
                        currentColor[index] =
                            currentColor[index].slice(remainingCount);
                        remainingCount = 0;
                        if (acc[index].text === "\n") {
                            paragraphTime[index] =
                                paragraphTime[index].slice(remainingCount);
                        }
                    }
                }
            }

            const percentage = (currentText.length / wholeText.length) * 100;
            endTime = relativeTime;

            if (name === "suggestion-open") {
                // use isSuggestionOpen to filter specific data
                chartData.push({
                    time: relativeTime,
                    percentage: percentage,
                    eventSource,
                    color: textColor,
                    currentText,
                    currentColor,
                    isSuggestionOpen: true,
                });
            } else {
                chartData.push({
                    time: relativeTime,
                    percentage: percentage,
                    eventSource,
                    color: textColor,
                    currentText,
                    currentColor,
                });
            } // data for each character
            preEvent = event;

            return acc;
        }, []);

        paragraphTime.push({ time: data.endTime });
        paragraphTime = adjustTime(paragraphTime);
        for (let i = 0; i < paragraphTime.length - 1; i++) {
            
            const startTime = paragraphTime[i].time;
            const endTime = paragraphTime[i + 1].time;
            const color = generateColor(i);
            paragraphColor.push({
                type: "box",
                xMin: startTime,
                xMax: endTime,
                yMin: -5,
                yMax: 105,
                backgroundColor: color,
                borderWidth: 0,
                zIndex: -10,
                drawTime: "beforeDatasetsDraw",
            });
        }
        console.log("Para Time", paragraphTime);
        combinedText = combinedText.slice(0, -1); // delete last "\n"
        textElements = combinedText;
        chartData = chartData.slice(0, -1); // delete last "\n"
        chartData[0].isSuggestionOpen = false; // change the init api insert into false so not show in the chart
        renderChart();
        calculateSessionAnalytics(data);
    };

    const calculateSessionAnalytics = (data) => {
        let totalInsertions = 0;
        let totalDeletions = 0;
        let totalSuggestions = 0;
        let totalInsertionTime = 0;
        let totalDeletionTime = 0;
        let totalSuggestionTime = 0;
        let totalProcessedCharacters = data.text[0].length;

        data.info.forEach((event) => {
            const { name, event_time, count, pos } = event;
            const eventTime = new Date(event_time);
            const relativeTime =
                (eventTime - data.info[0].event_time) / (1000 * 60); // in minutes
            if (name === "text-insert") {
                totalInsertions++;
                totalInsertionTime += relativeTime;
            } else if (name === "text-delete") {
                totalDeletions++;
                totalDeletionTime += relativeTime;
            } else if (name === "suggestion-open") {
                totalSuggestions++;
                totalSuggestionTime += relativeTime;
            }
        });

        updateSessionSummary(
            totalProcessedCharacters,
            totalInsertions,
            totalDeletions,
            totalSuggestions,
        );
    };

    const updateSessionSummary = (
        totalProcessedCharacters,
        totalInsertions,
        totalDeletions,
        totalSuggestions,
    ) => {
        const totalEvents = totalInsertions + totalDeletions + totalSuggestions;

        document.getElementById("totalText").textContent =
            `Total Text: ${totalProcessedCharacters} characters`;
        document.getElementById("totalInsertions").textContent =
            `Insertions: ${totalInsertions}`;
        document.getElementById("totalDeletions").textContent =
            `Deletions: ${totalDeletions}`;
        document.getElementById("totalSuggestions").textContent =
            `Suggestions: ${totalSuggestions}`;
    };

    const renderChart = () => {
        if (chart) {
            chart.destroy();
        }
        const lineChart = document.getElementById("chart").getContext("2d");
        const processedData = chartData.map((data, index) => {
            if (
                index > 0 &&
                chartData[index - 1].percentage === data.percentage
            ) {
                return { x: data.time, y: null };
            }
            if(
                index > 0 &&
                chartData[index - 1].eventSource === "api" &&
                chartData[index].eventSource === "user"
            ) {
                return { x: data.time, y: null };
            }
            if (
                index > 0 &&
                chartData[index - 1].eventSource === "user" &&
                chartData[index].eventSource === "user" &&
                (chartData[index].time - chartData[index - 1].time) > 0.3
            ) {
                return { x: data.time, y: null };
            }

            return { x: data.time, y: data.percentage };
        });

        let selectPoint = null;
        chart = new Chart(lineChart, {
            type: "line",
            data: {
                labels: chartData.map((data) => data.time.toFixed(2)),
                datasets: [
                    {
                        label: "process",
                        data: processedData,
                        borderColor: chartData.map((data) => data.color),
                        backgroundColor: "transparent",
                        segment: {
                            borderColor: (lineChart) =>
                                chartData[lineChart.p1DataIndex].color,
                        },
                        tension: 0.1,
                    },
                ],
            },
            options: {
                interaction: {
                    mode: "nearest",
                    intersect: true,
                },
                onClick: (event, chartElements) => {
                    if (chartElements.length > 0) {
                        const index = chartElements[0].index;
                        if (selectPoint !== index) {
                            selectPoint = index;
                            chart.update();
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        enabled: true,
                        mode: "nearest",
                        intersect: true,
                        callbacks: {
                            title: (tooltipItems) => {
                                const data =
                                    chartData[tooltipItems[0].dataIndex];
                                return `Time: ${data.time.toFixed(2)} mins`;
                            },
                            label: (tooltipItem) => {
                                const data = chartData[tooltipItem.dataIndex];
                                const eventType =
                                    data.eventSource === "user"
                                        ? "User"
                                        : "API";
                                return `Progress: ${data.percentage.toFixed(2)}% | Event: ${data.eventSource}`;
                            },
                        },
                    },
                    annotation: {
                        annotations: [
                            ...paragraphColor,
                            ...chartData
                                .filter((data) => data.isSuggestionOpen)
                                .map((data) => ({
                                    type: "point",
                                    pointStyle: "triangle",
                                    rotation: 180,
                                    xMax: data.time,
                                    xMin: data.time,
                                    yMin: data.percentage + 1,
                                    yMax: data.percentage + 5,
                                    borderColor: "#FFB6B3",
                                    borderWidth: 1,
                                    radius: 3,
                                    backgroundColor: "#FFB6B3",
                                    interactive: true,
                                })),
                        ],
                    },
                },
                elements: {
                    point: {
                        radius: (context) => {
                            if (selectPoint !== null && context.dataIndex === selectPoint) {
                                return 8;
                            }
                            return 1;
                        },
                        hoverRadius: 8,
                        hoverBackgroundColor: "rgba(255, 99, 132, 0.8)",
                        hoverBorderColor: "rgba(255, 99, 132, 1)",
                    },
                },
                scales: {
                    x: {
                        type: "linear",
                        title: {
                            display: true,
                            text: "Time (mins)",
                        },
                        ticks: {
                            stepSize: 1,
                        },
                        grid: {
                            display: false,
                        },
                    },
                    y: {
                        min: 0,
                        max: 100,
                        offset: true,
                        title: {
                            display: true,
                            text: "Process(%)",
                        },
                        ticks: {
                            stepSize: 10,
                        },
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
        lineChart.canvas.addEventListener("click", (event) => {
            const points = chart.getElementsAtEventForMode(
                event,
                "nearest",
                { intersect: true },
                true,
            );
            if (points.length > 0) {
                const point = points[0];
                const data = chartData[point.index];

                textElements = data.currentText
                    .split("")
                    .map((char, index) => ({
                        text: char,
                        textColor: data.currentColor[index],
                    }));
                currentTime = data.time;
            }
        });
    };
</script>

<div class="App">
    <header class="App-header">
        <nav>
            <a on:click={open2close} href=" ">Instruction</a>
        </nav>
        <div class="container">
            {#if isOpen}
                <div class="introduction-background">
                    <div class="introduction">
                        <h2>Welcome to the CoAuthor visualization!</h2>
                        <p>
                            This platform allows you to explore the <b
                                >human-AI collaborative writing process</b
                            >
                            using the
                            <a
                                href="https://coauthor.stanford.edu/"
                                target="_blank">CoAuthor dataset</a
                            >. View how writers interacted with GPT-3, analyze
                            AI-generated suggestions, and track text evolution
                            in real time.
                        </p>
                        <p>
                            Discover insights into <b>human-AI collaboration</b>
                            and have fun!
                        </p>
                        <button class="start-button" on:click={open2close}
                            >Start Exploring</button
                        >
                    </div>
                </div>
            {/if}
            <div class="content-box">
                <div class="dropdown-container">
                    <b>Select Session: &nbsp;</b>
                    <select
                        bind:value={selectedSession}
                        on:change={handleSessionChange}
                    >
                        {#each sessions as session}
                            <option value={session.session_id}>
                                {session.prompt_code} - {session.session_id}
                            </option>
                        {/each}
                    </select>
                </div>

                <div class="summary-container">
                    <div class="chart-explanation">
                        <div>
                            <span class="triangle-text">▼</span>
                            user open the AI suggestion
                        </div>
                        <div>
                            <span class="user-line">●</span> user writing
                        </div>
                        <div>
                            <span class="api-line">●</span> AI writing
                        </div>
                    </div>
                    <div class="session-summary">
                        <h3>Session Summary</h3>
                        <div id="totalText"></div>
                        <div id="totalInsertions"></div>
                        <div id="totalDeletions"></div>
                        <div id="totalSuggestions"></div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="chart" height="300" width="500"></canvas>
                </div>
            </div>
            <div class="content-box">
                <div class="progress-container">
                    <span>{currentTime.toFixed(2)}mins</span>
                    <progress value={currentTime} max={time100}></progress>
                </div>
                <div class="scale-container">
                    <div class="scale" id="scale"></div>
                </div>
                <div class="text-container">
                    {#each textElements as element, index}
                        <span
                            class="text-span"
                            style="color: {element.textColor}"
                            >{element.text}</span
                        >
                    {/each}
                </div>
            </div>
        </div>
    </header>
</div>

<style>
    .App-header {
        text-align: center;
    }

    .App {
        margin: 0px;
    }

    .container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 20px;
        width: 90%;
        max-width: 1200px;
        margin: 0 auto;
        margin-top: 70px;
    }

    .content-box {
        flex: 1;
        border: 1px solid lightgray;
        border-radius: 15px;
        padding: 25px;
        box-shadow:
            0px 2px 5px rgba(0, 0, 0, 0.2),
            2px 2px 5px rgba(0, 0, 0, 0.2),
            -2px 2px 5px rgba(0, 0, 0, 0.2);
        font-family: Poppins, sans-serif;
        font-size: 14px;
        white-space: pre-wrap;
        text-align: left;
    }

    .chart-container {
        width: 100%;
    }

    .text-container {
        width: 100%;
    }

    .text-span {
        display: inline;
    }

    .progress-container {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: hsl(6, 100%, 90%);
        border-radius: 20px;
        color: white;
        width: fit-content;
        position: relative;
    }

    .progress-container span {
        background-color: transparent;
        position: absolute;
        z-index: 1;
        text-align: center;
        top: 10%;
    }

    :root {
        --progColor: hsl(6, 100%, 75%);
        --progHeight: 20px;
        --progBackgroundColor: hsl(6, 100%, 90%);
    }

    progress {
        width: 600px;
        appearance: none;
    }

    progress::-webkit-progress-value {
        height: var(--progHeight);
        border-radius: 20px;
        background: var(--progColor);
    }

    progress::-webkit-progress-bar {
        height: var(--progHeight);
        border-radius: 20px;
        background: var(--progBackgroundColor);
    }

    progress::-moz-progress-bar {
        height: var(--progHeight);
        border-radius: 20px;
        background: var(--progColor);
    }

    .dropdown-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }

    .summary-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        justify-content: center;
        gap: 20px;
    }

    .session-summary {
        padding: 5px;
        border: 1px solid lightgray;
        border-radius: 5px;
        box-shadow: 0px 2px 3px rgba(0, 0, 0, 0.2);
        font-family: Poppins, sans-serif;
        font-size: 12px;
        background-color: #f9f9f9;
        width: 200px;
        line-height: 1.1;
    }
    .session-summary h3 {
        margin-bottom: 2px;
        font-size: 12px;
    }

    .session-summary div {
        margin-bottom: 2px;
    }

    .chart-explanation {
        padding: 5px;
        font-family: Poppins, sans-serif;
        font-size: 12px;
        width: 200px;
        line-height: 1.1;
    }

    .triangle-text {
        color: hsl(6, 100%, 75%);
    }

    .user-line {
        color: #66c2a5;
    }

    .api-line {
        color: #fc8d62;
    }

    .introduction-background {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 999;
    }

    .introduction {
        background: white;
        padding: 20px;
        border-radius: 10px;
        max-width: 500px;
        text-align: center;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
    }

    .introduction h2 {
        margin-bottom: 10px;
    }

    .start-button {
        margin-top: 15px;
        padding: 10px 20px;
        background: #137a7f;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
    }

    .start-button:hover {
        background: #86cecb;
    }

    nav {
            position: fixed;
            top: 0;
            width: 100%;
            background-color: white;
            padding: 1em 0;
            margin: 0px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            z-index: 1;
            left: 0;
            display: flex;
            justify-content: flex-end;
        }
        
    nav a {
        color: #333;
        text-decoration: none;
        margin: 0 1em;
        font-weight: 500;
        cursor: pointer;
    }
    
</style>
