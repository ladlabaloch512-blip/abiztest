import eel
eel.init('web')
print("Starting eel")
try:
    eel.start('index.html', mode=None, port=8000, host='localhost')
except Exception as e:
    print(f"Error: {e}")
