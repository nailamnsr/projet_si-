from django.shortcuts import render,redirect,get_object_or_404
from .models import Employe,Service,Conge,Contract,Evaluation,Salaire,OffreEmploi,Candidature,Entretien,Absence
from .forms import EmployeForm,serviceForm,congeForm,ContractForm,EvaluationForm,AbsenceForm,SalaireForm,OffreEmploiForm,CandidatureForm,EntretienForm
from django.db.models import Q
from datetime import timedelta,date
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, DurationField
import csv
import tempfile
from django.http import HttpResponse
from django.template.loader import render_to_string
 

# Create your views here.
def redirect_to_role(request, role):
    if role == 'manager':
        return redirect('login_manager')  # Redirige vers la page d'évaluation des employés
    elif role == 'agent_rh':
        return redirect('login_agent_rh')  # Redirige vers la liste des employés
    elif role == 'candidat':
        return redirect('login_candidat')  # Redirige vers la page des offres d'emploi pour le candidat
    else:
        return redirect('home')  # Rediriger vers l'accueil si le rôle est invalide 
#authentification    
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_manager(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='manager').exists():
            login(request, user)
            return redirect('evaluation_employe') # Redirige le manager
        else:
            messages.error(request, 'Identifiants invalides ou vous n\'êtes pas un manager.')
    return render(request, 'auth/login_manager.html')
from django.views.decorators.csrf import csrf_protect


def login_agent_rh(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='agent rh').exists():
            login(request, user)
            return redirect('main_rh')  # Redirige l'agent RH
        else:
            messages.error(request, 'Identifiants invalides ou vous n\'êtes pas un agent RH.')
    return render(request, 'auth/login_agent_rh.html')

def login_candidat(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='candidat').exists():
            login(request, user)
            return redirect('candidat_home')  # Redirige le candidat
        else:
            messages.error(request, 'Identifiants invalides ou vous n\'êtes pas un candidat.')
    return render(request, 'auth/login_candidat.html')
def home(request):
    return render(request, 'home.html')
    
def main_rh(request):
    # Récupération de tous les objets des modèles
    employes = Employe.objects.all()
    services = Service.objects.all()
    conges = Conge.objects.all()
    contrats = Contract.objects.all()

    # Contexte pour la vue
    context = {
        'employes': employes,
        'services': services,
        'conges': conges,
        'contrats': contrats,
    }

    # Rendu de la page
    return render(request, 'rh/main_rh.html', context)


#gestion des employe 
def gestion_employe(request):
    query = request.GET.get('q', '') 

    if query:
        
        employes = Employe.objects.filter(
            Q(nom__icontains=query) | Q(prenom__icontains=query) | Q(code__icontains=query)
        )
    else:
        
        employes = Employe.objects.all()

    # Contexte pour la vue
    context = {
        'employes': employes,
        'query': query,  # Inclure la recherche pour la réutiliser dans le formulaire ou l'interface
    }

    # Rendu de la page
    return render(request, 'rh/employes/gestion_employe.html', context)
# Ajouter un employé
def employe_create(request):
    if request.method == "POST":
        form = EmployeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_rh')
    else:
        form = EmployeForm()
    return render(request, 'rh/employes/employe_form.html', {'form': form})

# Modifier un employé
def employe_update(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        form = EmployeForm(request.POST, instance=employe)
        if form.is_valid():
            form.save()
            return redirect('main_rh')
    else:
        form = EmployeForm(instance=employe)
    return render(request, 'rh/employes/employe_form.html', {'form': form})

# Supprimer un employé
def employe_delete(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        employe.delete()
        return redirect('main_rh')
    return render(request, 'rh/employes/employe_confirm_delete.html', {'employe': employe})

# etablir une fiche demploye

#ajouter conge
def ajouter_conge(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        form = congeForm(request.POST)
        if form.is_valid():
            conge = form.save(commit=False)
            conge.id_employe = employe  # Link the employee to the leave
            jours_pris = (conge.date_fin - conge.date_debut).days + 1  # Calculate leave days

            if employe.solde_conge < jours_pris:
                # Handle case where the employee doesn't have enough leave
                form.add_error(None, "Solde de congé insuffisant")
                return render(request, 'rh/employes/ajouter_conge.html', {'form': form, 'employe': employe})

            # If enough balance, update and save
            employe.solde_conge -= jours_pris
            employe.save()
            conge.save()

            return redirect('gestion_employe')  # Redirect to employee management page
    else:
        form = congeForm()

    return render(request, 'rh/employes/ajouter_conge.html', {'form': form, 'employe': employe})
#affichage des conges 
def fiche_employe(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    congés = employe.conge_set.all()
    absences = Absence.objects.filter(employe=employe) # Récupérer tous les congés de l'employé

    # Créer une liste de dictionnaires contenant les informations nécessaires
    conge_data = []
    for conge in congés:
        jours_pris = conge.get_nombre_jours()  # Nombre de jours pris pour chaque congé
        jours_restants = employe.solde_conge - jours_pris  # Calcul des jours restants
        conge_data.append({
            'conge': conge,
            'jours_restants': jours_restants,
        })
    
    return render(request, 'rh/employes/fiche_employe.html', {
        'employe': employe,
        'absences':absences,
        'conge_data': conge_data,
    })

#evaluation des employes 
def evaluation_employe(request):
    evaluations = Evaluation.objects.all()
    return render(request, 'manager/evaluation_employe.html', {'evaluations': evaluations})
#creation dune evaluation
def evaluation_create(request):
    if request.method == "POST":
        form = EvaluationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('evaluation_employe')
    else:
        form = EvaluationForm()
    return render(request, 'manager/evaluation_form.html', {'form': form})
#modification dune evaluation
def evaluation_update(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    if request.method == "POST":
        form = EvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            return redirect('evaluation_employe')
    else:
        form = EvaluationForm(instance=evaluation)
    return render(request, 'manager/evaluation_form.html', {'form': form})
#supprision dune evaluation
def evaluation_delete(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    if request.method == "POST":
        evaluation.delete()  
        return redirect('evaluation_employe')  
    return render(request, 'manager/evaluation_confirm_delete.html', {'evaluation': evaluation})
def generate_report_for_evaluation(request, pk):
    evaluation = get_object_or_404(Evaluation, pk=pk)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rapport_evaluation_{evaluation.id_employe}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Employé', 'Date d\'Évaluation', 'Objectifs Atteints', 'Compétences Développées', 'Note de performance'])
    writer.writerow([evaluation.id_employe, evaluation.date_evaluation, evaluation.objecttifs, evaluation.competances, evaluation.performance_globale])

    return response


#gestion des services 
def gestion_service(request):
    query = request.GET.get('q', '')  # Récupère la valeur de la recherche depuis les paramètres GET

    if query:
        # Filtre les services selon la recherche (nom_service ou code_service)
        services = Service.objects.filter(
            Q(nom_service__icontains=query) | Q(code_service__icontains=query)
        )
    else:
        # Si pas de recherche, récupère tous les services
        services = Service.objects.all()

    # Contexte pour la vue
    context = {
        'services': services,
        'query': query,  # Inclure la recherche pour l'interface utilisateur
    }

    # Rendu de la page
    return render(request, 'rh/services/gestion_service.html', context)
# Ajouter un service
def service_create(request):
    if request.method == "POST":
        form = serviceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_rh')
    else:
        form = serviceForm()
    return render(request, 'rh/services/service_form.html', {'form': form})

# Modifier un service
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = serviceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('main_rh')
    else:
        form = serviceForm(instance=service)
    return render(request, 'rh/services/service_form.html', {'form': form})

#  supprimer un service
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        service.delete()
        return redirect('main_rh')  # Redirige vers la liste principale après suppression
    return render(request, 'rh/services/service_comfirm_delete.html', {'service': service})

#gestion des contrats 
def gestion_contrat(request):
    query = request.GET.get('q', '')  # Récupère la valeur de la recherche depuis les paramètres GET

    if query:
        # Filtre les contrats selon la recherche (code_contrat)
        contracts = Contract.objects.filter(
            Q(code_contrat__icontains=query)
        )
    else:
        # Si pas de recherche, récupère tous les contrats
        contracts = Contract.objects.all()

    # Contexte pour la vue
    context = {
        'contracts': contracts,
        'query': query,  # Inclure la recherche pour l'interface utilisateur
    }

    # Rendu de la page
    return render(request, 'rh/contrats/gestion_contrat.html', context)
# Créer un contrat
def contract_create(request):
    if request.method == "POST":
        form = ContractForm(request.POST)
        print(request.POST)  # Vérifiez ici les données soumises
        if form.is_valid():
            form.save()
            print("Formulaire valide et contrat enregistré")  # Vérification supplémentaire
            return redirect('gestion_contrat')  # Redirection après enregistrement
        else:
            print("Formulaire non valide : ", form.errors)  # Affiche les erreurs de validation
    else:
        form = ContractForm()
    return render(request, 'rh/contrats/contrat_form.html', {'form': form})


# Modifier un contrat
def contract_update(request, pk):
    contrat = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = ContractForm(request.POST, instance=contrat)
        if form.is_valid():
            form.save()
            return redirect('gestion_contrat')  # Redirection après modification
    else:
        form = ContractForm(instance=contrat)
    return render(request, 'rh/contrats/contrat_form.html', {'form': form})

# Supprimer un contrat
def contract_delete(request, pk):
    contrat = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        contrat.delete()
        return redirect('gestion_contrat')  # Redirection après suppression
    return render(request, 'rh/contrats/contrat_confirm_delete.html', {'contrat': contrat})
#afficher les deatils d'un contrat 
def afficher_contrat(request, pk):
    # Récupérer le contrat correspondant à la clé primaire pk
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'rh/contrats/afficher_contrat.html', {'contract': contract})


def marquer_absence(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    absence=Absence.objects.filter(employe=employe)

    if request.method == "POST":
        form = AbsenceForm(request.POST)
        if form.is_valid():
            absence = form.save(commit=False)  # Ne sauvegarde pas encore
            absence.employe = employe  # Associe l'absence à l'employé
            absence.save()  # Sauvegarde l'absence avec la date
            employe.incrementer_absence()  # Incrémente le nombre d'absences
            return redirect('fiche_employe', pk=employe.pk)  # Redirige vers la fiche employé
    else:
        form = AbsenceForm()

    return render(request, 'rh/employes/marquer_absence.html', {'form': form, 'employe': employe,'absence':absence})

def analyse_tableaux(request):
    # Effectifs Totaux
    effectifs = Contract.objects.values('type_contrat').annotate(total=Count('id_employe'))

    # Statistiques de Diversité
    repartition_sexe = Employe.objects.values('sexe').annotate(total=Count('id'))
    repartition_age = {
        'moins_30': Employe.objects.filter(date_naissance__gte=date.today().replace(year=date.today().year - 30)).count(),
        '30_50': Employe.objects.filter(
            date_naissance__lt=date.today().replace(year=date.today().year - 30),
            date_naissance__gte=date.today().replace(year=date.today().year - 50)
        ).count(),
        'plus_50': Employe.objects.filter(date_naissance__lt=date.today().replace(year=date.today().year - 50)).count(),
    }
    top_performers = Employe.objects.annotate(avg_score=Avg('evaluation__performance_globale')).order_by('-avg_score')[:5]

    
    context = {
        'effectifs': effectifs,
        'repartition_sexe': repartition_sexe,
        'repartition_age': repartition_age,
        'top_performers': top_performers,}
    return render(request, 'rh/employes/analyse_tableaux.html', context)







#cree gestion salaire 
#importe la bibliotheque 
#'''


from django.shortcuts import render, redirect


def candidat_home(request):
    offres = OffreEmploi.objects.all()  # Récupérer toutes les offres d'emploi
    context = {'offres': offres}
    return render(request, 'condidat/main_condidat.html', context)




# Vue pour soumettre une candidature

def postuler(request, offre_id):
    offre = get_object_or_404(OffreEmploi, id=offre_id)

    if request.method == 'POST':
        form = CandidatureForm(request.POST)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.candidat = request.user  # Associe le candidat connecté
            candidature.offre = offre  # Associe l'offre sélectionnée
            candidature.save()
            return redirect('mes_candidatures')
    else:
        form = CandidatureForm()

    context = {'form': form, 'offre': offre}
    return render(request, 'condidat/postuler.html', context)

# Vue pour afficher les candidatures du candidat

def mes_candidatures(request, offre_id=None):
    if offre_id:
        # Filter candidatures based on the specific offer
        candidatures = Candidature.objects.filter(candidat=request.user, offre_id=offre_id)
    else:
        # Show all candidatures for the user
        candidatures = Candidature.objects.filter(candidat=request.user)
    return render(request, 'condidat/mes_condidatures.html', {'candidatures': candidatures})

# Vue pour afficher les entretiens du candidat

def mes_entretiens(request):
    # Récupérer tous les entretiens du candidat actuel
    entretiens = Entretien.objects.filter(candidature__candidat=request.user)
    return render(request, 'condidat/mes_entretiens.html', {'entretiens': entretiens})

# Vue pour l'agent RH : publier une offre d'emploi

def publier_offre(request):
    if request.method == 'POST':
        form = OffreEmploiForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rh/recrutement/gestion_recrutement')
    else:
        form = OffreEmploiForm()
    return render(request, 'rh/recrutement/publier_offre.html', {'form': form})

# Vue pour l'agent RH : programmer un entretien

def programmer_entretien(request):
    # Récupérer les candidatures, filtrer si nécessaire
    candidatures = Candidature.objects.all()  # Vous pouvez appliquer un filtre selon le besoin (par exemple, par statut ou utilisateur connecté)
    
    if request.method == 'POST':
        form = EntretienForm(request.POST)
        if form.is_valid():
            form.save()
            # Rediriger vers la page après la soumission du formulaire (exemple : gestion du recrutement)
            return redirect('rh/recrutement/gestion_recrutement')
    else:
        form = EntretienForm()
    
    return render(request, 'rh/recrutement/programmer_entretien.html', {'form': form, 'candidatures': candidatures})

# Vue pour l'agent RH : gestion des candidatures et entretiens

def gestion_recrutement(request):
    # Récupérer les candidatures et les entretiens
    candidatures = Candidature.objects.all()
    entretiens = Entretien.objects.all()
    offres = OffreEmploi.objects.all()
    
    return render(request, 'rh/recrutement/gestion_recrutement.html', {
        'candidatures': candidatures,
        'entretiens': entretiens,
        'offres': offres
    })

def afficher_fiche_de_paye(request, pk):
    try:
        employe = Employe.objects.get(pk=pk)  # Get the employee by pk
        salaire = Salaire.objects.get(employe=employe)  # Try to get the corresponding salary
    except Employe.DoesNotExist:
        # If the employee doesn't exist, handle the error
        messages.error(request, "L'employé avec l'ID donné n'existe pas.")
        return redirect('employe_non_trouve')  # Redirect to an error page or other route
    except Salaire.DoesNotExist:
        # If no salary is found for the employee, handle the error
        messages.error(request, "Aucune fiche de paye trouvée pour cet employé.")
        return redirect('ajouter_salaire', pk=pk)  # Redirect to a page where you can add salary for the employee

    # If both employee and salary are found, render the fiche de paye
    return render(request, 'rh/salaires/fiche_de_paye.html', {
        'employe': employe,
        'salaire': salaire
    })

def ajouter_salaire(request, pk):
    try:
        employe = Employe.objects.get(pk=pk)  # Récupérer l'employé avec l'ID fourni
    except Employe.DoesNotExist:
        return redirect('employe_non_trouve')  # Gérer l'erreur si l'employé n'existe pas

    if request.method == 'POST':
        form = SalaireForm(request.POST)
        if form.is_valid():
            salaire = form.save(commit=False)

            # Récupérer les valeurs pour les absences et les demandes de massrouf
            nb_absences = employe.nb_absence  # Assurez-vous que 'nb_absence' est bien défini dans le modèle Employe
            nbr_massrouf = form.cleaned_data.get('nbr_massrouf', 0)  # Assurez-vous que 'nbr_massrouf' est inclus dans le formulaire

            # Calcul du salaire quotidien
            salaire_quot = salaire.salaire_base / 30

            # Calcul du salaire total
            salaire.salaire_quot = salaire_quot
            salaire.salaire_total = (
                salaire.salaire_base
                + salaire.primes
                - (salaire_quot * nb_absences)  # Déduction des absences
                - (salaire_quot * nbr_massrouf )  # Déduction des massrouf
            )

            salaire.employe = employe  # Lier l'employé à ce salaire
            salaire.save()  # Sauvegarder les informations du salaire

            return redirect('gestion_employe')  # Rediriger après avoir enregistré avec succès
    else:
        form = SalaireForm()

    return render(request, 'rh/salaires/ajouter_salaire.html', {
        'form': form,
        'employe': employe,  # Passer l'employé à la template pour l'affichage
    })
   