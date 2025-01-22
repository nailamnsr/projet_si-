from django.shortcuts import render,redirect,get_object_or_404
from .models import Employe,Service,Conge,Contract,Evaluation,Salaire,OffreEmploi,Candidature,Entretien,Absence
from .forms import EmployeForm,serviceForm,congeForm,ContractForm,EvaluationForm,AbsenceForm,SalaireForm,OffreEmploiForm,CandidatureForm,EntretienForm
from django.db.models import Q
from datetime import timedelta,date
from django.db.models import Count, Avg
import csv 
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect

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
def contact_us(request):
    return render(request, 'q.html')
#page principal de lagent rh     
def main_rh(request):
    employes = Employe.objects.all()
    services = Service.objects.all()
    conges = Conge.objects.all()
    contrats = Contract.objects.all()
    context = {
        'employes': employes,
        'services': services,
        'conges': conges,
        'contrats': contrats,
    }
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

    context = {
        'employes': employes,
        'query': query,  }
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

 

#ajouter conge
def ajouter_conge(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        form = congeForm(request.POST)
        if form.is_valid():
            conge = form.save(commit=False)
            conge.id_employe = employe  
            jours_pris = (conge.date_fin - conge.date_debut).days + 1 

            if employe.solde_conge < jours_pris:
                 
                form.add_error(None, "Solde de congé insuffisant")
                return render(request, 'rh/employes/ajouter_conge.html', {'form': form, 'employe': employe})
            employe.solde_conge -= jours_pris
            employe.save()
            conge.save()
            return redirect('gestion_employe')   
    else:
        form = congeForm()
    return render(request, 'rh/employes/ajouter_conge.html', {'form': form, 'employe': employe})


#affichage des conges 
def fiche_employe(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    congés = employe.conge_set.all()
    absences = Absence.objects.filter(employe=employe) 
    conge_data = []
    for conge in congés:
        jours_pris = conge.get_nombre_jours()  
        jours_restants = employe.solde_conge - jours_pris  
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
    query = request.GET.get('q', '') 

    if query:
        
        services = Service.objects.filter(
            Q(nom_service__icontains=query) | Q(code_service__icontains=query)
        )
    else:
        services = Service.objects.all()
    context = {
        'services': services,
        'query': query,  
    }
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
        return redirect('main_rh')  
    return render(request, 'rh/services/service_comfirm_delete.html', {'service': service})


#gestion des contrats 
def gestion_contrat(request):
    query = request.GET.get('q', '')  

    if query:
       
        contracts = Contract.objects.filter(
            Q(code_contrat__icontains=query)
        )
    else:
        contracts = Contract.objects.all()
    context = {
        'contracts': contracts,
        'query': query,  }
    return render(request, 'rh/contrats/gestion_contrat.html', context)



# Créer un contrat
def contract_create(request):
    if request.method == "POST":
        form = ContractForm(request.POST)
        print(request.POST)  
        if form.is_valid():
            form.save()
            print("Formulaire valide et contrat enregistré")  
            return redirect('gestion_contrat')  
        else:
            print("Formulaire non valide : ", form.errors)
    else:
        # Si la méthode est GET, initialiser un formulaire vide
        form = ContractForm()

    return render(request, 'rh/contrats/contrat_form.html', {'form': form})


# Modifier un contrat
def contract_update(request, pk):
    contrat = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        form = ContractForm(request.POST, instance=contrat)
        if form.is_valid():
            form.save()
            return redirect('gestion_contrat')  
    else:
        form = ContractForm(instance=contrat)
    return render(request, 'rh/contrats/contrat_form.html', {'form': form})


# Supprimer un contrat
def contract_delete(request, pk):
    contrat = get_object_or_404(Contract, pk=pk)
    if request.method == "POST":
        contrat.delete()
        return redirect('gestion_contrat')  
    return render(request, 'rh/contrats/contrat_confirm_delete.html', {'contrat': contrat}) 
def afficher_contrat(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, 'rh/contrats/afficher_contrat.html', {'contract': contract})

#marquer une absence
def marquer_absence(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    absence=Absence.objects.filter(employe=employe)

    if request.method == "POST":
        form = AbsenceForm(request.POST)
        if form.is_valid():
            absence = form.save(commit=False)  
            absence.employe = employe  
            absence.save()  
            employe.incrementer_absence()  
            return redirect('fiche_employe', pk=employe.pk)   
    else:
        form = AbsenceForm()

    return render(request, 'rh/employes/marquer_absence.html', {'form': form, 'employe': employe,'absence':absence})


#analyse et tableaux
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




# page principale candidat
def candidat_home(request):
    offres = OffreEmploi.objects.all()  
    context = {'offres': offres}
    return render(request, 'condidat/main_condidat.html', context)




#  soumettre une candidature
def postuler(request, offre_id):
    offre = get_object_or_404(OffreEmploi, id=offre_id)

    if request.method == 'POST':
        form = CandidatureForm(request.POST)
        if form.is_valid():
            candidature = form.save(commit=False)
            candidature.candidat = request.user  
            candidature.offre = offre  
            candidature.save()
            return redirect('mes_candidatures')
    else:
        form = CandidatureForm()

    context = {'form': form, 'offre': offre}
    return render(request, 'condidat/postuler.html', context)

# afficher les candidatures du candidat
def mes_candidatures(request, offre_id=None):
    if offre_id:
        candidatures = Candidature.objects.filter(candidat=request.user, offre_id=offre_id)
    else:
        candidatures = Candidature.objects.filter(candidat=request.user)
    return render(request, 'condidat/mes_condidatures.html', {'candidatures': candidatures})


#  afficher les entretiens du candidat
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

#programmer un entretien
def programmer_entretien(request):
    candidatures = Candidature.objects.all()  
    if request.method == 'POST':
        form = EntretienForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion_recrutement')
    else:
        form = EntretienForm()
    
    return render(request, 'rh/recrutement/programmer_entretien.html', {'form': form, 'candidatures': candidatures})


#gestion des candidatures et entretiens
def gestion_recrutement(request):
    candidatures = Candidature.objects.all()
    entretiens = Entretien.objects.all()
    offres = OffreEmploi.objects.all()
    
    return render(request, 'rh/recrutement/gestion_recrutement.html', {
        'candidatures': candidatures,
        'entretiens': entretiens,
        'offres': offres
    })

#afficher la fiche de paye
def afficher_fiche_de_paye(request, pk):
    try:
        employe = Employe.objects.get(pk=pk)  
        salaire = Salaire.objects.get(employe=employe)  
    except Employe.DoesNotExist:
        
        messages.error(request, "L'employé avec l'ID donné n'existe pas.")
        return redirect('employe_non_trouve')  
    except Salaire.DoesNotExist:
     
        messages.error(request, "Aucune fiche de paye trouvée pour cet employé.")
        return redirect('ajouter_salaire', pk=pk)  
    return render(request, 'rh/salaires/fiche_de_paye.html', {
        'employe': employe,
        'salaire': salaire
    })

#ajouter le salaiare
def ajouter_salaire(request, pk):
    try:
        employe = Employe.objects.get(pk=pk)  
    except Employe.DoesNotExist:
        return redirect('employe_non_trouve')  
    if request.method == 'POST':
        form = SalaireForm(request.POST)
        if form.is_valid():
            salaire = form.save(commit=False)
            nb_absences = employe.nb_absence 
            nbr_massrouf = form.cleaned_data.get('nbr_massrouf', 0)  
            salaire_quot = salaire.salaire_base / 30
            salaire.salaire_quot = salaire_quot
            salaire.salaire_total = (
                (salaire.salaire_base
                + salaire.primes)
                - (salaire_quot * nb_absences) 
                - (salaire_quot * nbr_massrouf )  
            )

            salaire.employe = employe  
            salaire.save()  

            return redirect('gestion_employe')  
    else:
        form = SalaireForm()

    return render(request, 'rh/salaires/ajouter_salaire.html', {
        'form': form,
        'employe': employe,   
    })
