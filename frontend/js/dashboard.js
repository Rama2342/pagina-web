// Funcionalidades específicas del dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación
    if (!auth.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    // Cargar datos del usuario
    loadUserData();
    
    // Cargar estadísticas
    loadStatistics();
    
    // Cargar actividad reciente
    loadRecentActivity();
    
    // Configurar event listeners
    setupDashboardEvents();
    
    // Iniciar actualizaciones automáticas
    startAutoUpdates();
});

async function loadUserData() {
    try {
        const data = await auth.fetchProtectedData();
        
        if (data) {
            // Actualizar UI con datos del usuario
            if (document.getElementById('welcomeMessage')) {
                document.getElementById('welcomeMessage').textContent = data.message;
            }
            if (document.getElementById('userName')) {
                document.getElementById('userName').textContent = data.user;
            }
            if (document.getElementById('userEmail')) {
                document.getElementById('userEmail').textContent = data.email;
            }
            
            // Simular fecha de registro
            const joinDate = new Date();
            joinDate.setMonth(joinDate.getMonth() - 2);
            if (document.getElementById('userSince')) {
                document.getElementById('userSince').textContent = joinDate.toLocaleDateString();
            }
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        showNotification('Error al cargar datos del usuario', 'error');
    }
}

function loadStatistics() {
    // Simular datos de estadísticas (en una app real esto vendría del backend)
    const stats = {
        sessions: Math.floor(Math.random() * 100) + 50,
        tasks: Math.floor(Math.random() * 50) + 20,
        messages: Math.floor(Math.random() * 200) + 100
    };
    
    // Animar contadores
    animateCounter('statSessions', stats.sessions);
    animateCounter('statTasks', stats.tasks);
    animateCounter('statMessages', stats.messages);
}

function animateCounter(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.setAttribute('data-target', targetValue);
    
    let current = 0;
    const duration = 2000;
    const step = targetValue / (duration / 16);
    
    const timer = setInterval(() => {
        current += step;
        if (current >= targetValue) {
            element.textContent = targetValue;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

function loadRecentActivity() {
    // Simular actividad reciente (en una app real esto vendría del backend)
    const activities = [
        'Inicio de sesión exitoso',
        'Perfil actualizado',
        'Nueva tarea creada',
        'Reporte generado',
        'Configuración modificada'
    ];
    
    const activityList = document.getElementById('activityList');
    if (!activityList) return;
    
    activityList.innerHTML = '';
    
    activities.forEach(activity => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="activity-icon">🔹</span>
            <span class="activity-text">${activity}</span>
            <span class="activity-time">Hace ${Math.floor(Math.random() * 60)} min</span>
        `;
        activityList.appendChild(li);
    });
}

function setupDashboardEvents() {
    // Configurar el botón de logout
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
                auth.logout();
            }
        });
    }
    
    // Efectos hover en botones de acción
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 5px 15px rgba(0, 217, 255, 0.4)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
        
        // Agregar funcionalidad a los botones
        button.addEventListener('click', function() {
            const buttonText = this.textContent.trim();
            switch(buttonText) {
                case 'Nuevo Proyecto':
                    showNotification('Función de nuevo proyecto en desarrollo', 'info');
                    break;
                case 'Ver Reportes':
                    showNotification('Función de reportes en desarrollo', 'info');
                    break;
                case 'Configuración':
                    showNotification('Función de configuración en desarrollo', 'info');
                    break;
            }
        });
    });
    
    // Efectos de hover en las tarjetas
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.2)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = 'none';
        });
    });
}

function startAutoUpdates() {
    // Actualizar estadísticas cada 30 segundos
    setInterval(() => {
        loadStatistics();
    }, 30000);
    
    // Actualizar actividad cada minuto
    setInterval(() => {
        loadRecentActivity();
    }, 60000);
    
    // Verificar autenticación periódicamente
    setInterval(() => {
        if (!auth.isAuthenticated()) {
            showNotification('Sesión expirada. Redirigiendo al login...', 'error');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    }, 300000); // Cada 5 minutos
}

// Funciones utilitarias para el dashboard
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Aplicar estilos
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        background: type === 'error' ? 'rgba(255, 0, 0, 0.1)' : 
                  type === 'success' ? 'rgba(0, 255, 0, 0.1)' : 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        border: `1px solid ${type === 'error' ? 'rgba(255, 0, 0, 0.2)' : 
                               type === 'success' ? 'rgba(0, 255, 0, 0.2)' : 'rgba(255, 255, 255, 0.2)'}`,
        borderRadius: '10px',
        padding: '15px',
        color: 'white',
        zIndex: '10000',
        maxWidth: '300px',
        animation: 'slideIn 0.3s ease'
    });
    
    document.body.appendChild(notification);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Función para actualizar el reloj en tiempo real (opcional)
function startClock() {
    function updateClock() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const dateString = now.toLocaleDateString();
        
        const clockElement = document.getElementById('dashboardClock');
        if (clockElement) {
            clockElement.innerHTML = `
                <div>${dateString}</div>
                <div>${timeString}</div>
            `;
        }
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

// Función para cargar datos en tiempo real desde el backend
async function loadRealTimeData() {
    try {
        const response = await fetch(`${auth.apiBase}/user`, {
            headers: auth.getAuthHeaders()
        });
        
        if (response.ok) {
            const userData = await response.json();
            
            // Actualizar información del usuario en tiempo real
            if (userData.user && document.getElementById('userProfile')) {
                document.getElementById('userProfile').innerHTML = `
                    <strong>Usuario:</strong> ${userData.user.username}<br>
                    <strong>Email:</strong> ${userData.user.email}<br>
                    <strong>Miembro desde:</strong> ${new Date(userData.user.created_at).toLocaleDateString()}
                `;
            }
        }
    } catch (error) {
        console.error('Error loading real-time data:', error);
    }
}

// Iniciar funcionalidades adicionales cuando esté disponible
document.addEventListener('DOMContentLoaded', function() {
    // Iniciar reloj si existe el elemento
    if (document.getElementById('dashboardClock')) {
        startClock();
    }
    
    // Cargar datos en tiempo real cada minuto
    setInterval(loadRealTimeData, 60000);
});

// Exportar funciones para uso global
window.showNotification = showNotification;
window.auth = auth;

// Manejar errores globales
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    showNotification('Ocurrió un error inesperado', 'error');
});

// Manejar promesas no capturadas
window.addEventListener('unhandledrejection', function(e) {
    console.error('Promesa no capturada:', e.reason);
    showNotification('Error en la aplicación', 'error');
});