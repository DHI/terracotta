"""app.py

Instantiated versions of the Flask API.
"""

from terracotta.api import create_app

app_debug = create_app(debug=True)
app_production = create_app(debug=False)
