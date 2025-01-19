from django.contrib import admin

# Register your models here.
from .models import Employe,Service,Conge,Contract,Evaluation,Absence,OffreEmploi,Candidature,Entretien,Salaire

admin.site.register(Employe)
admin.site.register(Service)
admin.site.register(Conge)
admin.site.register(Contract)
admin.site.register(Evaluation)
admin.site.register(Absence)
admin.site.register(OffreEmploi)
admin.site.register(Candidature)
admin.site.register(Entretien)
admin.site.register(Salaire)