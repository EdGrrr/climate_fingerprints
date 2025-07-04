import json
from flask import Flask, render_template, request, Response, jsonify
from threading import Thread, Event
from queue import Queue
import os
import time

app = Flask(__name__,
            static_folder='static')
clients = []
DATA_FILE = "data.json"

# Load initial data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        stored_data = json.load(f)
else:
    stored_data = []

class Notifier(Thread):
    def __init__(self):
        super().__init__()
        self.updated = Event()
        self.data_queue = []

    def run(self):
        while True:
            self.updated.wait()
            self.updated.clear()
            while self.data_queue:
                data = self.data_queue.pop(0)
                for client in clients:
                    try:
                        client.put(data)
                    except:
                        pass

notifier = Notifier()
notifier.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/budget')
def budget():
    return render_template('index_budget.html')


@app.route('/fingerprint')
def users():
    return render_template('fingerprint.html')

@app.route('/trigger')
def trigger():
    x = request.args.get("x", type=float)
    y = request.args.get("y", type=float)
    t = request.args.get("t", type=float)
    value = request.args.get("value", default=50, type=float)  # Default: mid-scale

    if x is not None and y is not None and t is not None and (t>=0) and (t < 10000):
        data = {"x": x, "y": y, "value": value, "t": t, "submit_time": time.time()}
        stored_data.append(data)

        with open(DATA_FILE, "w") as f:
            json.dump(stored_data, f)

        notifier.data_queue.append(data)
        notifier.updated.set()
        return f"Added point: ({x}, {y}, {t}, value={value})"
    return "Missing x or y", 400

@app.route('/data')
def get_data():
    return jsonify(stored_data)

@app.route('/events')
def events():
    def stream():
        q = Queue()
        clients.append(q)
        try:
            while True:
                data = q.get()
                yield f"data: {json.dumps(data)}\n\n"
        except GeneratorExit:
            clients.remove(q)
    return Response(stream(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
