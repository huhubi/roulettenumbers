from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import random
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

game_data = {
    "balance": 100,
    "history": [],  
    "current_bet": {"number": None, "amount": 0},  
    "running": True,
    "result": None
}

def get_color(number):
    if number == 0:
        return "grün"
    elif number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
        return "rot"
    else:
        return "schwarz"

def play_game():
    while game_data["running"]:
        time.sleep(10)  
        
        number = random.randint(0, 36)
        color = get_color(number)
        game_data["history"].append((number, color))
        game_data["result"] = {"number": number, "color": color}
        
        if game_data["current_bet"]["amount"] > 0:
            if game_data["current_bet"]["number"] == number:
                winnings = game_data["current_bet"]["amount"] * 35  
                game_data["balance"] += winnings
                result_text = f"Gewonnen! Du erhältst {winnings}€."
            else:
                game_data["balance"] -= game_data["current_bet"]["amount"]
                result_text = f"Verloren. Du verlierst {game_data['current_bet']['amount']}€."
        else:
            result_text = "Kein Einsatz gemacht."
        
        game_data["current_bet"] = {"number": None, "amount": 0}

        total_games = len(game_data["history"])
        number_counts = {num: sum(1 for n, _ in game_data["history"] if n == num) for num in range(37)}
        number_probs = {num: (count / total_games) * 100 if total_games > 0 else 0 for num, count in number_counts.items()}

        socketio.emit('game_update', {
            "result": {"number": number, "color": color},
            "balance": game_data["balance"],
            "result_text": result_text,
            "statistics": {
                "total_games": total_games,
                "number_probs": number_probs
            }
        })

@app.route('/')
def index():
    return render_template('index.html', balance=game_data["balance"])

@app.route('/place_bet', methods=['POST'])
def place_bet():
    data = request.json
    try:
        number = int(data.get('number'))
        amount = int(data.get('amount'))
    except ValueError:
        return jsonify({"error": "Ungültige Eingabe. Bitte eine Zahl und einen Betrag angeben."}), 400

    if number < 0 or number > 36:
        return jsonify({"error": "Ungültige Zahl. Wähle eine Zahl zwischen 0 und 36."}), 400
    if amount <= 0 or amount > game_data["balance"]:
        return jsonify({"error": "Ungültiger Betrag. Setze innerhalb deines Guthabens."}), 400

    game_data["current_bet"] = {"number": number, "amount": amount}
    return jsonify({"message": f"Einsatz von {amount}€ auf Zahl {number} platziert!"})

@app.route('/reset', methods=['POST'])
def reset_balance():
    game_data["balance"] = 100
    return jsonify({"message": "Guthaben wurde zurückgesetzt!", "balance": game_data["balance"]})

threading.Thread(target=play_game, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)
