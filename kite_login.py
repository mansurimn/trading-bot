from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# =========================
# 🔴 LOGGER SETUP
# =========================
def setup_logger():
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = f"logs/kite_login_{today}.log"

    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_filename)
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logging.info("===== KITE LOGIN STARTED =====")

setup_logger()

# =========================
# 🔴 LOAD CONFIG
# =========================
try:
    load_dotenv()

    API_KEY = os.getenv("KITE_API_KEY")
    API_SECRET = os.getenv("KITE_API_SECRET")

    if not API_KEY or not API_SECRET:
        raise ValueError("KITE_API_KEY or KITE_API_SECRET missing in .env")

    logging.info("Environment variables loaded successfully")

except Exception as e:
    logging.error(f"Config error: {str(e)}")
    exit(1)

# =========================
# 🔴 INIT KITE
# =========================
try:
    kite = KiteConnect(api_key=API_KEY)
    logging.info("KiteConnect initialized")

except Exception as e:
    logging.error(f"Kite initialization failed: {str(e)}")
    exit(1)

# =========================
# 🔴 STEP 1: LOGIN URL
# =========================
try:
    login_url = kite.login_url()
    logging.info("Login URL generated")

    print("\n👉 Open this URL in browser and login:\n")
    print(login_url)

except Exception as e:
    logging.error(f"Failed to generate login URL: {str(e)}")
    exit(1)

# =========================
# 🔴 STEP 2: INPUT TOKEN
# =========================
try:
    request_token = input("\nEnter request_token from URL: ").strip()

    if not request_token:
        raise ValueError("Request token cannot be empty")

    logging.info("Request token received")

except Exception as e:
    logging.error(f"Input error: {str(e)}")
    exit(1)

# =========================
# 🔴 STEP 3: GENERATE ACCESS TOKEN
# =========================
try:
    data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = data["access_token"]

    logging.info("Access token generated successfully")

    print("\n✅ Access Token Generated:\n")
    print(access_token)

except Exception as e:
    logging.error(f"Access token generation failed: {str(e)}")
    print("\n❌ Failed to generate access token")
    exit(1)

# =========================
# 🔴 STEP 4: SAVE TO .env
# =========================
try:
    env_path = ".env"

    if not os.path.exists(env_path):
        raise FileNotFoundError(".env file not found")

    with open(env_path, "r") as file:
        lines = file.readlines()

    with open(env_path, "w") as file:
        found = False
        for line in lines:
            if line.startswith("KITE_ACCESS_TOKEN="):
                file.write(f"KITE_ACCESS_TOKEN={access_token}\n")
                found = True
            else:
                file.write(line)

        if not found:
            file.write(f"\nKITE_ACCESS_TOKEN={access_token}\n")

    logging.info("Access token saved to .env successfully")
    print("\n✅ Access token saved to .env")

except Exception as e:
    logging.error(f"Failed to update .env: {str(e)}")
    print("\n⚠️ Could not save token automatically. Please update manually.")

# =========================
# 🔴 DONE
# =========================
logging.info("===== KITE LOGIN COMPLETED =====")
print("\n🎯 Setup complete. You can now run your bot.")