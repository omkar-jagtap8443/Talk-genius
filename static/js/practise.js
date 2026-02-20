// static/js/practise.js - FIXED Recording functionality
class PracticeSession {
    constructor() {
        console.log('🚀 PracticeSession initializing...');
        this.isRecording = false;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.stream = null;
        this.timerInterval = null;
        this.recordingTime = 0;
        this.recordingStartTime = null;
        
        // MediaPipe components
        this.pose = null;
        this.faceMesh = null;
        
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
        console.log('✅ PracticeSession initialized');
    }

    initializeElements() {
        this.videoElement = document.getElementById('cameraPreview');
        this.overlayCanvas = document.getElementById('overlayCanvas');
        this.ctx = this.overlayCanvas ? this.overlayCanvas.getContext('2d') : null;
        
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
        
        console.log('📋 Elements initialized');
    }

    async initializeCamera() {
        console.log('📹 Initializing camera...');
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 1280,
                    height: 720,
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            console.log('✅ Got media stream:', this.stream);

            if (this.videoElement) {
                this.videoElement.srcObject = this.stream;
                
                // Wait for video to load
                await new Promise((resolve) => {
                    this.videoElement.onloadedmetadata = () => {
                        this.videoElement.play();
                        this.setupCanvasSize();
                        resolve();
                    };
                    setTimeout(resolve, 1000);
                });
            }
            console.log('✅ Camera ready');
            return true;

        } catch (error) {
            console.error('❌ Camera error:', error);
            this.showError('Camera not available: ' + error.message);
            return false;
        }
    }

    setupCanvasSize() {
        if (this.overlayCanvas && this.videoElement) {
            this.overlayCanvas.width = this.videoElement.videoWidth || 640;
            this.overlayCanvas.height = this.videoElement.videoHeight || 480;
        }
    }

    async initializeMediaPipe() {
        console.log('🤖 Initializing MediaPipe...');
        try {
            // Pose detection
            if (typeof Pose !== 'undefined') {
                this.pose = new Pose({
                    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
                });

                this.pose.setOptions({
                    modelComplexity: 2,
                    smoothLandmarks: true,
                    enableSegmentation: true,
                    smoothSegmentation: true,
                    minDetectionConfidence: 0.7,
                    minTrackingConfidence: 0.7
                });

                this.pose.onResults((results) => this.onPoseResults(results));
                console.log('✅ Pose initialized');
            }

            // Face Mesh
            if (typeof FaceMesh !== 'undefined') {
                this.faceMesh = new FaceMesh({
                    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
                });

                this.faceMesh.setOptions({
                    maxNumFaces: 1,
                    refineLandmarks: true,
                    minDetectionConfidence: 0.5,
                    minTrackingConfidence: 0.5
                });

                this.faceMesh.onResults((results) => this.onFaceResults(results));
                console.log('✅ Face Mesh initialized');
            }
        } catch (error) {
            console.warn('⚠️ MediaPipe error:', error);
        }
    }

    onPoseResults(results) {
        if (!this.isRecording || !this.ctx) return;

        try {
            this.ctx.save();
            this.ctx.clearRect(0, 0, this.overlayCanvas.width, this.overlayCanvas.height);

            if (results.poseLandmarks) {
                // Draw pose landmarks
                drawConnectors(this.ctx, results.poseLandmarks, POSE_CONNECTIONS, {color: '#00FF00', lineWidth: 2});
                drawLandmarks(this.ctx, results.poseLandmarks, {color: '#FF0000', lineWidth: 1, radius: 3});
                
                const postureScore = this.analyzePosture(results.poseLandmarks);
                this.postureData.push({ timestamp: this.recordingTime, score: postureScore });
                this.updatePostureFeedback(postureScore);
            }
            this.ctx.restore();
        } catch (error) {
            console.warn('Pose processing error:', error);
        }
    }

    onFaceResults(results) {
        if (!this.isRecording) return;

        try {
            if (results.multiFaceLandmarks && results.multiFaceLandmarks[0]) {
                const eyeContactScore = this.analyzeEyeContact(results.multiFaceLandmarks[0]);
                this.eyeContactData.push({ timestamp: this.recordingTime, score: eyeContactScore });
                this.updateEyeContactFeedback(eyeContactScore);
            }
        } catch (error) {
            console.warn('Face processing error:', error);
        }
    }

    analyzePosture(landmarks) {
        if (!landmarks || landmarks.length < 33) return 50;
        
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const leftHip = landmarks[23];
        const rightHip = landmarks[24];
        const leftEar = landmarks[7];
        const rightEar = landmarks[8];
        const nose = landmarks[0];
        
        if (!leftShoulder || !rightShoulder || !leftHip || !rightHip) return 50;

        let score = 100;
        
        // Shoulder alignment (horizontal)
        const shoulderDiff = Math.abs(leftShoulder.y - rightShoulder.y);
        score -= shoulderDiff * 150;
        
        // Hip alignment
        const hipDiff = Math.abs(leftHip.y - rightHip.y);
        score -= hipDiff * 150;
        
        // Spine alignment (vertical posture)
        const shoulderMidX = (leftShoulder.x + rightShoulder.x) / 2;
        const hipMidX = (leftHip.x + rightHip.x) / 2;
        const spineDeviation = Math.abs(shoulderMidX - hipMidX);
        score -= spineDeviation * 100;
        
        // Head position (forward head posture check)
        if (leftEar && rightEar) {
            const earMidX = (leftEar.x + rightEar.x) / 2;
            const headForward = Math.abs(earMidX - shoulderMidX);
            score -= headForward * 80;
        }
        
        // Shoulder slouch check (depth)
        if (leftShoulder.z && rightShoulder.z && leftHip.z && rightHip.z) {
            const shoulderDepth = Math.abs(leftShoulder.z - rightShoulder.z);
            const hipDepth = Math.abs(leftHip.z - rightHip.z);
            score -= (shoulderDepth + hipDepth) * 50;
        }
        
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    analyzeEyeContact(faceLandmarks) {
        if (!faceLandmarks || faceLandmarks.length < 10) return 50;

        const nose = faceLandmarks[1];
        if (!nose) return 50;

        const deviation = Math.abs(nose.x - 0.5);
        let score = 100 - (deviation * 200);
        
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    async startRecording() {
        console.log('▶️ START RECORDING PRESSED');
        
        if (this.isRecording) {
            console.log('⚠️ Already recording');
            return;
        }

        try {
            // Initialize camera
            const cameraReady = await this.initializeCamera();
            if (!cameraReady) {
                console.error('❌ Camera initialization failed');
                return;
            }

            // Initialize MediaPipe
            await this.initializeMediaPipe();

            // Reset data
            this.recordedChunks = [];
            this.postureData = [];
            this.eyeContactData = [];
            this.recordingTime = 0;

            // Setup media recorder
            console.log('🎬 Setting up MediaRecorder...');
            const mimeType = this.getSupportedMimeType();
            console.log('📝 Using MIME type:', mimeType);

            this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                    console.log('📦 Chunk received, total chunks:', this.recordedChunks.length);
                }
            };

            this.mediaRecorder.onstart = () => {
                console.log('✅ MediaRecorder started');
                this.isRecording = true;
                this.recordingStartTime = Date.now();
                this.clearRecordingUI();
                this.startTimer();
                this.startRealTimeFeedback();
                this.startMediaPipeProcessing();
                
                // Start transcription
                if (window.LiveTranscription) {
                    this.liveTranscription = new LiveTranscription();
                    this.liveTranscription.start();
                    window.practiceSession = this;
                    console.log('🎤 Transcription started');
                } else {
                    console.warn('⚠️ LiveTranscription not available');
                }
                
                this.updateRecordingUI(true);
            };

            this.mediaRecorder.onstop = () => {
                console.log('⏹️ MediaRecorder stopped, processing...');
                this.handleRecordingStop();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('❌ MediaRecorder error:', event.error);
                this.showError('Recording error: ' + event.error);
                this.isRecording = false;
            };

            // Start recording
            console.log('🔴 Calling mediaRecorder.start()');
            this.mediaRecorder.start(1000);

        } catch (error) {
            console.error('❌ Error in startRecording:', error);
            console.error('Error stack:', error.stack);
            this.showError('Failed to start recording: ' + error.message);
            this.isRecording = false;
            this.updateRecordingUI(false);
        }
    }

    getSupportedMimeType() {
        const types = [
            'video/webm;codecs=vp9',
            'video/webm;codecs=vp8',
            'video/webm',
            'video/mp4'
        ];

        for (let type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                console.log('✅ Supported MIME type:', type);
                return type;
            }
        }

        console.warn('⚠️ No specific MIME type supported, using default');
        return '';
    }

    startMediaPipeProcessing() {
        console.log('🔄 Starting MediaPipe processing');
        const process = async () => {
            if (!this.isRecording || !this.videoElement || this.videoElement.readyState < 2) {
                return;
            }

            try {
                if (this.pose) {
                    await this.pose.send({ image: this.videoElement });
                }
                if (this.faceMesh) {
                    await this.faceMesh.send({ image: this.videoElement });
                }
            } catch (error) {
                console.warn('MediaPipe processing error:', error);
            }

            if (this.isRecording) {
                setTimeout(process, 100);
            }
        };

        process();
    }

    startTimer() {
        this.recordingTime = 0;
        this.timerInterval = setInterval(() => {
            this.recordingTime++;
            this.updateTimer();
        }, 1000);
    }

    updateTimer() {
        if (this.timerEl) {
            const minutes = Math.floor(this.recordingTime / 60);
            const seconds = this.recordingTime % 60;
            this.timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    startRealTimeFeedback() {
        this.feedbackInterval = setInterval(() => {
            if (this.liveTranscription) {
                this.updateLiveMetrics();
            }
        }, 2000);
    }

    updateLiveMetrics() {
        if (!this.isRecording) return;

        // Update speech metrics from live transcription
        if (this.liveTranscription) {
            const currentTranscript = this.liveTranscription.getFullTranscript();
            console.log('Current transcript:', currentTranscript);
            
            // Calculate WPM (words per minute)
            const wpm = this.calculateWPM(currentTranscript);
            console.log('WPM:', wpm);
            this.updatePaceFeedback(wpm);
            
            // Count filler words
            const fillerCount = this.countFillerWords(currentTranscript);
            console.log('Filler count:', fillerCount);
            this.updateFillerFeedback(fillerCount);
            
            // Update transcript display
            this.updateTranscriptDisplay(currentTranscript);
            
            // Generate live suggestions based on metrics
            const suggestions = this.generateLiveSuggestions(wpm, fillerCount);
            this.updateSuggestions(suggestions);
        } else {
            console.log('No live transcription available');
        }

        // Update posture and eye contact metrics
        this.updateVisualMetrics();
    }

    calculateWPM(transcript) {
        if (!transcript || transcript.trim().length === 0) return 0;
        
        // Count words
        const words = transcript.trim().split(/\s+/).filter(w => w.length > 0);
        const wordCount = words.length;
        
        // Calculate minutes elapsed
        if (this.recordingTime === 0) return 0;
        const minutes = this.recordingTime / 60;
        
        // Calculate WPM
        const wpm = Math.round(wordCount / minutes);
        return wpm;
    }

    countFillerWords(transcript) {
        if (!transcript || transcript.trim().length === 0) {
            console.log('No transcript to analyze');
            return 0;
        }
        
        const fillerWords = ['um', 'uh', 'uhm', 'like', 'you know', 'actually', 'basically', 'literally', 'sort of', 'kind of', 'i mean', 'right', 'so', 'well', 'okay', 'ah', 'er', 'hmm'];
        const lowerTranscript = transcript.toLowerCase();
        console.log('Analyzing transcript:', lowerTranscript);
        
        let count = 0;
        for (let filler of fillerWords) {
            // Escape special regex characters and use word boundaries
            const escapedFiller = filler.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const regex = new RegExp('(^|\\s)' + escapedFiller + '(\\s|$|[,.])', 'gi');
            const matches = lowerTranscript.match(regex);
            if (matches) {
                count += matches.length;
                console.log(`Found ${matches.length} "${filler}"`, matches);
            }
        }
        
        console.log(`Total filler words: ${count}`);
        return count;
    }

    generateLiveSuggestions(wpm, fillerCount) {
        const suggestions = [];
        
        // Pace suggestions
        if (wpm === 0) {
            suggestions.push('🎤 Start speaking to get feedback...');
        } else if (wpm < 120) {
            suggestions.push('⚡ Speak a bit faster');
        } else if (wpm > 180) {
            suggestions.push('⏱️ Slow down your pace');
        } else if (140 <= wpm && wpm <= 160) {
            suggestions.push('✅ Perfect speaking pace!');
        }
        
        // Filler word suggestions
        if (fillerCount > 10) {
            suggestions.push('🚫 Reduce filler words');
        } else if (fillerCount > 5) {
            suggestions.push('💬 Try to minimize filler words');
        } else if (fillerCount <= 2) {
            suggestions.push('🎯 Excellent filler word control!');
        }
        
        return suggestions.slice(0, 3);
    }

    updateVisualMetrics() {
        const postureScore = this.getAverageScore(this.postureData);
        const eyeScore = this.getAverageScore(this.eyeContactData);
        
        if (postureScore > 0) {
            this.updatePostureFeedback(postureScore);
        }
        if (eyeScore > 0) {
            this.updateEyeContactFeedback(eyeScore);
        }
    }

    updateTranscriptDisplay(transcript) {
        if (!this.liveTranscriptEl) return;
        
        if (transcript && transcript.trim()) {
            this.liveTranscriptEl.innerHTML = `<div class="transcript-content">${this.escapeHtml(transcript)}</div>`;
            this.liveTranscriptEl.scrollTop = this.liveTranscriptEl.scrollHeight;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async sendRealTimeFeedback() {
        if (!this.isRecording || !window.currentSession?.sessionId) return;

        try {
            const postureData = {
                posture_score: this.getAverageScore(this.postureData),
                eye_contact_score: this.getAverageScore(this.eyeContactData)
            };

            const response = await fetch('/realtime_feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: window.currentSession.sessionId,
                    posture_data: postureData,
                    recording_time: this.recordingTime
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.feedback) {
                    this.updateRealTimeUI(data.feedback);
                }
            }
        } catch (error) {
            console.warn('Feedback error:', error);
        }
    }

    getAverageScore(dataArray) {
        if (!dataArray || dataArray.length === 0) return 0;
        const recent = dataArray.slice(-10);
        const avg = recent.reduce((sum, item) => sum + item.score, 0) / recent.length;
        return Math.round(avg);
    }

    updateRealTimeUI(feedback) {
        if (!feedback) return;

        const posture = feedback.posture || {};
        const speech = feedback.speech || {};

        if (posture.score !== undefined) {
            this.updatePostureFeedback(posture.score);
        }
        if (posture.eye_contact_score !== undefined) {
            this.updateEyeContactFeedback(posture.eye_contact_score);
        }
        if (speech.current_wpm !== undefined) {
            this.updatePaceFeedback(speech.current_wpm);
        }
        if (speech.filler_rate !== undefined) {
            this.updateFillerFeedback(speech.filler_rate);
        }
        if (feedback.suggestions && feedback.suggestions.length > 0) {
            this.updateSuggestions(feedback.suggestions);
        }
    }

    updatePostureFeedback(score) {
        if (this.postureScoreEl) {
            this.postureScoreEl.textContent = `${Math.round(score)}%`;
            this.postureScoreEl.className = `metric-value ${this.getScoreClass(score)}`;
        }
        const feedbackEl = document.getElementById('postureFeedback');
        if (feedbackEl) {
            if (score >= 80) feedbackEl.textContent = 'Excellent posture!';
            else if (score >= 60) feedbackEl.textContent = 'Good posture';
            else if (score >= 40) feedbackEl.textContent = 'Fair posture';
            else feedbackEl.textContent = 'Adjust your posture';
        }
    }

    updateEyeContactFeedback(score) {
        if (this.eyeContactScoreEl) {
            this.eyeContactScoreEl.textContent = `${Math.round(score)}%`;
            this.eyeContactScoreEl.className = `metric-value ${this.getScoreClass(score)}`;
        }
        const feedbackEl = document.getElementById('eyeContactFeedback');
        if (feedbackEl) {
            if (score >= 75) feedbackEl.textContent = 'Great eye contact!';
            else if (score >= 50) feedbackEl.textContent = 'Good eye contact';
            else feedbackEl.textContent = 'Look at the camera more';
        }
    }

    updatePaceFeedback(wpm) {
        if (this.paceValueEl) {
            this.paceValueEl.textContent = `${Math.round(wpm)} WPM`;
            if (140 <= wpm && wpm <= 160) {
                this.paceValueEl.className = 'metric-value excellent';
            } else if (wpm < 120 || wpm > 180) {
                this.paceValueEl.className = 'metric-value poor';
            } else {
                this.paceValueEl.className = 'metric-value good';
            }
        }
        const feedbackEl = document.getElementById('paceFeedback');
        if (feedbackEl) {
            if (140 <= wpm && wpm <= 160) feedbackEl.textContent = 'Perfect pace!';
            else if (wpm < 120) feedbackEl.textContent = 'Speak faster';
            else if (wpm > 180) feedbackEl.textContent = 'Slow down';
            else feedbackEl.textContent = 'Good pace';
        }
    }

    updateFillerFeedback(count) {
        if (this.fillerCountEl) {
            this.fillerCountEl.textContent = count;
            if (count <= 2) this.fillerCountEl.className = 'metric-value excellent';
            else if (count <= 5) this.fillerCountEl.className = 'metric-value good';
            else if (count <= 10) this.fillerCountEl.className = 'metric-value average';
            else this.fillerCountEl.className = 'metric-value poor';
        }
        const feedbackEl = document.getElementById('fillerFeedback');
        if (feedbackEl) {
            if (count <= 2) feedbackEl.textContent = 'Excellent!';
            else if (count <= 5) feedbackEl.textContent = 'Good control';
            else if (count <= 10) feedbackEl.textContent = 'Try to reduce';
            else feedbackEl.textContent = 'Needs work';
        }
    }

    updateSuggestions(suggestions) {
        if (!this.liveSuggestionsEl) return;
        if (!suggestions || suggestions.length === 0) {
            this.liveSuggestionsEl.innerHTML = '<div class="suggestion-item">✅ Keep it up!</div>';
            return;
        }
        this.liveSuggestionsEl.innerHTML = suggestions.slice(0, 3).map(s => {
            const text = typeof s === 'string' ? s : JSON.stringify(s);
            // Check if suggestion already has emoji
            const hasEmoji = /[🎤⚡⏱️✅🚫💬🎯]/.test(text);
            return `<div class="suggestion-item">${hasEmoji ? text : '💡 ' + text}</div>`;
        }).join('');
    }

    getScoreClass(score) {
        if (score >= 80) return 'excellent';
        if (score >= 60) return 'good';
        if (score >= 40) return 'average';
        return 'poor';
    }

    stopRecording() {
        console.log('⏹️ STOP RECORDING PRESSED');
        if (!this.isRecording) {
            console.log('⚠️ Not currently recording');
            return;
        }

        try {
            this.isRecording = false;

            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                console.log('⏹️ Stopping MediaRecorder...');
                this.mediaRecorder.stop();
            }

            if (this.timerInterval) clearInterval(this.timerInterval);
            if (this.feedbackInterval) clearInterval(this.feedbackInterval);

            if (this.liveTranscription) {
                this.liveTranscription.stop();
                this.speechData.transcript = this.liveTranscription.getTranscript();
                console.log('📝 Transcript captured:', this.speechData.transcript.substring(0, 100));
            }

            this.updateRecordingUI(false);
            console.log('✅ Recording stopped');

        } catch (error) {
            console.error('❌ Error stopping recording:', error);
        }
    }

    handleRecordingStop() {
        console.log('💾 Handling recording stop...');
        console.log('📊 Total chunks recorded:', this.recordedChunks.length);
        console.log('📊 Recording duration:', this.recordingTime, 'seconds');
        
        // Show processing
        this.showProcessingSection();
        
        // Save recording
        setTimeout(() => this.saveRecording(), 500);
    }

    async saveRecording() {
        console.log('💾 Saving recording...');
        try {
            if (this.recordedChunks.length === 0) {
                console.error('❌ No chunks to save');
                this.showError('No recording data captured');
                this.hideProcessingSection();
                return;
            }

            // Determine MIME type
            const mimeType = this.getSupportedMimeType() || 'video/webm';
            const blob = new Blob(this.recordedChunks, { type: mimeType });
            console.log('📦 Blob created:', blob.size, 'bytes, type:', blob.type);

            const formData = new FormData();
            formData.append('video', blob, 'recording.webm');
            formData.append('posture_data', JSON.stringify({
                posture: this.postureData,
                eye_contact: this.eyeContactData,
                duration: this.recordingTime
            }));
            formData.append('transcript', this.speechData.transcript);

            console.log('📤 Uploading to /save_recording...');
            const response = await fetch('/save_recording', {
                method: 'POST',
                body: formData
            });

            console.log('📥 Response status:', response.status);
            const result = await response.json();
            console.log('📋 Response:', result);

            if (response.ok && result.success) {
                console.log('✅ Recording saved successfully');
                console.log('📊 Overall score:', result.overall_score);
                
                // Wait then redirect
                setTimeout(() => {
                    console.log('🔄 Redirecting to /analysis...');
                    window.location.href = '/analysis';
                }, 2000);

            } else {
                throw new Error(result.error || 'Save failed');
            }

        } catch (error) {
            console.error('❌ Error saving recording:', error);
            this.showError('Failed to save: ' + error.message);
            this.hideProcessingSection();
        }
    }

    updateRecordingUI(recording) {
        if (this.startBtn) this.startBtn.disabled = recording;
        if (this.stopBtn) this.stopBtn.disabled = !recording;
        if (this.recordingStatusEl) {
            this.recordingStatusEl.textContent = recording ? 'Recording' : 'Not Recording';
            this.recordingStatusEl.className = recording ? 'status-recording' : 'status-not-recording';
        }
    }

    clearRecordingUI() {
        // Clear metrics display
        if (this.paceValueEl) this.paceValueEl.textContent = '-- WPM';
        if (this.fillerCountEl) this.fillerCountEl.textContent = '0';
        if (this.liveTranscriptEl) this.liveTranscriptEl.textContent = '';
        
        // Clear suggestions
        if (this.liveSuggestionsEl) {
            this.liveSuggestionsEl.innerHTML = '<div class="suggestion-item">🎤 Listening for your speech...</div>';
        }
        
        // Reset feedback text
        const feedbackElements = ['paceFeedback', 'fillerFeedback'];
        feedbackElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = 'Analyzing...';
        });
    }

    showError(message) {
        console.error('❌ ERROR:', message);
        alert('Error: ' + message);
    }

    showProcessingSection() {
        const recording = document.getElementById('recordingSection');
        const processing = document.getElementById('processingSection');
        if (recording) recording.style.display = 'none';
        if (processing) processing.style.display = 'block';
        console.log('⏳ Showing processing section');
        
        // Start progress animation
        this.animateProgress();
    }

    animateProgress() {
        const steps = document.querySelectorAll('.progress-step');
        if (!steps || steps.length === 0) return;
        
        let currentStep = 0;
        
        // Clear all active states
        steps.forEach(step => step.classList.remove('active'));
        
        // Set first step as active
        if (steps[0]) steps[0].classList.add('active');
        
        // Animate through steps
        const progressInterval = setInterval(() => {
            currentStep++;
            
            // Remove previous active
            if (currentStep > 0 && steps[currentStep - 1]) {
                steps[currentStep - 1].classList.remove('active');
            }
            
            // Add new active
            if (currentStep < steps.length && steps[currentStep]) {
                steps[currentStep].classList.add('active');
            }
            
            // Stop when all steps are done
            if (currentStep >= steps.length - 1) {
                clearInterval(progressInterval);
            }
        }, 3000); // Change step every 3 seconds
    }

    hideProcessingSection() {
        const recording = document.getElementById('recordingSection');
        const processing = document.getElementById('processingSection');
        if (processing) processing.style.display = 'none';
        if (recording) recording.style.display = 'block';
        console.log('❌ Hiding processing section');
    }

    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => {
                track.stop();
                console.log('🛑 Stopped track:', track.kind);
            });
        }
        if (this.timerInterval) clearInterval(this.timerInterval);
        if (this.feedbackInterval) clearInterval(this.feedbackInterval);
        if (this.liveTranscription) this.liveTranscription.abort();
        console.log('🧹 Cleanup complete');
    }
}

// Global session
let practiceSession = null;
let currentSession = { sessionId: null, topic: null, topicType: null, topicKeywords: [] };
window.currentSession = currentSession;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 Page loaded, initializing PracticeSession');
    practiceSession = new PracticeSession();
    console.log('🎯 Ready to record!');
});

// Global functions for onclick handlers
function startRecording() {
    console.log('🎬 startRecording() called from HTML');
    if (practiceSession) {
        practiceSession.startRecording();
    } else {
        console.error('❌ practiceSession not initialized');
    }
}

function stopRecording() {
    console.log('⏹️ stopRecording() called from HTML');
    if (practiceSession) {
        practiceSession.stopRecording();
    } else {
        console.error('❌ practiceSession not initialized');
    }
}

function selectTopic(topic) {
    console.log('📌 Topic selected:', topic);
    currentSession.topic = topic;
    currentSession.topicType = 'text';
    startSession();
}

function useCustomTopic() {
    const input = document.getElementById('customTopicInput');
    const topic = input.value.trim();
    if (topic) {
        console.log('📌 Custom topic:', topic);
        currentSession.topic = topic;
        currentSession.topicType = 'text';
        startSession();
    }
}

async function startSession() {
    console.log('🚀 Starting session...');
    try {
        const formData = new FormData();
        formData.append('topic_text', currentSession.topic);

        const response = await fetch('/upload_topic', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('📋 Session response:', data);

        if (data.success) {
            currentSession.sessionId = data.session_id;
            currentSession.topicKeywords = data.keywords || [];
            console.log('✅ Session created:', currentSession.sessionId);
            showRecordingSection();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('❌ Session error:', error);
        alert('Error starting session');
    }
}

function showRecordingSection() {
    console.log('🎬 Showing recording section');
    const topicSection = document.getElementById('topicSection');
    const recordingSection = document.getElementById('recordingSection');
    
    if (topicSection) topicSection.classList.remove('active');
    if (recordingSection) recordingSection.style.display = 'block';

    const topicEl = document.getElementById('currentTopic');
    if (topicEl) topicEl.textContent = currentSession.topic;
    
    console.log('✅ Recording section displayed');
}

function goBackToTopics() {
    console.log('🔙 Going back to topics');
    const topicSection = document.getElementById('topicSection');
    const recordingSection = document.getElementById('recordingSection');
    
    if (recordingSection) recordingSection.style.display = 'none';
    if (topicSection) topicSection.classList.add('active');
    
    if (practiceSession && practiceSession.isRecording) {
        practiceSession.stopRecording();
    }
    if (practiceSession) {
        practiceSession.cleanup();
    }
}
