from django.db import models
from django.db import models
from django.db.models import Sum 
from django.utils import timezone 
from django.core.exceptions import ValidationError


class Service(models.Model):
    nom_service = models.CharField(max_length=100)
    code_service = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.nom_service} {self.code_service}"
    
    
class Employe(models.Model):
    CHOICE_SEXE =[('female','female'),('male','male')]
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    date_embauche = models.DateField()
    adresse = models.TextField()
    id_service =  models.ForeignKey(Service,on_delete=models.CASCADE)
    historique_professionnel = models.TextField(blank=True, null=True)
    competences = models.TextField(blank=True, null=True)
    formations = models.TextField(blank=True, null=True)
    solde_conge = models.PositiveIntegerField(default=0)
    droits_conge = models.PositiveIntegerField(default=0)
    nb_absence = models.PositiveIntegerField(default=0)  # Compteur d'absences
    nb_massrouf=models.PositiveIntegerField(default=0)
    sexe=models.CharField(max_length=10,choices=CHOICE_SEXE)
    def incrementer_absence(self):
        """Méthode pour incrémenter le nombre d'absences."""
        self.nb_absence += 1
        self.save()
        
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    def jours_utilises(self):  
        return Conge.objects.filter(id_employe=self).aggregate(Sum('jours_pris'))['jours_pris__sum'] or 0  

    def jours_restants(self):  
        return self.solde_conge  
    
    def total_jours_conge(self):  
        return self.droits_conge  # Ou un autre calcul selon vos besoins 

class Conge (models.Model):
    TYPE_CONGE_CHOICES = [
        ('ANNUEL', 'Congé Annuel'),
        ('MALADIE', 'Congé Maladie'),
        ('MATERNITE', 'Congé de Maternité'),
        ('PATERNITE', 'Congé de Paternité'),
        ('SANS_SOLDE', 'Congé Sans Solde'),
        ('AUTRE', 'Autre'),
    ]
    code_conge = models.CharField(max_length=10 , unique=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    id_employe=models.ForeignKey(Employe,on_delete=models.CASCADE)
    type_conge = models.CharField(max_length=20, choices=TYPE_CONGE_CHOICES)
    def __str__(self):
        return f"{self.code_conge} du  {self.date_debut} au {self.date_fin}"
    def save(self, *args, **kwargs):
       
        
        jours_pris = (self.date_fin - self.date_debut).days + 1  # Inclure les deux jours
        if self.id_employe:
            self.id_employe.solde_conge -= jours_pris
            self.id_employe.save()
        super().save(*args, **kwargs)  # Appeler la méthode save() par défaut après modification
    def get_nombre_jours(self):
        # Calculer le nombre de jours entre la date de début et la date de fin
        return (self.date_fin - self.date_debut).days + 1  # Inclure les deux jours
  
class Contract(models.Model):
    TYPE_CHOICES_CONTRATS=[
        ('CDI','Contrats à durée indéterminée'),
        ('CDD','contrats à durée déterminée'),
        ('STAGE','stage'),
    ]
    
    code_contrat = models.CharField(max_length=100)
    date_debut_contrat=models.DateField()
    date_fin_contrat=models.DateField()
    type_contrat=models.CharField(max_length=20,choices=TYPE_CHOICES_CONTRATS)
    id_employe=models.ForeignKey(Employe,on_delete=models.CASCADE)
    type_salaire = models.CharField(
        max_length=10,
        choices=[('mensuel', 'Mensuel'), ('quotidien', 'Quotidien')],
        default='mensuel'
    )
    montant_salaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
      return f"{self.code_contrat} du  {self.date_debut_contrat} au {self.date_fin_contrat}"
    

class Evaluation(models.Model):
    id_employe=models.ForeignKey(Employe,on_delete=models.CASCADE)
    date_evaluation=models.DateField()
    objecttifs=models.TextField()
    competances=models.TextField()
    performance_globale = models.DecimalField(max_digits=5, decimal_places=2)

 
class Absence(models.Model):
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='absences')
    date_absence = models.DateField()
    est_absent = models.BooleanField(default=True)
    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour incrémenter le nombre d'absences."""
        if not self.pk:  # L'absence est ajoutée pour la première fois
            self.employe.incrementer_absence()  # Appel de la méthode pour incrémenter
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Absence de {self.employe.nom} {self.employe.prenom} le {self.date_absence}"
      


class Salaire(models.Model):
    employe = models.OneToOneField(Employe, on_delete=models.CASCADE)
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2)
    salaire_quot = models.DecimalField(max_digits=10, decimal_places=2)
    primes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_paiement = models.DateField()
    salaire_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    nbr_massrouf=models.PositiveIntegerField(default=0)
    def calculer_deductions_absences(self, mois, annee):
        """Calculer les déductions liées aux absences."""
        absences_count = self.employe.absences.filter(
            date_absence__year=annee,
            date_absence__month=mois
        ).count()
        return self.salaire_quot * absences_count

    def calculer_massrouf(self, mois, annee):
        """Calculer le total des avances MASSROUF pour le mois."""
        massroufs = Massrouf.objects.filter(
            employe=self.employe,
            date_demande__year=annee,
            date_demande__month=mois,
            approuve=True
        )
        return massroufs.aggregate(total=models.Sum('montant'))['total'] or 0

    def save(self, *args, **kwargs):
        """Calculer le salaire total."""
        # Calcul du salaire quotidien
        self.salaire_quot = self.salaire_base / 30
        
        # Récupérer le mois et l'année de la date de paiement
        mois = self.date_paiement.month
        annee = self.date_paiement.year
        
        # Calculer les déductions pour absences
        deductions_absences = self.calculer_deductions_absences(mois, annee)
        
        # Calculer le total des avances MASSROUF
        total_massrouf = self.calculer_massrouf(mois, annee)
        
        # Calcul du salaire total
        self.salaire_total = (
            self.salaire_base -
            deductions_absences +
            self.primes -
            total_massrouf
        )
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Salaire de {self.employe.nom} {self.employe.prenom} pour le mois de {self.date_paiement}" 
    

from django.contrib.auth.models import User

class OffreEmploi(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.titre

class Candidature(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('refusee', 'Refusée'),
    ]

    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name='candidatures')
    candidat = models.ForeignKey(User, on_delete=models.CASCADE)
    lettre_motivation = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='en_attente')
    
    # Champs pour les informations personnelles
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=15)
    adresse = models.TextField()

    def __str__(self):
        return f"{self.candidat.username} - {self.offre.titre}"

class Entretien(models.Model):
    candidature = models.ForeignKey(Candidature, on_delete=models.CASCADE)
    date = models.DateTimeField()
    lieu = models.CharField(max_length=200)
    remarques = models.TextField(blank=True)

    def __str__(self):
        return f"Entretien - {self.candidature.candidat.username} - {self.date}"