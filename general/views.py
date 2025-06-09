from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
import datetime 
from django.contrib.auth import authenticate, login, logout, get_backends, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
import string
from .forms import RegistroUsuarioForm, EditarPerfilForm, CursoForm, InscripcionCursoForm, ReportarForm, ActividadForm, ExamenForm, PreguntaForm, OpcionForm, VerdaderoFalsoForm, EnvioForm, CalificacionForm , FormularioReporteRendimiento, ConfirmarCalificacionIAForm, CriterioCalificacionIAForm , CrearExamenIAForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from .models import Curso, AlumnoCurso, UsuarioPersonalizado, Actividad, Examen, Pregunta, Opcion, Respuesta, Intento, Envio, CalificacionPorPreguntaIA, CalificacionGlobalIA, RetroalimentacionIA, ReporteRendimiento, CalificacionIA, CriterioCalificacionIA
from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.utils import timezone
from datetime import date, datetime
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.db import models
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from .decorators import verificar_acceso_curso, docente_curso_requerido, docente_requerido, verificar_alumno_inscrito

from django.conf import settings
import openai
import json
from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from decimal import Decimal
from django.utils.html import format_html
from django.utils import timezone



client = OpenAI(api_key=settings.OPENAI_API_KEY)


User = get_user_model()

#primer sprint

def inicio(request):
    return render(request, 'inicio.html')

def iniciar_sesion(request):
    msj = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('inicio')
        else:
            msj = "Correo o contraseña incorrectas. Intente de nuevo"
    return render(request, 'iniciar_sesion.html', {'msj':msj})

def salir(request):
    logout(request)
    return redirect('inicio')

def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()


            backend = get_backends()[0] 
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"

            login(request, user) 

            return redirect('inicio')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'registrar_usuario.html', {'form': form})

class CustomPasswordResetView(PasswordResetView):
    template_name = 'recovery/password_reset.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_submitted'] = self.request.method == 'POST'
        return context

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'recovery/password_reset_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_submitted'] = self.request.method == 'POST'
        return context
    
#segundo sprint

@login_required
def ver_perfil(request):
    return render(request, 'perfil.html', {'usuario':request.user})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('ver_perfil')
    else:
        form = EditarPerfilForm(instance=request.user)

    return render(request, 'editar_perfil.html', {'form': form})

def generar_codigo():
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Curso.objects.filter(codigo_acceso=codigo).exists():
            return codigo

@login_required
def crear_curso(request):
    if request.user.rol != 'Profesor': 
        messages.error(request, "No tienes permiso para crear cursos.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.id_profesor = request.user 
            curso.codigo_acceso = generar_codigo()
            curso.save()
            return redirect('dashboard')

    else:
        form = CursoForm()

    return render(request, 'crear_curso.html', {'form': form})

@login_required
def dashboard(request):
    usuario = request.user
    es_profesor = usuario.rol == "Profesor"
    if es_profesor:
        cursos_creados = Curso.objects.filter(id_profesor=usuario) 
    else:
        cursos_creados = None

    cursos_inscritos = AlumnoCurso.objects.filter(alumno=usuario) 

    return render(request, "dashboard.html", {
        "es_profesor": es_profesor,
        "cursos_creados": cursos_creados,
        "cursos_inscritos": cursos_inscritos
    })
@verificar_acceso_curso
@login_required
def board(request, codigo_acceso, curso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividades = Actividad.objects.filter(curso=curso).order_by('-fecha')
    examenes = Examen.objects.filter(curso=curso).order_by('-fecha_inicio')
    hoy = date.today()
    return render(request, 'board.html',{
        'curso':curso,
        'actividades': actividades,
        'examenes': examenes,
        'hoy': hoy
    })

def board_leave(request, codigo_acceso):
    usuario = request.user
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    inscripcion = get_object_or_404(AlumnoCurso, alumno=usuario, curso=curso)

    if request.method == "POST":
        inscripcion.delete()
        return redirect('dashboard')
    
    return render(request, 'board_leave.html', {
        "curso":curso
    })

@login_required
def board_borrar(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    if request.method == "POST":
        curso.delete()
        return redirect('dashboard')
    return render(request, 'board_borrar.html', {'curso':curso})

@login_required
def board_actualizar(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso)

        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CursoForm(instance=curso)
    
    return render(request, 'board_actualizar.html', {
        'form':form, 'curso':curso
    })

@login_required
def inscribirse_curso(request):
    
    if request.method == "POST":
        form = InscripcionCursoForm(request.POST)
        if form.is_valid():
            codigo_acceso = form.cleaned_data["codigo_acceso"]

            # Buscar el curso por su código de acceso
            curso = Curso.objects.filter(codigo_acceso=codigo_acceso).first()

            # Validar que el curso existe
            if not curso:
                messages.error(request, "El curso no existe.")
                return redirect("inscribirse_curso")

            # Validar que el profesor no intente inscribirse en su propio curso
            if curso.id_profesor == request.user:
                messages.error(request, "No puedes inscribirte en tu propio curso.")
                return redirect("inscribirse_curso")

            # Verificar si el usuario ya está inscrito en el curso
            if AlumnoCurso.objects.filter(curso=curso, alumno=request.user).exists():
                # Si ya está inscrito, mostrar el mensaje de error
                messages.error(request, "Ya estás inscrito en este curso.")
                return redirect("inscribirse_curso")  # Redirigir para que el mensaje se vea

            # Si no está inscrito, registrar la inscripción
            AlumnoCurso.objects.create(curso=curso, alumno=request.user)
            messages.success(request, f"Te has inscrito en {curso.nombre_curso} correctamente.")

            # Redirigir al dashboard
            return redirect("dashboard")

    else:
        form = InscripcionCursoForm()

    return render(request, "inscribirse_curso.html", {"form": form})

@login_required
def board_view_students(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    alumnos_inscritos = AlumnoCurso.objects.filter(curso=curso).select_related('alumno')

    return render(request, 'board_view_students.html', {
        'curso':curso,
        'alumnos_inscritos':alumnos_inscritos
    })

@login_required
def board_remove_student(request, codigo_acceso, id_alumno):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == "POST":
        AlumnoCurso.objects.filter(curso=curso, alumno_id=id_alumno).delete()

    return redirect('board_view_students', codigo_acceso=codigo_acceso)

from django.http import HttpResponseForbidden
from django.db.models import Q

@login_required
def other_profile(request, id):
    usuario = request.user
    alumno = get_object_or_404(UsuarioPersonalizado, id=id)

    if usuario.id == alumno.id:
        return redirect('ver_perfil')

    # Verificar relación académica:
    # Caso 1: Ambos son alumnos del mismo curso
    cursos_comunes = AlumnoCurso.objects.filter(
        curso__in=AlumnoCurso.objects.filter(alumno=usuario).values('curso'),
        alumno=alumno
    ).exists()

    # Caso 2: Usuario logueado es profesor de un curso donde el otro es alumno
    como_profesor = Curso.objects.filter(
        id_profesor=usuario,
        alumnocurso__alumno=alumno
    ).exists()

    # Caso 3: Usuario logueado es alumno en curso impartido por el otro (profesor)
    como_estudiante = Curso.objects.filter(
        id_profesor=alumno,
        alumnocurso__alumno=usuario
    ).exists()

    if not (cursos_comunes or como_profesor or como_estudiante):
        return render(request, '403.html', status=403)

    return render(request, 'other_profile.html', {'alumno': alumno})


@login_required
def report(request, id):
    usuario = request.user
    alumno = get_object_or_404(UsuarioPersonalizado, id=id)

    if request.method == "POST":
        form = ReportarForm(request.POST)

        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.reportante = usuario
            reporte.reportado = alumno
            reporte.save()
            return redirect('report_success')
    else:
        form = ReportarForm()

    return render(request, 'report.html', {
        'form': form,
        'reportado': alumno,
        'reportante': usuario
    })


@login_required
def report_success(request):
    msj = "El reporte ha sido enviado. Nos pondremos en contacto contigo pronto"
    return render(request, 'report_success.html', {'msj':msj})

@login_required
def board_add_content(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ActividadForm(request.POST, request.FILES)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.curso = curso
            actividad.docente = request.user
            actividad.save()
            return redirect('board', codigo_acceso=curso.codigo_acceso)
    else:
        form = ActividadForm()

    return render(request, 'board_add_content.html', {
        'curso': curso,
        'form': form
    })


@login_required
def content_edit(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ActividadForm(request.POST, request.FILES, instance=actividad)
        if form.is_valid():
            form.save()
            return redirect('board', codigo_acceso=codigo_acceso)
    else:
        form = ActividadForm(instance=actividad)

    return render(request, 'board_edit_content.html', {
        'curso': curso,
        'form': form
    })


@login_required
def content_delete(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == 'POST':
        actividad.delete()
        return redirect('board', codigo_acceso=codigo_acceso)

    return render(request, 'board_delete_content.html', {
        'curso': curso,
        'actividad': actividad
    })

@verificar_alumno_inscrito
@login_required
def content_detail(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    envio = Envio.objects.filter(alumno=request.user, actividad=actividad).first()
    ya_enviado = envio is not None
    calificacion = envio.calificacion if envio else None

    return render(request, 'board_content_detail.html', {
        'curso': curso,
        'actividad': actividad,
        'ya_enviado': ya_enviado,
        'calificacion': calificacion,
        'now': timezone.now(),
    })
    
    
    
    
    
    
    #Tercer Sprint
@login_required
def crear_examen(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('board', codigo_acceso=curso.codigo_acceso)

    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            examen = form.save(commit=False)
            examen.curso = curso
            examen.creado_por = request.user
            examen.save()
            messages.success(request, "Examen creado exitosamente")
            return redirect('listar_preguntas', slug=examen.slug)
        else:
            messages.error(request, "Error al crear el examen, intenta de nuevo")
    else:
        form = ExamenForm()

    return render(request, 'crear_examen.html', {'form': form, 'curso': curso})

@login_required
def agregar_pregunta(request, slug):
    
    examen = get_object_or_404(Examen, slug=slug)

    # Validar que solo el creador del examen pueda agregar preguntas
    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    # Formset para opciones de opción múltiple
    OpcionFormSet = modelformset_factory(
        Opcion,
        form=OpcionForm,
        extra=3,
        min_num=2,
        validate_min=True,
        max_num=5,
        validate_max=True,
        can_delete=True
    )

    vf_form = VerdaderoFalsoForm()
    formset = OpcionFormSet(queryset=Opcion.objects.none())  # Inicial vacío para GET

    if request.method == 'POST':
        pregunta_form = PreguntaForm(request.POST)
        tipo = request.POST.get('tipo')

        if not tipo:
            messages.error(request, "Debes seleccionar un tipo de pregunta.")
            return render(request, 'agregar_pregunta.html', {
                'pregunta_form': pregunta_form,
                'formset': formset,
                'vf_form': vf_form,
                'examen': examen,
            })

        if tipo == 'opcion_multiple':
            formset = OpcionFormSet(request.POST, queryset=Opcion.objects.none())

            if pregunta_form.is_valid() and formset.is_valid():
                pregunta = pregunta_form.save(commit=False)
                pregunta.examen = examen
                pregunta.tipo = tipo
                pregunta.save()

                opciones_correctas = 0
                opciones_guardadas = 0

                for opcion_form in formset:
                    if opcion_form.cleaned_data.get('DELETE'):
                        continue
                    
                    texto = opcion_form.cleaned_data.get('texto')
                    if not texto:
                        continue

                    opcion = opcion_form.save(commit=False)
                    opcion.pregunta = pregunta
                    opcion.save()
                    opciones_guardadas += 1

                    if opcion.es_correcta:
                        opciones_correctas += 1

                # Validaciones específicas para opción múltiple
                if opciones_guardadas < 2:
                    messages.error(request, "Debes ingresar al menos 2 opciones.")
                   # pregunta.delete()
                   # return redirect('agregar_pregunta', slug=examen.slug)
                elif opciones_correctas == 0:
                    messages.error(request, "Debes marcar al menos una opción como correcta.")
                    pregunta.delete()
                   # return redirect('agregar_pregunta', slug=examen.slug)
                else:
                    messages.success(request, "Pregunta de opción múltiple agregada correctamente.")
                    return redirect('listar_preguntas', slug=examen.slug)

        elif tipo == 'verdadero_falso':
            vf_form = VerdaderoFalsoForm(request.POST)

            if pregunta_form.is_valid() and vf_form.is_valid():
                pregunta = pregunta_form.save(commit=False)
                pregunta.examen = examen
                pregunta.tipo = tipo
                pregunta.save()

                respuesta = vf_form.cleaned_data['respuesta']
                Opcion.objects.create(
                    pregunta=pregunta,
                    texto='Verdadero',
                    es_correcta=(respuesta == 'verdadero')
                )
                Opcion.objects.create(
                    pregunta=pregunta,
                    texto='Falso',
                    es_correcta=(respuesta == 'falso')
                )

                messages.success(request, "Pregunta de Verdadero/Falso agregada correctamente.")
                return redirect('listar_preguntas', slug=examen.slug)
            else:
                error_message = "Error en el formulario: "
                if not pregunta_form.is_valid():
                    error_message += f"Pregunta - {pregunta_form.errors} "
                if not vf_form.is_valid():
                    error_message += f"VF - {vf_form.errors}"
                messages.error(request, error_message.strip())

        elif tipo == 'abierta':
            if pregunta_form.is_valid():
                pregunta = pregunta_form.save(commit=False)
                pregunta.examen = examen
                pregunta.tipo = tipo
                pregunta.save()
                messages.success(request, "Pregunta abierta agregada correctamente.")
                return redirect('listar_preguntas', slug=examen.slug)
            else:
                messages.error(request, f"Error en el formulario de pregunta abierta: {pregunta_form.errors}")

        else:
            messages.error(request, f"Tipo de pregunta inválido: {tipo}")

    else:
        pregunta_form = PreguntaForm()

    return render(request, 'agregar_pregunta.html', {
        'pregunta_form': pregunta_form,
        'formset': formset,
        'vf_form': vf_form,
        'examen': examen,
    })

@login_required
def listar_preguntas(request, slug):
    examen = get_object_or_404(Examen, slug=slug)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    preguntas = Pregunta.objects.filter(examen=examen)
    return render(request, 'listar_preguntas.html', {'examen': examen, 'preguntas': preguntas})

@login_required
def editar_pregunta(request, slug, pk):
    
    examen = get_object_or_404(Examen, slug=slug)
    pregunta = get_object_or_404(Pregunta, id=pk, examen=examen)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    tipo = pregunta.tipo
    vf_form = VerdaderoFalsoForm()
    formset = None

    # Obtener opciones actuales y calcular cuántos formularios vacíos se requieren
    opciones_existentes = Opcion.objects.filter(pregunta=pregunta)
    extra = max(0, 5 - opciones_existentes.count())

    OpcionFormSet = modelformset_factory(
        Opcion,
        form=OpcionForm,
        extra=extra,
        min_num=2,
        validate_min=True,
        max_num=5,
        validate_max=True,
        can_delete=True
    )

    if request.method == 'POST':
        pregunta_form = PreguntaForm(request.POST, instance=pregunta)
        pregunta_form.data = pregunta_form.data.copy()
        pregunta_form.data['tipo'] = pregunta.tipo
        
        pregunta_form.fields['tipo'].disabled = True

        if tipo == 'opcion_multiple':
            formset = OpcionFormSet(request.POST, queryset=opciones_existentes)

            if pregunta_form.is_valid() and formset.is_valid():
                pregunta = pregunta_form.save()

                opciones_correctas = 0
                opciones_guardadas = 0

                for opcion_form in formset:
                    if opcion_form.cleaned_data.get('DELETE'):
                        if opcion_form.instance.pk:
                            opcion_form.instance.delete()
                        continue

                    texto = opcion_form.cleaned_data.get('texto')
                    if not texto:
                        continue

                    opcion = opcion_form.save(commit=False)
                    opcion.pregunta = pregunta
                    opcion.save()
                    opciones_guardadas += 1

                    if opcion.es_correcta:
                        opciones_correctas += 1

                if opciones_guardadas < 2:
                    messages.error(request, "Debes mantener al menos 2 opciones.")
                elif opciones_correctas == 0:
                    messages.error(request, "Debe haber al menos una opción correcta.")
                    #pregunta.delete()
                else:
                    messages.success(request, "Pregunta de opción múltiple actualizada correctamente.")
                    return redirect('listar_preguntas', slug=slug)

        elif tipo == 'verdadero_falso':
            vf_form = VerdaderoFalsoForm(request.POST)

            if pregunta_form.is_valid() and vf_form.is_valid():
                pregunta = pregunta_form.save()
                respuesta = vf_form.cleaned_data['respuesta']

                opciones = Opcion.objects.filter(pregunta=pregunta)
                for opcion in opciones:
                    if opcion.texto.lower() == 'verdadero':
                        opcion.es_correcta = (respuesta == 'verdadero')
                    elif opcion.texto.lower() == 'falso':
                        opcion.es_correcta = (respuesta == 'falso')
                    opcion.save()

                messages.success(request, "Pregunta de Verdadero/Falso actualizada correctamente.")
                return redirect('listar_preguntas', slug=slug)

        elif tipo == 'abierta':
            if pregunta_form.is_valid():
                pregunta_form.save()
                messages.success(request, "Pregunta abierta actualizada correctamente.")
                return redirect('listar_preguntas', slug=slug)
            else:
                messages.error(request, f"Error en el formulario: {pregunta_form.errors}")

    else:
        pregunta_form = PreguntaForm(instance=pregunta)
        
        pregunta_form.fields['tipo'].disabled = True

        if tipo == 'opcion_multiple':
            formset = OpcionFormSet(queryset=opciones_existentes)

        elif tipo == 'verdadero_falso':
            opciones = Opcion.objects.filter(pregunta=pregunta)
            respuesta = 'verdadero' if opciones.filter(texto__iexact='verdadero', es_correcta=True).exists() else 'falso'
            vf_form = VerdaderoFalsoForm(initial={'respuesta': respuesta})

    return render(request, 'editar_pregunta.html', {
        'pregunta_form': pregunta_form,
        'formset': formset,
        'vf_form': vf_form,
        'examen': examen,
        'modo_edicion': True,
        'pregunta': pregunta,
    })

@login_required
def eliminar_pregunta(request, slug, pk):
    examen = get_object_or_404(Examen, slug=slug)
    pregunta = get_object_or_404(Pregunta, id=pk, examen=examen)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    if request.method == 'POST':
        pregunta.delete()
        messages.success(request, "Pregunta eliminada correctamente.")
        return redirect('listar_preguntas', slug=slug)

    return render(request, 'eliminar_pregunta.html', {'pregunta': pregunta, 'examen': examen})

@login_required
def ver_examen(request, slug):
    examen = get_object_or_404(Examen, slug=slug)
    es_docente = request.user == examen.creado_por
    ahora = timezone.now().date()

    disponible = examen.fecha_inicio <= ahora and (not examen.fecha_fin or examen.fecha_fin >= ahora)

    estado = "cerrado"
    if disponible:
        ya_respondido = Respuesta.objects.filter(examen=examen, estudiante=request.user).exists()
        estado = "respondido" if ya_respondido else "disponible"

    preguntas = Pregunta.objects.filter(examen=examen).prefetch_related('opcion_set') if es_docente else None

    return render(request, 'ver_examen.html', {
        'examen': examen,
        'es_docente': es_docente,
        'disponible': disponible,
        'estado': estado,
        'preguntas': preguntas,
    })

@login_required
def iniciar_examen(request, slug):
    examen = get_object_or_404(Examen, slug=slug)
    estudiante = request.user
    ahora = timezone.now().date()
    curso = examen.curso

    # Verificación de acceso
    if estudiante != examen.creado_por and not AlumnoCurso.objects.filter(curso=curso, alumno=estudiante).exists():
        raise PermissionDenied("No tienes permiso para presentar este examen.")

    if examen.fecha_inicio > ahora or (examen.fecha_fin and examen.fecha_fin < ahora):
        messages.error(request, "Este examen no está disponible en este momento.")
        return redirect('ver_examen', slug=examen.slug)

    if estudiante == examen.creado_por:
        messages.info(request, "Eres el creador del examen, no puedes presentarlo.")
        return redirect('ver_examen', slug=examen.slug)

    # ✅ Verificar si ya ha completado el examen
    if Respuesta.objects.filter(examen=examen, estudiante=estudiante).exists():
        messages.warning(request, "Ya respondiste este examen.")
        return redirect('ver_examen', slug=examen.slug)

    # ✅ Registrar intento si no existe
    intento, creado = Intento.objects.get_or_create(
        examen=examen,
        estudiante=estudiante,
        completado=False
    )

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                pregunta_id = key.split('_')[1]
                try:
                    pregunta = Pregunta.objects.get(id=pregunta_id, examen=examen)

                    if pregunta.tipo == "abierta":
                        Respuesta.objects.create(
                            examen=examen,
                            estudiante=estudiante,
                            pregunta=pregunta,
                            respuesta_texto=value
                        )
                    else:
                        opcion = Opcion.objects.get(id=value, pregunta=pregunta)
                        Respuesta.objects.create(
                            examen=examen,
                            estudiante=estudiante,
                            pregunta=pregunta,
                            opcion_seleccionada=opcion
                        )
                except (Pregunta.DoesNotExist, Opcion.DoesNotExist):
                    continue

        # ✅ Marcar intento como completado
        intento.completado = True
        intento.save()

        messages.success(request, "Respuestas enviadas correctamente.")
        return redirect('ver_examen', slug=examen.slug)

    preguntas = Pregunta.objects.filter(examen=examen).prefetch_related('opcion_set')
    return render(request, 'iniciar_examen.html', {
        'examen': examen,
        'preguntas': preguntas,
    })

    
@login_required
def editar_examen(request, slug):
    
    examen = get_object_or_404(Examen, slug=slug)

    # Solo el profesor que creó el examen puede editarlo
    if request.user != examen.creado_por:
        messages.error(request, "No tienes permiso para editar este examen.")
        return redirect('ver_examen', slug=slug)

    if request.method == 'POST':
        form = ExamenForm(request.POST, instance=examen)
        if form.is_valid():
            examen_actualizado = form.save(commit=False)
            # Validar que el título no esté vacío (ya lo hace form.is_valid())
            if examen_actualizado.titulo.strip() == '':
                messages.error(request, "Por favor, ingrese un título.")
            # Validar que haya al menos una pregunta
            elif examen.pregunta_set.count() == 0:
                messages.error(request, "Debe haber al menos una pregunta.")
            else:
                examen_actualizado.save()
                messages.success(request, "Examen actualizado con éxito.")
                return redirect('ver_examen', slug=examen.slug)
        else:
            messages.error(request, "Error al actualizar el examen, intenta de nuevo.")
    else:
        form = ExamenForm(instance=examen)

    return render(request, 'editar_examen.html', {
        'form': form,
        'examen': examen,
    })

@login_required
def eliminar_examen(request, slug):
    examen = get_object_or_404(Examen, slug=slug)

    if request.user != examen.creado_por:
        raise PermissionDenied("No tienes permiso para eliminar este examen.")

    intentos_activos = Intento.objects.filter(examen=examen, completado=False)

    if intentos_activos.exists():
        # Si hay intentos activos, no lo eliminamos y mostramos los usuarios en la plantilla
        return render(request, 'eliminar_examen.html', {
            'examen': examen,
            'intentos_activos': intentos_activos
        })

    if request.method == 'POST':
        examen.delete()
        
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)



    return render(request, 'eliminar_examen.html', {
        'examen': examen,
        'intentos_activos': []
    })
    
@verificar_acceso_curso
@login_required
def examenes_por_calificar(request, codigo_acceso, curso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('board', codigo_acceso=codigo_acceso)

    examenes = Examen.objects.filter(curso=curso)
    examenes_con_respuestas = []

    for examen in examenes:
        estudiantes_con_respuestas = Respuesta.objects.filter(examen=examen).values_list('estudiante', flat=True).distinct()
        if estudiantes_con_respuestas.exists():
            examenes_con_respuestas.append(examen)

    return render(request, 'examenes_por_calificar.html', {
        'curso': curso,
        'examenes': examenes_con_respuestas
    })
    
def seleccionar_estudiante(request, slug):
    examen = get_object_or_404(Examen, slug=slug)

    # IDs de estudiantes que han respondido el examen
    estudiantes_ids = Respuesta.objects.filter(
        examen=examen
    ).values_list('estudiante', flat=True).distinct()

    # Excluir estudiantes con retroalimentación IA ya generada (estado=True)
    estudiantes_con_ia = RetroalimentacionIA.objects.filter(
        examen=examen,
        estado=True
    ).values_list('usuario_id', flat=True)

    # Filtrar solo los que aún no tienen retroalimentación IA completada
    estudiantes = User.objects.filter(
        id__in=estudiantes_ids
    ).exclude(id__in=estudiantes_con_ia)

    context = {
        'examen': examen,
        'estudiantes': estudiantes
    }
    return render(request, 'seleccionar_estudiante.html', context)
    
@login_required
def calificar_respuestas(request, slug, estudiante_id):
    
    examen = get_object_or_404(Examen, slug=slug)
    estudiante = get_object_or_404(User, id=estudiante_id)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante).select_related('pregunta')

    # Validación: si ya tiene puntaje asignado, bloquear acceso
    if respuestas.exists() and all(res.puntaje is not None for res in respuestas):
        messages.warning(request, "Este estudiante ya fue calificado para este examen.")
        return redirect('seleccionar_estudiante', slug=slug)

    if request.method == 'POST':
        for respuesta in respuestas:
            puntaje_str = request.POST.get(f'puntaje_{respuesta.id}')
            comentario = request.POST.get(f'comentario_{respuesta.id}')

            try:
                respuesta.puntaje = float(puntaje_str) if puntaje_str else None
            except ValueError:
                respuesta.puntaje = None

            respuesta.comentario = comentario
            respuesta.save()

        messages.success(request, "Calificación guardada con éxito.")
        return redirect('seleccionar_estudiante', slug=slug)
    
    return render(request, 'calificar_respuestas.html', {
        'examen': examen,
        'estudiante': estudiante,
        'respuestas': respuestas
    })
    
@login_required
@verificar_acceso_curso
def lista_retroalimentacion(request, codigo_acceso, curso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    # Recuperar exámenes evaluados por IA
    retroalimentaciones_ia = RetroalimentacionIA.objects.filter(
        usuario=request.user,
        examen__curso=curso,
        estado=True
    ).select_related('examen')

    if request.user.rol == 'Profesor':
        if curso.id_profesor != request.user:
            # Docente que no es creador → tratar como estudiante

            respuestas = Respuesta.objects.filter(
                estudiante=request.user,
                puntaje__isnull=False,
                examen__curso=curso
            ).select_related('examen')

            tiene_retro_ia = retroalimentaciones_ia.exists()
            tiene_respuestas = respuestas.exists()

            if not tiene_respuestas and not tiene_retro_ia:
                return render(request, 'retroalimentacion_lista.html', {
                    'mensaje': 'No hay retroalimentación disponible',
                    'codigo_acceso': codigo_acceso,
                    'es_docente': False
                })

            examenes = {}

            # Calificaciones manuales
            for respuesta in respuestas:
                examen = respuesta.examen
                examenes[examen] = examenes.get(examen, 0) + (respuesta.puntaje or 0)

            # Calificaciones IA
            for retro in retroalimentaciones_ia:
                examen = retro.examen
                examenes[examen] = 'IA'

            return render(request, 'retroalimentacion_lista.html', {
                'examenes': examenes,
                'codigo_acceso': codigo_acceso,
                'es_docente': False
            })

        # Si es creador, mostrar exámenes con alguna respuesta
        examenes_con_retro = Examen.objects.filter(
            respuesta__puntaje__isnull=False,
            curso=curso
        ).distinct()

        examenes_ia = Examen.objects.filter(
            retroalimentacionia__estado=True,
            retroalimentacionia__examen__curso=curso
        ).distinct()

        examenes_combinados = (examenes_con_retro | examenes_ia).distinct()

        return render(request, 'retroalimentacion_lista.html', {
            'examenes': examenes_combinados,
            'codigo_acceso': codigo_acceso,
            'es_docente': True
        })

    else:
        # Usuario estudiante
        respuestas = Respuesta.objects.filter(
            estudiante=request.user,
            puntaje__isnull=False,
            examen__curso=curso
        ).select_related('examen')

        tiene_retro_ia = retroalimentaciones_ia.exists()
        tiene_respuestas = respuestas.exists()

        if not tiene_respuestas and not tiene_retro_ia:
            return render(request, 'retroalimentacion_lista.html', {
                'mensaje': 'No hay retroalimentación disponible',
                'codigo_acceso': codigo_acceso,
                'es_docente': False
            })

        examenes = {}
        for respuesta in respuestas:
            examen = respuesta.examen
            if examen not in examenes:
                examenes[examen] = {'tipo': 'manual', 'puntaje': 0}
            examenes[examen]['puntaje'] += respuesta.puntaje or 0


        for retro in retroalimentaciones_ia:
            examen = retro.examen
            examenes[examen] = {'tipo': 'IA'}

        return render(request, 'retroalimentacion_lista.html', {
            'examenes': examenes,
            'codigo_acceso': codigo_acceso,
            'es_docente': False
        })

@login_required
def detalle_retroalimentacion(request, examen_id):
    
    respuestas = Respuesta.objects.filter(estudiante=request.user, examen_id=examen_id).select_related('pregunta')

    if not respuestas.exists():
        messages.warning(request, "No hay retroalimentación para este examen.")
        # Redirigir correctamente con el código de curso
        examen = get_object_or_404(Examen, id=examen_id)
        return redirect('lista_retroalimentacion', codigo_acceso=examen.curso.codigo_acceso)

    examen = respuestas.first().examen
    curso = examen.curso

    return render(request, 'retroalimentacion_detalle.html', {
        'respuestas': respuestas,
        'examen': examen,
        'codigo_acceso': curso.codigo_acceso
    })

@login_required
def alumnos_con_retroalimentacion(request, examen_id):
    list(get_messages(request))
    examen = get_object_or_404(Examen, id=examen_id, curso__id_profesor=request.user)

    # Obtener la suma de puntajes por estudiante
    estudiantes_con_puntaje = Respuesta.objects.filter(
        examen=examen,
        puntaje__isnull=False
    ).values(
        'estudiante__id',
        'estudiante__username',
        'estudiante__email'
    ).annotate(
        puntaje_total=Sum('puntaje')
    ).order_by('estudiante__username')

    return render(request, 'alumnos_con_retroalimentacion.html', {
        'examen': examen,
        'estudiantes': estudiantes_con_puntaje,
        'codigo_acceso': examen.curso.codigo_acceso
    })
    

@login_required
def editar_retroalimentacion(request, examen_id, estudiante_id):
    list(get_messages(request))
    
    examen = get_object_or_404(Examen, id=examen_id, curso__id_profesor=request.user)
    estudiante = get_object_or_404(User, id=estudiante_id)

    respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante).select_related('pregunta')

    if request.method == 'POST':
        total_puntaje = 0
        for respuesta in respuestas:
            comentario = request.POST.get(f'comentario_{respuesta.id}', '').strip()
            puntaje = request.POST.get(f'puntaje_{respuesta.id}')
            try:
                puntaje = float(puntaje)
            except (ValueError, TypeError):
                puntaje = 0

            respuesta.comentario = comentario
            respuesta.puntaje = puntaje
            respuesta.save()
            total_puntaje += puntaje

        messages.success(request, "Retroalimentación actualizada con éxito.")
        return redirect('alumnos_con_retroalimentacion', examen_id=examen.id)

    return render(request, 'editar_retroalimentacion.html', {
        'examen': examen,
        'estudiante': estudiante,
        'respuestas': respuestas
    })

@login_required
def eliminar_retroalimentacion(request, examen_id, estudiante_id):
    
    examen = get_object_or_404(Examen, id=examen_id, curso__id_profesor=request.user)
    estudiante = get_object_or_404(User, id=estudiante_id)

    if request.method == 'POST':
        # Eliminar solo los puntajes y comentarios, no las respuestas en sí
        respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante)
        for respuesta in respuestas:
            respuesta.puntaje = None
            respuesta.comentario = ''
            respuesta.save()

        messages.success(request, "Retroalimentación eliminada correctamente.")
        return redirect('alumnos_con_retroalimentacion', examen_id=examen.id)

    return render(request, 'eliminar_retroalimentacion.html', {
        'examen': examen,
        'estudiante': estudiante,
    })


# Cuarto sprint

@login_required
def enviar_actividad(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    # Solo el alumno que pertenece al curso puede enviar
    if request.user == curso.id_profesor:
        return redirect('dashboard')

    if Envio.objects.filter(alumno=request.user, actividad=actividad).exists():
        messages.warning(request, "Ya enviaste esta actividad.")
        return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)

    if request.method == 'POST':
        form = EnvioForm(request.POST, request.FILES)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.alumno = request.user
            envio.docente = actividad.docente
            envio.curso = curso
            envio.actividad = actividad
            envio.save()
            messages.success(request, "Actividad enviada con éxito.")
            return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    else:
        form = EnvioForm()

    return render(request, 'enviar_actividad.html', {
        'form': form,
        'actividad': actividad,
        'curso': curso,
    })


from django.utils import timezone

@login_required
def enviar_actividad(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    # Solo el alumno puede enviar
    if request.user == curso.id_profesor:
        return redirect('dashboard')

    if Envio.objects.filter(alumno=request.user, actividad=actividad).exists():
        messages.warning(request, "Ya enviaste esta actividad.")
        return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)

    # Validar la fecha limite
    ahora = timezone.now()
    if actividad.fecha_limite and not actividad.permite_entrega_tardia:
        if ahora > actividad.fecha_limite:
            messages.error(request, "La fecha límite de entrega ha pasado y no se permiten entregas tardías.")
            return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)

    if request.method == 'POST':
        form = EnvioForm(request.POST, request.FILES)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.alumno = request.user
            envio.docente = actividad.docente
            envio.curso = curso
            envio.actividad = actividad
            envio.save()
            messages.success(request, "Actividad enviada con éxito.")
            return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    else:
        form = EnvioForm()

    return render(request, 'enviar_actividad.html', {
        'form': form,
        'actividad': actividad,
        'curso': curso,
    })


@login_required
def listar_entregas(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, curso=curso, id=id_actividad)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    entregas = Envio.objects.filter(actividad=actividad)
    return render(request, 'listar_entregas.html', {
        'actividad': actividad,
        'curso': curso,
        'entregas': entregas
    })


@login_required
def calificar_entrega(request, codigo_acceso, id_envio):
    envio = get_object_or_404(Envio, id=id_envio, curso__codigo_acceso=codigo_acceso)

    if request.user != envio.docente:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=envio)
        if form.is_valid():
            form.save()
            messages.success(request, "Calificación guardada con éxito.")
            return redirect('listar_entregas', codigo_acceso=codigo_acceso, id_actividad=envio.actividad.id)
    else:
        form = CalificacionForm(instance=envio)

    return render(request, 'calificar_entrega.html', {
        'form': form,
        'envio': envio
    })


# ultimo esfuerzo compañeros

def chatgpt_form(request):
    return render(request, 'chatgpt_form.html') 

@csrf_exempt
def chatgpt_prompt(request):
    if request.method == "POST":
        prompt = request.POST.get("prompt", "")

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content
            return JsonResponse({"response": reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def evaluar_con_ia(pregunta, respuesta_texto):
    """
    Simulación de una evaluación por IA.
    Reemplaza esto con un modelo real o llamada a un servicio.
    """
    # Aquí debería ir tu lógica real de IA (por ejemplo, OpenAI o un modelo local).
    return True if "clave" in respuesta_texto.lower() else False

User = get_user_model()

def calificar_examen_IA(request, slug, estudiante_id):
    examen = get_object_or_404(Examen, slug=slug)
    estudiante = get_object_or_404(User, id=estudiante_id)

    # Verifica que solo el docente pueda calificar
    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    respuestas = Respuesta.objects.filter(
        examen=examen, estudiante=estudiante
    ).select_related('pregunta', 'opcion_seleccionada')

    if not respuestas.exists():
        messages.warning(request, "Este estudiante no ha respondido este examen.")
        return redirect('seleccionar_estudiante', slug=slug)

    preguntas_respuestas = []
    resultados_por_pregunta = []

    for r in respuestas:
        if r.respuesta_texto:
            respuesta_mostrada = r.respuesta_texto
        elif r.opcion_seleccionada:
            respuesta_mostrada = r.opcion_seleccionada.texto
        else:
            respuesta_mostrada = "Sin respuesta"

        preguntas_respuestas.append({
            'pregunta': r.pregunta,
            'respuesta': respuesta_mostrada
        })

        # --- Evaluación con IA ---
        prompt = f"""
        Pregunta del examen: {r.pregunta.texto}
        Respuesta del estudiante: {respuesta_mostrada}
        ¿Es correcta esta respuesta? Responde solo con: sí o no.
        """

        try:
            respuesta_ia = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un examinador experto. Evalúa si la respuesta es correcta."},
                    {"role": "user", "content": prompt}
                ]
            )
            decision = respuesta_ia.choices[0].message.content.strip().lower()
            es_correcta = decision.startswith("sí")
        except Exception as e:
            es_correcta = False  # En caso de error, mejor asumir incorrecto

        resultados_por_pregunta.append((r.pregunta, respuesta_mostrada, es_correcta))

    numero_de_preguntas = len(resultados_por_pregunta)
    valor_maximo_pregunta = 100 // numero_de_preguntas

    num_correctas = sum(1 for _, _, correcta in resultados_por_pregunta if correcta)
    calificacion_final = num_correctas * valor_maximo_pregunta

    # Guardar calificación global
    calificacion_global, _ = CalificacionGlobalIA.objects.update_or_create(
        examen=examen,
        usuario=estudiante,
        defaults={'calificacion_global': calificacion_final}
    )

    # Si no todas son correctas, guardar calificaciones individuales
    if num_correctas != numero_de_preguntas:
        for pregunta, _, correcta in resultados_por_pregunta:
            CalificacionPorPreguntaIA.objects.update_or_create(
                examen=examen,
                usuario=estudiante,
                pregunta=pregunta,
                calificacion_global=calificacion_global,
                defaults={
                    'calificacion_individual': valor_maximo_pregunta if correcta else 0
                }
            )
    else:
        # Si todas fueron correctas, eliminar calificaciones individuales si existían
        CalificacionPorPreguntaIA.objects.filter(
            examen=examen, usuario=estudiante
        ).delete()

    # Pasamos los resultados al template
    preguntas_resultados = [
        {
            'pregunta': pregunta,
            'respuesta': respuesta,
            'es_correcta': es_correcta
        }
        for pregunta, respuesta, es_correcta in resultados_por_pregunta
    ]

    RetroalimentacionIA.objects.update_or_create(
    usuario=estudiante,
    examen=examen,
    defaults={'estado': True,'id_calificacion_global': calificacion_global}
    )

    return render(request, 'calificar_respuestas_IA.html', {
        'examen': examen,
        'estudiante': estudiante,
        'preguntas_respuestas': preguntas_respuestas,
        'numero_de_preguntas': numero_de_preguntas,
        'valor_maximo_pregunta': valor_maximo_pregunta,
        'calificacion_global': calificacion_global,
        'preguntas_resultados': preguntas_resultados,
    })

def evaluar_respuesta_con_chatgpt(pregunta, respuesta):
    prompt = (
        f"Eres un calificador automático. Evalúa si la siguiente respuesta responde correctamente a la pregunta."
        f"\n\nPregunta: \"{pregunta}\"\nRespuesta del estudiante: \"{respuesta}\"\n\n"
        f"Responde únicamente con 'sí' si es correcta o 'no' si no lo es."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un calificador de exámenes extremadamente preciso."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        resultado = response.choices[0].message.content.strip().lower()
        return resultado.startswith("sí")
    except Exception as e:
        print("Error evaluando con IA:", str(e))
        return False  # fallback si falla la IA
    
def mostrar_resultado_calificacion_IA(request, slug, estudiante_id):
    examen = get_object_or_404(Examen, slug=slug)
    estudiante = get_object_or_404(settings.AUTH_USER_MODEL, id=estudiante_id)
    calificacion_global = get_object_or_404(CalificacionGlobalIA, examen=examen, usuario=estudiante)

    calificaciones = CalificacionPorPreguntaIA.objects.filter(
        calificacion_global=calificacion_global
    ).select_related('pregunta')

    respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante)
    respuestas_dict = {r.pregunta.id: r.respuesta_texto for r in respuestas}

    contexto = {
        'examen': examen,
        'estudiante': estudiante,
        'calificacion_global': calificacion_global,
        'calificaciones': [
            {
                'pregunta': c.pregunta,
                'calificacion_individual': c.calificacion_individual,
                'respuesta': respuestas_dict.get(c.pregunta.id, '')
            } for c in calificaciones
        ]
    }
    return render(request, 'calificar_respuestas_IA.html', contexto)


def retroalimentacion_ia_estudiante(request, examen_id):
    examen = get_object_or_404(Examen, id=examen_id)
    estudiante = request.user

    # Obtener la retroalimentacion IA para este estudiante y examen
    retro = RetroalimentacionIA.objects.filter(usuario=estudiante, examen=examen).select_related('id_calificacion_global').first()
    if not retro or not retro.id_calificacion_global:
        messages.warning(request, "No hay calificación automática disponible para este examen.")
        return redirect('lista_retroalimentacion', codigo_acceso=examen.curso.codigo_acceso)

    calificacion_global = retro.id_calificacion_global.calificacion_global

    # Obtener todas las preguntas del examen
    preguntas = Pregunta.objects.filter(examen=examen)

    preguntas_resultados = []

    for pregunta in preguntas:
        # Obtener la respuesta del estudiante para esa pregunta
        respuesta_obj = Respuesta.objects.filter(examen=examen, estudiante=estudiante, pregunta=pregunta).first()
        if respuesta_obj:
            if respuesta_obj.respuesta_texto:
                respuesta_texto = respuesta_obj.respuesta_texto
            elif respuesta_obj.opcion_seleccionada:
                respuesta_texto = respuesta_obj.opcion_seleccionada.texto
            else:
                respuesta_texto = "Sin respuesta"
        else:
            respuesta_texto = "Sin respuesta"

        # Buscar calificacion individual IA para esta pregunta
        calificacion_individual_obj = CalificacionPorPreguntaIA.objects.filter(
            examen=examen,
            usuario=estudiante,
            pregunta=pregunta
        ).first()

        # Lógica: si tiene calificación > 0 es correcta, sino incorrecta
        es_correcta = False
        if calificacion_individual_obj:
            es_correcta = calificacion_individual_obj.calificacion_individual > 0
        else:
            # Si no existe calificación individual y calif global = 100, entonces es correcta
            if calificacion_global == 100:
                es_correcta = True

        preguntas_resultados.append({
            'pregunta': pregunta,
            'respuesta': respuesta_texto,
            'es_correcta': es_correcta
        })

    numero_de_preguntas = preguntas.count()

    return render(request, 'detalle_retroalimentacion_ia.html', {
        'examen': examen,
        'estudiante': estudiante,
        'numero_de_preguntas': numero_de_preguntas,
        'calificacion': calificacion_global,
        'preguntas_resultados': preguntas_resultados,
    })

#Cuarto Sprint
def generar_pdf_reporte(reporte):
    from django.http import HttpResponse
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    from io import BytesIO
    
    promedios_estudiantes = reporte.obtener_promedios_estudiantes()
    
    total_estudiantes = len(promedios_estudiantes)
    if total_estudiantes > 0:
        promedio_general = sum(datos['promedio'] for datos in promedios_estudiantes) / total_estudiantes
        aprobados = len([datos for datos in promedios_estudiantes if datos['promedio'] >= 70])
        en_riesgo = len([datos for datos in promedios_estudiantes if 60 <= datos['promedio'] < 70])
        reprobados = len([datos for datos in promedios_estudiantes if datos['promedio'] < 60])
    else:
        promedio_general = 0
        aprobados = en_riesgo = reprobados = 0
    
    #Contexto para el template
    contexto = {
        'reporte' : reporte,
        'promedios_estudiantes' : promedios_estudiantes,
        'total_estudiantes' : total_estudiantes,
        'promedio_general' : round(promedio_general, 2),
        'aprobados' : aprobados,
        'en_riesgo' : en_riesgo,
        'reprobados' : reprobados,
    }
    
    plantilla = get_template('reporte_pdf.html')
    html = plantilla.render(contexto)
    
    #Crear el PDF
    resultado = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), resultado)
    
    if not pdf.err:
        #Configurar la respuesta HTTP
        respuesta = HttpResponse(resultado.getvalue(), content_type='application/pdf')
        nombre_archivo = f"reporte_{reporte.curso.nombre_curso}_{reporte.fecha_inicio}_{reporte.fecha_fin}.pdf"
        respuesta['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        return respuesta
    
    return None

@login_required
def crear_reporte_rendimiento(request):
    """Vista para crear un nuevo reporte de rendimiento"""
    if request.method == 'POST':
        formulario = FormularioReporteRendimiento(request.user, request.POST)
        if formulario.is_valid():
            reporte = formulario.save(commit=False)
            reporte.docente = request.user
            reporte.save()
            messages.success(request, "Reporte creado con éxito")
            return redirect('reportes_curso', codigo_acceso=reporte.curso.codigo_acceso)
        else:
            messages.error(request, "Error al generar el reporte, intenta de nuevo")
    else:
        formulario = FormularioReporteRendimiento(request.user)
    
    return render(request, 'reporte_crear.html', {'formulario': formulario})


@login_required
@verificar_acceso_curso
def reportes_curso(request, codigo_acceso, curso):
    if request.user != curso.id_profesor:
        raise PermissionDenied("Solo el docente puede ver los reportes")
    
    reportes = ReporteRendimiento.objects.filter(curso = curso)
    
    return render(request, 'reporte_lista.html', {
        'curso': curso,
        'reportes': reportes
    })
    
@login_required
def detalle_reporte(request, id_reporte):
    reporte = get_object_or_404(ReporteRendimiento, id = id_reporte)
    
    #Verificar que el usuario sea el docente del curso
    if reporte.curso.id_profesor != request.user:
        raise PermissionDenied("No tienes permiso para ver este reporte")
    
    promedios_estudiantes = reporte.obtener_promedios_estudiantes()
    
    return render(request, 'reporte_detalle.html', {
        'reporte': reporte,
        'promedios_estudiantes': promedios_estudiantes
    })
    
@login_required
def eliminar_reporte(request, id_reporte):
    reporte = get_object_or_404(ReporteRendimiento, id=id_reporte)
    
    if reporte.curso.id_profesor != request.user:
        raise PermissionDenied("No tienes permiso para eliminar este reporte")
    
    if request.method == 'POST':
        codigo_acceso = reporte.curso.codigo_acceso
        try:
            reporte.delete()
            messages.success(request, "Reporte eliminado con éxito")
        except Exception:
            messages.error(request, "Error al eliminar el reporte, intenta de nuevo")
            
        return redirect('reportes_curso', codigo_acceso = codigo_acceso)
    
    return render(request, 'reporte_eliminar.html', {'reporte' : reporte})

@login_required
def descargar_pdf_reporte(request, id_reporte):
    reporte = get_object_or_404(ReporteRendimiento, id=id_reporte)
    
    if reporte.curso.id_profesor != request.user:
        raise PermissionDenied("No tienes permiso para descargar este reporte")
    
    try:
        respuesta_pdf = generar_pdf_reporte(reporte)
        if respuesta_pdf:
            return respuesta_pdf
        else:
            messages.error(request, "Error al generar el PDF, intenta de nuevo")
    except Exception as e:
        messages.error(request, "Error al generar el PDF, intenta de nuevo")
        
    return redirect('detalle_reporte', id_reporte=id_reporte)


def generar_calificacion_con_ia(contenido_codigo, lenguaje, criterios, puntaje_maximo, instrucciones_adicionales):
    """Función para generar calificación de código usando OpenAI (respuesta en texto plano)"""
    try:
        prompt = f"""
        Eres un evaluador experto de código de programación. Debes evaluar el siguiente código en {lenguaje} según los criterios proporcionados.

        CRITERIOS DE EVALUACIÓN:
        {criterios}

        PUNTAJE MÁXIMO: {puntaje_maximo}

        INSTRUCCIONES ADICIONALES:
        {instrucciones_adicionales}

        CÓDIGO A EVALUAR:
        ```{lenguaje}
        {contenido_codigo}
        ```

        Por favor, proporciona:
        1. Una calificación numérica (0 a {puntaje_maximo})
        2. Retroalimentación detallada explicando la calificación, incluyendo:
           - Análisis de funcionalidad
           - Análisis de eficiencia y complejidad
           - Análisis de estilo y buenas prácticas
           - Sugerencias específicas de mejora
        3. Ejemplos de cómo mejorar el código si es necesario

        Responde en formato de texto plano, claro y estructurado.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un evaluador experto de código de programación que proporciona calificaciones justas y retroalimentación constructiva."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        resultado_texto = response.choices[0].message.content
        return {
            'respuesta': resultado_texto
        }

    except Exception as e:
        raise Exception(f"Error al generar calificación con IA: {str(e)}")


def extraer_texto_codigo(ruta_archivo):
    """Función para extraer código de archivos comunes de programación"""
    try:
        # Primero intentamos leer como texto plano (para archivos de código)
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            return archivo.read()
    except UnicodeDecodeError:
        # Si falla, intentamos con PyPDF2 para PDFs
        try:
            import PyPDF2
            with open(ruta_archivo, 'rb') as archivo:
                lector = PyPDF2.PdfReader(archivo)
                texto = ""
                for pagina in lector.pages:
                    texto += pagina.extract_text()
                return texto
        except Exception:
            # Si todo falla, devolver mensaje por defecto
            return "No se pudo extraer el código del archivo. Verifica el formato."
        
@login_required
@docente_curso_requerido
def procesar_calificacion_ia(request, codigo_acceso, id_actividad):
    """Procesar calificación automática de código por IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso, generado_por_ia=True)
    
    # Verificar si existen criterios de calificación
    criterio_ia = getattr(actividad, 'criterio_ia', None)
    if not criterio_ia:
        messages.error(request, "Esta actividad no tiene criterios de calificación por IA configurados.")
        return redirect('configurar_criterios_ia', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    
    # Obtener entregas sin calificar
    entregas_pendientes = Envio.objects.filter(
        actividad=actividad,
        calificacion__isnull=True,
        calificacion_ia__isnull=True
    )
    
    if not entregas_pendientes.exists():
        messages.info(request, "No hay entregas pendientes de calificar para esta actividad.")
        return redirect('calificar_actividades_ia', codigo_acceso=codigo_acceso)
    
    if request.method == 'POST':
        calificaciones_exitosas = 0
        calificaciones_fallidas = 0
        
        for envio in entregas_pendientes:
            try:
                # Leer el contenido del archivo de código
                contenido_codigo = extraer_texto_codigo(envio.archivo.path)
                
                # Generar calificación con IA
                resultado_ia = generar_calificacion_con_ia(
                    contenido_codigo,
                    criterio_ia.lenguaje_programacion,
                    criterio_ia.criterios_evaluacion,
                    criterio_ia.puntaje_maximo,
                    criterio_ia.instrucciones_adicionales
                )

                # Extraer calificación y retroalimentación del texto de la IA
                respuesta_ia = resultado_ia.get('respuesta', '')
                import re
                match = re.search(r'calificación numérica.*?(\d+(\.\d+)?)', respuesta_ia, re.IGNORECASE)
                calificacion = float(match.group(1)) if match else None
                retroalimentacion = respuesta_ia

                # Guardar calificación de IA
                CalificacionIA.objects.create(
                    envio=envio,
                    calificacion_sugerida=calificacion,
                    retroalimentacion_ia=retroalimentacion,
                    criterios_utilizados=criterio_ia.criterios_evaluacion
                )

                calificaciones_exitosas += 1
                
            except Exception as e:
                calificaciones_fallidas += 1
                print(f"Error al calificar envío {envio.id}: {str(e)}")
        
        if calificaciones_exitosas > 0:
            messages.success(
                request, 
                f"Se procesaron {calificaciones_exitosas} entregas de código con IA. "
                f"Revisa las calificaciones sugeridas antes de confirmarlas."
            )
        
        if calificaciones_fallidas > 0:
            messages.warning(
                request, 
                f"{calificaciones_fallidas} entregas no pudieron ser procesadas."
            )
        
        return redirect('revisar_calificaciones_ia', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    
    return render(request, 'procesar_calificacion_ia.html', {
        'curso': curso,
        'actividad': actividad,
        'entregas_pendientes': entregas_pendientes,
        'criterio_ia': criterio_ia
    })
    
@login_required
@docente_curso_requerido
def actividades_calificables_ia(request, codigo_acceso):
    """Vista para mostrar actividades que pueden ser calificadas con IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    
    # Obtener actividades de código con envíos pendientes de calificar
    actividades = Actividad.objects.filter(
        curso=curso,
        generado_por_ia=True
    ).annotate(
        total_envios=Count('envio'),
        envios_pendientes=Count('envio', filter=models.Q(envio__calificacion__isnull=True))
    ).filter(envios_pendientes__gt=0)
    
    actividades_con_envios = []
    for actividad in actividades:
        # Verificar si tiene criterios de IA configurados
        tiene_criterios = hasattr(actividad, 'criterio_ia')
        
        # Solo incluir actividades con criterios configurados
        if tiene_criterios:
            actividades_con_envios.append({
                'actividad': actividad,
                'envios_pendientes': actividad.envios_pendientes
            })
    
    return render(request, 'calificar_ia/actividades_calificables.html', {
        'curso': curso,
        'actividades_con_envios': actividades_con_envios
    })

@login_required
@docente_curso_requerido
def envios_por_calificar_ia(request, codigo_acceso, id_actividad):
    """Vista para mostrar envíos pendientes de calificar para una actividad"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso, generado_por_ia=True)
    
    # Verificar si tiene criterios de IA configurados
    if not hasattr(actividad, 'criterio_ia'):
        messages.warning(request, "Esta actividad no tiene criterios de calificación por IA configurados.")
        return redirect('configurar_criterios_ia', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    
    # Obtener envíos pendientes de calificar
    envios = Envio.objects.filter(
        actividad=actividad,
        calificacion__isnull=True,
        calificacion_ia__isnull=True
    ).select_related('alumno')
    
    return render(request, 'calificar_ia/envios_por_calificar.html', {
        'curso': curso,
        'actividad': actividad,
        'envios': envios
    })

@login_required
@docente_curso_requerido
def calificar_envio_ia(request, codigo_acceso, id_envio):
    """Vista para calificar un envío individual con IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    envio = get_object_or_404(Envio, id=id_envio, curso=curso, calificacion__isnull=True)
    actividad = envio.actividad
    
    # Verificar si la actividad es calificable por IA
    if not actividad.generado_por_ia:
        messages.error(request, "Esta actividad no está configurada para calificación con IA.")
        return redirect('listar_entregas', codigo_acceso=codigo_acceso, id_actividad=actividad.id)
    
    # Verificar si tiene criterios de IA configurados
    if not hasattr(actividad, 'criterio_ia'):
        messages.warning(request, "Esta actividad no tiene criterios de calificación por IA configurados.")
        return redirect('configurar_criterios_ia', codigo_acceso=codigo_acceso, id_actividad=actividad.id)
    
    criterio_ia = actividad.criterio_ia
    
    if request.method == 'POST':
        form = ConfirmarCalificacionIAForm(request.POST)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            
            if accion == 'confirmar':
                try:
                    # Extraer el contenido del código
                    contenido_codigo = extraer_texto_codigo(envio.archivo.path)
                    
                    # Generar calificación con IA
                    resultado_ia = generar_calificacion_con_ia(
                        contenido_codigo,
                        criterio_ia.lenguaje_programacion,
                        criterio_ia.criterios_evaluacion,
                        criterio_ia.puntaje_maximo,
                        criterio_ia.instrucciones_adicionales
                    )
                    
                    # Guardar calificación de IA
                    calificacion_ia = CalificacionIA.objects.create(
                        envio=envio,
                        calificacion_sugerida=resultado_ia['calificacion'],
                        retroalimentacion_ia=resultado_ia['retroalimentacion'],
                        criterios_utilizados=criterio_ia.criterios_evaluacion,
                        confirmada_por_docente=True,
                        fecha_confirmacion=timezone.now()
                    )
                    
                    # Asignar calificación al envío
                    envio.calificacion = resultado_ia['calificacion']
                    envio.save()
                    
                    messages.success(request, "Calificación con IA aplicada correctamente.")
                    return redirect('envios_por_calificar_ia', codigo_acceso=codigo_acceso, id_actividad=actividad.id)
                    
                except Exception as e:
                    messages.error(request, f"Error al calificar con IA: {str(e)}")
            
            elif accion == 'revisar':
                # Redirigir a calificación manual
                return redirect('calificar_entrega', codigo_acceso=codigo_acceso, id_envio=envio.id)
    else:
        form = ConfirmarCalificacionIAForm()
        
        try:
            # Extraer el contenido del código
            contenido_codigo = extraer_texto_codigo(envio.archivo.path)
            
            # Generar calificación con IA (solo para mostrar)
            resultado_ia = generar_calificacion_con_ia(
                contenido_codigo,
                criterio_ia.lenguaje_programacion,
                criterio_ia.criterios_evaluacion,
                criterio_ia.puntaje_maximo,
                criterio_ia.instrucciones_adicionales
            )
            
            calificacion_ia = resultado_ia['calificacion']
            retroalimentacion_ia = resultado_ia['retroalimentacion']
            
        except Exception as e:
            calificacion_ia = None
            retroalimentacion_ia = f"Error al generar calificación: {str(e)}"
    
    return render(request, 'calificar_ia/calificar_envio_ia.html', {
        'curso': curso,
        'actividad': actividad,
        'envio': envio,
        'form': form,
        'calificacion_ia': calificacion_ia,
        'retroalimentacion_ia': retroalimentacion_ia
    })

@login_required
@docente_curso_requerido
def calificar_todos_ia(request, codigo_acceso, id_actividad):
    """Vista para calificar todos los envíos de una actividad con IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso, generado_por_ia=True)
    
    # Verificar si tiene criterios de IA configurados
    if not hasattr(actividad, 'criterio_ia'):
        messages.warning(request, "Esta actividad no tiene criterios de calificación por IA configurados.")
        return redirect('configurar_criterios_ia', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    
    # Obtener envíos pendientes de calificar
    envios = Envio.objects.filter(
        actividad=actividad,
        calificacion__isnull=True,
        calificacion_ia__isnull=True
    )
    
    cantidad_envios = envios.count()
    
    if cantidad_envios == 0:
        messages.info(request, "No hay envíos pendientes para calificar.")
        return redirect('envios_por_calificar_ia', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    
    if request.method == 'POST':
        criterio_ia = actividad.criterio_ia
        calificaciones_exitosas = 0
        calificaciones_fallidas = 0
        
        for envio in envios:
            try:
                # Extraer el contenido del código
                contenido_codigo = extraer_texto_codigo(envio.archivo.path)
                
                # Generar calificación con IA
                resultado_ia = generar_calificacion_con_ia(
                    contenido_codigo,
                    criterio_ia.lenguaje_programacion,
                    criterio_ia.criterios_evaluacion,
                    criterio_ia.puntaje_maximo,
                    criterio_ia.instrucciones_adicionales
                )
                
                # Guardar calificación de IA
                calificacion_ia = CalificacionIA.objects.create(
                    envio=envio,
                    calificacion_sugerida=resultado_ia['calificacion'],
                    retroalimentacion_ia=resultado_ia['retroalimentacion'],
                    criterios_utilizados=criterio_ia.criterios_evaluacion,
                    confirmada_por_docente=True,
                    fecha_confirmacion=timezone.now()
                )
                
                # Asignar calificación al envío
                envio.calificacion = resultado_ia['calificacion']
                envio.save()
                
                calificaciones_exitosas += 1
                
            except Exception as e:
                calificaciones_fallidas += 1
                print(f"Error al calificar envío {envio.id}: {str(e)}")
        
        if calificaciones_exitosas > 0:
            messages.success(
                request, 
                f"Se calificaron {calificaciones_exitosas} envíos con IA correctamente."
            )
        
        if calificaciones_fallidas > 0:
            messages.warning(
                request, 
                f"{calificaciones_fallidas} envíos no pudieron ser calificados."
            )
        
        return redirect('envios_por_calificar_ia', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    
    return render(request, 'calificar_ia/confirmar_calificar_todos.html', {
        'curso': curso,
        'actividad': actividad,
        'cantidad_envios': cantidad_envios
    })

@login_required
@docente_curso_requerido
def calificar_actividades_ia(request, codigo_acceso):
    """Vista principal para mostrar todas las actividades que pueden ser calificadas con IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    
    # Obtener TODAS las actividades entregables del curso
    actividades = Actividad.objects.filter(
        curso=curso,
        entregable=True
    ).order_by('-fecha')
    
    actividades_con_datos = []
    for actividad in actividades:
        # Contar envíos totales
        total_envios = Envio.objects.filter(actividad=actividad).count()
        
        # Contar envíos pendientes de calificar
        envios_pendientes = Envio.objects.filter(
            actividad=actividad,
            calificacion__isnull=True
        ).count()
        
        # Contar envíos ya calificados
        envios_calificados = Envio.objects.filter(
            actividad=actividad,
            calificacion__isnull=False
        ).count()
        
        # Contar calificaciones de IA pendientes de revisar
        calificaciones_pendientes = CalificacionIA.objects.filter(
            envio__actividad=actividad,
            confirmada_por_docente=False
        ).count()
        
        # Verificar si tiene criterios de IA configurados
        tiene_criterios = hasattr(actividad, 'criterio_ia')
        
        # Determinar si es calificable por IA
        es_calificable_ia = actividad.generado_por_ia or tiene_criterios
        
        actividades_con_datos.append({
            'actividad': actividad,
            'total_envios': total_envios,
            'envios_pendientes': envios_pendientes,
            'envios_calificados': envios_calificados,
            'calificaciones_pendientes': calificaciones_pendientes,
            'tiene_criterios': tiene_criterios,
            'es_calificable_ia': es_calificable_ia,
            'puede_configurar_ia': not es_calificable_ia,  # Puede configurar IA si no está configurada
        })
    
    return render(request, 'lista_actividades_ia.html', {
        'curso': curso,
        'actividades_con_datos': actividades_con_datos
    })

@login_required
@docente_curso_requerido
def revisar_calificaciones_ia(request, codigo_acceso, id_actividad):
    """Vista para revisar calificaciones generadas por IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    # Obtener calificaciones de IA pendientes de revisar
    calificaciones_ia = CalificacionIA.objects.filter(
        envio__actividad=actividad,
        confirmada_por_docente=False
    ).select_related('envio__alumno')

    # Convertir retroalimentación IA (JSON o texto) en formato HTML legible
    for calificacion in calificaciones_ia:
        retro = calificacion.retroalimentacion_ia
        try:
            data = json.loads(retro)
            texto = format_html("<br>".join(
                f"<strong>{k}:</strong> {v}" for k, v in data.items()
            ))
            calificacion.retroalimentacion_ia = texto
        except json.JSONDecodeError:
            # Si no es JSON válido, mostrar el texto como está
            calificacion.retroalimentacion_ia = retro

    return render(request, 'revisar_calificaciones_ia.html', {
        'curso': curso,
        'actividad': actividad,
        'calificaciones_ia': calificaciones_ia
    })

@login_required
@docente_curso_requerido
def confirmar_calificacion_individual(request, codigo_acceso, id_calificacion_ia):
    """Vista para confirmar una calificación individual de IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    calificacion_ia = get_object_or_404(
        CalificacionIA, 
        id=id_calificacion_ia,
        envio__curso=curso,
        confirmada_por_docente=False
    )
    
    if request.method == 'POST':
        form = ConfirmarCalificacionIAForm(request.POST)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            calificacion_ajustada = form.cleaned_data.get('calificacion_ajustada')
            comentarios_docente = form.cleaned_data.get('comentarios_docente', '')
            
            if accion == 'confirmar':
                # Confirmar la calificación de IA
                calificacion_final = calificacion_ajustada if calificacion_ajustada else calificacion_ia.calificacion_sugerida
                
                # Actualizar el envío con la calificación final
                envio = calificacion_ia.envio
                envio.calificacion = calificacion_final
                envio.save()
                
                # Marcar como confirmada
                calificacion_ia.confirmada_por_docente = True
                calificacion_ia.fecha_confirmacion = timezone.now()
                calificacion_ia.save()
                
                # Si hay comentarios del docente, agregarlos
                if comentarios_docente:
                    calificacion_ia.retroalimentacion_ia += f"\n\nComentarios del docente:\n{comentarios_docente}"
                    calificacion_ia.save()
                
                messages.success(request, "Calificación confirmada correctamente.")
                
            elif accion == 'revisar':
                # Redirigir a calificación manual
                return redirect('calificar_entrega', 
                              codigo_acceso=codigo_acceso, 
                              id_envio=calificacion_ia.envio.id)
            
            return redirect('revisar_calificaciones_ia', 
                          codigo_acceso=codigo_acceso, 
                          id_actividad=calificacion_ia.envio.actividad.id)
    else:
        form = ConfirmarCalificacionIAForm()
    
    return render(request, 'confirmar_calificacion_individual.html', {
        'curso': curso,
        'calificacion_ia': calificacion_ia,
        'form': form
    })

@login_required
@docente_curso_requerido
def configurar_criterios_ia(request, codigo_acceso, id_actividad):
    """Vista para configurar criterios de calificación por IA"""
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)
    
    # Verificar si ya existen criterios
    criterio_ia = getattr(actividad, 'criterio_ia', None)
    
    if request.method == 'POST':
        if criterio_ia:
            form = CriterioCalificacionIAForm(request.POST, instance=criterio_ia)
        else:
            form = CriterioCalificacionIAForm(request.POST)
        
        if form.is_valid():
            criterio = form.save(commit=False)
            criterio.actividad = actividad
            criterio.save()
            
            # Marcar la actividad como generada por IA si no lo está
            if not actividad.generado_por_ia:
                actividad.generado_por_ia = True
                actividad.save()
            
            messages.success(request, "Criterios de calificación por IA configurados correctamente.")
            return redirect('calificar_actividades_ia', codigo_acceso=codigo_acceso)
    else:
        if criterio_ia:
            form = CriterioCalificacionIAForm(instance=criterio_ia)
        else:
            form = CriterioCalificacionIAForm()
    
    return render(request, 'configurar_criterios_ia.html', {
        'curso': curso,
        'actividad': actividad,
        'form': form,
        'editando': criterio_ia is not None
    })

@login_required
def crear_examen_ia(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.method == "POST":
        form = CrearExamenIAForm(request.POST)
        if form.is_valid():
            tema = form.cleaned_data['tema']
            num_preguntas = form.cleaned_data['numero_preguntas']
            dificultad = form.cleaned_data['dificultad']
            tipos = form.cleaned_data['tipos']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']

            instrucciones = []
            if 'opcion_multiple' in tipos:
                instrucciones.append(
                    "Algunas preguntas deben ser de opción múltiple con 1 respuesta correcta y 3 incorrectas. "
                    "Formato:\nPREGUNTA: ...\nOPCIONES:\nA. ...\nB. ...\nC. ...\nD. ...\nRESPUESTA CORRECTA: <Letra>"
                )
            if 'verdadero_falso' in tipos:
                instrucciones.append(
                    "Algunas preguntas deben ser de verdadero o falso. "
                    "Formato:\nPREGUNTA: ...\nTIPO: verdadero_falso\nRESPUESTA CORRECTA: Verdadero/Falso"
                )
            if 'abierta' in tipos:
                instrucciones.append(
                    "Algunas preguntas deben ser de respuesta abierta. "
                    "Formato:\nPREGUNTA: ...\nTIPO: abierta\nRESPUESTA ESPERADA: ..."
                )

            prompt = f"""Genera {num_preguntas} preguntas mezclando los siguientes tipos: {', '.join(tipos)}.
Tema: "{tema}", Dificultad: "{dificultad}".
Sigue los siguientes formatos de ejemplo:
{chr(10).join(instrucciones)}
"""

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un generador de exámenes útil."},
                        {"role": "user", "content": prompt}
                    ]
                )
                contenido = response.choices[0].message.content
                request.session['examen_ia'] = {
                    'contenido': contenido,
                    'tema': tema,
                    'num_preguntas': num_preguntas,
                    'dificultad': dificultad,
                    'curso_id': curso.id,
                    'fecha_inicio': str(form.cleaned_data['fecha_inicio']),
                    'fecha_fin': str(form.cleaned_data['fecha_fin']),
                }
                return redirect('vista_previa_examen_ia', codigo_acceso=curso.codigo_acceso)

            except Exception as e:
                return render(request, "crear_examen_ia.html", {
                    "form": form,
                    "error": f"Error al generar el examen: {str(e)}"
                })

    else:
        form = CrearExamenIAForm()

    return render(request, "crear_examen_ia.html", {"form": form, "curso": curso})


@login_required
def vista_previa_examen_ia(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    examen_data = request.session.get('examen_ia')
    if not examen_data:
        return redirect('dashboard')

    # Esta línea debe estar fuera del if, porque se usa tanto en GET como en POST
    bloques = examen_data['contenido'].split("PREGUNTA:")
    bloques = [b.strip() for b in bloques if b.strip()]  # eliminar cadenas vacías

    if request.method == "POST":
        curso = get_object_or_404(Curso, id=examen_data['curso_id'])
        examen = Examen.objects.create(
            titulo=f"Examen generado por IA - {examen_data['tema']}",
            descripcion=f"{examen_data['num_preguntas']} preguntas, dificultad {examen_data['dificultad']}",
            curso=curso,
            creado_por=request.user,
            fecha_inicio=date.fromisoformat(examen_data['fecha_inicio']),
            fecha_fin=date.fromisoformat(examen_data['fecha_fin']),
        )

        for bloque in bloques:
            if "TIPO: verdadero_falso" in bloque:
                texto = bloque.split("TIPO:")[0].strip()
                respuesta = bloque.split("RESPUESTA CORRECTA:")[1].strip()
                p = Pregunta.objects.create(examen=examen, texto=texto, tipo="verdadero_falso")
                Opcion.objects.create(pregunta=p, texto="Verdadero", es_correcta=(respuesta.lower() == "verdadero"))
                Opcion.objects.create(pregunta=p, texto="Falso", es_correcta=(respuesta.lower() == "falso"))

            elif "TIPO: abierta" in bloque or "RESPUESTA ESPERADA:" in bloque:
                texto = bloque.split("TIPO:")[0].strip() if "TIPO:" in bloque else bloque.split("RESPUESTA ESPERADA:")[0].strip()
                Pregunta.objects.create(examen=examen, texto=texto, tipo="abierta")

            elif "OPCIONES:" in bloque and "RESPUESTA CORRECTA:" in bloque:
                partes = bloque.split("OPCIONES:")
                texto = partes[0].strip()
                opciones_y_resp = partes[1].split("RESPUESTA CORRECTA:")
                opciones = opciones_y_resp[0].strip().split("\n")
                letra_correcta = opciones_y_resp[1].strip()

                p = Pregunta.objects.create(examen=examen, texto=texto, tipo="opcion_multiple")

                for opcion in opciones:
                    if len(opcion) < 3:
                        continue
                    letra = opcion[:1]
                    texto_opcion = opcion[3:].strip()
                    Opcion.objects.create(
                        pregunta=p,
                        texto=texto_opcion,
                        es_correcta=(letra.upper() == letra_correcta.upper())
                    )

        messages.success(request, "Examen creado por IA con éxito.")
        del request.session['examen_ia']
        return redirect('listar_preguntas', slug=examen.slug)

    return render(request, "vista_previa_examen_ia.html", {
        "contenido": examen_data['contenido'],
        "bloques": bloques,
        "codigo_acceso": curso.codigo_acceso,
    })