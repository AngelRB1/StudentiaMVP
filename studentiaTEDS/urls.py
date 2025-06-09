from django.urls import path, include
from django.contrib import admin
from general import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from general.views import CustomPasswordResetView, CustomPasswordResetConfirmView, chatgpt_prompt

urlpatterns = [
    #primer sprint
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('login/', views.iniciar_sesion, name="iniciar_sesion"),
    path('logout/', views.salir, name='salir'),
    path('signup/', views.registrar_usuario, name="registrar_usuario"),
    path('recovery/send/', auth_views.PasswordResetDoneView.as_view(template_name='recovery/password_reset_done.html'), name='password_reset_done'),
    path('recovery/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='recovery/password_reset_complete.html'), name='password_reset_complete'),
    path('recovery/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('recovery/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    #segundo sprint
    path('profile/', views.ver_perfil, name='ver_perfil'),
    path('profile/edit', views.editar_perfil, name='editar_perfil'),
    path('new/course', views.crear_curso, name='crear_curso'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("course/join", views.inscribirse_curso, name="inscribirse_curso"),
    path("board/<str:codigo_acceso>", views.board, name="board"),
    path("board/<str:codigo_acceso>/leave", views.board_leave, name="board_leave"),
    path("board/<str:codigo_acceso>/delete", views.board_borrar, name="board_borrar"),
    path("board/<str:codigo_acceso>/update", views.board_actualizar, name="board_actualizar"),
    path("board/<str:codigo_acceso>/view/students", views.board_view_students, name="board_view_students"),
    path("board/<str:codigo_acceso>/remove/<int:id_alumno>", views.board_remove_student, name="board_remove_student"),
    path('profile/view/<int:id>', views.other_profile, name='other_profile'),
    path('report/student/<int:id>', views.report, name="report"),
    path('report/student/success', views.report_success, name="report_success"),
    path("board/<str:codigo_acceso>/add/content", views.board_add_content, name="board_add_content"),
    path("board/<str:codigo_acceso>/actividad/<int:id_actividad>/edit", views.content_edit, name="content_edit"),
    path("board/<str:codigo_acceso>/actividad/<int:id_actividad>/delete", views.content_delete, name="content_delete"),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/view', views.content_detail, name='content_detail'),
    
    #Tercer sprint 
    path('board/<str:codigo_acceso>/add/examen/', views.crear_examen, name='crear_examen'),
    path('examenes/<slug:slug>/preguntas/', views.listar_preguntas, name='listar_preguntas'),
    path('examenes/<slug:slug>/agregar/', views.agregar_pregunta, name='agregar_pregunta'),
    path('examenes/<slug:slug>/ver/', views.ver_examen, name='ver_examen'),
    path('examenes/<slug:slug>/iniciar/', views.iniciar_examen, name='iniciar_examen'),
    path('examenes/<slug:slug>/editar/', views.editar_examen, name='editar_examen'),
    path('examenes/<slug:slug>/eliminar/', views.eliminar_examen, name='eliminar_examen'),
    path('examen/<slug:slug>/pregunta/<int:pk>/editar/', views.editar_pregunta, name='editar_pregunta'),
    path('examen/<slug:slug>/pregunta/<int:pk>/eliminar/', views.eliminar_pregunta, name='eliminar_pregunta'),
    path('curso/<str:codigo_acceso>/calificar/', views.examenes_por_calificar, name='examenes_por_calificar'),
    path('examen/<slug:slug>/estudiantes/', views.seleccionar_estudiante, name='seleccionar_estudiante'),
    path('examen/<slug:slug>/calificar/<int:estudiante_id>/', views.calificar_respuestas, name='calificar_respuestas'),
    path('mis-retroalimentaciones/<str:codigo_acceso>/', views.lista_retroalimentacion, name='lista_retroalimentacion'),
    path('retroalimentacion/<int:examen_id>/', views.detalle_retroalimentacion, name='detalle_retroalimentacion'),
    path('editar-retroalimentacion/<int:examen_id>/', views.alumnos_con_retroalimentacion, name='alumnos_con_retroalimentacion'),
    path('editar-retroalimentacion/<int:examen_id>/<int:estudiante_id>/editar/', views.editar_retroalimentacion, name='editar_retroalimentacion'),
    path('editar-retroalimentacion/<int:examen_id>/<int:estudiante_id>/eliminar/', views.eliminar_retroalimentacion, name='eliminar_retroalimentacion'),
    
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/enviar/', views.enviar_actividad, name='enviar_actividad'),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/entregas/', views.listar_entregas, name='listar_entregas'),
    path('board/<str:codigo_acceso>/entrega/<int:id_envio>/calificar/', views.calificar_entrega, name='calificar_entrega'),

    path('chatgpt/', views.chatgpt_form, name='chatgpt_form'), 
    path('chatgpt/send/', views.chatgpt_prompt, name='chatgpt_prompt'), 

    path('examen/<slug:slug>/calificar-ia/<int:estudiante_id>/', views.calificar_examen_IA, name='calificar_respuestas_IA'),
    path('retroalimentacion/ia/<int:examen_id>/', views.retroalimentacion_ia_estudiante, name='retroalimentacion_ia_estudiante'),
    
    path('reportes/crear/', views.crear_reporte_rendimiento, name='crear_reporte_rendimiento'),
    path('reportes/curso/<str:codigo_acceso>/', views.reportes_curso, name='reportes_curso'),
    path('reportes/detalle/<int:id_reporte>/', views.detalle_reporte, name='detalle_reporte'),
    path('reportes/eliminar/<int:id_reporte>/', views.eliminar_reporte, name='eliminar_reporte'),
    path('reportes/descargar/<int:id_reporte>/', views.descargar_pdf_reporte, name='descargar_pdf_reporte'),
    path('board/<str:codigo_acceso>/calificar-ia/', views.calificar_actividades_ia, name='calificar_actividades_ia'),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/procesar-ia/', views.procesar_calificacion_ia, name='procesar_calificacion_ia'),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/revisar-ia/', views.revisar_calificaciones_ia, name='revisar_calificaciones_ia'),
    path('board/<str:codigo_acceso>/<int:id_calificacion_ia>/confirmar/', views.confirmar_calificacion_individual, name='confirmar_calificacion_individual'),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/criterios-ia/', views.configurar_criterios_ia, name='configurar_criterios_ia'),
    
    # Agregar estas URLs en urls.py
    path('board/<str:codigo_acceso>/calificar-ia/', views.actividades_calificables_ia, name='actividades_calificables_ia'),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/envios-ia/', views.envios_por_calificar_ia, name='envios_por_calificar_ia'),
    path('board/<str:codigo_acceso>/envio/<int:id_envio>/calificar-ia/', views.calificar_envio_ia, name='calificar_envio_ia'),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/calificar-todos-ia/', views.calificar_todos_ia, name='calificar_todos_ia'),
    
    path('curso/<str:codigo_acceso>/crear_examen_ia/', views.crear_examen_ia, name='crear_examen_ia'),
    
    path('<str:codigo_acceso>/vista-previa-examen-ia/', views.vista_previa_examen_ia, name='vista_previa_examen_ia'),


]

    




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)