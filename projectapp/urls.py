from django.urls import path
from . import views
urlpatterns = [
    #main path 
    path('', views.home, name='home'),  # Page d'accueil
    path('redirect/<str:role>/', views.redirect_to_role, name='redirect_to_role'),  # Redirection en fonction du rôle
    path('login/manager/', views.login_manager, name='login_manager'),  # Connexion Manager
    path('login/agent_rh/', views.login_agent_rh, name='login_agent_rh'),  # Connexion Agent RH
    path('login/candidat/', views.login_candidat, name='login_candidat'),  # Connexion Candidat
    path('manager/', views.evaluation_employe, name='evaluation_employe'),  # Évaluation Manager 
    path('agenrh/',views.main_rh ,name='main_rh'),
  
    path('agentrh/gestion_employe/',views.gestion_employe,name='gestion_employe'),
    path('agentrh/gestion_service/',views.gestion_service,name='gestion_service'),
    path('agentrh/gestion_contrat/',views.gestion_contrat,name='gestion_contrat'),
    path('agentrh/analyse_tableaux/',views.analyse_tableaux,name='analyse_tableaux'),
    path('agentrh/recrutement/', views.gestion_recrutement, name='gestion_recrutement'),
    #path('agentrh/analyse_tableaux/analyse_absence/',views.analyse_absences,name='analyse_absences'),
    #employe
    path('newemploye/', views.employe_create, name='employe_create'),
    path('<int:pk>/editemploye/', views.employe_update, name='employe_update'), 
    path('<int:pk>/deleteemploye/', views.employe_delete, name='employe_delete'),
    path('<int:pk>/ficheemploye/', views.fiche_employe, name='fiche_employe'),
    path('<int:pk>/ajouterconge/', views.ajouter_conge, name='ajouter_conge'),
    path('<int:pk>/marquer-absence/', views.marquer_absence, name='marquer_absence'),
    #service
    path('newservice/', views.service_create, name='service_create'),
    path('<int:pk>/editservice/', views.service_update, name='service_update'),
    path('<int:pk>/deleteservice/', views.service_delete, name='service_delete'),
    #contrats
    path('newcontract/', views.contract_create, name='contract_create'),
    path('<int:pk>/editcontract/', views.contract_update, name='contract_update'),
    path('<int:pk>/deletecontract/', views.contract_delete, name='contract_delete'), 

    #manager's paths 
    path('manager/evaluation/create/', views.evaluation_create, name='evaluation_create'),
    path('manager/evaluation/update/<int:pk>/', views.evaluation_update, name='evaluation_update'),
    path('manager/evaluation/delete/<int:pk>/', views.evaluation_delete, name='evaluation_delete'),
    path('manager/evaluation/rapport/<int:pk>/', views.generate_report_for_evaluation, name='generate_report_for_evaluation'),
    #condidat's paths 
    path('candidat/', views.candidat_home, name='candidat_home'),
    path('postuler/<int:offre_id>/', views.postuler, name='postuler'),
    path('postuler/<int:offre_id>/condidat/mes_condidatures/', views.mes_candidatures, name='mes_candidatures'),
    path('mes-entretiens/', views.mes_entretiens, name='mes_entretiens'),
    path('publier-offre/', views.publier_offre, name='publier_offre'),
    path('programmer-entretien/', views.programmer_entretien, name='programmer_entretien'),
    path('gestion-recrutement/', views.gestion_recrutement, name='gestion_recrutement'),
    path('main/condidat/mes_candidatures/', views.mes_candidatures, name='mes_candidatures'),
]