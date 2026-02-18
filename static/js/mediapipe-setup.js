// static/js/mediapipe-setup.js - MediaPipe configuration and utilities
class MediaPipeManager {
    constructor() {
        this.pose = null;
        this.faceMesh = null;
        this.hands = null;
        this.isInitialized = false;
    }

    async initialize() {
        try {
            await this.initializePose();
            await this.initializeFaceMesh();
            this.isInitialized = true;
            console.log('MediaPipe manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize MediaPipe:', error);
            throw error;
        }
    }

    async initializePose() {
        this.pose = new Pose({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
            }
        });

        await this.pose.setOptions({
            modelComplexity: 1,
            smoothLandmarks: true,
            enableSegmentation: false,
            smoothSegmentation: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        return this.pose;
    }

    async initializeFaceMesh() {
        this.faceMesh = new FaceMesh({
            locateFile: (file) => {
                return `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`;
            }
        });

        await this.faceMesh.setOptions({
            maxNumFaces: 1,
            refineLandmarks: true,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });

        return this.faceMesh;
    }

    // Posture analysis utilities
    calculatePostureScore(landmarks) {
        if (!landmarks) return 50;

        try {
            const keyPoints = this.extractKeyPoints(landmarks);
            return this.analyzePostureFromKeyPoints(keyPoints);
        } catch (error) {
            console.error('Posture calculation error:', error);
            return 50;
        }
    }

    extractKeyPoints(landmarks) {
        return {
            leftShoulder: landmarks[11],
            rightShoulder: landmarks[12],
            leftHip: landmarks[23],
            rightHip: landmarks[24],
            leftElbow: landmarks[13],
            rightElbow: landmarks[14],
            nose: landmarks[0]
        };
    }

    analyzePostureFromKeyPoints(points) {
        let score = 100;

        // Shoulder alignment check
        if (points.leftShoulder && points.rightShoulder) {
            const shoulderSlope = Math.abs(points.leftShoulder.y - points.rightShoulder.y);
            score -= shoulderSlope * 100;
        }

        // Hip alignment check
        if (points.leftHip && points.rightHip) {
            const hipSlope = Math.abs(points.leftHip.y - points.rightHip.y);
            score -= hipSlope * 100;
        }

        // Spinal alignment (shoulder to hip)
        if (points.leftShoulder && points.leftHip && points.rightShoulder && points.rightHip) {
            const leftAlignment = Math.abs(points.leftShoulder.x - points.leftHip.x);
            const rightAlignment = Math.abs(points.rightShoulder.x - points.rightHip.x);
            const avgAlignment = (leftAlignment + rightAlignment) / 2;
            score -= avgAlignment * 50;
        }

        return Math.max(0, Math.min(100, Math.round(score)));
    }

    // Eye contact analysis
    calculateEyeContactScore(faceLandmarks) {
        if (!faceLandmarks || faceLandmarks.length === 0) return 50;

        try {
            // Use face bounding box and key points to estimate gaze
            const faceBounds = this.calculateFaceBounds(faceLandmarks);
            const gazeDirection = this.estimateGazeDirection(faceLandmarks);
            
            return this.estimateEyeContactFromGaze(gazeDirection, faceBounds);
        } catch (error) {
            console.error('Eye contact calculation error:', error);
            return 50;
        }
    }

    calculateFaceBounds(landmarks) {
        let minX = 1, maxX = 0, minY = 1, maxY = 0;
        
        landmarks.forEach(landmark => {
            minX = Math.min(minX, landmark.x);
            maxX = Math.max(maxX, landmark.x);
            minY = Math.min(minY, landmark.y);
            maxY = Math.max(maxY, landmark.y);
        });

        return {
            centerX: (minX + maxX) / 2,
            centerY: (minY + maxY) / 2,
            width: maxX - minX,
            height: maxY - minY
        };
    }

    estimateGazeDirection(landmarks) {
        // Simplified gaze estimation using nose and eye positions
        const nose = landmarks[1];
        const leftEye = landmarks[33];
        const rightEye = landmarks[263];
        
        if (!nose || !leftEye || !rightEye) {
            return { x: 0.5, y: 0.5 }; // Default center
        }

        const eyeCenter = {
            x: (leftEye.x + rightEye.x) / 2,
            y: (leftEye.y + rightEye.y) / 2
        };

        // Calculate deviation from face center
        return {
            x: nose.x - eyeCenter.x,
            y: nose.y - eyeCenter.y
        };
    }

    estimateEyeContactFromGaze(gazeDirection, faceBounds) {
        // Calculate how centered the gaze is
        const gazeDistance = Math.sqrt(gazeDirection.x ** 2 + gazeDirection.y ** 2);
        
        // Convert to score (0-100)
        let score = 100 - (gazeDistance * 200);
        return Math.max(0, Math.min(100, Math.round(score)));
    }

    // Visualization utilities
    drawPoseLandmarks(ctx, landmarks, options = {}) {
        if (!landmarks) return;

        const {
            color = '#00FF00',
            lineWidth = 2,
            pointColor = '#FF0000',
            pointSize = 2
        } = options;

        // Draw connections
        if (window.POSE_CONNECTIONS) {
            drawConnectors(ctx, landmarks, POSE_CONNECTIONS, {
                color: color,
                lineWidth: lineWidth
            });
        }

        // Draw landmarks
        drawLandmarks(ctx, landmarks, {
            color: pointColor,
            lineWidth: 1,
            radius: pointSize
        });
    }

    drawFaceLandmarks(ctx, landmarks, options = {}) {
        if (!landmarks) return;

        const {
            color = '#E0E0E0',
            lineWidth = 1
        } = options;

        // Draw face mesh
        if (window.FACEMESH_TESSELATION) {
            drawConnectors(ctx, landmarks, FACEMESH_TESSELATION, {
                color: color,
                lineWidth: lineWidth
            });
        }
    }

    // Performance optimization
    throttle(callback, delay) {
        let lastCall = 0;
        return function (...args) {
            const now = new Date().getTime();
            if (now - lastCall < delay) {
                return;
            }
            lastCall = now;
            return callback(...args);
        };
    }

    // Cleanup
    destroy() {
        if (this.pose) {
            this.pose.close();
        }
        if (this.faceMesh) {
            this.faceMesh.close();
        }
        if (this.hands) {
            this.hands.close();
        }
        
        this.isInitialized = false;
        console.log('MediaPipe manager destroyed');
    }
}

// Global MediaPipe manager instance
let mediaPipeManager = null;

// Initialize MediaPipe when needed
async function initializeMediaPipe() {
    if (!mediaPipeManager) {
        mediaPipeManager = new MediaPipeManager();
        await mediaPipeManager.initialize();
    }
    return mediaPipeManager;
}

// Utility function for coordinate conversion
function convertToPixelCoordinates(normalizedX, normalizedY, canvasWidth, canvasHeight) {
    return {
        x: normalizedX * canvasWidth,
        y: normalizedY * canvasHeight
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MediaPipeManager, initializeMediaPipe };
}