// speech-recognition.js - Web Speech API integration for live transcription

class LiveTranscription {
    constructor() {
        // Get speech recognition API (cross-browser support)
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech Recognition API not supported in this browser');
            this.recognition = null;
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.isListening = false;
        this.transcript = '';
        this.interimTranscript = '';
        this.isFinal = false;
        
        this.setupRecognition();
    }
    
    setupRecognition() {
        if (!this.recognition) return;
        
        // Set language
        this.recognition.lang = 'en-US';
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;
        
        // Handle results
        this.recognition.onstart = () => {
            this.isListening = true;
            console.log('Speech recognition started');
        };
        
        this.recognition.onresult = (event) => {
            this.interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    this.transcript += transcript + ' ';
                    this.isFinal = true;
                } else {
                    this.interimTranscript += transcript;
                }
            }
            
            // Update UI with transcript
            this.updateTranscriptDisplay();
        };
        
        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            console.log('Speech recognition ended');
        };
    }
    
    start() {
        if (!this.recognition) {
            console.warn('Speech Recognition not available');
            return;
        }
        
        this.transcript = '';
        this.interimTranscript = '';
        this.isFinal = false;
        
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
        }
    }
    
    stop() {
        if (!this.recognition) return;
        
        try {
            this.recognition.stop();
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
    }
    
    abort() {
        if (!this.recognition) return;
        
        try {
            this.recognition.abort();
        } catch (error) {
            console.error('Error aborting speech recognition:', error);
        }
    }
    
    updateTranscriptDisplay() {
        const transcriptEl = document.getElementById('liveTranscript');
        if (!transcriptEl) return;
        
        const fullTranscript = this.transcript + ' ' + this.interimTranscript;
        
        if (fullTranscript.trim()) {
            transcriptEl.innerHTML = `<div class="transcript-final">${this.transcript}</div>
                                      <div class="transcript-interim">${this.interimTranscript}</div>`;
            // Auto-scroll to bottom
            transcriptEl.scrollTop = transcriptEl.scrollHeight;
        }
    }
    
    getTranscript() {
        return this.transcript.trim();
    }
    
    getFullTranscript() {
        return (this.transcript + ' ' + this.interimTranscript).trim();
    }
    
    clearTranscript() {
        this.transcript = '';
        this.interimTranscript = '';
        this.updateTranscriptDisplay();
    }
}

// Export for use in main script
window.LiveTranscription = LiveTranscription;
