// Notificación simple para mostrar mensajes en pantalla
function showNotification(message, type = 'info') {
    alert(`${type.toUpperCase()}: ${message}`);
}
window.showNotification = showNotification;
// Notificación simple para mostrar mensajes en pantalla
function showNotification(message, type = 'info') {
    // Puedes personalizar el diseño aquí
    alert(`${type.toUpperCase()}: ${message}`);
}
// Sistema de autenticación mejorado
class Auth {
    constructor() {
        this.token = localStorage.getItem('token');
        this.userData = JSON.parse(localStorage.getItem('userData') || '{}');
        this.apiBase = appConfig.getApiBase(); // Usar configuración dinámica
    }

    async login(username, password) {
        try {
            console.log('Intentando login con:', username);
            console.log('Conectando a:', this.apiBase);
            
            const response = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    username: username.trim(),
                    password: password.trim()
                })
            });

            // Verificar el estado de la respuesta
            if (!response.ok) {
                console.error('Error HTTP:', response.status, response.statusText);
                
                // Intentar obtener el error del response
                try {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Error ${response.status}: ${response.statusText}`);
                } catch (e) {
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }
            }

            const data = await response.json();
            console.log('Respuesta del login:', data);
            
            if (data.success) {
                this.token = data.token;
                this.userData = data.user_data;
                
                // Guardar en localStorage
                localStorage.setItem('token', this.token);
                localStorage.setItem('userData', JSON.stringify(this.userData));
                
                return { success: true, data: data };
            } else {
                return { success: false, error: data.error || 'Error desconocido' };
            }
        } catch (error) {
            console.error('Error en login:', error);
            
            // Mensajes de error más específicos
            let errorMessage = 'Error de conexión con el servidor';
            
            if (error.message.includes('Failed to fetch')) {
                errorMessage = `
                    No se puede conectar con el servidor. 
                    Verifica:
                    1. Que el servidor esté ejecutándose en ${this.apiBase}
                    2. Que la IP/hostname sea correcta
                    3. Que el firewall permita conexiones al puerto 5000
                    4. Que estés en la misma red (si es desde otra máquina)
                `;
            } else if (error.message.includes('500')) {
                errorMessage = 'Error interno del servidor. Contacta al administrador.';
            } else if (error.message.includes('401')) {
                errorMessage = 'Credenciales inválidas. Verifica tu usuario y contraseña.';
            } else {
                errorMessage = error.message;
            }
            
            return { success: false, error: errorMessage };
        }
    }
    async register(username, email, password) {
        try {
            console.log('Intentando registrar:', username, email);
            console.log('Conectando a:', this.apiBase);
            const response = await fetch(`${this.apiBase}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();
            console.log('Respuesta del registro:', data);
            
            if (response.status === 201 && data.success) {
                return { success: true, message: data.message };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            console.error('Error en registro:', error);
            return { 
                success: false, 
                error: `Error de conexión con el servidor (${this.apiBase})` 
            };
        }
    }

    logout() {
        this.token = null;
        this.userData = {};
        localStorage.removeItem('token');
        localStorage.removeItem('userData');
        window.location.href = '/login.html';
    }

    isAuthenticated() {
        return this.token !== null;
    }

    isAdmin() {
        return this.isAuthenticated() && this.userData.is_admin === true;
    }

    getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    getUserData() {
        return this.userData;
    }

    // Verificar acceso a una página específica
    checkPageAccess(page) {
        if (!this.isAuthenticated()) {
            // Usuario no autenticado - solo puede ver index, login y register
            const publicPages = ['/', '/index.html', '/login.html', '/register.html'];
            if (!publicPages.includes(page)) {
                window.location.href = '/login.html';
                return false;
            }
            return true;
        }

        // Usuario autenticado
        if (page === '/admin.html' && !this.isAdmin()) {
            // Usuario común intentando acceder a admin
            showNotification('Acceso denegado. Se requieren privilegios de administrador', 'error');
            window.location.href = '/dashboard.html';
            return false;
        }

        // Usuario autenticado intentando acceder a login/register
        const authPages = ['/login.html', '/register.html'];
        if (authPages.includes(page)) {
            window.location.href = '/dashboard.html';
            return false;
        }

        return true;
    }
}

const auth = new Auth();

// Modifica la función loadAcademicInfo para usar fetchWithTimeout
async function loadAcademicInfo() {
    try {
        const response = await fetchWithTimeout(`${auth.apiBase}/user/academic-info`, {
            headers: auth.getAuthHeaders()
        }, 8000); // 8 segundos timeout

        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                updateAcademicInfo(data.academic_info);
            } else {
                console.error('Error en academic info:', data.error);
                updateAcademicInfo({
                    promedio_general: 0.0,
                    asistencia: 0,
                    materias_activas: 0,
                    estado: 'No disponible'
                });
            }
        } else {
            console.error('Error HTTP en academic info:', response.status);
            updateAcademicInfo({
                promedio_general: 0.0,
                asistencia: 0,
                materias_activas: 0,
                estado: 'No disponible'
            });
        }
    } catch (error) {
        console.error('Error loading academic info:', error);
        updateAcademicInfo({
            promedio_general: 0.0,
            asistencia: 0,
            materias_activas: 0,
            estado: 'Error de conexión'
        });
    }
}
// Función para verificar acceso en cada página
function checkPageAccess() {
    const currentPath = window.location.pathname;
    return auth.checkPageAccess(currentPath);
}

// Función para redirigir según el rol después del login
function redirectAfterLogin(userData) {
    if (userData.is_admin) {
        window.location.href = '/admin.html';
    } else {
        window.location.href = '/dashboard.html';
    }
}

// Middleware para verificar autenticación en páginas protegidas
function requireAuth() {
    if (!auth.isAuthenticated()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// Middleware para verificar si es administrador
function requireAdmin() {
    if (!auth.isAdmin()) {
        showNotification('Acceso denegado. Se requieren privilegios de administrador', 'error');
        window.location.href = '/dashboard.html';
        return false;
    }
    return true;
}

// Función para actualizar la UI con datos del usuario
function updateUserInterface(userData) {
    console.log("Actualizando UI con datos:", userData);
    
    // Información principal del dashboard
    if (document.getElementById('userName')) {
        document.getElementById('userName').textContent = userData.nombre || userData.username || 'Usuario';
    }
    if (document.getElementById('userEmail')) {
        document.getElementById('userEmail').textContent = userData.email || 'email@ejemplo.com';
    }
    if (document.getElementById('userCode')) {
        document.getElementById('userCode').textContent = userData.matricula || 'SI-0000';
    }
    if (document.getElementById('userCourse')) {
        document.getElementById('userCourse').textContent = userData.grado || 'Curso no asignado';
    }
    
    // Información del header
    if (document.getElementById('userRole')) {
        document.getElementById('userRole').textContent = userData.role || 'Usuario';
    }
    if (document.getElementById('userGrade')) {
        document.getElementById('userGrade').textContent = userData.grado || 'No asignado';
    }
    if (document.getElementById('footerUser')) {
        document.getElementById('footerUser').textContent = userData.nombre || userData.username || 'Usuario';
    }
    if (document.getElementById('welcomeMessage')) {
        document.getElementById('welcomeMessage').textContent = `Bienvenido, ${userData.nombre || userData.username || 'Usuario'}`;
    }
    
    // Información adicional
    if (document.getElementById('userTurn')) {
        document.getElementById('userTurn').textContent = userData.turno || 'No asignado';
    }
    if (document.getElementById('userStatus')) {
        document.getElementById('userStatus').textContent = userData.estado || 'Activo';
    }

    // Mostrar/ocultar elementos según el rol
    if (document.getElementById('adminLink')) {
        if (userData.is_admin) {
            document.getElementById('adminLink').style.display = 'block';
        } else {
            document.getElementById('adminLink').style.display = 'none';
        }
    }
}

// Funciones para el dashboard
async function loadAcademicInfo() {
    try {
        const response = await fetch(`${auth.apiBase}/user/academic-info`, {
            headers: auth.getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success) {
                updateAcademicInfo(data.academic_info);
            } else {
                console.error('Error en academic info:', data.error);
                // Mostrar datos por defecto si hay error
                updateAcademicInfo({
                    promedio_general: 0.0,
                    asistencia: 0,
                    materias_activas: 0,
                    estado: 'No disponible'
                });
            }
        } else {
            console.error('Error HTTP en academic info:', response.status);
            // Mostrar datos por defecto si hay error
            updateAcademicInfo({
                promedio_general: 0.0,
                asistencia: 0,
                materias_activas: 0,
                estado: 'No disponible'
            });
        }
    } catch (error) {
        console.error('Error loading academic info:', error);
        // Mostrar datos por defecto si hay error
        updateAcademicInfo({
            promedio_general: 0.0,
            asistencia: 0,
            materias_activas: 0,
            estado: 'Error de conexión'
        });
    }
}

function updateAcademicInfo(academicData) {
    // Actualizar estadísticas académicas si existen los elementos
    if (document.getElementById('statAverage')) {
        document.getElementById('statAverage').textContent = academicData.promedio_general || 0.0;
    }
    if (document.getElementById('statAttendance')) {
        document.getElementById('statAttendance').textContent = (academicData.asistencia || 0) + '%';
    }
    if (document.getElementById('statSubjects')) {
        document.getElementById('statSubjects').textContent = academicData.materias_activas || 0;
    }
    
    // Actualizar información adicional si existe
    if (document.getElementById('academicStatus')) {
        document.getElementById('academicStatus').textContent = academicData.estado || 'No disponible';
    }
    if (document.getElementById('academicGrade')) {
        document.getElementById('academicGrade').textContent = academicData.grado || 'No asignado';
    }
    if (document.getElementById('academicSpecialty')) {
        document.getElementById('academicSpecialty').textContent = academicData.especialidad || 'No especificado';
    }
}

async function loadActivities() {
    try {
        // Simular carga de actividades
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
            }
        ];
        
        updateActivitiesList(activities);
    } catch (error) {
        console.error('Error loading activities:', error);
    }
}

function updateActivitiesList(activities) {
    const activitiesList = document.querySelector('.activities-list');
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
        // Simular carga de noticias
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

// Manejo de formularios
document.addEventListener('DOMContentLoaded', function() {
    // Verificar acceso a la página actual
    if (!checkPageAccess()) return;
    
    // Formulario de login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        console.log('Formulario de login encontrado');
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const loginButton = document.getElementById('loginButton');
            const originalText = loginButton.textContent;
            
            loginButton.disabled = true;
            loginButton.textContent = 'Iniciando sesión...';
            
            try {
                const result = await auth.login(username, password);
                
                if (result.success) {
                    showNotification('Login exitoso', 'success');
                    // Redirigir según el rol
                    setTimeout(() => {
                        redirectAfterLogin(result.data.user_data);
                    }, 1000);
                } else {
                    showNotification('Error: ' + result.error, 'error');
                    loginButton.disabled = false;
                    loginButton.textContent = originalText;
                }
            } catch (error) {
                showNotification('Error de conexión: ' + error.message, 'error');
                loginButton.disabled = false;
                loginButton.textContent = originalText;
            }
        });
    }
    
    // Formulario de registro
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        console.log('Formulario de registro encontrado');
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (password !== confirmPassword) {
                showNotification('Las contraseñas no coinciden', 'error');
                return;
            }
            
            const registerButton = document.getElementById('registerButton');
            const originalText = registerButton.textContent;
            
            registerButton.disabled = true;
            registerButton.textContent = 'Creando cuenta...';
            
            try {
                const result = await auth.register(username, email, password);
                
                if (result.success) {
                    showNotification('Cuenta creada exitosamente. Ahora puedes iniciar sesión.', 'success');
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 2000);
                } else {
                    showNotification('Error: ' + result.error, 'error');
                    registerButton.disabled = false;
                    registerButton.textContent = originalText;
                }
            } catch (error) {
                showNotification('Error de conexión: ' + error.message, 'error');
                registerButton.disabled = false;
                registerButton.textContent = originalText;
            }
        });
    }
    
    // Logout
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
                auth.logout();
            }
        });
    }
    
    // Si estamos en una página protegida, cargar datos del usuario
    const protectedPages = ['/dashboard.html', '/admin.html'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.includes(currentPath) && auth.isAuthenticated()) {
        const userData = auth.getUserData();
        if (userData && Object.keys(userData).length > 0) {
            updateUserInterface(userData);
        }
        
        // Verificar acceso admin para páginas de administración
        if (currentPath === '/admin.html' && !auth.isAdmin()) {
            showNotification('Acceso denegado. Se requieren privilegios de administrador', 'error');
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 2000);
        }
    }
    
    // Si estamos en el dashboard, cargar datos adicionales
    if (window.location.pathname === '/dashboard.html') {
        // Cargar datos académicos
        loadAcademicInfo();
        
        // Cargar actividades y noticias
        loadActivities();
        loadNews();
        
        // Iniciar reloj
        startRealTimeClock();
    }
});

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
window.updateUserInterface = updateUserInterface;
window.requireAuth = requireAuth;
window.requireAdmin = requireAdmin;

