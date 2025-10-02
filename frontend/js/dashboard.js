// Funcionalidades específicas del dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación
    if (!auth.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    // Mostrar indicador de carga
    showNotification('Cargando información del usuario...', 'info');
    
    // Cargar datos del usuario
    loadUserProfile();
    
    // Cargar información académica
    loadAcademicInfo();
    
    // Cargar actividades y noticias
    loadActivities();
    loadNews();
    
    // Iniciar reloj y actualizaciones
    startRealTimeClock();
    startAutoUpdates();
    
    // Configurar event listeners
    setupDashboardEvents();
    
    // Monitorear conexión
    setupConnectionMonitoring();
    
    // Ocultar indicador de carga después de 2 segundos
    setTimeout(() => {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            if (notification.textContent.includes('Cargando información')) {
                notification.remove();
            }
        });
    }, 2000);
});

async function loadUserProfile() {
    try {
        const response = await fetch(`${auth.apiBase}/user/full-profile`, {
            headers: auth.getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                // Actualizar UI con datos reales del usuario
                updateUserInterface(data.user);
                
                // Guardar datos en localStorage para uso posterior
                localStorage.setItem('userData', JSON.stringify(data.user));
            }
        } else if (response.status === 401) {
            // Token inválido o expirado
            auth.logout();
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
        showNotification('Error al cargar perfil del usuario', 'error');
        
        // Intentar cargar datos desde localStorage como fallback
        const savedData = localStorage.getItem('userData');
        if (savedData) {
            updateUserInterface(JSON.parse(savedData));
        }
    }
}

async function loadAcademicInfo() {
    try {
        const response = await fetch(`${auth.apiBase}/user/academic-info`, {
            headers: auth.getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                // Actualizar información académica
                updateAcademicInfo(data.academic_info);
            }
        }
    } catch (error) {
        console.error('Error loading academic info:', error);
        showNotification('Error al cargar información académica', 'error');
    }
}

function updateUserInterface(userData) {
    // Información principal
    if (document.getElementById('userName')) {
        document.getElementById('userName').textContent = userData.username;
    }
    if (document.getElementById('userEmail')) {
        document.getElementById('userEmail').textContent = userData.email;
    }
    if (document.getElementById('userCode')) {
        document.getElementById('userCode').textContent = userData.matricula;
    }
    if (document.getElementById('userCourse')) {
        document.getElementById('userCourse').textContent = userData.curso;
    }
    if (document.getElementById('userRole')) {
        document.getElementById('userRole').textContent = userData.role;
    }
    if (document.getElementById('userGrade')) {
        document.getElementById('userGrade').textContent = userData.curso;
    }
    if (document.getElementById('footerUser')) {
        document.getElementById('footerUser').textContent = userData.username;
    }
    if (document.getElementById('welcomeMessage')) {
        document.getElementById('welcomeMessage').textContent = `Bienvenido, ${userData.username}`;
    }
    
    // Información adicional si existe en los elementos
    if (document.getElementById('userTurn')) {
        document.getElementById('userTurn').textContent = userData.turno || 'Mañana';
    }
    if (document.getElementById('userStatus')) {
        document.getElementById('userStatus').textContent = userData.estado || 'Regular';
    }
}

function updateAcademicInfo(academicData) {
    // Actualizar estadísticas académicas
    if (document.getElementById('statAverage')) {
        document.getElementById('statAverage').textContent = academicData.promedio_general;
        document.getElementById('statAverage').setAttribute('data-target', academicData.promedio_general);
    }
    if (document.getElementById('statAttendance')) {
        document.getElementById('statAttendance').textContent = academicData.asistencia + '%';
        document.getElementById('statAttendance').setAttribute('data-target', academicData.asistencia);
    }
    if (document.getElementById('statSubjects')) {
        document.getElementById('statSubjects').textContent = academicData.materias_activas;
        document.getElementById('statSubjects').setAttribute('data-target', academicData.materias_activas);
    }
    
    // Animar contadores
    animateCounter('statAverage', academicData.promedio_general);
    animateCounter('statAttendance', academicData.asistencia);
    animateCounter('statSubjects', academicData.materias_activas);
    
    // Actualizar última actualización
    if (document.getElementById('lastUpdate')) {
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
    }
}

function animateCounter(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let current = 0;
    const duration = 2000;
    const step = targetValue / (duration / 16);
    
    const timer = setInterval(() => {
        current += step;
        if (current >= targetValue) {
            element.textContent = elementId === 'statAverage' ? targetValue.toFixed(1) : Math.round(targetValue);
            clearInterval(timer);
        } else {
            element.textContent = elementId === 'statAverage' ? current.toFixed(1) : Math.floor(current);
        }
    }, 16);
}

async function loadActivities() {
    try {
        // Simular carga de actividades (en una app real vendría del backend)
        const activities = [
            {
                type: 'exam',
                title: 'Examen de Matemáticas',
                description: 'Unidad 3 - Álgebra',
                time: 'Hoy - 10:00 AM',
                urgent: true
            },
            {
                type: 'assignment',
                title: 'Entrega de Historia',
                description: 'Revolución Industrial',
                time: 'Mañana - 2:00 PM',
                important: true
            },
            {
                type: 'event',
                title: 'Olimpíadas de Ciencias',
                description: 'Fase regional',
                time: '15/09 - 9:00 AM'
            }
        ];
        
        updateActivitiesList(activities);
    } catch (error) {
        console.error('Error loading activities:', error);
    }
}

function updateActivitiesList(activities) {
    const activitiesList = document.getElementById('upcomingActivities');
    if (!activitiesList) return;
    
    activitiesList.innerHTML = '';
    
    activities.forEach(activity => {
        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        
        if (activity.urgent) activityItem.classList.add('urgent');
        if (activity.important) activityItem.classList.add('important');
        
        let icon = '📚';
        if (activity.type === 'assignment') icon = '📝';
        if (activity.type === 'event') icon = '🎯';
        
        activityItem.innerHTML = `
            <div class="activity-icon">${icon}</div>
            <div class="activity-content">
                <h4>${activity.title}</h4>
                <p>${activity.description}</p>
                <span class="activity-time">${activity.time}</span>
            </div>
        `;
        
        activitiesList.appendChild(activityItem);
    });
}

async function loadNews() {
    try {
        // Simular carga de noticias (en una app real vendría del backend)
        const news = [
            {
                date: '25/08/2024',
                title: 'Inscripciones 2024 Abiertas',
                content: 'Las inscripciones para el próximo ciclo lectivo estarán abiertas desde el 1 de octubre.'
            },
            {
                date: '20/08/2024',
                title: 'Torneo Deportivo Intercolegial',
                content: 'Este sábado se realizará el torneo de fútbol en las instalaciones del colegio.'
            }
        ];
        
        updateNewsList(news);
    } catch (error) {
        console.error('Error loading news:', error);
    }
}

function updateNewsList(news) {
    const newsContainer = document.querySelector('.news-list');
    if (!newsContainer) return;
    
    newsContainer.innerHTML = '';
    
    news.forEach(newsItem => {
        const newsElement = document.createElement('div');
        newsElement.className = 'news-item';
        newsElement.innerHTML = `
            <div class="news-date">${newsItem.date}</div>
            <h4>${newsItem.title}</h4>
            <p>${newsItem.content}</p>
        `;
        
        newsContainer.appendChild(newsElement);
    });
}

const API_URL = 'http://localhost:5000';

async function loadMessages() {
    const res = await fetch(`${API_URL}/api/student-messages`);
    const data = await res.json();
    const container = document.getElementById('student-messages');
    if (data.messages && data.messages.length > 0) {
        container.innerHTML = data.messages.map(msg => 
            `<div class="notification">
                <div><strong>${new Date(msg.fecha).toLocaleString()}</strong></div>
                <div>${msg.texto}</div>
            </div>`
        ).join('');
    } else {
        container.textContent = "No hay mensajes.";
    }
}
loadMessages();

function startRealTimeClock() {
    function updateClock() {
        const now = new Date();
        const timeElement = document.getElementById('currentTime');
        const dateElement = document.getElementById('currentDate');
        
        if (timeElement && dateElement) {
            const timeString = now.toLocaleTimeString('es-ES', { 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            });
            
            const options = { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            };
            const dateString = now.toLocaleDateString('es-ES', options);
            
            timeElement.textContent = timeString;
            dateElement.textContent = dateString;
        }
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

function startAutoUpdates() {
    // Actualizar información cada 5 minutos
    setInterval(() => {
        loadUserProfile();
        loadAcademicInfo();
    }, 300000);
    
    // Actualizar actividades cada hora
    setInterval(() => {
        loadActivities();
    }, 3600000);
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
    
    // Configurar botones de acciones
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.querySelector('span').textContent;
            showNotification(`Acción: ${action}`, 'info');
        });
    });
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close">×</button>
        </div>
    `;
    
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
    
    // Configurar botón de cerrar
    notification.querySelector('.notification-close').addEventListener('click', function() {
        notification.remove();
    });
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Añadir esta función para manejar errores de conexión
function setupConnectionMonitoring() {
    let isOnline = true;
    
    // Verificar conexión periódicamente
    setInterval(async () => {
        try {
            const response = await fetch(`${auth.apiBase}/health`, {
                method: 'GET',
                headers: auth.getAuthHeaders()
            });
            
            if (!response.ok && isOnline) {
                isOnline = false;
                showNotification('Conexión perdida con el servidor', 'error');
            } else if (response.ok && !isOnline) {
                isOnline = true;
                showNotification('Conexión restaurada', 'success');
                // Recargar datos cuando se restablece la conexión
                loadUserProfile();
                loadAcademicInfo();
            }
        } catch (error) {
            if (isOnline) {
                isOnline = false;
                showNotification('Conexión perdida con el servidor', 'error');
            }
        }
    }, 30000); // Verificar cada 30 segundos
}

// Manejar errores globales
window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    showNotification('Ocurrió un error inesperado', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Promesa no capturada:', e.reason);
    showNotification('Error en la aplicación', 'error');
});

// Exportar funciones para uso global
window.showNotification = showNotification;
window.auth = auth;
