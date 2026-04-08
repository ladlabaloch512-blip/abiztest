from bottle import route, run, template

@route('/')
def index():
    return '<b>Hello!</b>!'

run(host='localhost', port=8080)
