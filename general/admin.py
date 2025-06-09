from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    UsuarioPersonalizado, Curso, ConfiguracionCurso, AlumnoCurso,
    Reporte, Actividad, Envio,
    Examen, Intento, Pregunta, Opcion, Respuesta,
    CalificacionGlobalIA, CalificacionPorPreguntaIA, RetroalimentacionIA
)

# UsuarioPersonalizado
class UsuarioPersonalizadoAdmin(UserAdmin):
    model = UsuarioPersonalizado
    list_display = ['username', 'email', 'rol', 'is_active']
    list_filter = ['rol', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('rol', 'sobre_mi', 'foto_perfil')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('rol', 'sobre_mi', 'foto_perfil')}),
    )

admin.site.register(UsuarioPersonalizado, UsuarioPersonalizadoAdmin)

# Curso
class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre_curso', 'id_profesor', 'codigo_acceso', 'descripcion')
    search_fields = ('nombre_curso', 'id_profesor__username', 'codigo_acceso')
    list_filter = ('id_profesor',)

admin.site.register(Curso, CursoAdmin)

# ConfiguracionCurso
class ConfiguracionCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'estado')
    search_fields = ('curso__nombre_curso',)
    list_filter = ('estado',)

admin.site.register(ConfiguracionCurso, ConfiguracionCursoAdmin)

# AlumnoCurso
class AlumnoCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'alumno')
    search_fields = ('curso__nombre_curso', 'alumno__username')
    list_filter = ('curso',)

admin.site.register(AlumnoCurso, AlumnoCursoAdmin)

# Reporte
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('reportante', 'reportado', 'curso', 'motivo')
    search_fields = ('reportante__username', 'reportado__username', 'curso__nombre_curso')
    list_filter = ('curso',)

admin.site.register(Reporte, ReporteAdmin)

# Actividad
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'docente', 'fecha', 'entregable', 'permite_entrega_tardia', 'generado_por_ia', 'fecha_limite')
    search_fields = ('titulo', 'curso__nombre_curso', 'docente__username')
    list_filter = ('curso', 'entregable', 'generado_por_ia', 'permite_entrega_tardia')
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

admin.site.register(Actividad, ActividadAdmin)

# Envio
@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = ('id', 'alumno', 'docente', 'curso', 'actividad', 'fecha', 'calificacion')
    list_filter = ('curso', 'actividad', 'docente', 'fecha')
    search_fields = ('alumno__username', 'docente__username', 'curso__nombre_curso', 'actividad__titulo')
    list_editable = ('calificacion',)
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

# Examen
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'creado_por', 'fecha_inicio', 'fecha_fin', 'entregas_tardias', 'slug')
    search_fields = ('titulo', 'curso__nombre_curso', 'creado_por__username')
    list_filter = ('curso', 'entregas_tardias')
    prepopulated_fields = {"slug": ("titulo",)}

admin.site.register(Examen, ExamenAdmin)

# Intento
class IntentoAdmin(admin.ModelAdmin):
    list_display = ('examen', 'estudiante', 'fecha_inicio', 'completado')
    search_fields = ('examen__titulo', 'estudiante__username')
    list_filter = ('completado',)

admin.site.register(Intento, IntentoAdmin)

# Pregunta
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'examen', 'tipo')
    search_fields = ('texto', 'examen__titulo')
    list_filter = ('tipo', 'examen')

admin.site.register(Pregunta, PreguntaAdmin)

# Opcion
class OpcionAdmin(admin.ModelAdmin):
    list_display = ('texto', 'pregunta', 'es_correcta')
    search_fields = ('texto', 'pregunta__texto')
    list_filter = ('es_correcta',)

admin.site.register(Opcion, OpcionAdmin)

# Respuesta
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ('examen', 'estudiante', 'pregunta', 'puntaje')
    search_fields = ('estudiante__username', 'pregunta__texto', 'examen__titulo')
    list_filter = ('examen',)

admin.site.register(Respuesta, RespuestaAdmin)

# CalificacionGlobalIA
class CalificacionGlobalIAAdmin(admin.ModelAdmin):
    list_display = ('examen', 'usuario', 'calificacion_global')
    search_fields = ('usuario__username', 'examen__titulo')
    list_filter = ('examen',)

admin.site.register(CalificacionGlobalIA, CalificacionGlobalIAAdmin)

# CalificacionPorPreguntaIA
class CalificacionPorPreguntaIAAdmin(admin.ModelAdmin):
    list_display = ('examen', 'usuario', 'pregunta', 'calificacion_individual', 'calificacion_global')
    search_fields = ('usuario__username', 'pregunta__texto', 'examen__titulo')
    list_filter = ('examen',)

admin.site.register(CalificacionPorPreguntaIA, CalificacionPorPreguntaIAAdmin)

@admin.register(RetroalimentacionIA)
class RetroalimentacionIAAdmin(admin.ModelAdmin):
    list_display = ('id_retroalimentacion_ia', 'usuario', 'examen', 'estado')
    list_filter = ('estado', 'examen')
    search_fields = ('usuario__username', 'examen__titulo')