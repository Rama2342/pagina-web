// Script de inicialización global
document.addEventListener('DOMContentLoaded', function() {
    console.log('Aplicación inicializada');
    
    // Verificar acceso a la página actual
    if (typeof auth !== 'undefined') {
        auth.checkPageAccess(window.location.pathname);
    }
    
    // Configurar comportamiento global del logout
    const logoutButtons = document.querySelectorAll('[id*="logout"], [class*="logout"]');
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
                auth.logout();
            }
        });
    });
    
    // Mostrar información del usuario si está autenticado
    if (typeof auth !== 'undefined' && auth.isAuthenticated()) {
        const userData = auth.getUserData();
        if (userData) {
            console.log('Usuario autenticado:', userData.username);
            
            // Actualizar elementos de UI comunes
            const userElements = document.querySelectorAll('[id*="user"], [class*="user"]');
            userElements.forEach(element => {
                if (element.id === 'userName' && userData.nombre) {
                    element.textContent = userData.nombre;
                } else if (element.id === 'userEmail') {
                    element.textContent = userData.email;
                }
            });
        }
    }
});
