// Additional utility functions for the API Test UI

class AiderApiClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.currentSession = null;
        this.eventSource = null;
    }
    
    async createSession(options = {}) {
        const defaultOptions = {
            model: 'gpt-4o-mini',
            files: ['index.html'],
            edit_format: 'diff',
            auto_commits: false
        };
        
        const requestData = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(`${this.baseUrl}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentSession = data;
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async sendMessage(message, options = {}) {
        if (!this.currentSession) {
            throw new Error('No active session. Create a session first.');
        }
        
        const requestData = {
            message,
            session_id: this.currentSession.session_id,
            files: this.currentSession.files,
            stream: false,
            ...options
        };
        
        try {
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async streamMessage(message, onEvent, options = {}) {
        if (!this.currentSession) {
            throw new Error('No active session. Create a session first.');
        }
        
        const requestData = {
            message,
            session_id: this.currentSession.session_id,
            files: this.currentSession.files,
            stream: true,
            ...options
        };
        
        // Close existing stream
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        return new Promise((resolve, reject) => {
            // First send the POST request
            fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            }).then(response => {
                if (!response.ok) {
                    reject(new Error(`HTTP ${response.status}`));
                    return;
                }
                
                // Create EventSource for the streaming response
                this.eventSource = new EventSource(`${this.baseUrl}/chat`);
                
                this.eventSource.onmessage = (event) => {
                    onEvent('message', event.data);
                };
                
                ['start', 'processing', 'response', 'complete', 'error'].forEach(eventType => {
                    this.eventSource.addEventListener(eventType, (event) => {
                        onEvent(eventType, event.data);
                        
                        if (eventType === 'complete' || eventType === 'error') {
                            this.eventSource.close();
                            resolve();
                        }
                    });
                });
                
                this.eventSource.onerror = () => {
                    onEvent('error', 'Connection error');
                    this.eventSource.close();
                    reject(new Error('Stream connection error'));
                };
            }).catch(reject);
        });
    }
    
    async getFiles() {
        if (!this.currentSession) {
            throw new Error('No active session. Create a session first.');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/sessions/${this.currentSession.session_id}/files`);
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data: data.files };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getFileContent(filePath) {
        if (!this.currentSession) {
            throw new Error('No active session. Create a session first.');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/sessions/${this.currentSession.session_id}/file_content?file_path=${encodeURIComponent(filePath)}`);
            const data = await response.json();
            
            if (response.ok) {
                return { success: true, data: data.content };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async deleteSession() {
        if (!this.currentSession) {
            throw new Error('No active session to delete.');
        }
        
        try {
            const response = await fetch(`${this.baseUrl}/sessions/${this.currentSession.session_id}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentSession = null;
                return { success: true, data };
            } else {
                return { success: false, error: data };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async getModels() {
        try {
            const response = await fetch(`${this.baseUrl}/models`);
            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// Predefined test scenarios
const testScenarios = {
    'simple-html': {
        name: 'Simple HTML Page',
        message: 'Create a simple HTML page with a header, some content, and a button that shows an alert when clicked',
        files: ['index.html']
    },
    
    'todo-app': {
        name: 'Todo App',
        message: 'Create a todo application with HTML, CSS, and JavaScript. Include add, delete, and mark complete functionality.',
        files: ['index.html', 'style.css', 'script.js']
    },
    
    'landing-page': {
        name: 'Landing Page',
        message: 'Create a modern landing page for a tech startup with hero section, features, and contact form.',
        files: ['index.html', 'style.css', 'script.js']
    },
    
    'calculator': {
        name: 'Calculator',
        message: 'Create a calculator web app with HTML, CSS, and JavaScript that can perform basic arithmetic operations.',
        files: ['index.html', 'style.css', 'script.js']
    },
    
    'weather-widget': {
        name: 'Weather Widget',
        message: 'Create a weather widget that shows current weather information with a clean design.',
        files: ['index.html', 'style.css', 'script.js']
    }
};

// Utility functions
function formatResponse(response) {
    if (typeof response === 'string') {
        try {
            return JSON.stringify(JSON.parse(response), null, 2);
        } catch {
            return response;
        }
    }
    return JSON.stringify(response, null, 2);
}

function logToConsole(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] ${message}`, data || '');
}

function showNotification(message, type = 'info') {
    // Simple notification system
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 4px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#28a745';
            break;
        case 'error':
            notification.style.backgroundColor = '#dc3545';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ffc107';
            notification.style.color = '#212529';
            break;
        default:
            notification.style.backgroundColor = '#007bff';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification {
        animation: slideIn 0.3s ease-out;
    }
`;
document.head.appendChild(style);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AiderApiClient, testScenarios, formatResponse, logToConsole, showNotification };
} 