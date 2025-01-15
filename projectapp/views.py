from django.shortcuts import render,redirect,get_object_or_404
from .models import Employe,Service,Conge,Contract,Evaluation,Salaire,OffreEmploi,Candidature,Entretien
from .forms import EmployeForm,serviceForm,congeForm,ContractForm,EvaluationForm,AbsenceForm,SalaireForm,OffreEmploiForm,CandidatureForm,EntretienForm
from django.db.models import Q
from datetime import timedelta,date
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, DurationField
import csv
import tempfile
from django.http import HttpResponse
from django.template.loader import render_to_string
#from weasyprint import HTML

# Create your views here.
def redirect_to_role(request, role):
    if role == 'manager':
        return redirect('evaluation_employe')  # Redirige vers la page d'évaluation des employés
    elif role == 'agent_rh':
        return redirect('main_rh')  # Redirige vers la liste des employés
    elif role == 'candidat':
        return redirect('candidat_home')  # Redirige vers la page des offres d'emploi pour le candidat
    else:
        return redirect('home')  # Rediriger vers l'accueil si le rôle est invalide
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
def fiche_employe(request,pk):
    employe = get_object_or_404(Employe, pk=pk)
    return render(request, 'rh/employes/fiche_employe.html', {'employe': employe})
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
    congés = employe.conge_set.all()  # Récupérer tous les congés de l'employé

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
        'conge_data': conge_data,
    })
#marquer des abcense 
def marquer_absence(request, pk):
    employe = get_object_or_404(Employe, pk=pk)

    if request.method == "POST":
        # Incrémenter le nombre d'absences
        employe.incrementer_absence()
        return redirect('fiche_employe', pk=employe.pk)  # Rediriger vers la fiche de l'employé après l'ajout de l'absence

    return render(request, 'rh/employes/marquer_absence.html', {'employe': employe})
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
        contrats = Contract.objects.filter(
            Q(code_contrat__icontains=query)
        )
    else:
        # Si pas de recherche, récupère tous les contrats
        contrats = Contract.objects.all()

    # Contexte pour la vue
    context = {
        'contrats': contrats,
        'query': query,  # Inclure la recherche pour l'interface utilisateur
    }

    # Rendu de la page
    return render(request, 'rh/contrats/gestion_contrat.html', context)
# Créer un contrat
def contract_create(request):
    if request.method == "POST":
        form = ContractForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion_contrat')  # Redirection vers la liste des employés
    else:
        form = ContractForm()
    return render(request, 'rh/contrats/contrat_form.html', {'form':form})

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



def marquer_absence(request, pk):
    employe = get_object_or_404(Employe, pk=pk)

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

    return render(request, 'rh/employes/marquer_absence.html', {'form': form, 'employe': employe})

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


def calculer_salaire(request):
    if request.method == 'POST':
        form = SalaireForm(request.POST)
        if form.is_valid():
            salaire = form.save(commit=False)
            salaire.save()  # Sauvegarde du salaire calculé
            
            # Calcul du salaire total selon la formule
            mois = salaire.date_paiement.month
            annee = salaire.date_paiement.year
            salaire.calculer_deductions_absences(mois, annee)
            salaire.calculer_massrouf(mois, annee)
            salaire.save()
            
            # Récupérer la fiche de paie
            context = {
                'employe': salaire.employe,
                'salaire_total': salaire.salaire_total,
                'date_paiement': salaire.date_paiement,
                'salaire_base': salaire.salaire_base,
                'primes': salaire.primes,
                'deductions_absences': salaire.calculer_deductions_absences(mois, annee),
                'total_massrouf': salaire.calculer_massrouf(mois, annee)
            }
            html = render_to_string('fiche_de_paye.html', context)
            response = HttpResponse(html)
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = 'attachment; filename="fiche_de_paye.pdf"'
            return response
    else:
        form = SalaireForm()

    return render(request, 'rh/salaires/calculer_salaire.html', {'form': form})

'''def fiche_de_paye(request, salaire_id):
    # Récupérer l'objet Salaire
    salaire = get_object_or_404(Salaire, id=salaire_id)

    # Contexte pour la fiche de paie
    context = {
        'employe': salaire.employe,
        'salaire_base': salaire.salaire_base,
        'primes': salaire.primes,
        'date_paiement': salaire.date_paiement,
        'salaire_total': salaire.salaire_total,
        'deductions_absences': salaire.calculer_deductions_absences(
            salaire.date_paiement.month, salaire.date_paiement.year),
        'total_massrouf': salaire.calculer_massrouf(
            salaire.date_paiement.month, salaire.date_paiement.year),
    }

    # Vérifiez si l'utilisateur demande un PDF
    if request.GET.get('format') == 'pdf':
        html_string = render_to_string('fiche_de_paye.html', context)
       # html = HTML(string=html_string)
       # result = html.write_pdf()

        # Crée un fichier temporaire pour le PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="fiche_de_paye_{salaire.employe.nom}.pdf"'
        #response.write(result)
        return response

    # Sinon, afficher la fiche de paie en HTML
    return render(request, 'rh/salaires/fiche_de_paye.html', context)


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