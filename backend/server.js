const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware de seguridad
app.use(helmet({
    contentSecurityPolicy: false
}));

app.use(cors({
  origin: process.env.FRONTEND_URL || ['http://localhost:3000', 'https://dramariamparoenriquezreumatologiaintegral.com', 'http://dramariamparoenriquezreumatologiaintegral.com'],
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});
app.use('/api/', limiter);

// Middleware para parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Serve static files from frontend directory
app.use(express.static(path.join(__dirname, '../frontend')));

// API Routes
app.use('/api/contact', require('./routes/contact'));
app.use('/api/appointments', require('./routes/appointments'));

// Serve frontend files
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

app.get('/reservations', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/reservations.html'));
});

app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/admin.html'));
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Algo salió mal!' });
});

// 404 handler for API routes
app.use('/api/*', (req, res) => {
  res.status(404).json({ error: 'Ruta de API no encontrada' });
});

// Serve index.html for any other routes (SPA fallback)
app.use('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

app.listen(PORT, () => {
  console.log(`🏥 Servidor iniciado en http://localhost:${PORT}`);
  console.log(`📋 Sitio web: http://localhost:${PORT}`);
  console.log(`📅 Reservas: http://localhost:${PORT}/reservations`);
  console.log(`⚙️  Admin: http://localhost:${PORT}/admin`);
});

