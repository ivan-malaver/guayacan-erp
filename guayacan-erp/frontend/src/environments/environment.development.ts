// Ajustes del frontend en DESARROLLO (npm start). angular.json cambia environment.ts por este archivo al compilar.
export const environment = {
  produccion: false,
  // Ruta relativa: el proxy de desarrollo (proxy.conf.json) la reenvía a Django en http://localhost:8000
  api: '/api/v1',
};
