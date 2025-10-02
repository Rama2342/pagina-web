@echo off
title Iniciando Servidor Flask con SSH (Puerto 22)
echo ================================================
echo Iniciando servidor Flask con soporte SSH remoto
echo ================================================
echo.

REM Verificar si se ejecuta como Administrador (necesario para firewall y servicios)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Ejecutando como Administrador.
) else (
    echo [ERROR] Este script debe ejecutarse como Administrador.
    echo Haz clic derecho en el archivo y selecciona "Ejecutar como administrador".
    pause
    exit /b 1
)

REM Paso 1: Verificar e instalar OpenSSH Server si no existe
echo [INFO] Verificando OpenSSH Server...
sc query sshd >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] OpenSSH Server no encontrado. Instalando...
    powershell -Command "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"
    if %errorLevel% neq 0 (
        echo [ERROR] Fallo al instalar OpenSSH. Ejecuta manualmente en PowerShell como Admin:
        echo Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
        pause
        exit /b 1
    )
    echo [OK] OpenSSH Server instalado.
)

REM Paso 2: Configurar el servicio SSH para inicio automático
echo [INFO] Configurando servicio SSH para inicio automatico...
powershell -Command "Set-Service -Name sshd -StartupType Automatic"
sc config sshd start= auto >nul 2>&1

REM Paso 3: Iniciar el servicio SSH si no esta corriendo
echo [INFO] Iniciando servicio SSH (puerto 22)...
sc query sshd | findstr /i "RUNNING" >nul 2>&1
if %errorLevel% neq 0 (
    net start sshd
    if %errorLevel% neq 0 (
        echo [ERROR] Fallo al iniciar SSH. Verifica la configuracion.
        echo Intenta manualmente: net start sshd
        pause
        exit /b 1
    )
    echo [OK] Servicio SSH iniciado.
) else (
    echo [OK] Servicio SSH ya esta corriendo.
)

REM Paso 4: Abrir puerto 22 en el Firewall de Windows (si no esta abierto)
echo [INFO] Configurando Firewall para puerto 22 (SSH)...
netsh advfirewall firewall add rule name="SSH Server (puerto 22)" dir=in action=allow protocol=TCP localport=22 >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Regla de firewall ya existe o error menor.
) else (
    echo [OK] Puerto 22 abierto en el Firewall.
)

REM Paso 5: Obtener IP local para acceso remoto
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    set IP=%IP: =%
)
echo [INFO] Tu IP local para SSH: %IP% (puerto 22)
echo [INFO] Para conectar remotamente: ssh tu_usuario@%IP% -p 22
echo.

REM Paso 6: Iniciar el servidor Flask
echo [INFO] Iniciando servidor Flask en puerto 5000...
echo Presiona Ctrl+C para detener.
cd /d "%~dp0"
python main.py

REM Si el servidor se detiene, opcionalmente detener SSH (comentado por defecto)
REM net stop sshd
echo.
echo ================================================
echo Servidor detenido. SSH sigue activo (puerto 22).
echo Para detener SSH manualmente: net stop sshd
echo ================================================
pause