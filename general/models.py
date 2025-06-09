from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Count
from django.core.validators import MinValueValidator, MaxValueValidator

#primer sprint

class UsuarioPersonalizado(AbstractUser):
    ROLES = (
        ('Estudiante', 'Estudiante'),
        ('Profesor', 'Profesor')
    )
    rol = models.CharField(max_length=10, choices=ROLES, default='Estudiante')

    sobre_mi = models.TextField(max_length=2000, blank=True, null=True)

    foto_perfil = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)

    def __str__(self):
        return f"{self.username}({self.rol})"

#segundo sprint

class Curso(models.Model):
    id_profesor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre_curso = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500)
    codigo_acceso = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.nombre_curso

class ConfiguracionCurso(models.Model):
    ESTADOS = [
        (1, 'Activo'),
        (2, 'Borrador'),
        (3, 'Eliminado'),
    ]

    curso = models.OneToOneField(Curso, on_delete=models.CASCADE)
    estado = models.IntegerField(choices=ESTADOS, default=1)

    def __str__(self):
        return f"Configuración de {self.curso.nombre_curso}"

class AlumnoCurso(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    alumno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alumno.username} en {self.curso.nombre_curso}"
    
class Reporte(models.Model):
    reportante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes_realizados'
    )
    reportado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes_recibidos'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.TextField()
    contenido = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reportante.username} reportó a {self.reportado.username}"
    
class Actividad(models.Model):
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='actividades_creadas'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='actividades/', null=True, blank=True)
    entregable = models.BooleanField(default=True)
    generado_por_ia = models.BooleanField(default=False)
    titulo = models.CharField(max_length=255)
    contenido = models.TextField()
    permite_entrega_tardia = models.BooleanField(default=False)
    fecha_limite = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.titulo} - {self.curso.nombre_curso}"

class Envio(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='envios_realizados'
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='envios_recibidos'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='envios/')
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.alumno.username} envió {self.actividad.titulo}"


#Tercer Sprint 

class Examen(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    entregas_tardias = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titulo)
            slug = base_slug
            contador = 1
            while Examen.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo
    
class Intento(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    completado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.estudiante.username} - {self.examen.titulo} ({'Completado' if self.completado else 'En progreso'})"

class Pregunta(models.Model):
    TIPO_PREGUNTA_CHOICES = [
        ('abierta', 'Abierta'),
        ('opcion_multiple', 'Opción Múltiple'),
        ('verdadero_falso', 'Verdadero/Falso'),
    ]

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_PREGUNTA_CHOICES, default='abierta')

    def __str__(self):
        return self.texto

class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)
    es_correcta = models.BooleanField(default=False)

    def __str__(self):
        return self.texto
    
class Respuesta(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    respuesta_texto = models.TextField(blank=True, null=True)
    opcion_seleccionada = models.ForeignKey(Opcion, null=True, blank=True, on_delete=models.SET_NULL)
    puntaje = models.PositiveIntegerField(null=True, blank=True)
    comentario = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('examen', 'estudiante', 'pregunta')
        
        
#

class CalificacionGlobalIA(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    calificacion_global = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"Global IA - {self.usuario.username} - {self.examen.titulo}: {self.calificacion_global}"


class CalificacionPorPreguntaIA(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    calificacion_global = models.ForeignKey(CalificacionGlobalIA, on_delete=models.CASCADE, related_name='calificaciones_individuales')
    calificacion_individual = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return f"IA - {self.usuario.username} - {self.pregunta.texto[:30]}...: {self.calificacion_individual}"

class RetroalimentacionIA(models.Model):
    id_retroalimentacion_ia = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    examen = models.ForeignKey('Examen', on_delete=models.CASCADE)
    estado = models.BooleanField(default=False)
    
    id_calificacion_global = models.OneToOneField(
        CalificacionGlobalIA,
        on_delete=models.CASCADE,
        related_name='retroalimentacion_ia',
        null=True,  # <-- permitir temporalmente nulos
        blank=True  # <-- opcional para el admin/formularios
    )


    class Meta:
        unique_together = ('usuario', 'examen')

    def __str__(self):
        return f"Retroalimentación - {self.usuario} / {self.examen} / Estado: {'✅' if self.estado else '❌'}"

#Cuarto Sprint
class ReporteRendimiento(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='reportes_rendimiento')  # Corregido: sin espacios
    docente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reportes_creados')
    titulo = models.CharField(max_length=200)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']  
        verbose_name = 'Reporte de Rendimiento'
        verbose_name_plural = 'Reportes de Rendimiento'
    
    # Métodos movidos fuera de la clase Meta
    def __str__(self):
        return f"{self.titulo} - {self.curso.nombre_curso}"
    
    def obtener_promedios_estudiantes(self):
        """Calcula el promedio de cada estudiante en el rango de fechas"""
        from django.db.models import Avg, Sum, Count
        import datetime
        
        datos_estudiantes = []
        alumnos_curso = AlumnoCurso.objects.filter(curso=self.curso)
        from django.utils import timezone
        for alumno_curso in alumnos_curso:
            estudiante = alumno_curso.alumno

            # Asegurar que las fechas sean timezone-aware
            fecha_inicio_dt = timezone.make_aware(
                datetime.datetime.combine(self.fecha_inicio, datetime.time.min)
            ) if timezone.is_naive(datetime.datetime.combine(self.fecha_inicio, datetime.time.min)) else datetime.datetime.combine(self.fecha_inicio, datetime.time.min)
            fecha_fin_dt = timezone.make_aware(
                datetime.datetime.combine(self.fecha_fin, datetime.time.max)
            ) if timezone.is_naive(datetime.datetime.combine(self.fecha_fin, datetime.time.max)) else datetime.datetime.combine(self.fecha_fin, datetime.time.max)

            # Calcular promedio de calificaciones de envios
            promedio_envios = Envio.objects.filter(
                alumno=estudiante, 
                curso=self.curso, 
                fecha__range=[fecha_inicio_dt, fecha_fin_dt], 
                calificacion__isnull=False
            ).aggregate(promedio=Avg('calificacion'))['promedio']
            
            # Calcular promedio de respuestas de examenes
            respuestas_examenes = Respuesta.objects.filter(
                estudiante=estudiante,
                examen__curso=self.curso,
                examen__fecha_inicio__range=[self.fecha_inicio, self.fecha_fin],
                puntaje__isnull=False
            ).aggregate(
                total_puntaje=Sum('puntaje'), 
                total_respuestas=Count('id')
            )
            
            promedio_examenes = None
            if respuestas_examenes['total_respuestas'] and respuestas_examenes['total_puntaje']:
                promedio_examenes = respuestas_examenes['total_puntaje'] / respuestas_examenes['total_respuestas']
                
            
            promedio_final = None
            if promedio_envios is not None and promedio_examenes is not None:
                promedio_final = (float(promedio_envios) + float(promedio_examenes)) / 2
            elif promedio_envios is not None:
                promedio_final = promedio_envios
            elif promedio_examenes is not None:
                promedio_final = promedio_examenes
                
            if promedio_final is not None:
                datos_estudiantes.append({
                    'estudiante': estudiante, 
                    'promedio': round(promedio_final, 2), 
                    'promedio_envios': round(promedio_envios, 2) if promedio_envios else None, 
                    'promedio_examenes': round(promedio_examenes, 2) if promedio_examenes else None, 
                })
        
        return datos_estudiantes          
        return datos_estudiantes          
            
class CriterioCalificacionIA(models.Model):
    """Criterios para calificación automática de código por IA"""
    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, related_name='criterio_ia')
    lenguaje_programacion = models.CharField(
        max_length=50,
        help_text="Lenguaje de programación a evaluar (ej: Python, Java, JavaScript)"
    )
    criterios_evaluacion = models.TextField(
        help_text="Describe los criterios que la IA debe usar para calificar el código (ej: funcionalidad, eficiencia, estilo)"
    )
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    instrucciones_adicionales = models.TextField(
        blank=True, 
        help_text="Instrucciones específicas para la IA sobre cómo evaluar el código"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Criterios IA - {self.actividad.titulo} ({self.lenguaje_programacion})"

class CalificacionIA(models.Model):
    """Registro de calificaciones de código realizadas por IA"""
    envio = models.OneToOneField(Envio, on_delete=models.CASCADE, related_name='calificacion_ia')
    calificacion_sugerida = models.DecimalField(max_digits=5, decimal_places=2)
    retroalimentacion_ia = models.TextField()
    criterios_utilizados = models.TextField()
    fecha_calificacion = models.DateTimeField(auto_now_add=True)
    confirmada_por_docente = models.BooleanField(default=False)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Calificación IA - {self.envio.actividad.titulo} - {self.envio.alumno.username}"


