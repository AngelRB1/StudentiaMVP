from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioPersonalizado, Curso, Reporte, Actividad, Examen, Pregunta, Opcion, Envio, ReporteRendimiento, CriterioCalificacionIA
from django.forms import modelformset_factory, inlineformset_factory
from django.forms.models import inlineformset_factory
from django.utils.timezone import localtime


class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'type': 'email', 'placeholder': 'Ingresa tu correo electrónico'})
    )

    class Meta:
        model = UsuarioPersonalizado
        fields = ('username', 'email', 'rol', 'sobre_mi', 'foto_perfil', 'password1', 'password2')

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = UsuarioPersonalizado
        fields = ('username', 'email', 'rol', 'sobre_mi', 'foto_perfil')

        widgets = {
            'username': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'sobre_mi': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-control'
            }),

        }

        help_texts = {
            'username': '',
            'foto_perfil': '',
            'email': '',
        }


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre_curso', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

class InscripcionCursoForm(forms.Form):
    codigo_acceso = forms.CharField(label="Código de Curso", max_length=10, required=True)

    class Meta:
        fields = ['codigo_acceso']
        widgets = {
            'codigo_acceso': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }


class ReportarForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe el motivo del reporte',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motivo'].required = False

    def clean_motivo(self):
        motivo = self.cleaned_data.get('motivo', '').strip()
        if not motivo:
            raise forms.ValidationError("Por favor, ingrese el motivo del reporte.")
        return motivo

   

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'contenido', 'archivo', 'entregable', 'generado_por_ia', 'permite_entrega_tardia', 'fecha_limite']
        widgets = {
            'fecha_limite': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si hay una fecha límite, convertirla a hora local y formato correcto
        if self.instance and self.instance.fecha_limite:
            local_fecha = localtime(self.instance.fecha_limite)
            self.initial['fecha_limite'] = local_fecha.strftime('%Y-%m-%dT%H:%M')

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['titulo', 'descripcion', 'fecha_inicio', 'fecha_fin', 'entregas_tardias']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio:
                self.initial['fecha_inicio'] = self.instance.fecha_inicio.strftime('%Y-%m-%d')
            if self.instance.fecha_fin:
                self.initial['fecha_fin'] = self.instance.fecha_fin.strftime('%Y-%m-%d')

class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['texto', 'tipo']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }

OpcionFormSet = inlineformset_factory(
    Pregunta,
    Opcion,
    fields=['texto', 'es_correcta'],
    extra=2,
    can_delete=True
)

class OpcionForm(forms.ModelForm):
    class Meta:
        model = Opcion
        fields = ['texto', 'es_correcta']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 2, 'cols': 30}),
        }

class VerdaderoFalsoForm(forms.Form):
    respuesta = forms.ChoiceField(
        choices=[('verdadero', 'Verdadero'), ('falso', 'Falso')],
        widget=forms.RadioSelect,
        label="Respuesta correcta"
    )
    

class EnvioForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['archivo']
        widgets = {
            'archivo': forms.ClearableFileInput(attrs={'accept': 'application/pdf'}),
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            raise forms.ValidationError("Por favor, seleccione un archivo.")
        if not archivo.name.endswith('.pdf'):
            raise forms.ValidationError("Solo se permiten archivos PDF.")
        return archivo
    
class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Envio
        fields = ['calificacion']
        widgets = {
            'calificacion': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

#Cuarto Sprint
class FormularioReporteRendimiento(forms.ModelForm):
    class Meta:
        model = ReporteRendimiento
        fields = ['titulo', 'curso', 'fecha_inicio', 'fecha_fin']
        labels = {
            'titulo': 'Título del Reporte',
            'curso': 'Curso',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
        }
        
        
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'placeholder': 'Seleccione fecha de inicio'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'placeholder': 'Seleccione fecha de fin'
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Reporte Primer Trimestre'
            }),
            'curso': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        
    def __init__(self, usuario, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar cursos del docente actual
        self.fields['curso'].queryset = Curso.objects.filter(id_profesor=usuario)
        
    def clean(self):
        datos_limpios = super().clean()
        fecha_inicio = datos_limpios.get('fecha_inicio')
        fecha_fin = datos_limpios.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise forms.ValidationError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        return datos_limpios


class CriterioCalificacionIAForm(forms.ModelForm):
    class Meta:
        model = CriterioCalificacionIA
        fields = ['lenguaje_programacion', 'criterios_evaluacion', 'puntaje_maximo', 'instrucciones_adicionales']
        widgets = {
            'lenguaje_programacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Python, Java, JavaScript, C++, etc.'
            }),
            'criterios_evaluacion': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Ej: Funcionalidad (40%), Eficiencia (20%), Estilo de código (20%), Documentación (20%)'
            }),
            'puntaje_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'step': 0.01
            }),
            'instrucciones_adicionales': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Instrucciones adicionales para la IA sobre cómo evaluar el código...'
            })
        }
        labels = {
            'lenguaje_programacion': 'Lenguaje de Programación',
            'criterios_evaluacion': 'Criterios de Evaluación',
            'puntaje_maximo': 'Puntaje Máximo',
            'instrucciones_adicionales': 'Instrucciones Adicionales'
        }

class ConfirmarCalificacionIAForm(forms.Form):
    """Formulario para confirmar o rechazar calificación de IA"""
    OPCIONES = [
        ('confirmar', 'Confirmar Calificación'),
        ('revisar', 'Revisar Manualmente')
    ]
    
    accion = forms.ChoiceField(
        choices=OPCIONES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="¿Qué deseas hacer con esta calificación?"
    )
    
    calificacion_ajustada = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0,
            'max': 100,
            'step': 0.01
        }),
        label="Calificación Ajustada (opcional)"
    )
    
    comentarios_docente = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Comentarios adicionales sobre el código...'
        }),
        required=False,
        label="Comentarios del Docente"
    )


class CrearExamenIAForm(forms.Form):
    tema = forms.CharField(max_length=100, label="Temas del examen")
    numero_preguntas = forms.IntegerField(min_value=1, label="Numero de preguntas")
    dificultad = forms.ChoiceField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta')])
    tipos = forms.MultipleChoiceField(
        choices=[('opcion_multiple', 'Opción Múltiple'), ('verdadero_falso', 'Verdadero/Falso'), ('abierta', 'Abierta')],
        widget=forms.CheckboxSelectMultiple, label="Tipos de pregunta"
    )
    fecha_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise forms.ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
