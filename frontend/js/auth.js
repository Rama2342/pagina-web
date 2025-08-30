class Auth {
    constructor() {
        this.token = localStorage.getItem('token');
        this.user = JSON.parse(localStorage.getItem('user') || '{}');
        this.apiBase = 'http://localhost:5000/api';
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.token = data.token;
                this.user = { id: data.user_id, username: username };
                
                localStorage.setItem('token', this.token);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                return { success: true, data: data };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Error de conexión con el servidor' };
        }
    }

    async register(username, email, password) {
        try {
            const response = await fetch(`${this.apiBase}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();
            
            if (response.status === 201) {
                return { success: true, message: data.message };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Error de conexión con el servidor' };
        }
    }

    logout() {
        this.token = null;
        this.user = {};
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }

    isAuthenticated() {
        return this.token !== null;
    }

    getAuthHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }

    async fetchProtectedData() {
        if (!this.isAuthenticated()) {
            return null;
        }

        try {
            const response = await fetch(`${this.apiBase}/dashboard`, {
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                return await response.json();
            } else if (response.status === 401) {
                this.logout();
                return null;
            } else {
                return null;
            }
        } catch (error) {
            console.error('Error fetching protected data:', error);
            return null;
        }
    }
}

// Instancia global de autenticación
const auth = new Auth();

// Función para verificar autenticación en páginas protegidas
function checkAuth() {
    const protectedPages = ['/dashboard'];
    const currentPath = window.location.pathname;
    
    if (protectedPages.includes(currentPath) && !auth.isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    
    return true;
}

// Manejo de formularios
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación primero
    if (!checkAuth()) return;
    
    // Formulario de login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const loginButton = document.getElementById('loginButton');
            loginButton.disabled = true;
            loginButton.textContent = 'Iniciando sesión...';
            
            const result = await auth.login(username, password);
            
            if (result.success) {
                window.location.href = '/dashboard';
            } else {
                alert('Error: ' + result.error);
                loginButton.disabled = false;
                loginButton.textContent = 'Iniciar Sesión';
            }
        });
    }
    
    // Formulario de registro
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (password !== confirmPassword) {
                alert('Las contraseñas no coinciden');
                return;
            }
            
            const registerButton = document.getElementById('registerButton');
            registerButton.disabled = true;
            registerButton.textContent = 'Creando cuenta...';
            
            const result = await auth.register(username, email, password);
            
            if (result.success) {
                alert('Cuenta creada exitosamente. Ahora puedes iniciar sesión.');
                window.location.href = '/login';
            } else {
                alert('Error: ' + result.error);
                registerButton.disabled = false;
                registerButton.textContent = 'Registrarse';
            }
        });
    }
    
    // Cargar datos del dashboard si estamos en esa página
    if (window.location.pathname === '/dashboard') {
        auth.fetchProtectedData().then(data => {
            if (data) {
                if (document.getElementById('welcomeMessage')) {
                    document.getElementById('welcomeMessage').textContent = data.message;
                }
                if (document.getElementById('userEmail')) {
                    document.getElementById('userEmail').textContent = data.email;
                }
                if (document.getElementById('userName')) {
                    document.getElementById('userName').textContent = data.user;
                }
            }
        }).catch(error => {
            console.error('Error loading dashboard data:', error);
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
});