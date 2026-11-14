// Ajustes del frontend en PRODUCCIÓN (npm run build).
export const environment = {
  produccion: true,
  // En producción el servidor web (Caddy o Nginx) publica la API en el mismo dominio bajo /api/v1
  api: '/api/v1',
};
