import os, shutil, gzip, smtplib
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from email.message import EmailMessage

class Command(BaseCommand):
    help = "Sauvegarde la base SQLite et envoie par email (optionnel)"
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help="Email pour recevoir le backup")
        parser.add_argument('--keep', type=int, default=7, help="Nombre de backups à conserver")
    
    def handle(self, *args, **options):
        db_path = getattr(settings, 'DATABASES', {}).get('default', {}).get('NAME', 'db.sqlite3')
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'dokaha_backup_{timestamp}.sqlite3.gz')
        
        # Compression gzip
        with open(db_path, 'rb') as f_in:
            with gzip.open(backup_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Backup créé : {backup_file}"))
        
        # Nettoyage anciens backups
        keep = options['keep']
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith('dokaha_backup')])
        for old in backups[:-keep]:
            os.remove(old)
            self.stdout.write(f"🗑️ Supprimé : {old}")
        
        # Envoi email (optionnel)
        email = options.get('email')
        if email and getattr(settings, 'EMAIL_HOST', None):
            try:
                msg = EmailMessage()
                msg['Subject'] = f"🐔 Backup DOKAHA - {timestamp}"
                msg['From'] = settings.DEFAULT_FROM_EMAIL
                msg['To'] = email
                msg.set_content(f"Backup DOKAHA du {timestamp}\n\nFichier joint : {os.path.basename(backup_file)}")
                
                with open(backup_file, 'rb') as f:
                    msg.add_attachment(f.read(), maintype='application', subtype='gzip', filename=os.path.basename(backup_file))
                
                with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    if settings.EMAIL_USE_TLS: server.starttls()
                    if settings.EMAIL_HOST_USER: server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    server.send_message(msg)
                self.stdout.write(self.style.SUCCESS(f"📧 Backup envoyé à {email}"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Échec envoi email : {e}"))
