# ADR 003: A blueprint replaces the removed dynamic-plugin route

Superset 6.1's frontend still requests `GET /dynamic-plugins/api/read`. Flask-AppBuilder 5 removed the view that served it, and upstream closed the gap as won't-fix. If that request fails, plugin loading never finishes and every dashboard stays on the spinner. `BLUEPRINTS` is the supported way to add a route without patching Superset. The handler returns 200 with an empty list for anonymous callers and on any exception. It does not register when the path already exists, so a future Superset fix wins.
