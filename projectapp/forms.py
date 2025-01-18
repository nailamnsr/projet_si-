from .models import Employe,Service,Conge,Contract,Evaluation,Absence,Salaire,Candidature,OffreEmploi,Entretien
from django import forms

class EmployeForm(forms.ModelForm):
    class Meta:
        model = Employe
        fields = ['code', 'nom', 'prenom', 'date_naissance', 'date_embauche', 'adresse', 'id_service','historique_professionnel','competences', 'formations','solde_conge','sexe' ]
class serviceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['code_service','nom_service']
class congeForm(forms.ModelForm):
    class Meta :
        model=Conge
        fields=['code_conge','date_debut','date_fin','type_conge','id_employe']
class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['code_contrat', 'date_debut_contrat', 'date_fin_contrat', 'id_employe', 'type_salaire', 'montant_salaire','type_contrat']
class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['id_employe' ,'date_evaluation','objecttifs','competances','performance_globale']


class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ['date_absence']
        widgets = {
            'date_absence': forms.DateInput(attrs={'type': 'date'}),
        }
class SalaireForm(forms.ModelForm):
    class Meta:
        model = Salaire
        fields = ['employe', 'salaire_base', 'primes', 'date_paiement','nbr_massrouf']

    def clean(self):
        cleaned_data = super().clean()
        salaire_base = cleaned_data.get('salaire_base')
        primes = cleaned_data.get('primes')
        
        if salaire_base is None or salaire_base <= 0:
            raise forms.ValidationError("Le salaire de base doit être un montant valide et supérieur à 0.")
        if primes is None:
            raise forms.ValidationError("Les primes doivent être spécifiées.")
        
        return cleaned_data
class OffreEmploiForm(forms.ModelForm):
    class Meta:
        model = OffreEmploi
        fields = ['titre', 'description']

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['nom', 'prenom', 'email', 'telephone', 'adresse', 'lettre_motivation']
        widgets = {
            'lettre_motivation': forms.Textarea(attrs={'rows': 5}),
        }

class EntretienForm(forms.ModelForm):
    class Meta:
        model = Entretien
        fields = ['candidature', 'date', 'lieu', 'remarques']

    def clean_date(self):
        date = self.cleaned_data.get('date')
        candidature = self.cleaned_data.get('candidature')

        # Vérifier s'il y a déjà un entretien programmé à cette date pour la même candidature
        if Entretien.objects.filter(candidature=candidature, date=date).exists():
            raise forms.ValidationError("Un entretien est déjà programmé à cette date.")
        return date