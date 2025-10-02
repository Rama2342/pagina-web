// Verificador de conexión y estado del servidor
class ConnectionChecker {
    constructor() {
        this.apiBase = auth.apiBase;
        this.isOnline = false;
        this.retryCount = 0;
        this.maxRetries = 5;
        this.timeout = 8000; // Aumentar timeout a 8 segundos
    }

    async checkServerStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            const response = await fetch(`${this.apiBase}/health`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            
            clearTimeout(timeoutId);
            
            this.isOnline = response.ok;
            this.retryCount = 0;
            return this.isOnline;
        } catch (error) {
            console.log('Error checking server status:', error.name);
            this.isOnline = false;
            this.retryCount++;
            
            if (this.retryCount >= this.maxRetries) {
                await this.tryDiscoverServer();
            }
            
            return false;
        }
    }

    async tryDiscoverServer() {
        console.log('Attempting to discover server...');
        
        // Try common alternative URLs
        const alternatives = [
            `http://${window.location.hostname}:5000/api/health`,
            `http://${window.location.hostname}:5001/api/health`,
            'http://localhost:5000/api/health',
            'http://127.0.0.1:5000/api/health'
        ];
        
        for (const url of alternatives) {
            try {
                const response = await fetch(url, { method: 'GET' });
                if (response.ok) {
                    console.log(`Discovered server at: ${url}`);
                    // Update the API base for all components
                    auth.apiBase = url.replace('/health', '');
                    this.apiBase = auth.apiBase;
                    this.isOnline = true;
                    this.retryCount = 0;
                    
                    showNotification(`Servidor descubierto en: ${auth.apiBase}`, 'success');
                    return true;
                }
            } catch (e) {
                // Continue to next alternative
                console.log(`Server not found at: ${url}`);
            }
        }
        
        return false;
    }

    showConnectionStatus() {
        const statusElement = document.createElement('div');
        statusElement.id = 'connection-status';
        statusElement.style.cssText = `
            position: fixed;
            bottom: 10px;
            right: 10px;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            z-index: 9999;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        `;

        if (this.isOnline) {
            statusElement.style.background = 'rgba(46, 213, 115, 0.2)';
            statusElement.style.border = '1px solid rgba(46, 213, 115, 0.5)';
            statusElement.style.color = '#2ed573';
            statusElement.innerHTML = `🟢 Conectado a ${this.apiBase}`;
        } else {
            statusElement.style.background = 'rgba(255, 71, 87, 0.2)';
            statusElement.style.border = '1px solid rgba(255, 71, 87, 0.5)';
            statusElement.style.color = '#ff4757';
            statusElement.innerHTML = `🔴 Sin conexión (${this.apiBase})`;
            
            if (this.retryCount > 0) {
                statusElement.innerHTML += `<br><small>Reintentando... (${this.retryCount}/${this.maxRetries})</small>`;
            }
        }

        // Eliminar estado anterior si existe
        const existingStatus = document.getElementById('connection-status');
        if (existingStatus) {
            existingStatus.remove();
        }

        document.body.appendChild(statusElement);
    }

    async init() {
        await this.checkServerStatus();
        this.showConnectionStatus();
        
        // Verificar periódicamente
        setInterval(async () => {
            await this.checkServerStatus();
            this.showConnectionStatus();
        }, 10000); // Check every 10 seconds
    }
}

// Inicializar verificador de conexión
const connectionChecker = new ConnectionChecker();

// Verificar conexión al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure auth is initialized
    setTimeout(() => {
        connectionChecker.init();
    }, 1000);
});
