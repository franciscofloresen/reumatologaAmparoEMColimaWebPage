#!/bin/bash

echo "🏥 Iniciando sistema de reservas para Dra. María Amparo Enríquez Maldonado"
echo "=================================================="

# Start the backend server
echo "📡 Iniciando servidor backend..."
cd backend
npm start &
BACKEND_PID=$!

echo "✅ Servidor backend iniciado en http://localhost:3000"
echo "✅ Panel de administración disponible en: http://localhost:3000/../frontend/admin.html"
echo "✅ Sistema de reservas disponible en: http://localhost:3000/../frontend/reservations.html"
echo "✅ Sitio web principal disponible en: http://localhost:3000/../frontend/index.html"
echo ""
echo "📋 Para acceder a los archivos:"
echo "   - Sitio web: frontend/index.html"
echo "   - Reservas: frontend/reservations.html" 
echo "   - Admin: frontend/admin.html"
echo ""
echo "🛑 Para detener el servidor, presiona Ctrl+C"

# Wait for Ctrl+C
trap "echo '🛑 Deteniendo servidor...'; kill $BACKEND_PID; exit" INT
wait $BACKEND_PID
