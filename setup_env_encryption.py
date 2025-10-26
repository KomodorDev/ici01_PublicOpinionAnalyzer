from services.settings_service import SettingsService

def main():
    # Choose environment file (.env.dev, .env.prod, etc.)
    s = SettingsService(env="dev")

    # Generate a new encryption key if not present
    s.generate_key(password="admin")  # only needed once per project

    # Encrypt the .env file
    s.encrypt_env()

if __name__ == "__main__":
    main()
