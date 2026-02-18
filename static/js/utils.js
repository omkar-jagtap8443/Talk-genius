// static/js/utils.js - Utility functions
class TalkGeniusUtils {
    static formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    static formatDate(timestamp) {
        return new Date(timestamp * 1000).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static getScoreColor(score) {
        if (score >= 90) return '#10b981'; // green
        if (score >= 80) return '#84cc16'; // lime
        if (score >= 70) return '#eab308'; // yellow
        if (score >= 60) return '#f97316'; // orange
        return '#ef4444'; // red
    }

    static getScoreCategory(score) {
        if (score >= 90) return 'excellent';
        if (score >= 80) return 'very-good';
        if (score >= 70) return 'good';
        if (score >= 60) return 'average';
        if (score >= 50) return 'needs-improvement';
        return 'poor';
    }

    static calculateAverage(numbers) {
        if (!numbers || numbers.length === 0) return 0;
        const sum = numbers.reduce((a, b) => a + b, 0);
        return sum / numbers.length;
    }

    static calculateStandardDeviation(numbers) {
        if (!numbers || numbers.length === 0) return 0;
        const avg = this.calculateAverage(numbers);
        const squareDiffs = numbers.map(value => Math.pow(value - avg, 2));
        const avgSquareDiff = this.calculateAverage(squareDiffs);
        return Math.sqrt(avgSquareDiff);
    }

    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        }
    }

    static showNotification(message, type = 'info', duration = 3000) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        // Add styles if not already added
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 10000;
                    transform: translateX(400px);
                    transition: transform 0.3s ease;
                }
                .notification.show {
                    transform: translateX(0);
                }
                .notification-content {
                    padding: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                .notification-close {
                    background: none;
                    border: none;
                    font-size: 1.2rem;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                }
                .notification-info { border-left: 4px solid #3b82f6; }
                .notification-success { border-left: 4px solid #10b981; }
                .notification-warning { border-left: 4px solid #f59e0b; }
                .notification-error { border-left: 4px solid #ef4444; }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);

        // Close button handler
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.classList.remove('show');
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }

        return notification;
    }

    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }

    static generateRandomId(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    }

    static isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    static getBrowserInfo() {
        const ua = navigator.userAgent;
        let browserName;
        let browserVersion;

        if (ua.includes('Chrome') && !ua.includes('Edg')) {
            browserName = 'Chrome';
            browserVersion = ua.match(/Chrome\/([0-9.]+)/)[1];
        } else if (ua.includes('Firefox')) {
            browserName = 'Firefox';
            browserVersion = ua.match(/Firefox\/([0-9.]+)/)[1];
        } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
            browserName = 'Safari';
            browserVersion = ua.match(/Version\/([0-9.]+)/)[1];
        } else if (ua.includes('Edg')) {
            browserName = 'Edge';
            browserVersion = ua.match(/Edg\/([0-9.]+)/)[1];
        } else {
            browserName = 'Unknown';
            browserVersion = 'Unknown';
        }

        return {
            name: browserName,
            version: browserVersion,
            userAgent: ua
        };
    }

    static checkCameraSupport() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    static checkMicrophoneSupport() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    static async checkPermissions() {
        const permissions = {
            camera: false,
            microphone: false
        };

        try {
            // Check camera
            const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
            cameraStream.getTracks().forEach(track => track.stop());
            permissions.camera = true;
        } catch (error) {
            permissions.camera = false;
        }

        try {
            // Check microphone
            const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            micStream.getTracks().forEach(track => track.stop());
            permissions.microphone = true;
        } catch (error) {
            permissions.microphone = false;
        }

        return permissions;
    }

    static async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static parseJSONSafe(str, defaultValue = null) {
        try {
            return JSON.parse(str);
        } catch (error) {
            return defaultValue;
        }
    }

    static stringifyJSONSafe(obj, defaultValue = '{}') {
        try {
            return JSON.stringify(obj);
        } catch (error) {
            return defaultValue;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TalkGeniusUtils;
}