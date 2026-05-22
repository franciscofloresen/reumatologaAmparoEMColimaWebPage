# Backend - Página Web Reumatología

## Instalación

```bash
cd backend
npm install
```

## Configuración

1. Copia `.env.example` a `.env`
2. Configura las variables de entorno:
   - `EMAIL_USER`: Tu email de Gmail
   - `EMAIL_PASS`: App password de Gmail
   - `DOCTOR_EMAIL`: Email de la doctora

## Ejecutar

```bash
# Desarrollo
npm run dev

# Producción
npm start
```

## Endpoints

### Contacto
- `POST /api/contact` - Enviar mensaje de contacto

### Citas
- `POST /api/appointments` - Solicitar cita
- `GET /api/appointments/availability?date=YYYY-MM-DD` - Ver horarios disponibles

### Health Check
- `GET /health` - Estado del servidor
