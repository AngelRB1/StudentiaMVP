from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import Curso, AlumnoCurso,Examen
from django.contrib import messages


def verificar_alumno_inscrito(view_func):
    @wraps(view_func)
    def wrapper(request, codigo_acceso, *args, **kwargs):
        curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

        # Verificar si el usuario está inscrito como alumno
        if request.user != curso.id_profesor and not AlumnoCurso.objects.filter(curso=curso, alumno=request.user).exists():
            raise PermissionDenied("Solo los alumnos inscritos pueden acceder a esta vista.")

        # Inyectar el curso en kwargs si lo quieres usar en la vista
        #kwargs['curso'] = curso
        return view_func(request, codigo_acceso, *args, **kwargs)
    return wrapper


def verificar_acceso_curso(view_func):
    @wraps(view_func)
    def wrapper(request, codigo_acceso, *args, **kwargs):
        curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

        if request.user != curso.id_profesor and not AlumnoCurso.objects.filter(curso=curso, alumno=request.user).exists():
            raise PermissionDenied("No tienes permiso para acceder a este curso.")

        # Inyectar el curso en la vista para evitar duplicarlo
        kwargs['curso'] = curso
        return view_func(request, codigo_acceso, *args, **kwargs)
    return wrapper


def verificar_acceso_examen(view_func):
    def _wrapped_view(request, slug, *args, **kwargs):
        examen = get_object_or_404(Examen, slug=slug)
        curso = examen.curso

        if request.user.rol == 'Profesor' and request.user != curso.id_profesor:
            return redirect('no_autorizado')  # o 'inicio'
        elif request.user.rol == 'Estudiante' and not curso.estudiantes.filter(id=request.user.id).exists():
            return redirect('no_autorizado')

        return view_func(request, slug, *args, **kwargs)
    return _wrapped_view

def docente_requerido(vista_funcion):
    """Decorador que verifica que el usuario sea docente"""
    @wraps(vista_funcion)
    def _vista_envuelta(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('iniciar_sesion')
        if request.user.rol != 'Profesor':
            raise PermissionDenied("Solo docentes pueden acceder a esta funcion")
        return vista_funcion(request, *args, **kwargs)
    return _vista_envuelta

def docente_curso_requerido(vista_funcion):
    @wraps(vista_funcion)
    def _vista_envuelta(request, codigo_acceso, *args, **kwargs):
        curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
        if request.user != curso.id_profesor:
            raise PermissionDenied("Solo el docente de este curso puede realiza esta acción")
        return vista_funcion(request, codigo_acceso, *args, **kwargs)
    return _vista_envuelta


def verificar_permiso_calificacion_ia(view_func):
    @wraps(view_func)
    def wrapper(request, codigo_acceso, *args, **kwargs):
        curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
        
        # Verificar que el usuario sea el profesor del curso
        if request.user != curso.id_profesor:
            raise PermissionDenied("Solo el docente del curso puede calificar con IA.")
        
        # Inyectar el curso en la vista
        kwargs['curso'] = curso
        return view_func(request, codigo_acceso, *args, **kwargs)
    return wrapper
        

