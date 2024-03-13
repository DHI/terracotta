import os
from terracotta.client.flask_api import create_app

TERRACOTTA_API_URL = os.environ["TERRACOTTA_API_URL"]

client_app = create_app(TERRACOTTA_API_URL)
