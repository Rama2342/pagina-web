// Script de inicialización específico para el dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard inicializado');
    
    // Verificar autenticación
    if (typeof auth === 'undefined' || !auth.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }
    
    // Cargar datos del usuario
    const userData = auth.getUserData();
    if (userData && Object.keys(userData).length > 0) {
        console.log('Datos del usuario encontrados:', userData);
        updateUserInterface(userData);
    } else {
        console.log('No hay datos de usuario, intentando cargar desde API...');
        
        // Intentar cargar desde el API
        fetch(`${auth.apiBase}/user/full-profile`, {
            headers: auth.getAuthHeaders()
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateUserInterface(data.user);
                localStorage.setItem('userData', JSON.stringify(data.user));
            }
        })
        .catch(error => {
            console.error('Error cargando datos del usuario:', error);
            showNotification('Error al cargar información del usuario', 'error');
        });
    }
    
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
});
