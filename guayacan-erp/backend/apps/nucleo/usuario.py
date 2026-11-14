"""Modelo de usuario sobre la tabla nucleo.usuario (AUTH_USER_MODEL en settings).

Escrito a mano (el resto de models.py es generado) porque Django exige métodos especiales para iniciar sesión.

Por qué no usa PermissionsMixin: los roles y permisos de GuayacanERP son POR FINCA y viven en las tablas
nucleo.usuario_rol, nucleo.rol_permiso y nucleo.permiso, no en las tablas de permisos de Django. Se consultan
con guayacan/permisos.py.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models.functions import Now


class UsuarioManager(BaseUserManager):
    """Crea usuarios con la contraseña cifrada (se usa en scripts y en la consola de Django)."""

    use_in_migrations = False  # este modelo no se migra (managed = False)

    def create_user(self, correo, password=None, **extra):
        if not correo:
            raise ValueError('El correo es obligatorio')
        # El correo se guarda normalizado y en minúscula para que el ingreso no distinga mayúsculas
        usuario = self.model(correo=self.normalize_email(correo).lower(), **extra)
        usuario.set_password(password)  # cifra con Argon2; nunca se guarda la clave en claro
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, password=None, **extra):
        extra['es_superusuario'] = True
        return self.create_user(correo, password, **extra)


class Usuario(AbstractBaseUser):
    """Persona que entra al sistema (administrador, operario, contador, cliente con cuenta)."""

    id = models.BigAutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    correo = models.EmailField(max_length=254, unique=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    # Django llama «password» al campo; en la base la columna se llama contrasena_hash
    password = models.CharField(max_length=255, db_column='contrasena_hash')
    es_superusuario = models.BooleanField(db_default=False)
    # is_active y last_login son nombres que Django espera; db_column apunta a las columnas en español
    is_active = models.BooleanField(db_column='activo', db_default=True)
    last_login = models.DateTimeField(db_column='ultimo_ingreso', null=True, blank=True)
    # Persona del registro de terceros a la que corresponde (si aplica)
    tercero = models.ForeignKey('terceros.Tercero', models.DO_NOTHING, db_column='tercero_id', related_name='+',
                                db_constraint=False, null=True, blank=True)
    creado_en = models.DateTimeField(db_default=Now(), editable=False)
    actualizado_en = models.DateTimeField(db_default=Now(), editable=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'               # se inicia sesión con el correo
    EMAIL_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre_completo']   # datos que pide createsuperuser además del correo y la clave

    class Meta:
        managed = False                     # la tabla la crea el SQL, no Django
        db_table = 'nucleo"."usuario'

    def __str__(self):
        return self.nombre_completo

    # Django pregunta is_staff / is_superuser en algunas herramientas; se responde con es_superusuario
    @property
    def is_staff(self):
        return self.es_superusuario

    @property
    def is_superuser(self):
        return self.es_superusuario
