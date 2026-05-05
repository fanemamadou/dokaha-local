# WSGI minimal - ne dépend ni de Django, ni des models, ni des imports complexes
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)
    # Message simple, sans emoji dans les bytes
    body = '<!DOCTYPE html><html><body><h1>✅ WSGI fonctionne !</h1><p>Si tu vois ceci, le rechargement PythonAnywhere est OK.</p></body></html>'
    return [body.encode('utf-8')]
