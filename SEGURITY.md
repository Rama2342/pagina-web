# 🔐 GUÍA DE SEGURIDAD - Sistema Escolar San Isidro

Esta guía contiene todas las medidas de seguridad implementadas en el sistema y cómo configurarlas correctamente.

## 📋 Índice

1. [Configuración Inicial](#configuración-inicial)
2. [Variables de Entorno](#variables-de-entorno)
3. [Medidas de Seguridad Implementadas](#medidas-de-seguridad-implementadas)
4. [Instalación Segura](#instalación-segura)
5. [Configuración de Producción](#configuración-de-producción)
6. [Monitoreo de Seguridad](#monitoreo-de-seguridad)
7. [Mejores Prácticas](#mejores-prácticas)

## 🚀 Configuración Inicial

### Paso 1: Generar Claves Secretas

```bash
# Ejecutar el generador de claves
python3 generate_secrets.py

# O generar manualmente
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"
```

### Paso 2: Configurar Variables de Entorno

Copia el archivo `.env` y configura según tu entorno:

```bash
# Para desarrollo
FLASK_ENV=development
FLASK_DEBUG=False
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5500

# Para producción
FLASK_ENV=production
FLASK_DEBUG=False
ALLOWED_ORIGINS=https://tudominio.com
```

### Paso 3: Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

## 🔑 Variables de Entorno

### Variables Críticas de Seguridad

| Variable | Descripción | Ejemplo | Requerida |
|----------|-------------|---------|-----------|
| `SECRET_KEY` | Clave para sesiones Flask | `abc123...` | ✅ |
| `JWT_SECRET_KEY` | Clave para tokens JWT | `xyz789...` | ✅ |
| `ALLOWED_ORIGINS` | Dominios permitidos CORS | `https://mi-app.com` | ✅ |
| `FLASK_ENV` | Entorno de ejecución | `production` | ✅ |

### Variables de Rate Limiting

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `RATE_LIMIT_PER_DAY` | Límite por día | 1000 |
| `RATE_LIMIT_PER_HOUR` | Límite por hora | 100 |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | Límite login | 5 |

## 🛡️ Medidas de Seguridad Implementadas

### 1. Headers de Seguridad

```http
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; ...
```

### 2. Validación de Datos

- **Sanitización HTML**: Previene inyección XSS
- **Validación de schemas**: Usando Marshmallow
- **Patrones regex**: Para formatos específicos
- **Detección de inyección SQL**: Patrones maliciosos

### 3. Autenticación y Autorización

- **JWT tokens**: Con expiración configurable
- **Rate limiting**: Por IP y por usuario
- **Blacklist de tokens**: Revocación segura
- **Contraseñas fuertes**: Validación obligatoria

### 4. Protección CORS

- **Orígenes específicos**: No wildcards en producción
- **Headers controlados**: Solo los necesarios
- **Credenciales seguras**: Configuración restrictiva

### 5. Detección de Amenazas

- **IPs sospechosas**: Bloqueo automático
- **Intentos de login**: Límites estrictos
- **Logging de seguridad**: Eventos registrados

## ⚙️ Instalación Segura

### Desarrollo

```bash
# 1. Clonar repositorio
git clone <tu-repo>
cd pagina-web-main

# 2. Generar claves secretas
python3 generate_secrets.py

# 3. Configurar entorno de desarrollo
echo "FLASK_ENV=development" >> .env
echo "FLASK_DEBUG=False" >> .env

# 4. Instalar dependencias
cd backend
pip install -r requirements.txt

# 5. Inicializar base de datos
python3 init_database.py

# 6. Ejecutar servidor
python3 main.py
```

### Producción

```bash
# 1. Configurar variables de producción
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY="tu-clave-super-secreta-produccion"
export JWT_SECRET_KEY="tu-jwt-clave-super-secreta-produccion"
export ALLOWED_ORIGINS="https://tudominio.com"

# 2. Usar servidor de producción
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 main:app

# 3. Configurar proxy reverso (Nginx)
# Ver configuración de Nginx más abajo
```

## 🔧 Configuración de Producción

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name tudominio.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        root /path/to/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

### Systemd Service

```ini
[Unit]
Description=Sistema Escolar API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/app/backend
Environment=PATH=/path/to/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=/path/to/app/.env
ExecStart=/path/to/venv/bin/waitress-serve --host=127.0.0.1 --port=5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📊 Monitoreo de Seguridad

### Logs de Seguridad

```bash
# Ver intentos de login fallidos
grep "LOGIN_FAILED" logs/app.log

# Ver IPs bloqueadas
grep "BLOCKED_IP" logs/app.log

# Ver intentos de inyección
grep "INJECTION_ATTEMPT" logs/app.log
```

### Métricas a Monitorear

1. **Intentos de login fallidos por IP**
2. **Requests con rate limit excedido**
3. **Intentos de acceso a endpoints admin sin permisos**
4. **Patrones de inyección SQL/XSS detectados**
5. **Uso de tokens expirados o revocados**

## ✅ Mejores Prácticas

### Para Desarrolladores

1. **Nunca hardcodear secretos** en el código
2. **Validar siempre** los inputs del usuario
3. **Usar HTTPS** en producción
4. **Mantener dependencias actualizadas**
5. **Revisar logs** regularmente

### Para Administradores

1. **Cambiar claves por defecto** inmediatamente
2. **Configurar backups** automáticos de la base de datos
3. **Monitorear recursos** del servidor
4. **Actualizar sistema operativo** regularmente
5. **Implementar firewall** apropiado

### Para Producción

1. **Usar variables de entorno** para configuración
2. **Configurar SSL/TLS** correctamente
3. **Implementar rate limiting** a nivel de infraestructura
4. **Configurar logging** centralizado
5. **Realizar auditorías** de seguridad regulares

## 🚨 Checklist de Seguridad

### Antes de Desplegar

- [ ] Claves secretas generadas y configuradas
- [ ] Variables de entorno de producción configuradas
- [ ] CORS configurado para dominios específicos
- [ ] HTTPS habilitado con certificado válido
- [ ] Rate limiting configurado apropiadamente
- [ ] Logging de seguridad habilitado
- [ ] Base de datos con acceso restringido
- [ ] Firewall configurado
- [ ] Backup strategy implementada

### Mantenimiento Regular

- [ ] Revisar logs de seguridad semanalmente
- [ ] Actualizar dependencias mensualmente
- [ ] Rotar claves secretas trimestralmente
- [ ] Auditoría de seguridad semestral
- [ ] Backup testing trimestral

## 🆘 En Caso de Incidente de Seguridad

1. **Bloquear acceso** inmediatamente si es necesario
2. **Rotar todas las claves** secretas
3. **Revisar logs** para determinar el alcance
4. **Notificar usuarios** si hay compromiso de datos
5. **Implementar medidas adicionales** según sea necesario

## 📞 Contacto

Para reportar vulnerabilidades de seguridad o consultas:
- Email: [eternauta.cronica@gmail.com]
- Crear issue en GitHub (para vulnerabilidades públicas)

---