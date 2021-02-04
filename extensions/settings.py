import os

class Settings:
    def __init__(self):
        self.ADMIN_ROLE=os.getenv('BOT_ADMIN_ROLE','Support')
        self.SUPER_COACH_ROLE=os.getenv('BOT_SUPER_COACH_ROLE','SuperCoach')
        self.COACH_ROLE=os.getenv('BOT_COACH_ROLE','Coach')
        self.FACILITATEUR_ROLE=os.getenv('BOT_FACILITATEUR_ROLE','Facilitateur')
        self.WELCOME_MODE=os.getenv('BOT_WELCOME_MODE', 'close')  #mode 'open' ou 'close'
        self.TEAM_PREFIX=os.getenv('BOT_TEAM_PREFIX', 'Equipe-') 