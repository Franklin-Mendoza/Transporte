/* ============================================================
   common.js — Utilidades compartidas del panel SIG Transporte
   Manejo de sesión JWT, fetch autenticado, toasts, helpers
   ============================================================ */

const API_BASE = "/api";

// ───────── Sesión ─────────

function guardarSesion(accessToken, refreshToken, usuario) {
  localStorage.setItem("sig_access_token", accessToken);
  localStorage.setItem("sig_refresh_token", refreshToken);
  localStorage.setItem("sig_usuario", JSON.stringify(usuario));
}

function obtenerUsuario() {
  const data = localStorage.getItem("sig_usuario");
  return data ? JSON.parse(data) : null;
}

function obtenerToken() {
  return localStorage.getItem("sig_access_token");
}

function cerrarSesion() {
  // Avisar al servidor para desactivar el token FCM si existiera
  localStorage.removeItem("sig_access_token");
  localStorage.removeItem("sig_refresh_token");
  localStorage.removeItem("sig_usuario");
  window.location.href = "/login";
}

function protegerPagina(rolesPermitidos = []) {
  const token = obtenerToken();
  const usuario = obtenerUsuario();
  if (!token || !usuario) {
    window.location.href = "/login";
    return null;
  }
  if (rolesPermitidos.length && !rolesPermitidos.includes(usuario.rol)) {
    window.location.href = "/login";
    return null;
  }
  return usuario;
}

// ───────── Fetch autenticado con renovación automática ─────────

async function apiFetch(endpoint, options = {}) {
  const token = obtenerToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let resp = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  // Si el token venció, intentar renovar con refresh_token
  if (resp.status === 401) {
    const renovado = await intentarRenovarToken();
    if (renovado) {
      headers["Authorization"] = `Bearer ${obtenerToken()}`;
      resp = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } else {
      cerrarSesion();
      return null;
    }
  }

  return resp;
}

async function intentarRenovarToken() {
  const refreshToken = localStorage.getItem("sig_refresh_token");
  if (!refreshToken) return false;

  try {
    const resp = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${refreshToken}`,
      },
    });
    if (!resp.ok) return false;
    const data = await resp.json();
    localStorage.setItem("sig_access_token", data.data.access_token);
    return true;
  } catch {
    return false;
  }
}

// ───────── Toasts ─────────

function mostrarToast(mensaje, tipo = "ok") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${tipo}`;
  toast.textContent = mensaje;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ───────── Helpers de formato ─────────

function formatearFecha(isoString) {
  if (!isoString) return "—";
  // El backend manda fechas en UTC sin 'Z' explícito (datetime.utcnow() de
  // Python). Se fuerza la interpretación como UTC y se muestra en hora de
  // Bolivia (America/La_Paz), sin importar la zona horaria del navegador.
  const conZ = isoString.endsWith("Z") ? isoString : isoString + "Z";
  const d = new Date(conZ);
  return d.toLocaleString("es-BO", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
    timeZone: "America/La_Paz",
  });
}

function formatearFechaCorta(isoString) {
  if (!isoString) return "—";
  const conZ = isoString.endsWith("Z") ? isoString : isoString + "Z";
  const d = new Date(conZ);
  return d.toLocaleDateString("es-BO", {
    day: "2-digit", month: "2-digit", year: "numeric",
    timeZone: "America/La_Paz",
  });
}

function badgeEstado(estado) {
  const etiquetas = {
    pendiente: "Pendiente",
    justificada: "Justificada",
    aceptada: "Aceptada",
    rechazada: "Rechazada",
    sin_respuesta: "Sin respuesta",
    excelente: "Excelente",
    bueno: "Bueno",
    regular: "Regular",
    deficiente: "Deficiente",
  };
  const texto = etiquetas[estado] || estado;
  return `<span class="badge-estado badge-${estado}">${texto}</span>`;
}

function iniciarReloj(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const actualizar = () => {
    el.textContent = new Date().toLocaleTimeString("es-BO");
  };
  actualizar();
  setInterval(actualizar, 1000);
}

// ───────── Sidebar activo según ruta actual ─────────

function marcarNavActivo() {
  const path = window.location.pathname;
  document.querySelectorAll(".sidebar-nav a").forEach(link => {
    if (link.getAttribute("href") === path) {
      link.classList.add("active");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  marcarNavActivo();
  const btnLogout = document.getElementById("btn-logout");
  if (btnLogout) {
    btnLogout.addEventListener("click", cerrarSesion);
  }
  const usuario = obtenerUsuario();
  const nombreEl = document.getElementById("nombre-usuario-sesion");
  const rolEl = document.getElementById("rol-usuario-sesion");
  if (usuario) {
    if (nombreEl) nombreEl.textContent = usuario.nombre_completo || usuario.nombre;
    if (rolEl) rolEl.textContent = usuario.rol.charAt(0).toUpperCase() + usuario.rol.slice(1);

    // Ocultar opciones exclusivas de admin si el usuario es autoridad
    if (usuario.rol !== "admin") {
      document.querySelectorAll(".solo-admin").forEach(el => el.style.display = "none");
    }
  }
});
