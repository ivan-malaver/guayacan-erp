// Mapa general de rutas de la aplicación. ARCHIVO GENERADO por docs/uml/fuentes/gen_frontend.py.
//
// CÓMO FUNCIONA
// - /ingreso es pública (pantalla de inicio de sesión).
// - Todo lo demás cuelga de una ruta protegida por sesionGuard: si no hay sesión, envía a /ingreso.
// - Cada módulo usa loadChildren (carga perezosa): su código se descarga solo cuando alguien entra,
//   así la aplicación abre rápido aunque tenga 26 módulos.
// - '**' captura cualquier dirección desconocida y devuelve al inicio.
import { Routes } from '@angular/router';

import { IngresoComponent } from './core/auth/ingreso.component';
import { sesionGuard } from './core/auth/sesion.guard';
import { InicioComponent } from './shared/inicio.component';

export const routes: Routes = [
  { path: 'ingreso', component: IngresoComponent, title: 'Ingreso' },
  {
    path: '',
    canActivate: [sesionGuard], // exige sesión iniciada para todo lo de abajo
    children: [
      { path: '', component: InicioComponent, title: 'Inicio' },
      { path: 'nucleo', title: "Núcleo de la plataforma", loadChildren: () => import('./features/nucleo/nucleo.routes').then((r) => r.RUTAS) },
      { path: 'seguridad', title: "Seguridad informática", loadChildren: () => import('./features/seguridad/seguridad.routes').then((r) => r.RUTAS) },
      { path: 'terceros', title: "Terceros y datos personales", loadChildren: () => import('./features/terceros/terceros.routes').then((r) => r.RUTAS) },
      { path: 'documental', title: "Gestión documental", loadChildren: () => import('./features/documental/documental.routes').then((r) => r.RUTAS) },
      { path: 'produccion', title: "Producción animal y agrícola", loadChildren: () => import('./features/produccion/produccion.routes').then((r) => r.RUTAS) },
      { path: 'riego', title: "Riego", loadChildren: () => import('./features/riego/riego.routes').then((r) => r.RUTAS) },
      { path: 'iot', title: "IoT, seguridad perimetral y robótica", loadChildren: () => import('./features/iot/iot.routes').then((r) => r.RUTAS) },
      { path: 'ambiental', title: "Ambiental", loadChildren: () => import('./features/ambiental/ambiental.routes').then((r) => r.RUTAS) },
      { path: 'inventario', title: "Inventario y cadena de frío", loadChildren: () => import('./features/inventario/inventario.routes').then((r) => r.RUTAS) },
      { path: 'compras', title: "Compras", loadChildren: () => import('./features/compras/compras.routes').then((r) => r.RUTAS) },
      { path: 'activos', title: "Activos y mantenimiento", loadChildren: () => import('./features/activos/activos.routes').then((r) => r.RUTAS) },
      { path: 'comercial', title: "Ventas", loadChildren: () => import('./features/comercial/comercial.routes').then((r) => r.RUTAS) },
      { path: 'crm', title: "Clientes potenciales (CRM)", loadChildren: () => import('./features/crm/crm.routes').then((r) => r.RUTAS) },
      { path: 'redes', title: "Canales y redes sociales", loadChildren: () => import('./features/redes/redes.routes').then((r) => r.RUTAS) },
      { path: 'turismo', title: "Turismo", loadChildren: () => import('./features/turismo/turismo.routes').then((r) => r.RUTAS) },
      { path: 'agenda', title: "Agenda y portería", loadChildren: () => import('./features/agenda/agenda.routes').then((r) => r.RUTAS) },
      { path: 'personal', title: "Personal, tareas y turnos", loadChildren: () => import('./features/personal/personal.routes').then((r) => r.RUTAS) },
      { path: 'formacion', title: "Formación", loadChildren: () => import('./features/formacion/formacion.routes').then((r) => r.RUTAS) },
      { path: 'nomina', title: "Nómina", loadChildren: () => import('./features/nomina/nomina.routes').then((r) => r.RUTAS) },
      { path: 'finanzas', title: "Finanzas y contabilidad", loadChildren: () => import('./features/finanzas/finanzas.routes').then((r) => r.RUTAS) },
      { path: 'estrategia', title: "Estrategia de negocio", loadChildren: () => import('./features/estrategia/estrategia.routes').then((r) => r.RUTAS) },
      { path: 'proyectos', title: "Proyectos (PMBOK 8)", loadChildren: () => import('./features/proyectos/proyectos.routes').then((r) => r.RUTAS) },
      { path: 'seguros', title: "Seguros", loadChildren: () => import('./features/seguros/seguros.routes').then((r) => r.RUTAS) },
      { path: 'cumplimiento', title: "Cumplimiento y certificaciones", loadChildren: () => import('./features/cumplimiento/cumplimiento.routes').then((r) => r.RUTAS) },
      { path: 'ia', title: "Inteligencia artificial", loadChildren: () => import('./features/ia/ia.routes').then((r) => r.RUTAS) },
      { path: 'adopcion', title: "Adopción de árboles y animales", loadChildren: () => import('./features/adopcion/adopcion.routes').then((r) => r.RUTAS) },
    ],
  },
  { path: '**', redirectTo: '' },
];
