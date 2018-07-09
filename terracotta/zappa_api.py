from terracotta.flask_api import create_app

app_debug = create_app(debug=True)
app_production = create_app(debug=False)
