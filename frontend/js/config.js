// Configuración dinámica de la aplicación
class AppConfig {
    constructor() {
        // Determinar si estamos en desarrollo (localhost) o en producción
        this.isDevelopment = window.location.hostname === 'localhost' || 
                             window.location.hostname === '127.0.0.1';
        
        // La API base: en desarrollo usamos localhost:5000, en producción usamos el mismo hostname y puerto 5000
        this.apiBase = this.isDevelopment 
            ? 'http://localhost:5000/api'
            : `http://${window.location.hostname}:5000/api`;
        
        console.log('Configuración cargada:', {
            entorno: this.isDevelopment ? 'Desarrollo' : 'Producción',
            apiBase: this.apiBase,
            hostname: window.location.hostname
        });
    }
    
    getApiBase() {
        return this.apiBase;
    }
    
    isDev() {
        return this.isDevelopment;
    }
}

// Instancia global de configuración
const appConfig = new AppConfig();
