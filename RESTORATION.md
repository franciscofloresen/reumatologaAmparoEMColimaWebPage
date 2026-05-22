# Sistema de Reservas Restaurado

## ✅ Cambios Realizados

### 1. Sistema de Reservas Recreado
- **Archivo**: `frontend/reservations.html`
- **Características**:
  - Formulario completo de reserva de citas
  - Validación de datos en tiempo real
  - Fecha mínima: hoy (no permite fechas pasadas)
  - Horario: 9:00 AM - 6:00 PM
  - Tipos de consulta: Primera vez, Seguimiento, Urgente
  - Mensajes de éxito/error
  - Diseño responsivo

### 2. Backend Actualizado
- **Archivo**: `backend/server.js`
- Restaurada ruta `/api/appointments`
- Restaurada ruta `/reservations`
- Ruta de appointments funcional con validación Joi

### 3. Frontend Actualizado
- **Archivo**: `frontend/index.html`
- Todos los botones "Reservar Cita" apuntan a `reservations.html`
- Sección de contacto con 2 opciones:
  1. Sistema de Reservas (interno)
  2. WhatsApp
- Chatbot actualizado con referencias al sistema de reservas

## 🎯 Funcionalidades del Sistema

### Formulario de Reservas
- ✅ Nombre y Apellido (requeridos)
- ✅ Teléfono (requerido, validado)
- ✅ Email (opcional)
- ✅ Fecha preferida (requerida, desde hoy en adelante)
- ✅ Hora preferida (requerida, 9:00-18:00)
- ✅ Tipo de consulta (requerido)
- ✅ Motivo de consulta (opcional)

### Validaciones Backend
- Joi schema validation
- Formato de teléfono
- Formato de email
- Fecha mínima (hoy)
- Hora en formato 24h
- Longitud de campos

### Almacenamiento
- Las citas se guardan en `backend/appointments.json`
- Cada cita tiene ID único
- Estado inicial: "pending"
- Timestamp de creación

## 🌐 URLs Disponibles

- **Sitio Principal**: http://localhost:3000
- **Reservas**: http://localhost:3000/reservations
- **Admin Testimonios**: http://localhost:3000/admin
- **API Citas**: http://localhost:3000/api/appointments

## 🔧 API Endpoints

### POST /api/appointments
Crear nueva cita
```json
{
  "firstName": "Juan",
  "lastName": "Pérez",
  "phone": "3121234567",
  "email": "juan@example.com",
  "preferredDate": "2025-10-15",
  "preferredTime": "10:00",
  "consultationType": "primera-vez",
  "reason": "Dolor en articulaciones"
}
```

### GET /api/appointments
Obtener todas las citas

### GET /api/appointments/:id
Obtener cita específica

### PUT /api/appointments/:id
Actualizar cita

### DELETE /api/appointments/:id
Eliminar cita

## 🚀 Cómo Usar

1. **Iniciar servidor**:
```bash
cd backend
npm start
```

2. **Acceder al sistema**:
- Visitar http://localhost:3000
- Click en "Reservar Cita"
- Llenar formulario
- Enviar

3. **Ver citas** (próximamente):
- Panel de admin para citas en desarrollo
- Actualmente se guardan en `appointments.json`

## 📊 Estado del Proyecto

- ✅ Sistema de reservas funcional
- ✅ Validación completa
- ✅ Almacenamiento persistente
- ✅ Diseño responsivo
- ✅ Mensajes de feedback
- ✅ Chatbot integrado
- ✅ Panel de testimonios

## 🔐 Seguridad

- Rate limiting en API
- Validación con Joi
- Sanitización de inputs
- CORS configurado
- Helmet headers

---

**Sistema restaurado**: 12 de Octubre, 2025
**Estado**: Completamente funcional y listo para producción
