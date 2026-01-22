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
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                padding: 40px;
                width: 100%;
                max-width: 900px;
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
            .logout-button {
                margin-top: 20px;
                padding: 10px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                cursor: pointer;
                width: 100%;
            }
            .logout-button:hover {
                background: #c82333;
            }
            .welcome-message {
                text-align: center;
                color: #28a745;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 20px;
            }
            .user-info-card {
                background: #f8f9fa;
                border-radius: 6px;
                padding: 15px;
                border-left: 4px solid #667eea;
            }
            .user-info-card h3 {
                font-size: 14px;
                color: #333;
                margin-bottom: 15px;
                font-weight: 600;
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
                background: #fff3cd;
                border-radius: 6px;
                padding: 15px;
                border-left: 4px solid #ffc107;
            }
            .settings-card h3 {
                font-size: 14px;
                color: #856404;
                margin-bottom: 15px;
                font-weight: 600;
            }
            .setting-item {
                margin-bottom: 15px;
            }
            .setting-item:last-child {
                margin-bottom: 0;
            }
            .setting-label {
                display: block;
                font-weight: 600;
                color: #856404;
                font-size: 12px;
                margin-bottom: 5px;
            }
            .setting-input {
                width: 100%;
                padding: 8px;
                border: 1px solid #ffc107;
                border-radius: 4px;
                font-size: 13px;
            }
            .setting-button {
                padding: 8px 15px;
                background: #ffc107;
                color: #856404;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 5px;
            }
            .setting-button:hover {
                background: #e0a800;
            }
            .cards-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 25px;
                margin-bottom: 20px;
            }
            @media (max-width: 992px) {
                .container {
                    max-width: 600px;
                }
                .cards-container {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>API MCP</h1>
            <p class="subtitle">Sistema de Gestión de Proveedores SAP</p>

            <!-- Vista de login -->
            <div id="loginView">
                <form id="loginForm">
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

            <!-- Vista autenticada -->
            <div id="authenticatedView" class="authenticated-view">
                <div class="welcome-message">Sesión activa</div>

                <!-- Contenedor de tarjetas en grid -->
                <div class="cards-container">
                    <!-- Tarjeta de información del usuario -->
                    <div class="user-info-card" id="userInfoCard">
                        <h3>Información del Usuario</h3>
                        <div class="info-row">
                            <span class="info-label">Usuario:</span>
                            <span class="info-value" id="infoUsername">-</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Session ID:</span>
                            <span class="info-value" id="infoSessionId">-</span>
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

                    <!-- Tarjeta de ajustes -->
                    <div class="settings-card" id="settingsCard">
                        <h3>AJUSTES</h3>
                        <div class="setting-item">
                            <label class="setting-label">Modo de Operación</label>
                            <select class="setting-input" id="modeSelect">
                                <option value="0">Productivo</option>
                                <option value="1">Pruebas</option>
                            </select>
                            <button class="setting-button" onclick="changeMode()">Cambiar Modo</button>
                        </div>
                    </div>
                </div>

                <div class="token-container" style="display: block;">
                    <div class="token-label">Token de Sesión:</div>
                    <div class="token-value" id="tokenValue"></div>
                    <button class="copy-button" onclick="copyToken()">Copiar Token</button>
                </div>

                <button class="logout-button" onclick="logout()">Cerrar Sesión</button>
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
                            // Token válido, mostrar vista autenticada
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
                    document.getElementById('infoSessionId').textContent = userData.session_id || '-';

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

                        // Guardar token en cookie (válida por 1 hora)
                        setCookie('session_token', token, 1);

                        // Mostrar vista autenticada
                        showAuthenticatedView(token);
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

            // Función para cambiar el modo
            async function changeMode() {
                const token = getCookie('session_token');
                if (!token) return;

                const newMode = document.getElementById('modeSelect').value;

                try {
                    const response = await fetch(`/pruebas/${newMode}`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        alert(`Modo cambiado a: ${data.modo_pruebas ? 'Pruebas' : 'Productivo'}`);
                    } else {
                        alert('Error al cambiar el modo');
                    }
                } catch (error) {
                    console.error('Error cambiando modo:', error);
                    alert('Error de conexión al cambiar el modo');
                }
            }

            // Verificar sesión existente al cargar la página
            checkExistingSession();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
