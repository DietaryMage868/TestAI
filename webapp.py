import os
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float, select, update, insert, exists
from sqlalchemy.orm import declarative_base, sessionmaker

app = Flask(__name__)
app.secret_key = 'demo-casino-key'

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    balance = Column(Integer, default=0)
    clicks = Column(Float, default=0)
    ref_id = Column(String)
    is_new = Column(Integer, default=1)

class GlobalCounter(Base):
    __tablename__ = 'global_counter'
    id = Column(Integer, primary_key=True)
    value = Column(Integer)

# Создание таблиц (один раз при старте)
with engine.begin() as conn:
    Base.metadata.create_all(conn)
    # Если нет глобального счётчика — создать
    if not conn.execute(select(GlobalCounter).where(GlobalCounter.id == 1)).first():
        conn.execute(insert(GlobalCounter).values(id=1, value=1000000))

def get_user(user_id):
    with Session() as session:
        return session.get(User, user_id)

def create_user(user_id, ref_id=None):
    with Session() as session:
        if not session.get(User, user_id):
            user = User(user_id=user_id, ref_id=ref_id)
            session.add(user)
            session.commit()

def update_user(user_id, **kwargs):
    with Session() as session:
        session.query(User).filter_by(user_id=user_id).update(kwargs)
        session.commit()

def get_counter():
    with Session() as session:
        counter = session.get(GlobalCounter, 1)
        return counter.value if counter else 0

def decrement_counter():
    with Session() as session:
        counter = session.get(GlobalCounter, 1)
        if counter.value > 0:
            counter.value -= 1
            session.commit()
        return counter.value

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
                update_user(ref_id, clicks=max(ref.clicks-1, 0))
    # Клик
    update_user(user_id, clicks=user.clicks+1)
    # 50% от кликов идут пригласившему
    if user and user.ref_id:
        ref = get_user(user.ref_id)
        if ref:
            update_user(user.ref_id, clicks=ref.clicks+0.5)
    counter = decrement_counter()
    # Если дошли до нуля — всем начислить 10 робуксов
    if counter == 0:
        with Session() as session:
            session.query(User).filter(User.clicks > 0).update({User.balance: User.balance + 10}, synchronize_session=False)
            session.commit()
    return jsonify({'counter': counter})

@app.route('/api/status', methods=['GET'])
def api_status():
    user_id = request.args.get('user_id')
    user = get_user(user_id)
    counter = get_counter()
    return jsonify({'counter': counter, 'balance': user.balance if user else 0, 'clicks': user.clicks if user else 0})

@app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    user_id = request.json.get('user_id')
    amount = int(request.json.get('amount'))
    user = get_user(user_id)
    if not user or user.balance < amount or amount < 100:
        return jsonify({'success': False, 'error': 'Недостаточно средств или сумма меньше 100'}), 400
    update_user(user_id, balance=user.balance-amount)
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
        if ref_id:
            ref = get_user(ref_id)
            if ref:
                update_user(ref_id, clicks=max(ref.clicks-1000, 0))
    if user and user.ref_id:
        ref = get_user(user.ref_id)
        if ref:
            update_user(user.ref_id, clicks=ref.clicks + user.clicks * 0.5)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(port=8080, debug=True)
