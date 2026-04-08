import eel
eel.init('web')
try:
    eel.start('index.html', size=(1200, 800), port=8080, host='127.0.0.1', mode=None)
except Exception as e:
    print(f"Error: {e}")
