import sqlite3
import os
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'demo-casino-key'

DB_PATH = 'clicker.db'

# Инициализация базы данных
if not os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        ref_id TEXT,
        is_new INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE global_counter (
        id INTEGER PRIMARY KEY, value INTEGER
    )''')
    c.execute('INSERT INTO global_counter (id, value) VALUES (1, 1000000)')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, balance, clicks, ref_id, is_new FROM users WHERE user_id=?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, ref_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, ref_id) VALUES (?, ?)', (user_id, ref_id))
    conn.commit()
    conn.close()

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for k, v in kwargs.items():
        c.execute(f'UPDATE users SET {k}=? WHERE user_id=?', (v, user_id))
    conn.commit()
    conn.close()

def get_counter():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM global_counter WHERE id=1')
    value = c.fetchone()[0]
    conn.close()
    return value

def decrement_counter():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE global_counter SET value = value - 1 WHERE id=1')
    conn.commit()
    c.execute('SELECT value FROM global_counter WHERE id=1')
    value = c.fetchone()[0]
    conn.close()
    return value

@app.route('/api/click', methods=['POST'])
def api_click():
    user_id = request.json.get('user_id')
    ref_id = request.json.get('ref_id')
    user = get_user(user_id)
    if not user:
        create_user(user_id, ref_id)
        user = get_user(user_id)
        # Фед. система: у пригласившего минус 1 клик
        if ref_id:
            ref = get_user(ref_id)
            if ref:
                update_user(ref_id, clicks=max(ref[2]-1, 0))
    # Клик
    update_user(user_id, clicks=user[2]+1)
    # 50% от кликов идут пригласившему
    if user[3]:
        ref = get_user(user[3])
        if ref:
            update_user(user[3], clicks=ref[2]+0.5)
    counter = decrement_counter()
    # Если дошли до нуля — всем начислить 10 робуксов
    if counter == 0:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance + 10 WHERE clicks > 0')
        conn.commit()
        conn.close()
    return jsonify({'counter': counter})

@app.route('/api/status', methods=['GET'])
def api_status():
    user_id = request.args.get('user_id')
    user = get_user(user_id)
    counter = get_counter()
    return jsonify({'counter': counter, 'balance': user[1] if user else 0, 'clicks': user[2] if user else 0})

@app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    user_id = request.json.get('user_id')
    amount = int(request.json.get('amount'))
    user = get_user(user_id)
    if not user or user[1] < amount or amount < 100:
        return jsonify({'success': False, 'error': 'Недостаточно средств или сумма меньше 100'}), 400
    # Снимаем с баланса
    update_user(user_id, balance=user[1]-amount)
    # Отправить админу (здесь просто лог)
    print(f'Заявка на вывод: {user_id} — {amount} робуксов')
    return jsonify({'success': True})

@app.route('/api/referral_bonus', methods=['POST'])
def api_referral_bonus():
    user_id = request.json.get('user_id')
    ref_id = request.json.get('ref_id')
    user = get_user(user_id)
    if not user:
        create_user(user_id, ref_id)
        user = get_user(user_id)
        # Если есть реферал и пользователь новый
        if ref_id:
            ref = get_user(ref_id)
            if ref:
                # Минус 1000 кликов у пригласившего
                update_user(ref_id, clicks=max(ref[2]-1000, 0))
    # 50% от всех кликов пользователя идут пригласившему
    if user and user[3]:
        ref = get_user(user[3])
        if ref:
            update_user(user[3], clicks=ref[2] + user[2] * 0.5)
    return jsonify({'success': True})

HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Казино WebApp</title>
    <style>
        body { font-family: Arial, sans-serif; background: #181818; color: #fff; text-align: center; }
        .container { margin-top: 50px; }
        input, select, button { margin: 10px; padding: 8px; border-radius: 5px; border: none; }
        button { background: #4caf50; color: #fff; cursor: pointer; }
        .balance { margin: 20px 0; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Казино WebApp (Демо)</h2>
        <form method="post">
            <label>Валюта:
                <select name="currency">
                    <option value="BTC">BTC</option>
                    <option value="ETH">ETH</option>
                    <option value="USDT">USDT</option>
                </select>
            </label><br>
            <label>Сумма депозита:
                <input type="number" name="amount" min="1" required>
            </label><br>
            <button type="submit">Депозит</button>
        </form>
        {% if balance %}
        <div class="balance">Ваш баланс: {{ balance }} {{ currency }}</div>
        {% endif %}
        <form method="post">
            <input type="hidden" name="play" value="1">
            <button type="submit">Крутить слоты 🎰</button>
        </form>
        {% if result %}
        <div class="balance">Результат: {{ result }}</div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    balance = session.get('balance', 0)
    currency = session.get('currency', 'BTC')
    result = None
    if request.method == 'POST':
        if 'play' in request.form:
            # Слот-машина
            import random
            if balance <= 0:
                result = 'Недостаточно средств!'
            else:
                slots = [random.choice(['🍒','🍋','🍀','7️⃣','🍉','⭐']) for _ in range(3)]
                if len(set(slots)) == 1:
                    win = 10
                    balance += win
                    result = f'Выпало {" ".join(slots)}! Вы выиграли {win} {currency}!'
                else:
                    balance -= 1
                    result = f'Выпало {" ".join(slots)}. Вы проиграли 1 {currency}.'
                session['balance'] = balance
        else:
            # Депозит
            currency = request.form['currency']
            amount = int(request.form['amount'])
            balance += amount
            session['balance'] = balance
            session['currency'] = currency
    return render_template_string(HTML, balance=balance, currency=currency, result=result)

if __name__ == '__main__':
    app.run(port=8080, debug=True)
