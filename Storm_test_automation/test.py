# app.py
import os

def load_env():
    with open('C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\.env') as f:
        for line in f:
            # Ignore comments and empty lines
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Load the environment variables
load_env()

# Now you can access them using os.getenv
my_secret_key = os.getenv('DLL_PATH')
database_url = os.getenv('PACKAGE')
debug_mode = os.getenv('STORMTEST')

print("Secret Key:", my_secret_key)
print("Database URL:", database_url)
print("Debug Mode:", debug_mode)
