from flask import Flask, render_template_string, request

app = Flask(__name__)

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

# Для демо: баланс хранится в сессии браузера (НЕ для продакшена)
from flask import session
app.secret_key = 'demo-casino-key'

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
