import getpass
from django.core.management.base import BaseCommand, CommandError
from users.models import User


class Command(BaseCommand):
    help = 'Crée un compte superadmin système/base de données sans entreprise associée (accès Django Admin).'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help="Nom d'utilisateur (lettres minuscules, chiffres, @, _)")
        parser.add_argument('--email', type=str, help='Adresse email du superadmin')
        parser.add_argument('--password', type=str, help='Mot de passe du superadmin')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')

        if not username:
            username = input("Nom d'utilisateur (ex: superadmin) : ").strip().lower()
        else:
            username = username.strip().lower()

        if not email:
            email = input("Email (ex: admin@system.local) : ").strip()
        else:
            email = email.strip()

        if not password:
            password = getpass.getpass("Mot de passe : ")
            confirm = getpass.getpass("Confirmez le mot de passe : ")
            if password != confirm:
                raise CommandError("Les mots de passe ne correspondent pas.")

        # Vérifier si l'utilisateur existe déjà
        user = User.objects.filter(username=username).first()
        if user:
            self.stdout.write(self.style.WARNING(f"L'utilisateur '{username}' existe déjà. Mise à jour de ses privilèges en superadmin système..."))
            user.is_staff = True
            user.is_superuser = True
            user.user_type = 'PLATFORM_ADMIN'
            user.company = None
            user.is_primary_admin = False
            user.set_password(password)
            user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Compte '{username}' mis à jour avec succès en Superadmin Système (company=None)."))
            return

        # Création d'un nouveau superutilisateur
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                user_type='PLATFORM_ADMIN',
                company=None,
                is_primary_admin=False,
            )
            self.stdout.write(self.style.SUCCESS(
                f"\n[SUCCÈS] Compte superadmin système créé avec succès !\n"
                f"- Nom d'utilisateur : {user.username}\n"
                f"- Email              : {user.email}\n"
                f"- Entreprise liée    : AUCUNE (compte système pur)\n"
                f"- Accès              : Django Admin sur http://localhost:8000/admin/\n"
            ))
        except Exception as exc:
            raise CommandError(f"Erreur lors de la création du superadmin : {exc}")
