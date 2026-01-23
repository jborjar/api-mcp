"""
Interfaz web para gestión de sesiones y configuración del sistema.
Proporciona una página HTML con formulario de login y panel de ajustes.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/start", response_class=HTMLResponse, tags=["Sistema"])
async def start_page():
    """
    Página de inicio con formulario de autenticación y panel de ajustes.
    Permite autenticarse, ver información de sesión y cambiar configuraciones.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API MCP - Login</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                background: transparent;
                padding: 20px;
                width: 100%;
                max-width: 1400px;
            }
            .login-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                padding: 40px;
                max-width: 500px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
                text-align: center;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                text-align: center;
                font-size: 14px;
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                color: #555;
                margin-bottom: 8px;
                font-weight: 500;
                font-size: 14px;
            }
            input[type="text"],
            input[type="password"] {
                width: 100%;
                padding: 12px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            input[type="text"]:focus,
            input[type="password"]:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            button:active {
                transform: translateY(0);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .message {
                margin-top: 20px;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                display: none;
            }
            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .token-container {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
                display: none;
            }
            .token-label {
                font-size: 12px;
                color: #666;
                margin-bottom: 8px;
                font-weight: 600;
            }
            .token-value {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                word-break: break-all;
                background: white;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #dee2e6;
            }
            .copy-button {
                margin-top: 10px;
                padding: 8px 12px;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                width: auto;
            }
            .copy-button:hover {
                background: #5a6268;
            }
            .hidden {
                display: none !important;
            }
            .authenticated-view {
                display: none;
            }
            .user-info-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border: 2px solid #667eea;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .user-info-card h3 {
                font-size: 16px;
                color: #333;
                margin-bottom: 15px;
                font-weight: 700;
                text-align: center;
            }
            .info-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
            }
            .info-row:last-child {
                border-bottom: none;
            }
            .info-label {
                font-weight: 600;
                color: #555;
                font-size: 13px;
            }
            .info-value {
                color: #333;
                font-size: 13px;
                text-align: right;
            }
            .scope-badge {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
                margin: 2px;
            }
            .settings-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border: 2px solid #667eea;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .settings-card h3 {
                font-size: 16px;
                color: #333;
                margin-bottom: 15px;
                font-weight: 700;
                text-align: center;
            }
            .setting-item {
                margin-bottom: 15px;
            }
            .setting-item:last-child {
                margin-bottom: 0;
            }
            .setting-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 15px;
            }
            .setting-label {
                display: block;
                font-weight: 600;
                color: #555;
                font-size: 13px;
                margin-bottom: 8px;
            }
            .setting-input {
                width: 100%;
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            .setting-input:focus {
                outline: none;
                border-color: #667eea;
            }
            .setting-button {
                width: 100%;
                padding: 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 10px;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .setting-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .setting-button:active {
                transform: translateY(0);
            }
            .setting-button:disabled {
                background: #cccccc;
                cursor: not-allowed;
                transform: none;
            }
            .setting-button:disabled:hover {
                transform: none;
                box-shadow: none;
            }
            .setting-button-danger {
                background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
            }
            .setting-button-danger:hover {
                box-shadow: 0 5px 15px rgba(220, 53, 69, 0.4);
            }
            .setting-button-warning {
                background: linear-gradient(135deg, #ffc107 0%, #28a745 100%);
            }
            .setting-button-warning:hover {
                box-shadow: 0 5px 15px rgba(255, 193, 7, 0.4);
            }
            .status-message {
                margin-top: 15px;
                padding: 12px;
                border-radius: 6px;
                font-size: 13px;
                text-align: left;
                display: none;
                white-space: pre-line;
            }
            .status-message.running {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(133, 100, 4, 0.2);
                border-radius: 50%;
                border-top-color: #856404;
                animation: spin 0.8s linear infinite;
                flex-shrink: 0;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .status-message.running {
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
                display: block;
            }
            .status-message.completed {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                display: block;
            }
            .status-message.failed {
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
                display: block;
            }
            .modal-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 9999;
                justify-content: center;
                align-items: center;
            }
            .modal-overlay.show {
                display: flex;
            }
            .modal-content {
                background: white;
                border-radius: 10px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                animation: modalSlideIn 0.3s ease-out;
            }
            @keyframes modalSlideIn {
                from {
                    transform: translateY(-50px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            .modal-header {
                font-size: 18px;
                font-weight: 700;
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }
            .modal-body {
                font-size: 14px;
                color: #555;
                line-height: 1.6;
                margin-bottom: 20px;
            }
            .modal-params {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                margin: 15px 0;
                border-left: 4px solid #667eea;
            }
            .modal-param-item {
                margin: 8px 0;
                font-size: 14px;
            }
            .modal-param-label {
                font-weight: 600;
                color: #333;
            }
            .modal-warning {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 12px;
                border-radius: 6px;
                margin-top: 15px;
                font-size: 13px;
                font-weight: 600;
            }
            .modal-buttons {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            .modal-button {
                flex: 1;
                padding: 12px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .modal-button-confirm {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .modal-button-confirm:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .modal-button-cancel {
                background: #e0e0e0;
                color: #555;
            }
            .modal-button-cancel:hover {
                background: #d0d0d0;
            }
            .cards-container {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 20px;
                width: 100%;
            }
            .column-stack {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            .api-card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border: 2px solid #667eea;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .api-card h3 {
                font-size: 16px;
                color: #333;
                margin-bottom: 10px;
                font-weight: 700;
                text-align: center;
            }
            .session-status {
                text-align: center;
                color: #28a745;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 15px;
            }
            .api-card .logout-button {
                width: 100%;
                margin-top: 12px;
                padding: 10px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }
            .api-card .logout-button:hover {
                background: #c82333;
            }
            .token-info {
                background: #f8f9fa;
                border-radius: 6px;
                padding: 12px;
            }
            .token-info .token-label {
                font-size: 11px;
                color: #666;
                margin-bottom: 8px;
                font-weight: 600;
            }
            .token-info .token-value {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                word-break: break-all;
                background: white;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #dee2e6;
                margin-bottom: 8px;
            }
            .token-info .copy-button {
                width: 100%;
                margin-top: 5px;
            }
            @media (max-width: 1200px) {
                .cards-container {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Vista de login -->
            <div id="loginView">
                <div class="login-card">
                    <h1>API MCP</h1>
                    <p class="subtitle">Sistema de Gestión de Proveedores SAP</p>

                    <form id="loginForm" onsubmit="return false;">
                        <div class="form-group">
                            <label for="username">Usuario</label>
                            <input type="text" id="username" name="username" required autocomplete="username">
                        </div>

                        <div class="form-group">
                            <label for="password">Contraseña</label>
                            <input type="password" id="password" name="password" required autocomplete="current-password">
                        </div>

                        <button type="submit" id="submitBtn">Autentificar</button>
                    </form>

                    <div id="message" class="message"></div>
                </div>
            </div>

            <!-- Vista autenticada -->
            <div id="authenticatedView" class="authenticated-view">
                <!-- Contenedor de las 3 columnas en grid -->
                <div class="cards-container">
                    <!-- Columna 1: API MCP + INFORMACIÓN DEL USUARIO -->
                    <div class="column-stack">
                        <!-- Tarjeta API MCP -->
                        <div class="api-card">
                            <h3>API MCP</h3>
                            <div class="session-status">Sesión activa</div>
                            <div class="token-info">
                                <div class="token-label">Token de Sesión:</div>
                                <div class="token-value" id="tokenValue"></div>
                                <button class="copy-button" onclick="copyToken()">Copiar Token</button>
                            </div>
                            <button class="logout-button" onclick="logout()">Cerrar Sesión</button>
                        </div>

                        <!-- Tarjeta de información del usuario -->
                        <div class="user-info-card" id="userInfoCard">
                            <h3>INFORMACIÓN DEL USUARIO</h3>
                            <div class="info-row">
                                <span class="info-label">Usuario:</span>
                                <span class="info-value" id="infoUsername">-</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Creada:</span>
                                <span class="info-value" id="infoCreatedAt">-</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Expira:</span>
                                <span class="info-value" id="infoExpiresAt">-</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Scopes:</span>
                                <span class="info-value" id="infoScopes">-</span>
                            </div>
                        </div>
                    </div>

                    <!-- Columna 2: Tarjeta de ajustes -->
                    <div class="settings-card" id="settingsCard">
                        <h3>AJUSTES</h3>
                        <!-- Fila 1: Modo de Operación y Sesiones activas -->
                        <div class="setting-row">
                            <div class="setting-item">
                                <label class="setting-label">Modo de Operación</label>
                                <select class="setting-input" id="modeSelect">
                                    <option value="0">Productivo</option>
                                    <option value="1">Pruebas</option>
                                </select>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">Sesiones activas</label>
                                <select class="setting-input" id="sessionLimitSelect">
                                    <option value="1">1</option>
                                    <option value="2">2</option>
                                    <option value="5">5</option>
                                </select>
                            </div>
                        </div>
                        <!-- Fila 2: Proveedores activos y Enviar correo a -->
                        <div class="setting-row">
                            <div class="setting-item">
                                <label class="setting-label">Proveedores activos</label>
                                <select class="setting-input" id="yearSelect">
                                    <!-- Se llenará dinámicamente con JavaScript -->
                                </select>
                            </div>
                            <div class="setting-item">
                                <label class="setting-label">Enviar correo a</label>
                                <input type="email" class="setting-input" id="emailSupervisor" readonly>
                            </div>
                        </div>
                        <!-- Fila de botones 1 -->
                        <div class="setting-row">
                            <button class="setting-button setting-button-danger" id="btnIniciarBase" onclick="iniciarBaseAuxiliar()">Iniciar Base Auxiliar</button>
                            <button class="setting-button setting-button-warning" id="btnCambiarAjustes">Cambiar Ajustes</button>
                        </div>
                        <!-- Fila de botones 2 -->
                        <div class="setting-row">
                            <button class="setting-button setting-button-warning" id="btnActualizarProveedores">Actualizar Proveedores</button>
                            <button class="setting-button setting-button-warning" id="btnRespaldarUsuarios">Respaldar Usuarios</button>
                        </div>
                        <div class="status-message" id="statusMessage"></div>
                    </div>

                    <!-- Columna 3: Tarjeta de Auditoría -->
                    <div class="settings-card" id="auditoriaCard">
                        <h3>AUDITORÍA INFORMACIÓN DE PROVEEDORES</h3>
                        <div class="setting-item">
                            <label class="setting-label">Seleccionar proveedor</label>
                            <select class="setting-input" id="proveedorSelect">
                                <option value="">-- Seleccione un proveedor --</option>
                            </select>
                        </div>
                        <button class="setting-button" id="btnAuditoriaProveedor">Consultar Información</button>
                        <div class="status-message" id="auditoriaStatusMessage"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal de confirmación -->
        <div class="modal-overlay" id="confirmModal">
            <div class="modal-content">
                <div class="modal-header">Confirmar Inicialización</div>
                <div class="modal-body">
                    <p>¿Está seguro de iniciar la base auxiliar con los siguientes parámetros?</p>
                    <div class="modal-params">
                        <div class="modal-param-item">
                            <span class="modal-param-label">Modo:</span>
                            <span id="modalModo"></span>
                        </div>
                        <div class="modal-param-item">
                            <span class="modal-param-label">Años de actividad:</span>
                            <span id="modalAnos"></span>
                        </div>
                        <div class="modal-param-item">
                            <span class="modal-param-label">Correo:</span>
                            <span id="modalCorreo"></span>
                        </div>
                    </div>
                    <div class="modal-warning">
                        ⚠️ ADVERTENCIA: Si existe una base operativa en este momento, será eliminada y se creará una nueva.
                    </div>
                </div>
                <div class="modal-buttons">
                    <button class="modal-button modal-button-cancel" onclick="cerrarModalConfirmacion()">Cancelar</button>
                    <button class="modal-button modal-button-confirm" onclick="confirmarInicializacion()">Iniciar</button>
                </div>
            </div>
        </div>

        <script>
            const form = document.getElementById('loginForm');
            const messageDiv = document.getElementById('message');
            const tokenValue = document.getElementById('tokenValue');
            const submitBtn = document.getElementById('submitBtn');
            const loginView = document.getElementById('loginView');
            const authenticatedView = document.getElementById('authenticatedView');

            // Funciones para manejo de cookies
            function setCookie(name, value, hours) {
                const expires = new Date();
                expires.setTime(expires.getTime() + hours * 60 * 60 * 1000);
                document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
            }

            function getCookie(name) {
                const nameEQ = name + "=";
                const ca = document.cookie.split(';');
                for(let i = 0; i < ca.length; i++) {
                    let c = ca[i];
                    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
                    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
                }
                return null;
            }

            function deleteCookie(name) {
                document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/`;
            }

            // Verificar si ya existe una sesión al cargar la página
            async function checkExistingSession() {
                const token = getCookie('session_token');
                if (token) {
                    // Validar token contra el servidor
                    try {
                        const response = await fetch('/me', {
                            method: 'GET',
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });

                        if (response.ok) {
                            const userData = await response.json();

                            // Verificar si tiene el scope sql:adm
                            if (!userData.scopes || !userData.scopes.includes('sql:adm')) {
                                // No tiene el scope requerido
                                deleteCookie('session_token');
                                showLoginView();
                                messageDiv.className = 'message error';
                                messageDiv.textContent = 'Acceso denegado: Se requiere el scope sql:adm';
                                messageDiv.style.display = 'block';
                                return;
                            }

                            // Token válido y tiene el scope, mostrar vista autenticada
                            showAuthenticatedView(token, userData);
                        } else {
                            // Token inválido o expirado, eliminar cookie y mostrar login
                            deleteCookie('session_token');
                            showLoginView();
                        }
                    } catch (error) {
                        // Error de conexión, eliminar cookie y mostrar login
                        deleteCookie('session_token');
                        showLoginView();
                    }
                }
            }

            // Mostrar vista autenticada
            async function showAuthenticatedView(token, userData = null) {
                loginView.style.display = 'none';
                authenticatedView.style.display = 'block';
                tokenValue.textContent = token;

                // Si no se proporcionó userData, obtenerla del servidor
                if (!userData) {
                    try {
                        const response = await fetch('/me', {
                            method: 'GET',
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });
                        if (response.ok) {
                            userData = await response.json();
                        }
                    } catch (error) {
                        console.error('Error obteniendo información del usuario:', error);
                    }
                }

                // Actualizar tarjeta de información del usuario
                if (userData) {
                    document.getElementById('infoUsername').textContent = userData.username || '-';

                    // Formatear fechas
                    const createdAt = userData.created_at ? new Date(userData.created_at).toLocaleString('es-MX') : '-';
                    const expiresAt = userData.expires_at ? new Date(userData.expires_at).toLocaleString('es-MX') : '-';

                    document.getElementById('infoCreatedAt').textContent = createdAt;
                    document.getElementById('infoExpiresAt').textContent = expiresAt;

                    // Mostrar scopes como badges
                    const scopesContainer = document.getElementById('infoScopes');
                    if (userData.scopes && userData.scopes.length > 0) {
                        scopesContainer.innerHTML = userData.scopes.map(scope =>
                            `<span class="scope-badge">${scope}</span>`
                        ).join(' ');
                    } else {
                        scopesContainer.textContent = 'Sin scopes';
                    }
                }

                // Cargar modo actual
                loadCurrentMode();

                // Llenar combo de años
                populateYears();

                // Cargar configuración de email
                loadEmailConfig();

                // Cargar configuración de sesiones y años
                loadSesionesConfig();
            }

            // Mostrar vista de login
            function showLoginView() {
                loginView.style.display = 'block';
                authenticatedView.style.display = 'none';
                form.reset();
                messageDiv.style.display = 'none';
            }

            // Event listener para el formulario de login
            form.addEventListener('submit', async (e) => {
                e.preventDefault();

                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                // Deshabilitar botón y mostrar estado de carga
                submitBtn.disabled = true;
                submitBtn.textContent = 'Autenticando...';
                messageDiv.style.display = 'none';

                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ username, password })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        // Autenticación exitosa
                        const token = data.access_token;

                        // Validar que el usuario tenga el scope sql:adm
                        const meResponse = await fetch('/me', {
                            method: 'GET',
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });

                        if (meResponse.ok) {
                            const userData = await meResponse.json();

                            // Verificar si tiene el scope sql:adm
                            if (!userData.scopes || !userData.scopes.includes('sql:adm')) {
                                messageDiv.className = 'message error';
                                messageDiv.textContent = 'Acceso denegado: Se requiere el scope sql:adm';
                                messageDiv.style.display = 'block';
                                return;
                            }

                            // Guardar token en cookie (válida por 1 hora)
                            setCookie('session_token', token, 1);

                            // Mostrar vista autenticada
                            showAuthenticatedView(token, userData);
                        } else {
                            messageDiv.className = 'message error';
                            messageDiv.textContent = 'Error al validar permisos';
                            messageDiv.style.display = 'block';
                        }
                    } else {
                        // Error de autenticación
                        messageDiv.className = 'message error';
                        messageDiv.textContent = data.detail || 'Error de autenticación';
                        messageDiv.style.display = 'block';
                    }
                } catch (error) {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = 'Error de conexión con el servidor';
                    messageDiv.style.display = 'block';
                } finally {
                    // Rehabilitar botón
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Autentificar';
                }
            });

            // Función para copiar token
            function copyToken() {
                const token = tokenValue.textContent;
                navigator.clipboard.writeText(token).then(() => {
                    const copyBtn = event.target;
                    const originalText = copyBtn.textContent;
                    copyBtn.textContent = 'Copiado!';
                    setTimeout(() => {
                        copyBtn.textContent = originalText;
                    }, 2000);
                });
            }

            // Función para cerrar sesión
            async function logout() {
                const token = getCookie('session_token');

                if (token) {
                    try {
                        // Llamar al endpoint de logout
                        await fetch('/auth/logout', {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });
                    } catch (error) {
                        console.error('Error al cerrar sesión:', error);
                    }
                }

                // Eliminar cookie
                deleteCookie('session_token');

                // Mostrar vista de login
                showLoginView();
            }

            // Función para cargar el modo actual
            async function loadCurrentMode() {
                const token = getCookie('session_token');
                if (!token) return;

                try {
                    const response = await fetch('/pruebas', {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('modeSelect').value = data.modo_pruebas ? '1' : '0';
                    }
                } catch (error) {
                    console.error('Error cargando modo actual:', error);
                }
            }

            // Función para cargar configuración de email
            async function loadEmailConfig() {
                const token = getCookie('session_token');
                if (!token) return;

                try {
                    const response = await fetch('/config/email', {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('emailSupervisor').value = data.email_supervisor;
                    }
                } catch (error) {
                    console.error('Error cargando configuración de email:', error);
                }
            }

            // Función para cargar configuración de sesiones y años
            async function loadSesionesConfig() {
                const token = getCookie('session_token');
                if (!token) return;

                try {
                    const response = await fetch('/config/sesiones', {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('sessionLimitSelect').value = data.sesiones_activas;
                        document.getElementById('yearSelect').value = data.anos_activo;
                    }
                } catch (error) {
                    console.error('Error cargando configuración de sesiones:', error);
                }
            }

            // Variable global para almacenar el interval de polling
            let pollingInterval = null;

            // Función para habilitar/deshabilitar todos los botones de ajustes
            function setButtonsEnabled(enabled) {
                document.getElementById('btnIniciarBase').disabled = !enabled;
                document.getElementById('btnCambiarAjustes').disabled = !enabled;
                document.getElementById('btnActualizarProveedores').disabled = !enabled;
                document.getElementById('btnRespaldarUsuarios').disabled = !enabled;
            }

            // Función para obtener el historial de jobs
            async function obtenerHistorialJobs() {
                const token = getCookie('session_token');
                if (!token) return null;

                try {
                    const response = await fetch('/inicializa_datos/jobs', {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        return await response.json();
                    }
                } catch (error) {
                    console.error('Error obteniendo historial de jobs:', error);
                }
                return null;
            }

            // Función para monitorear el progreso de un job
            async function monitorearProgreso(jobId) {
                const statusMessage = document.getElementById('statusMessage');

                try {
                    const response = await fetch(`/inicializa_datos/status/${jobId}`, {
                        method: 'GET'
                    });

                    if (response.ok) {
                        const data = await response.json();

                        // Si el job terminó (completed o failed)
                        if (data.status === 'completed' || data.status === 'failed') {
                            // Detener polling
                            if (pollingInterval) {
                                clearInterval(pollingInterval);
                                pollingInterval = null;
                            }

                            // Actualizar clase del mensaje
                            statusMessage.className = 'status-message ' + data.status;
                            statusMessage.style.display = 'block';

                            // Habilitar botones
                            setButtonsEnabled(true);

                            // Mensaje final con historial de jobs
                            if (data.status === 'completed') {
                                const historial = await obtenerHistorialJobs();
                                let mensaje = '✓ Inicialización completada exitosamente';

                                if (historial && historial.total_jobs > 0) {
                                    mensaje += `\n\nHistorial de inicializaciones: ${historial.total_jobs} total`;

                                    // Mostrar últimos 3 jobs
                                    const ultimosJobs = historial.jobs.slice(0, 3);
                                    ultimosJobs.forEach((job, index) => {
                                        // Validar que created_at exista y sea válido
                                        if (job.created_at) {
                                            const fecha = new Date(job.created_at);
                                            // Validar que la fecha sea válida (después del año 2000)
                                            if (fecha.getFullYear() > 2000) {
                                                const fechaFormateada = fecha.toLocaleString('es-MX', {
                                                    year: 'numeric',
                                                    month: '2-digit',
                                                    day: '2-digit',
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                    second: '2-digit'
                                                });
                                                const estado = job.status === 'completed' ? '✓' : job.status === 'failed' ? '✗' : '⏳';
                                                mensaje += `\n${estado} ${fechaFormateada} - ${job.status}`;
                                            }
                                        }
                                    });
                                }

                                statusMessage.innerHTML = mensaje.replace(/\\n/g, '<br>');
                            } else {
                                statusMessage.textContent = '✗ Error: ' + (data.error || 'Error desconocido');
                            }
                        } else {
                            // Todavía está corriendo - mostrar spinner con mensaje de progreso
                            statusMessage.className = 'status-message running';
                            statusMessage.style.display = 'block';
                            statusMessage.innerHTML = '<span>Ejecutando proceso de inicialización<br>' + (data.progress || 'Procesando...') + '   </span><span class="spinner"></span>';
                        }
                    } else if (response.status === 404) {
                        // Job no encontrado - el servidor pudo haber reiniciado
                        // Detener polling
                        if (pollingInterval) {
                            clearInterval(pollingInterval);
                            pollingInterval = null;
                        }

                        // Re-habilitar botones
                        setButtonsEnabled(true);

                        // Mostrar mensaje indicando que el tracking se perdió pero la inicialización pudo completarse
                        statusMessage.className = 'status-message completed';
                        statusMessage.style.display = 'block';

                        const historial = await obtenerHistorialJobs();
                        let mensaje = '✓ Proceso de inicialización completado';

                        if (historial && historial.total_jobs > 0) {
                            mensaje += `\n\nHistorial de inicializaciones: ${historial.total_jobs} total`;

                            // Mostrar últimos 3 jobs
                            const ultimosJobs = historial.jobs.slice(0, 3);
                            ultimosJobs.forEach((job, index) => {
                                // Validar que created_at exista y sea válido
                                if (job.created_at) {
                                    const fecha = new Date(job.created_at);
                                    // Validar que la fecha sea válida (después del año 2000)
                                    if (fecha.getFullYear() > 2000) {
                                        const fechaFormateada = fecha.toLocaleString('es-MX', {
                                            year: 'numeric',
                                            month: '2-digit',
                                            day: '2-digit',
                                            hour: '2-digit',
                                            minute: '2-digit',
                                            second: '2-digit'
                                        });
                                        const estado = job.status === 'completed' ? '✓' : job.status === 'failed' ? '✗' : '⏳';
                                        mensaje += `\n${estado} ${fechaFormateada} - ${job.status}`;
                                    }
                                }
                            });
                        }

                        statusMessage.innerHTML = mensaje.replace(/\\n/g, '<br>');
                    }
                } catch (error) {
                    console.error('Error monitoreando progreso:', error);
                }
            }

            // Funciones para el modal de confirmación
            function abrirModalConfirmacion() {
                const modo = document.getElementById('modeSelect').value;
                const anos = document.getElementById('yearSelect').value;
                const emailSupervisor = document.getElementById('emailSupervisor').value;

                const modoTexto = modo === '1' ? 'Pruebas' : 'Productivo';

                // Llenar datos del modal
                document.getElementById('modalModo').textContent = modoTexto;
                document.getElementById('modalAnos').textContent = anos;
                document.getElementById('modalCorreo').textContent = emailSupervisor;

                // Mostrar modal
                document.getElementById('confirmModal').classList.add('show');
            }

            function cerrarModalConfirmacion() {
                document.getElementById('confirmModal').classList.remove('show');
            }

            // Función para iniciar base auxiliar (muestra el modal)
            function iniciarBaseAuxiliar() {
                const token = getCookie('session_token');
                if (!token) return;

                abrirModalConfirmacion();
            }

            // Función que ejecuta la inicialización después de confirmar
            async function confirmarInicializacion() {
                cerrarModalConfirmacion();

                const token = getCookie('session_token');
                if (!token) return;

                // Obtener valores de configuración
                const modo = document.getElementById('modeSelect').value;
                const anos = document.getElementById('yearSelect').value;
                const emailSupervisor = document.getElementById('emailSupervisor').value;

                const statusMessage = document.getElementById('statusMessage');

                try {
                    // Deshabilitar botones
                    setButtonsEnabled(false);

                    // Mostrar mensaje inicial con spinner
                    statusMessage.className = 'status-message running';
                    statusMessage.style.display = 'block';
                    statusMessage.innerHTML = '<span>Iniciando proceso...   </span><span class="spinner"></span>';

                    // Paso 1: Establecer modo de operación
                    statusMessage.innerHTML = '<span>Estableciendo modo de operación...   </span><span class="spinner"></span>';
                    const modoResponse = await fetch(`/pruebas/${modo}`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (!modoResponse.ok) {
                        statusMessage.className = 'status-message failed';
                        statusMessage.style.display = 'block';
                        statusMessage.textContent = '✗ Error al establecer el modo de operación';
                        setButtonsEnabled(true);
                        return;
                    }

                    // Paso 2: Ejecutar inicialización con parámetros
                    statusMessage.innerHTML = '<span>Ejecutando proceso de inicialización<br>Preparando...   </span><span class="spinner"></span>';
                    const sessionLimit = document.getElementById('sessionLimitSelect').value;
                    const initResponse = await fetch(`/inicializa_datos?anos=${anos}&email=${encodeURIComponent(emailSupervisor)}&modo=${modo}&s_activas=${sessionLimit}`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (initResponse.ok) {
                        const data = await initResponse.json();

                        // Hacer polling cada 2 segundos
                        pollingInterval = setInterval(() => {
                            monitorearProgreso(data.job_id);
                        }, 2000);

                        // Primera consulta inmediata
                        monitorearProgreso(data.job_id);
                    } else {
                        const errorData = await initResponse.json();
                        statusMessage.className = 'status-message failed';
                        statusMessage.style.display = 'block';
                        statusMessage.textContent = '✗ Error: ' + (errorData.detail || 'Error desconocido');
                        setButtonsEnabled(true);
                    }
                } catch (error) {
                    console.error('Error iniciando base auxiliar:', error);
                    statusMessage.className = 'status-message failed';
                    statusMessage.style.display = 'block';
                    statusMessage.textContent = '✗ Error de conexión al iniciar la base auxiliar';
                    setButtonsEnabled(true);
                }
            }

            // Función para llenar el combo de años dinámicamente
            function populateYears() {
                const yearSelect = document.getElementById('yearSelect');
                const currentYear = new Date().getFullYear();

                // Limpiar opciones existentes
                yearSelect.innerHTML = '';

                // Agregar opciones de 0 a 9 años hacia atrás
                for (let i = 0; i < 10; i++) {
                    const option = document.createElement('option');
                    option.value = i;
                    if (i === 0) {
                        option.textContent = `Solo ${currentYear}`;
                    } else {
                        const startYear = currentYear - i;
                        option.textContent = `${startYear} - ${currentYear} (${i + 1} años)`;
                    }
                    yearSelect.appendChild(option);
                }
            }

            // Verificar sesión existente al cargar la página
            checkExistingSession();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
