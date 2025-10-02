// Funcionalidades para el panel de administración
document.addEventListener('DOMContentLoaded', function() {
    // Verificar autenticación y permisos de admin
    if (!auth.isAuthenticated()) {
        window.location.href = '/login.html';
        return;
    }
    
    if (!auth.isAdmin()) {
        showNotification('Acceso denegado. Se requieren privilegios de administrador', 'error');
        setTimeout(() => {
            window.location.href = '/dashboard.html';
        }, 2000);
        return;
    }
    
    // Configurar el formulario de subida
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('excelFile');
            const file = fileInput.files[0];
            
            if (!file) {
                showNotification('Por favor selecciona un archivo', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            const submitButton = uploadForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            
            try {
                const response = await fetch(`${auth.apiBase}/admin/upload-students`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${auth.token}`
                    },
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(`Archivo procesado: ${data.success_count} exitosos, ${data.error_count} errores`, 'success');
                    
                    // Mostrar resultados detallados
                    const resultDiv = document.getElementById('uploadResult');
                    resultDiv.innerHTML = `
                        <div class="result-summary">
                            <h4>Resultado del procesamiento:</h4>
                            <p><strong>Éxitos:</strong> ${data.success_count}</p>
                            <p><strong>Errores:</strong> ${data.error_count}</p>
                        </div>
                    `;
                    
                    if (data.errors && data.errors.length > 0) {
                        const errorsList = data.errors.map(error => `<li>${error}</li>`).join('');
                        resultDiv.innerHTML += `
                            <div class="result-errors">
                                <h5>Errores detallados:</h5>
                                <ul>${errorsList}</ul>
                            </div>
                        `;
                    }
                    
                    // Recargar la lista de estudiantes
                    loadStudents();
                } else {
                    showNotification('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showNotification('Error de conexión: ' + error.message, 'error');
            } finally {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        });
    }
    
    // Cargar lista de estudiantes
    loadStudents();
    
    // Configurar búsqueda
    const searchInput = document.getElementById('searchStudents');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadStudents(1, this.value);
            }, 500);
        });
    }
    
    // Configurar paginación
    document.getElementById('prevPage').addEventListener('click', function() {
        const currentPage = parseInt(this.getAttribute('data-current') || 1);
        if (currentPage > 1) {
            loadStudents(currentPage - 1);
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', function() {
        const currentPage = parseInt(this.getAttribute('data-current') || 1);
        const totalPages = parseInt(this.getAttribute('data-total') || 1);
        if (currentPage < totalPages) {
            loadStudents(currentPage + 1);
        }
    });
    
    // Configurar logout
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
                auth.logout();
            }
        });
    }
    
    const API_URL = 'http://localhost:5000';

    document.getElementById('publish-text-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const text = document.getElementById('admin-text').value;
        const res = await fetch(`${API_URL}/api/publish-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        document.getElementById('publish-result').textContent = data.message;
    });
});

// Ejemplo para admin.js y dashboard.js
const API_URL = 'http://localhost:5000';

fetch(`${API_URL}/api/publish-text`, {});
fetch(`${API_URL}/api/student-messages`);

// Función para cargar estudiantes
async function loadStudents(page = 1, search = '') {
    try {
        const studentsList = document.getElementById('studentsList');
        studentsList.innerHTML = '<p>Cargando estudiantes...</p>';
        
        const response = await fetch(`${auth.apiBase}/admin/students?page=${page}&per_page=10&search=${encodeURIComponent(search)}`, {
            headers: auth.getAuthHeaders()
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.students.length === 0) {
                studentsList.innerHTML = '<p>No se encontraron estudiantes.</p>';
            } else {
                studentsList.innerHTML = '';
                data.students.forEach(student => {
                    const studentElement = document.createElement('div');
                    studentElement.className = 'student-item';
                    studentElement.innerHTML = `
                        <div class="student-info">
                            <h4>${student.nombre} ${student.apellido}</h4>
                            <p><strong>Usuario:</strong> ${student.username} | <strong>Matrícula:</strong> ${student.matricula}</p>
                            <p><strong>Grado:</strong> ${student.grado} ${student.seccion} | <strong>Turno:</strong> ${student.turno}</p>
                            <p><strong>Estado:</strong> ${student.estado}</p>
                        </div>
                    `;
                    studentsList.appendChild(studentElement);
                });
            }
            
            // Actualizar paginación
            updatePagination(data, page, search);
        } else {
            studentsList.innerHTML = '<p>Error al cargar estudiantes.</p>';
        }
    } catch (error) {
        document.getElementById('studentsList').innerHTML = '<p>Error de conexión al cargar estudiantes.</p>';
    }
}

// Función para actualizar la paginación
function updatePagination(data, currentPage, search) {
    const prevButton = document.getElementById('prevPage');
    const nextButton = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    prevButton.setAttribute('data-current', currentPage);
    nextButton.setAttribute('data-current', currentPage);
    prevButton.setAttribute('data-total', data.pages);
    nextButton.setAttribute('data-total', data.pages);
    
    pageInfo.textContent = `Página ${currentPage} de ${data.pages}`;
    
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === data.pages;
    
    // Actualizar event listeners con los parámetros correctos
    prevButton.onclick = () => loadStudents(currentPage - 1, search);
    nextButton.onclick = () => loadStudents(currentPage + 1, search);
}
