from django.urls import path

from comercial import views

urlpatterns = [
    path("oportunidades", views.OportunidadeListaView.as_view()),
    path("oportunidades/<int:pk>", views.OportunidadeDetalheView.as_view()),
    path("empresas", views.EmpresaSugestoesView.as_view()),
]
