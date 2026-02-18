// static/js/playback.js - Analysis data visualization and charts
class AnalysisVisualizer {
    constructor() {
        this.charts = {};
        this.currentData = null;
    }

    initializeCharts() {
        this.initializeScoreRadar();
        this.initializeTimelineChart();
        this.initializeSpeechMetrics();
    }

    initializeScoreRadar() {
        const ctx = document.getElementById('scoreRadarChart');
        if (!ctx) return;

        // This would be populated with actual data
        this.charts.radar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Posture', 'Eye Contact', 'Pace', 'Clarity', 'Content'],
                datasets: [{
                    label: 'Your Score',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)'
                }]
            },
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    initializeTimelineChart() {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Posture Score',
                        data: [],
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Eye Contact',
                        data: [],
                        borderColor: 'rgb(118, 75, 162)',
                        backgroundColor: 'rgba(118, 75, 162, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    initializeSpeechMetrics() {
        const ctx = document.getElementById('speechMetricsChart');
        if (!ctx) return;

        this.charts.speech = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['WPM', 'Filler Words', 'Pauses', 'Grammar Issues'],
                datasets: [{
                    label: 'Your Metrics',
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    borderColor: [
                        'rgb(102, 126, 234)',
                        'rgb(239, 68, 68)',
                        'rgb(245, 158, 11)',
                        'rgb(16, 185, 129)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateCharts(data) {
        this.currentData = data;
        
        this.updateRadarChart(data);
        this.updateTimelineChart(data);
        this.updateSpeechChart(data);
        this.updateProgressBars(data);
    }

    updateRadarChart(data) {
        if (!this.charts.radar) return;

        const scores = data.overall_score?.breakdown || {};
        
        this.charts.radar.data.datasets[0].data = [
            scores.posture || 0,
            scores.eye_contact || 0,
            scores.pace || 0,
            scores.clarity || 0,
            scores.content || 0
        ];
        
        this.charts.radar.update();
    }

    updateTimelineChart(data) {
        if (!this.charts.timeline) return;

        const postureData = data.posture_analysis?.second_by_second || {};
        const timelineLabels = Object.keys(postureData).slice(0, 60); // First 60 seconds
        const postureScores = timelineLabels.map(second => 
            postureData[second]?.posture_scores?.length > 0 ?
            postureData[second].posture_scores.reduce((a, b) => a + b) / postureData[second].posture_scores.length : 0
        );
        const eyeContactScores = timelineLabels.map(second =>
            postureData[second]?.eye_contact_scores?.length > 0 ?
            postureData[second].eye_contact_scores.reduce((a, b) => a + b) / postureData[second].eye_contact_scores.length : 0
        );

        this.charts.timeline.data.labels = timelineLabels;
        this.charts.timeline.data.datasets[0].data = postureScores;
        this.charts.timeline.data.datasets[1].data = eyeContactScores;
        this.charts.timeline.update();
    }

    updateSpeechChart(data) {
        if (!this.charts.speech) return;

        const speechData = data.speech_analysis || {};
        
        this.charts.speech.data.datasets[0].data = [
            speechData.words_per_minute || 0,
            speechData.filler_words?.total_count || 0,
            speechData.pauses?.count || 0,
            speechData.grammar_errors?.count || 0
        ];
        
        this.charts.speech.update();
    }

    updateProgressBars(data) {
        const scores = data.overall_score?.breakdown || {};
        
        // Update progress bars
        this.updateProgressBar('postureProgress', scores.posture || 0);
        this.updateProgressBar('eyeContactProgress', scores.eye_contact || 0);
        this.updateProgressBar('speechProgress', scores.speech || 0);
        this.updateProgressBar('contentProgress', scores.content || 0);
    }

    updateProgressBar(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.width = `${value}%`;
            element.setAttribute('data-value', `${Math.round(value)}%`);
        }
    }

    createWordCloud(keywords) {
        const container = document.getElementById('wordCloud');
        if (!container) return;

        container.innerHTML = '';
        
        keywords.forEach((keyword, index) => {
            const wordElement = document.createElement('span');
            wordElement.className = 'cloud-word';
            wordElement.textContent = keyword.word || keyword;
            wordElement.style.fontSize = `${(keyword.count || 1) * 10 + 14}px`;
            wordElement.style.opacity = `${0.5 + (keyword.count || 1) * 0.1}`;
            wordElement.style.animationDelay = `${index * 0.1}s`;
            
            container.appendChild(wordElement);
        });
    }

    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Timeline visualization
function createPostureTimeline(data) {
    const container = document.getElementById('postureTimeline');
    if (!container) return;

    const secondBySecond = data.posture_analysis?.second_by_second || {};
    const totalSeconds = Object.keys(secondBySecond).length;
    
    if (totalSeconds === 0) {
        container.innerHTML = '<div class="no-timeline-data">No posture data available</div>';
        return;
    }

    let timelineHTML = '';
    
    Object.entries(secondBySecond).forEach(([second, metrics]) => {
        const postureScore = metrics.posture_scores?.length > 0 ? 
            metrics.posture_scores.reduce((a, b) => a + b) / metrics.posture_scores.length : 0;
        
        const status = getPostureStatus(postureScore);
        const width = 100 / totalSeconds;
        
        timelineHTML += `
            <div class="timeline-segment ${status}" 
                 style="width: ${width}%"
                 data-second="${second}"
                 data-score="${Math.round(postureScore)}">
                <div class="segment-tooltip">
                    Second ${second}: ${Math.round(postureScore)}% (${status})
                </div>
            </div>
        `;
    });

    container.innerHTML = timelineHTML;
    
    // Add hover effects
    container.querySelectorAll('.timeline-segment').forEach(segment => {
        segment.addEventListener('mouseenter', showTimelineTooltip);
        segment.addEventListener('mouseleave', hideTimelineTooltip);
    });
}

function getPostureStatus(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'average';
    return 'poor';
}

function showTimelineTooltip(event) {
    const tooltip = event.currentTarget.querySelector('.segment-tooltip');
    if (tooltip) {
        tooltip.style.visibility = 'visible';
        tooltip.style.opacity = '1';
    }
}

function hideTimelineTooltip(event) {
    const tooltip = event.currentTarget.querySelector('.segment-tooltip');
    if (tooltip) {
        tooltip.style.visibility = 'hidden';
        tooltip.style.opacity = '0';
    }
}

// Score visualization
function updateScoreDisplay(scoreData) {
    const overallScore = scoreData.total || 0;
    const breakdown = scoreData.breakdown || {};
    
    // Update main score display
    const scoreElement = document.getElementById('overallScore');
    if (scoreElement) {
        scoreElement.textContent = Math.round(overallScore);
        scoreElement.className = `score-value score-${getScoreCategory(overallScore)}`;
    }
    
    // Update breakdown scores
    updateBreakdownScore('postureScore', breakdown.posture);
    updateBreakdownScore('eyeContactScore', breakdown.eye_contact);
    updateBreakdownScore('speechScore', breakdown.speech);
    updateBreakdownScore('contentScore', breakdown.content);
}

function updateBreakdownScore(elementId, score) {
    const element = document.getElementById(elementId);
    if (element && score !== undefined) {
        element.textContent = `${Math.round(score)}%`;
        element.className = `breakdown-value ${getScoreCategory(score)}`;
    }
}

function getScoreCategory(score) {
    if (score >= 90) return 'excellent';
    if (score >= 80) return 'very-good';
    if (score >= 70) return 'good';
    if (score >= 60) return 'average';
    if (score >= 50) return 'needs-improvement';
    return 'poor';
}

// Speech analysis visualization
function createFillerWordsVisualization(fillerData) {
    const container = document.getElementById('fillerWordsViz');
    if (!container) return;

    const breakdown = fillerData.breakdown || {};
    const total = fillerData.total_count || 0;
    
    if (total === 0) {
        container.innerHTML = '<div class="no-filler-data">No filler words detected! Great job!</div>';
        return;
    }

    let visualizationHTML = '<div class="filler-words-grid">';
    
    Object.entries(breakdown).forEach(([word, count]) => {
        const percentage = (count / total) * 100;
        visualizationHTML += `
            <div class="filler-word-item">
                <span class="filler-word">"${word}"</span>
                <div class="filler-bar-container">
                    <div class="filler-bar" style="width: ${percentage}%"></div>
                </div>
                <span class="filler-count">${count}</span>
            </div>
        `;
    });
    
    visualizationHTML += '</div>';
    container.innerHTML = visualizationHTML;
}

// Export functionality
function generatePDFReport() {
    // This would integrate with a PDF generation library
    alert('PDF report generation would be implemented here with a library like jsPDF');
}

function downloadCSVData() {
    if (!window.currentAnalysisData) {
        alert('No data available to download');
        return;
    }

    const data = window.currentAnalysisData;
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Add headers
    csvContent += "Metric,Score\n";
    
    // Add overall score
    csvContent += `Overall Score,${data.overall_score?.total || 0}\n`;
    
    // Add breakdown scores
    const breakdown = data.overall_score?.breakdown || {};
    Object.entries(breakdown).forEach(([category, score]) => {
        csvContent += `${category},${score}\n`;
    });
    
    // Add speech metrics
    const speech = data.speech_analysis || {};
    csvContent += `Words Per Minute,${speech.words_per_minute || 0}\n`;
    csvContent += `Filler Words,${speech.filler_words?.total_count || 0}\n`;
    csvContent += `Pauses,${speech.pauses?.count || 0}\n`;
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "talkgenius_analysis.csv");
    document.body.appendChild(link);
    
    link.click();
    document.body.removeChild(link);
}

// Initialize when page loads
let analysisVisualizer = null;

document.addEventListener('DOMContentLoaded', function() {
    analysisVisualizer = new AnalysisVisualizer();
    
    // Initialize charts after a short delay to ensure DOM is ready
    setTimeout(() => {
        analysisVisualizer.initializeCharts();
    }, 100);
});

// Cleanup when leaving page
window.addEventListener('beforeunload', function() {
    if (analysisVisualizer) {
        analysisVisualizer.destroy();
    }
});