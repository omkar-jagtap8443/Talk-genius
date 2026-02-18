// static/js/practise.js - Main recording functionality
class PracticeSession {
    constructor() {
        this.isRecording = false;
        this.isPaused = false;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.stream = null;
        this.timerInterval = null;
        this.recordingTime = 0;
        
        // MediaPipe components
        this.pose = null;
        this.faceMesh = null;
        this.camera = null;
        
        // Live transcription
        this.liveTranscription = null;
        
        // Analysis data
        this.postureData = [];
        this.eyeContactData = [];
        this.speechData = {
            transcript: '',
            fillerWords: 0,
            wordCount: 0
        };
        
        // Real-time feedback
        this.feedbackInterval = null;
        
        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        this.videoElement = document.getElementById('cameraPreview');
        this.overlayCanvas = document.getElementById('overlayCanvas');
        this.ctx = this.overlayCanvas.getContext('2d');
        
        // Control buttons
        this.startBtn = document.getElementById('startRecordingBtn');
        this.stopBtn = document.getElementById('stopRecordingBtn');
        
        // Feedback elements
        this.postureScoreEl = document.getElementById('postureScore');
        this.eyeContactScoreEl = document.getElementById('eyeContactScore');
        this.paceValueEl = document.getElementById('paceValue');
        this.fillerCountEl = document.getElementById('fillerCount');
        this.liveSuggestionsEl = document.getElementById('liveSuggestions');
        this.liveTranscriptEl = document.getElementById('liveTranscript');
        
        // Status elements
        this.timerEl = document.getElementById('sessionTimer');
        this.recordingStatusEl = document.getElementById('recordingStatus');
    }

    setupEventListeners() {
        // Camera permission handling
        this.videoElement.addEventListener('loadedmetadata', () => {
            this.setupCanvasSize();
        });
    }

    async initializeCamera() {
        console.log('[DEBUG] initializeCamera called');
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 640,
                    height: 480,
                    facingMode: 'user'
                },
                audio: true
            });
            console.log('[DEBUG] Got user media stream:', this.stream);

            this.videoElement.srcObject = this.stream;
            console.log('[DEBUG] Set videoElement.srcObject');

            // Try to play the video element (handle autoplay restrictions)
            const playPromise = this.videoElement.play();
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('[DEBUG] videoElement.play() resolved');
                }).catch((error) => {
                    console.warn('[DEBUG] Autoplay prevented, user interaction needed:', error);
                });
            }

            // Wait for video to be ready
            await new Promise((resolve) => {
                if (this.videoElement.readyState >= 2) {
                    console.log('[DEBUG] videoElement readyState >= 2');
                    resolve();
                } else {
                    this.videoElement.onloadeddata = () => {
                        console.log('[DEBUG] videoElement onloadeddata fired');
                        resolve();
                    };
                }
            });

            // Set canvas size to match video
            this.setupCanvasSize();
            console.log('[DEBUG] setupCanvasSize called');

            console.log('[DEBUG] Camera initialized and video playing');

        } catch (error) {
            console.error('[DEBUG] Error accessing camera:', error);
            this.showError('Cannot access camera. Please check permissions.');
        }
    }

    setupCanvasSize() {
        if (this.videoElement.videoWidth && this.videoElement.videoHeight) {
            this.overlayCanvas.width = this.videoElement.videoWidth;
            this.overlayCanvas.height = this.videoElement.videoHeight;
        }
    }

    async initializeMediaPipe() {
        try {
            // Initialize Pose detection
            this.pose = new Pose({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
                }
            });

            this.pose.setOptions({
                modelComplexity: 1,
                smoothLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            this.pose.onResults((results) => {
                this.onPoseResults(results);
            });

            // Initialize Face Mesh for eye contact
            this.faceMesh = new FaceMesh({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
                }
            });

            this.faceMesh.setOptions({
                maxNumFaces: 1,
                refineLandmarks: true,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            this.faceMesh.onResults((results) => {
                this.onFaceResults(results);
            });

            console.log('MediaPipe models initialized');

        } catch (error) {
            console.error('Error initializing MediaPipe:', error);
        }
    }

    onPoseResults(results) {
        this.ctx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);
        
        if (results.poseLandmarks && this.isRecording && !this.isPaused) {
            // Draw pose landmarks
            drawConnectors(this.ctx, results.poseLandmarks, POSE_CONNECTIONS, {
                color: '#00FF00',
                lineWidth: 2
            });
            drawLandmarks(this.ctx, results.poseLandmarks, {
                color: '#FF0000',
                lineWidth: 1,
                radius: 2
            });

            // Analyze posture
            const postureScore = this.analyzePosture(results.poseLandmarks);
            this.postureData.push({
                timestamp: this.recordingTime,
                score: postureScore
            });

            // Update UI
            this.updatePostureFeedback(postureScore);
        }
    }

    onFaceResults(results) {
        if (results.multiFaceLandmarks && results.multiFaceLandmarks[0] && this.isRecording && !this.isPaused) {
            // Draw face landmarks
            drawConnectors(this.ctx, results.multiFaceLandmarks[0], FACEMESH_TESSELATION, {
                color: '#E0E0E0',
                lineWidth: 1
            });

            // Analyze eye contact
            const eyeContactScore = this.analyzeEyeContact(results.multiFaceLandmarks[0]);
            this.eyeContactData.push({
                timestamp: this.recordingTime,
                score: eyeContactScore
            });

            // Update UI
            this.updateEyeContactFeedback(eyeContactScore);
        }
    }

    analyzePosture(landmarks) {
        // Simplified posture analysis
        // In a real implementation, you'd calculate based on landmark positions
        
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];
        
        if (!leftShoulder || !rightShoulder || !leftHip || !rightHip) {
            return 50;
        }

        // Calculate shoulder alignment
        const shoulderDiff = Math.abs(leftShoulder.y - rightShoulder.y);
        const hipDiff = Math.abs(leftHip.y - rightHip.y);
        
        // Simple scoring (0-100)
        let score = 100 - (shoulderDiff * 200 + hipDiff * 200);
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    analyzeEyeContact(faceLandmarks) {
        // Simplified eye contact analysis
        // In real implementation, use gaze detection
        
        if (!faceLandmarks || faceLandmarks.length < 10) {
            return 50;
        }

        // Use nose position as proxy for gaze direction
        const nose = faceLandmarks[1];
        if (!nose) return 50;

        // Calculate deviation from center
        const deviation = Math.abs(nose.x - 0.5);
        let score = 100 - (deviation * 200);
        
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    async startRecording() {
        if (this.isRecording) return;

        console.log('[DEBUG] startRecording called');
        try {
            // Call start_recording endpoint
            const startResponse = await fetch('/start_recording', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!startResponse.ok) {
                throw new Error('Failed to start recording session');
            }

            const startData = await startResponse.json();
            if (!startData.success) {
                throw new Error(startData.error || 'Failed to start session');
            }

            // Always request camera and mic permissions before starting
            await this.initializeCamera();
            console.log('[DEBUG] initializeCamera finished');

            // Ensure video is playing and ready
            if (!this.stream || this.videoElement.readyState < 2) {
                console.error('[DEBUG] Camera not ready after initializeCamera');
                this.showError('Camera not ready. Please try again.');
                return;
            }

            // Reset previous data
            this.resetSessionData();
            console.log('[DEBUG] resetSessionData called');

            // Initialize MediaPipe
            if (!this.pose || !this.faceMesh) {
                await this.initializeMediaPipe();
                console.log('[DEBUG] initializeMediaPipe finished');
            }

            // Start MediaPipe camera processing
            this.startMediaPipeProcessing();
            console.log('[DEBUG] startMediaPipeProcessing called');

            // Setup media recorder
            await this.setupMediaRecorder();
            console.log('[DEBUG] setupMediaRecorder finished');

            // Start recording
            this.mediaRecorder.start(1000); // Collect data every second
            this.isRecording = true;
            console.log('[DEBUG] mediaRecorder started');

            // Start live transcription
            if (window.LiveTranscription) {
                this.liveTranscription = new LiveTranscription();
                this.liveTranscription.start();
                console.log('[DEBUG] Live transcription started');
            }

            // Start timer
            this.startTimer();
            console.log('[DEBUG] startTimer called');

            // Start real-time feedback
            this.startRealTimeFeedback();
            console.log('[DEBUG] startRealTimeFeedback called');

            // Update UI
            this.updateRecordingUI(true);
            console.log('[DEBUG] updateRecordingUI(true) called');
            
            console.log('[DEBUG] Recording started successfully');

        } catch (error) {
            console.error('[DEBUG] Error starting recording:', error);
            this.showError('Failed to start recording: ' + error.message);
            this.isRecording = false;
            this.updateRecordingUI(false);
        }
    }

    async setupMediaRecorder() {
        try {
            // Get supported mime types
            const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
                ? 'video/webm;codecs=vp9'
                : MediaRecorder.isTypeSupported('video/webm')
                    ? 'video/webm'
                    : 'video/mp4';

            // Use the stream directly with audio
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType,
                videoBitsPerSecond: 2500000
            });

            this.recordedChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.handleRecordingStop();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.showError('Error during recording: ' + event.error);
            };

        } catch (error) {
            console.error('Error setting up MediaRecorder:', error);
            throw error;
        }
    }

    startMediaPipeProcessing() {
        // Process frames through MediaPipe
        const processFrame = async () => {
            if (this.isRecording && this.videoElement.readyState >= 2) {
                try {
                    await this.pose.send({ image: this.videoElement });
                    await this.faceMesh.send({ image: this.videoElement });
                } catch (error) {
                    console.error('MediaPipe processing error:', error);
                }
            }
            
            if (this.isRecording) {
                setTimeout(() => processFrame(), 100); // Process every 100ms
            }
        };
        
        processFrame();
    }

    startTimer() {
        this.recordingTime = 0;
        this.timerInterval = setInterval(() => {
            this.recordingTime++;
            this.updateTimer();
        }, 1000);
    }

    updateTimer() {
        const minutes = Math.floor(this.recordingTime / 60);
        const seconds = this.recordingTime % 60;
        this.timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    startRealTimeFeedback() {
        this.feedbackInterval = setInterval(() => {
            this.sendRealTimeFeedback();
        }, 2000); // Send feedback every 2 seconds
    }

    async sendRealTimeFeedback() {
        if (!this.isRecording || !window.currentSession?.sessionId) return;

        try {
            const postureData = this.getCurrentPostureData();
            
            const response = await fetch('/realtime_feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: window.currentSession.sessionId,
                    posture_data: postureData,
                    recording_time: this.recordingTime
                })
            });

            if (response.ok) {
                const feedback = await response.json();
                this.updateRealTimeUI(feedback.feedback);
            }
        } catch (error) {
            console.error('Error sending real-time feedback:', error);
        }
    }

    getCurrentPostureData() {
        const recentPosture = this.postureData.slice(-10); // Last 10 readings
        const recentEyeContact = this.eyeContactData.slice(-10);
        
        return {
            posture_score: recentPosture.length > 0 ? 
                recentPosture.reduce((sum, data) => sum + data.score, 0) / recentPosture.length : 50,
            eye_contact_score: recentEyeContact.length > 0 ?
                recentEyeContact.reduce((sum, data) => sum + data.score, 0) / recentEyeContact.length : 50,
            recording_time: this.recordingTime
        };
    }

    updateRealTimeUI(feedback) {
        if (!feedback) return;

        // Update posture feedback
        if (feedback.posture) {
            const postureScore = feedback.posture.score || 0;
            this.updatePostureFeedback(postureScore);
            this.updateMetricCard('posture', postureScore, feedback.posture.posture_status);
        }

        // Update eye contact feedback
        if (feedback.posture?.eye_contact_score !== undefined) {
            this.updateEyeContactFeedback(feedback.posture.eye_contact_score);
            this.updateMetricCard('eyeContact', feedback.posture.eye_contact_score, feedback.posture.eye_contact_status);
        }

        // Update speech feedback
        if (feedback.speech) {
            const wpm = feedback.speech.current_wpm || 0;
            this.updatePaceFeedback(wpm);
            this.updateMetricCard('pace', wpm, feedback.speech.pace_status);
            
            const fillerRate = feedback.speech.filler_rate || 0;
            this.updateFillerFeedback(fillerRate);
        }

        // Update suggestions
        if (feedback.suggestions && feedback.suggestions.length > 0) {
            this.updateSuggestions(feedback.suggestions);
        }

        // Update overall score and alert level
        if (feedback.overall_score !== undefined && feedback.alert_level) {
            this.updateOverallStatus(feedback.overall_score, feedback.alert_level);
        }
    }

    updateMetricCard(metricType, value, status) {
        // Update metric cards with colors based on status
        let displayValue = value;
        let unit = '';
        
        if (metricType === 'pace') {
            unit = ' WPM';
        } else if (metricType === 'posture' || metricType === 'eyeContact') {
            displayValue = Math.round(value);
            unit = '%';
        }
        
        const statusClass = this.getStatusClass(status);
    }

    updatePostureFeedback(score) {
        if (!this.postureScoreEl) return;
        this.postureScoreEl.textContent = `${Math.round(score)}%`;
        this.postureScoreEl.className = `metric-value ${this.getScoreClass(score)}`;
        
        let feedback = '';
        if (score >= 80) feedback = 'Excellent posture!';
        else if (score >= 60) feedback = 'Good posture';
        else if (score >= 40) feedback = 'Fair posture';
        else feedback = 'Adjust your posture';
        
        const feedbackEl = document.getElementById('postureFeedback');
        if (feedbackEl) feedbackEl.textContent = feedback;
    }

    updateEyeContactFeedback(score) {
        if (!this.eyeContactScoreEl) return;
        this.eyeContactScoreEl.textContent = `${Math.round(score)}%`;
        this.eyeContactScoreEl.className = `metric-value ${this.getScoreClass(score)}`;
        
        let feedback = '';
        if (score >= 75) feedback = 'Great eye contact!';
        else if (score >= 50) feedback = 'Good eye contact';
        else feedback = 'Look at the camera more';
        
        const feedbackEl = document.getElementById('eyeContactFeedback');
        if (feedbackEl) feedbackEl.textContent = feedback;
    }

    updatePaceFeedback(wpm) {
        if (!this.paceValueEl) return;
        this.paceValueEl.textContent = `${Math.round(wpm)} WPM`;
        
        let feedback = '';
        if (140 <= wpm && wpm <= 160) {
            feedback = 'Perfect pace!';
            this.paceValueEl.className = 'metric-value excellent';
        } else if (wpm < 120) {
            feedback = 'Speaking too slowly';
            this.paceValueEl.className = 'metric-value poor';
        } else if (wpm > 180) {
            feedback = 'Speaking too fast';
            this.paceValueEl.className = 'metric-value poor';
        } else {
            feedback = 'Good pace';
            this.paceValueEl.className = 'metric-value good';
        }
        
        const feedbackEl = document.getElementById('paceFeedback');
        if (feedbackEl) feedbackEl.textContent = feedback;
    }

    updateFillerFeedback(count) {
        if (!this.fillerCountEl) return;
        this.fillerCountEl.textContent = count;
        
        let feedback = '';
        if (count <= 2) {
            feedback = 'Excellent!';
            this.fillerCountEl.className = 'metric-value excellent';
        } else if (count <= 5) {
            feedback = 'Good control';
            this.fillerCountEl.className = 'metric-value good';
        } else if (count <= 10) {
            feedback = 'Try to reduce';
            this.fillerCountEl.className = 'metric-value average';
        } else {
            feedback = 'Needs work';
            this.fillerCountEl.className = 'metric-value poor';
        }
        
        const feedbackEl = document.getElementById('fillerFeedback');
        if (feedbackEl) feedbackEl.textContent = feedback;
    }

    updateSuggestions(suggestions) {
        if (!this.liveSuggestionsEl) return;
        
        if (!suggestions || suggestions.length === 0) {
            this.liveSuggestionsEl.innerHTML = '<div class="suggestion-item">✅ Keep up the great work!</div>';
            return;
        }

        // Filter out empty suggestions and limit to 3
        const validSuggestions = suggestions.filter(s => s && typeof s === 'string').slice(0, 3);
        
        if (validSuggestions.length === 0) {
            this.liveSuggestionsEl.innerHTML = '<div class="suggestion-item">✅ Your delivery is excellent!</div>';
            return;
        }

        this.liveSuggestionsEl.innerHTML = validSuggestions.map((suggestion, index) => {
            // Clean up suggestion text by removing duplicate icons
            let cleanSuggestion = suggestion;
            if (suggestion.match(/^[💡👀🗣️🎯✅⏸️]/)) {
                cleanSuggestion = suggestion;
            } else {
                const icons = ['💡', '👀', '🗣️', '🎯', '✅', '⏸️'];
                const icon = icons[index % icons.length];
                cleanSuggestion = `${icon} ${suggestion}`;
            }
            return `<div class="suggestion-item">${cleanSuggestion}</div>`;
        }).join('');
    }

    updateOverallStatus(score, alertLevel) {
        // Update recording status with color coding
        const statusEl = this.recordingStatusEl;
        statusEl.textContent = 'Recording';
        statusEl.className = `status-recording status-${alertLevel}`;
    }

    getScoreClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'average';
        return 'poor';
    }

    getStatusClass(status) {
        // Convert status strings to CSS classes
        if (!status) return 'average';
        if (typeof status === 'string') {
            if (status.includes('good') || status.includes('excellent') || status.includes('ideal')) {
                return 'excellent';
            } else if (status.includes('okay') || status.includes('moderate') || status.includes('good')) {
                return 'good';
            } else if (status.includes('poor') || status.includes('slow') || status.includes('fast') || status.includes('high')) {
                return 'poor';
            }
        }
        return 'average';
    }

    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;

        this.isRecording = false;
        
        // Stop media recorder
        if (this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        // Stop live transcription
        if (this.liveTranscription) {
            this.liveTranscription.stop();
            this.speechData.transcript = this.liveTranscription.getTranscript();
            console.log('Transcript captured:', this.speechData.transcript);
        }
        
        // Stop timer
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        
        // Stop real-time feedback
        if (this.feedbackInterval) {
            clearInterval(this.feedbackInterval);
        }
        
        // Update UI
        this.updateRecordingUI(false);
        
        console.log('Recording stopped');
    }

    handleRecordingStop() {
        // Show processing screen
        showProcessingSection();
        
        // Save recording and process analysis
        this.saveRecording();
    }

    async saveRecording() {
        try {
            const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
            const formData = new FormData();
            
            formData.append('video', blob, 'recording.webm');
            formData.append('posture_data', JSON.stringify({
                posture: this.postureData,
                eye_contact: this.eyeContactData,
                duration: this.recordingTime
            }));
            formData.append('transcript', this.speechData.transcript);

            const response = await fetch('/save_recording', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Recording saved successfully:', result);
                
                // Redirect to analysis page
                setTimeout(() => {
                    window.location.href = '/analysis';
                }, 2000);
                
            } else {
                throw new Error('Failed to save recording');
            }

        } catch (error) {
            console.error('Error saving recording:', error);
            this.showError('Failed to save recording. Please try again.');
            
            // Go back to recording section
            document.getElementById('processingSection').style.display = 'none';
            document.getElementById('recordingSection').style.display = 'block';
        }
    }

    updateRecordingUI(recording) {
        if (recording) {
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.recordingStatusEl.textContent = 'Recording';
            this.recordingStatusEl.className = 'status-recording';
        } else {
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.recordingStatusEl.textContent = 'Not Recording';
            this.recordingStatusEl.className = 'status-not-recording';
        }
    }

    resetSessionData() {
        this.postureData = [];
        this.eyeContactData = [];
        this.speechData = {
            transcript: '',
            fillerWords: 0,
            wordCount: 0
        };
        this.recordingTime = 0;
    }

    showError(message) {
        alert(`Error: ${message}`);
    }

    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }
        if (this.feedbackInterval) {
            clearInterval(this.feedbackInterval);
        }
        if (this.liveTranscription) {
            this.liveTranscription.abort();
        }
    }
}

// Global practice session instance
let practiceSession = null;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    practiceSession = new PracticeSession();
});

// Global functions for HTML onclick handlers
function startRecording() {
    if (practiceSession) {
        practiceSession.startRecording();
    }
}

function stopRecording() {
    if (practiceSession) {
        practiceSession.stopRecording();
    }
}

function initializeCamera() {
    if (practiceSession) {
        practiceSession.initializeCamera();
    }
}

function initializeMediaPipe() {
    if (practiceSession) {
        practiceSession.initializeMediaPipe();
    }
}

function showProcessingSection() {
    document.getElementById('recordingSection').style.display = 'none';
    document.getElementById('processingSection').style.display = 'block';
    
    // Animate progress steps
    const steps = document.querySelectorAll('.progress-step');
    let currentStep = 0;
    
    const progressInterval = setInterval(() => {
        if (currentStep < steps.length) {
            steps[currentStep].classList.add('active');
            currentStep++;
        } else {
            clearInterval(progressInterval);
        }
    }, 1000);
}