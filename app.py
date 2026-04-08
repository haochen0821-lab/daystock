# -*- coding: utf-8 -*-
import os
import json
import math
import hashlib
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ══════════════════════════════════════════════════════════
#  Fee Calculation Engine
# ══════════════════════════════════════════════════════════

def get_fee_breakdown(market, trade_type, price, shares, broker_fee_usd=0.0,
                      discount=1.0, avg_cost=None, held_shares=0):
    """Unified fee calculation for TW and US markets.
    Returns dict with individual fee items and totals.
    """
    result = {
        'commission': 0.0,
        'transaction_tax': 0.0,
        'health_premium': 0.0,
        'sec_fee': 0.0,
        'total_fees': 0.0,
        'net_amount': 0.0,
        'gross_amount': price * shares,
        'health_premium_triggered': False,
    }

    if market == 'TW':
        # Commission: 0.1425% * discount, min NT$20
        commission = price * shares * 0.001425 * discount
        commission = max(commission, 20.0)
        result['commission'] = round(commission)

        if trade_type == 'sell':
            # Transaction tax: 0.3% of sell amount
            result['transaction_tax'] = round(price * shares * 0.003)

            # Health premium: 2.11% if sell profit >= NT$20,000
            if avg_cost is not None:
                profit = (price - avg_cost) * shares
                if profit >= 20000:
                    result['health_premium'] = round(price * shares * 0.0211)
                    result['health_premium_triggered'] = True

        result['total_fees'] = result['commission'] + result['transaction_tax'] + result['health_premium']

        if trade_type == 'buy':
            result['net_amount'] = result['gross_amount'] + result['total_fees']
        else:
            result['net_amount'] = result['gross_amount'] - result['total_fees']

    elif market == 'US':
        result['commission'] = round(broker_fee_usd, 4)

        if trade_type == 'sell':
            # SEC Fee: 0.00278% of sell amount, min $0.01
            sec = price * shares * 0.0000278
            sec = max(sec, 0.01) if sec > 0 else 0
            result['sec_fee'] = round(sec, 4)

        result['total_fees'] = result['commission'] + result['sec_fee']

        if trade_type == 'buy':
            result['net_amount'] = round(result['gross_amount'] + result['total_fees'], 4)
        else:
            result['net_amount'] = round(result['gross_amount'] - result['total_fees'], 4)

    return result


# ══════════════════════════════════════════════════════════
#  Flask App Setup
# ══════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = 'daystock-secret-key-2026'

db_path = os.environ.get('DATABASE_URL', 'sqlite:////data/daystock.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ══════════════════════════════════════════════════════════
#  DB Models (11)
# ══════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='member')  # member, admin, superadmin
    status = db.Column(db.String(20), default='active')  # active, disabled
    default_market = db.Column(db.String(5), default='TW')
    commission_discount = db.Column(db.Float, default=0.6)
    concentration_threshold = db.Column(db.Float, default=30.0)
    anniversary_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    market = db.Column(db.String(5), nullable=False)  # TW, US
    trade_type = db.Column(db.String(10), nullable=False)  # buy, sell
    symbol = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    shares = db.Column(db.Float, nullable=False)
    trade_date = db.Column(db.Date, nullable=False)
    account = db.Column(db.String(50), default='')
    reason_tag = db.Column(db.String(20), default='')
    note = db.Column(db.Text, default='')
    commission = db.Column(db.Float, default=0.0)
    transaction_tax = db.Column(db.Float, default=0.0)
    health_premium = db.Column(db.Float, default=0.0)
    sec_fee = db.Column(db.Float, default=0.0)
    total_fees = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    market = db.Column(db.String(5), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'symbol', 'market'),)


class Dividend(db.Model):
    __tablename__ = 'dividends'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    market = db.Column(db.String(5), nullable=False)
    ex_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remind_days = db.Column(db.Integer, default=7)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Journal(db.Model):
    __tablename__ = 'journals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    journal_date = db.Column(db.Date, nullable=False)
    mood = db.Column(db.String(10), default='')
    market_view = db.Column(db.String(10), default='')
    content = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'journal_date'),)


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    summary = db.Column(db.String(500), default='')
    category = db.Column(db.String(20), default='concept')  # concept, glossary, abbreviation, practical
    tags = db.Column(db.Text, default='')  # comma-separated
    published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookmarkFolder(db.Model):
    __tablename__ = 'bookmark_folders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'color'),)


class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('bookmark_folders.id'), nullable=False)
    note = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    tags = db.Column(db.Text, default='')  # JSON array of {label, color}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PortfolioMember(db.Model):
    __tablename__ = 'portfolio_members'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    market = db.Column(db.String(5), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserSetting(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    settings_json = db.Column(db.Text, default='{}')


# ══════════════════════════════════════════════════════════
#  Init DB
# ══════════════════════════════════════════════════════════

def init_db():
    db.create_all()
    # Create default superadmin if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@daystock.com',
            password_hash=generate_password_hash('admin1234'),
            role='superadmin',
            status='active'
        )
        db.session.add(admin)
        db.session.commit()
        print('Created default superadmin: admin / admin1234')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ══════════════════════════════════════════════════════════
#  Helper: role check decorators
# ══════════════════════════════════════════════════════════

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role not in ('admin', 'superadmin'):
            return jsonify({'error': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated


def superadmin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'superadmin':
            return jsonify({'error': 'Superadmin required'}), 403
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════
#  Helper: FIFO matching
# ══════════════════════════════════════════════════════════

def fifo_match(trades_list):
    """FIFO match buy/sell trades for a single symbol.
    Returns list of matched pairs with realized P&L.
    """
    buys = []
    matched = []

    for t in sorted(trades_list, key=lambda x: (x['trade_date'], x['id'])):
        if t['trade_type'] == 'buy':
            buys.append({
                'id': t['id'],
                'price': t['price'],
                'shares': t['shares'],
                'remaining': t['shares'],
                'date': t['trade_date'],
                'commission': t.get('commission', 0),
                'total_fees': t.get('total_fees', 0),
                'reason_tag': t.get('reason_tag', ''),
                'account': t.get('account', ''),
            })
        elif t['trade_type'] == 'sell':
            sell_remaining = t['shares']
            sell_price = t['price']
            sell_date = t['trade_date']
            sell_fees = t.get('total_fees', 0)
            sell_shares_total = t['shares']

            while sell_remaining > 0 and buys:
                buy = buys[0]
                match_shares = min(sell_remaining, buy['remaining'])

                # Proportional fee allocation
                buy_fee_portion = (match_shares / buy['shares']) * buy['total_fees']
                sell_fee_portion = (match_shares / sell_shares_total) * sell_fees

                buy_cost = buy['price'] * match_shares + buy_fee_portion
                sell_revenue = sell_price * match_shares - sell_fee_portion
                realized_pnl = sell_revenue - buy_cost

                hold_days = 0
                try:
                    bd = buy['date'] if isinstance(buy['date'], date) else datetime.strptime(str(buy['date']), '%Y-%m-%d').date()
                    sd = sell_date if isinstance(sell_date, date) else datetime.strptime(str(sell_date), '%Y-%m-%d').date()
                    hold_days = (sd - bd).days
                except:
                    pass

                matched.append({
                    'buy_id': buy['id'],
                    'sell_id': t['id'],
                    'symbol': t.get('symbol', ''),
                    'market': t.get('market', ''),
                    'shares': match_shares,
                    'buy_price': buy['price'],
                    'sell_price': sell_price,
                    'buy_date': str(buy['date']),
                    'sell_date': str(sell_date),
                    'buy_fees': round(buy_fee_portion, 4),
                    'sell_fees': round(sell_fee_portion, 4),
                    'realized_pnl': round(realized_pnl, 4),
                    'return_pct': round((realized_pnl / buy_cost) * 100, 2) if buy_cost > 0 else 0,
                    'hold_days': hold_days,
                    'reason_tag': buy.get('reason_tag', '') or t.get('reason_tag', ''),
                    'account': buy.get('account', '') or t.get('account', ''),
                })

                buy['remaining'] -= match_shares
                sell_remaining -= match_shares

                if buy['remaining'] <= 0:
                    buys.pop(0)

    return matched


# ══════════════════════════════════════════════════════════
#  Helper: yfinance wrappers
# ══════════════════════════════════════════════════════════

def yf_symbol(symbol, market):
    """Convert symbol to yfinance format."""
    if market == 'TW':
        s = symbol.replace('.TW', '')
        return f'{s}.TW'
    return symbol


def get_quote(symbol, market):
    """Get real-time quote for a stock."""
    import yfinance as yf
    import math
    try:
        ticker = yf.Ticker(yf_symbol(symbol, market))
        hist = ticker.history(period='5d')
        if hist.empty:
            return None
        # Drop NaN rows to handle intraday/delayed data
        closes = hist['Close'].dropna()
        if closes.empty:
            return None
        current = float(closes.iloc[-1])
        if math.isnan(current):
            return None
        prev = float(closes.iloc[-2]) if len(closes) >= 2 else current
        if math.isnan(prev):
            prev = current
        change = current - prev
        change_pct = (change / prev * 100) if prev != 0 else 0
        return {
            'symbol': symbol,
            'market': market,
            'price': round(current, 4),
            'change': round(change, 4),
            'change_pct': round(change_pct, 2),
        }
    except Exception:
        return None


def get_history(symbol, market, period='1y'):
    """Get historical OHLCV data."""
    import yfinance as yf
    try:
        ticker = yf.Ticker(yf_symbol(symbol, market))
        hist = ticker.history(period=period)
        if hist.empty:
            return []
        data = []
        for idx, row in hist.iterrows():
            data.append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 4),
                'high': round(float(row['High']), 4),
                'low': round(float(row['Low']), 4),
                'close': round(float(row['Close']), 4),
                'volume': int(row['Volume']),
            })
        return data
    except:
        return []


def get_dividend_info(symbol, market):
    """Get dividend info from yfinance."""
    import yfinance as yf
    try:
        ticker = yf.Ticker(yf_symbol(symbol, market))
        divs = ticker.dividends
        if divs.empty:
            return []
        result = []
        for idx, val in divs.items():
            result.append({
                'ex_date': idx.strftime('%Y-%m-%d'),
                'amount': round(float(val), 4),
            })
        return result[-10:]  # last 10
    except:
        return []


# ══════════════════════════════════════════════════════════
#  Auth Routes
# ══════════════════════════════════════════════════════════

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else None
        username = data.get('username', '').strip() if data else request.form.get('username', '').strip()
        password = data.get('password', '') if data else request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if user.status == 'disabled':
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Account disabled'})
                return render_template('login.html', error='Account disabled')
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful'})
            return redirect(url_for('dashboard'))

        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else None
        username = data.get('username', '').strip() if data else request.form.get('username', '').strip()
        email = data.get('email', '').strip() if data else request.form.get('email', '').strip()
        password = data.get('password', '') if data else request.form.get('password', '')

        if len(password) < 8:
            msg = 'Password must be at least 8 characters'
            if request.is_json:
                return jsonify({'success': False, 'message': msg})
            return render_template('register.html', error=msg)

        if User.query.filter((User.username == username) | (User.email == email)).first():
            msg = 'Username or email already taken'
            if request.is_json:
                return jsonify({'success': False, 'message': msg})
            return render_template('register.html', error=msg)

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role='member',
            status='active'
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)

        if request.is_json:
            return jsonify({'success': True, 'message': 'Registered successfully'})
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════
#  Page Routes
# ══════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/trades')
@login_required
def trades():
    return render_template('trades.html')

@app.route('/watchlist')
@login_required
def watchlist():
    return render_template('watchlist.html')

@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@app.route('/simulation')
@login_required
def simulation():
    return render_template('simulation.html')

@app.route('/report')
@login_required
def report():
    return render_template('report.html')

@app.route('/dividends')
@login_required
def dividends():
    return render_template('dividends.html')

@app.route('/journal')
@login_required
def journal():
    return render_template('journal.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/academy')
@login_required
def academy():
    return render_template('academy.html')

@app.route('/academy/manage')
@login_required
def academy_manage():
    if current_user.role not in ('admin', 'superadmin'):
        return redirect(url_for('academy'))
    return render_template('academy_manage.html')

@app.route('/academy/<int:article_id>')
@login_required
def academy_article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('academy_article.html', article=article)

@app.route('/bookmarks')
@login_required
def bookmarks():
    return render_template('bookmarks.html')

@app.route('/portfolios')
@login_required
def portfolios():
    return render_template('portfolios.html')

@app.route('/portfolios/<int:portfolio_id>')
@login_required
def portfolio_detail(portfolio_id):
    portfolio = Portfolio.query.filter_by(id=portfolio_id, user_id=current_user.id).first_or_404()
    return render_template('portfolio_detail.html', portfolio=portfolio)

@app.route('/admin')
@login_required
def admin_page():
    if current_user.role not in ('admin', 'superadmin'):
        return redirect(url_for('dashboard'))
    return render_template('admin.html')

@app.route('/version')
def version_info():
    try:
        with open('version.json', 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'version': 'dev', 'timestamp': datetime.utcnow().isoformat()})


# ══════════════════════════════════════════════════════════
#  Core Data API
# ══════════════════════════════════════════════════════════

@app.route('/api/stock/quote')
@login_required
def api_stock_quote():
    symbol = request.args.get('symbol', '')
    market = request.args.get('market', 'US')
    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400
    quote = get_quote(symbol, market)
    if quote:
        return jsonify(quote)
    return jsonify({'error': 'Quote not available'}), 404


@app.route('/api/stock/history')
@login_required
def api_stock_history():
    symbol = request.args.get('symbol', '')
    market = request.args.get('market', 'US')
    period_raw = request.args.get('period', '1y')
    # Map frontend shorthand to yfinance period format
    period_map = {'1M': '1mo', '3M': '3mo', '6M': '6mo', '1Y': '1y', '5Y': '5y'}
    period = period_map.get(period_raw, period_raw)
    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400
    data = get_history(symbol, market, period)
    return jsonify(data)


@app.route('/api/trades', methods=['GET'])
@login_required
def api_get_trades():
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date.desc()).all()
    result = []
    for t in trades:
        result.append({
            'id': t.id,
            'market': t.market,
            'trade_type': t.trade_type,
            'symbol': t.symbol,
            'price': t.price,
            'shares': t.shares,
            'trade_date': t.trade_date.isoformat(),
            'account': t.account,
            'reason_tag': t.reason_tag,
            'note': t.note,
            'commission': t.commission,
            'transaction_tax': t.transaction_tax,
            'health_premium': t.health_premium,
            'sec_fee': t.sec_fee,
            'total_fees': t.total_fees,
            'net_amount': t.net_amount,
            'health_premium_triggered': t.health_premium > 0,
        })
    return jsonify(result)


@app.route('/api/trades', methods=['POST'])
@login_required
def api_add_trade():
    data = request.get_json()
    market = data.get('market', 'TW')
    trade_type = data.get('trade_type', 'buy')
    symbol = data.get('symbol', '').strip().upper()
    price = float(data.get('price', 0))
    shares = float(data.get('shares', 0))
    trade_date_str = data.get('trade_date', '')
    account = (data.get('account') or '').strip()
    reason_tag = data.get('reason_tag') or ''
    note = (data.get('note') or '').strip()
    broker_fee = float(data.get('broker_fee', 0))

    if not symbol or price <= 0 or shares <= 0 or not trade_date_str:
        return jsonify({'error': 'Missing required fields'}), 400

    trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()

    # Calculate avg_cost for health premium check
    avg_cost = None
    if market == 'TW' and trade_type == 'sell':
        existing_buys = Trade.query.filter_by(
            user_id=current_user.id, symbol=symbol, market='TW', trade_type='buy'
        ).all()
        if existing_buys:
            total_cost = sum(t.price * t.shares for t in existing_buys)
            total_shares = sum(t.shares for t in existing_buys)
            if total_shares > 0:
                avg_cost = total_cost / total_shares

    fees = get_fee_breakdown(
        market=market, trade_type=trade_type, price=price, shares=shares,
        broker_fee_usd=broker_fee, discount=current_user.commission_discount,
        avg_cost=avg_cost
    )

    trade = Trade(
        user_id=current_user.id,
        market=market,
        trade_type=trade_type,
        symbol=symbol,
        price=price,
        shares=shares,
        trade_date=trade_date,
        account=account,
        reason_tag=reason_tag,
        note=note,
        commission=fees['commission'],
        transaction_tax=fees['transaction_tax'],
        health_premium=fees['health_premium'],
        sec_fee=fees['sec_fee'],
        total_fees=fees['total_fees'],
        net_amount=fees['net_amount'],
    )
    db.session.add(trade)
    db.session.commit()

    return jsonify({'success': True, 'id': trade.id, 'fees': fees})


@app.route('/api/trades/<int:trade_id>', methods=['PUT'])
@login_required
def api_update_trade(trade_id):
    trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'account' in data:
        trade.account = data['account'].strip()
    if 'reason_tag' in data:
        trade.reason_tag = data['reason_tag']
    if 'note' in data:
        trade.note = data['note'].strip()
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/trades/<int:trade_id>', methods=['DELETE'])
@login_required
def api_delete_trade(trade_id):
    trade = Trade.query.filter_by(id=trade_id, user_id=current_user.id).first_or_404()
    db.session.delete(trade)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/holdings/<symbol>')
@login_required
def api_get_holding(symbol):
    """Return current holding info for a symbol (for smart sell form)."""
    symbol = symbol.strip().upper()
    # Get all buy and sell trades for this symbol
    buys = Trade.query.filter_by(user_id=current_user.id, symbol=symbol, trade_type='buy').all()
    sells = Trade.query.filter_by(user_id=current_user.id, symbol=symbol, trade_type='sell').all()

    total_buy_shares = sum(t.shares for t in buys)
    total_buy_cost = sum(t.price * t.shares for t in buys)
    total_sell_shares = sum(t.shares for t in sells)

    remaining_shares = total_buy_shares - total_sell_shares
    avg_cost = (total_buy_cost / total_buy_shares) if total_buy_shares > 0 else 0

    # Get market from most recent buy
    market = buys[-1].market if buys else 'TW'

    return jsonify({
        'symbol': symbol,
        'market': market,
        'remaining_shares': remaining_shares,
        'avg_cost': round(avg_cost, 4),
        'total_buy_shares': total_buy_shares,
        'total_sell_shares': total_sell_shares,
    })


@app.route('/api/fees/preview', methods=['POST'])
@login_required
def api_fees_preview():
    data = request.get_json()
    market = data.get('market', 'TW')
    trade_type = data.get('trade_type', 'buy')
    price = float(data.get('price', 0))
    shares = float(data.get('shares', 0))
    broker_fee = float(data.get('broker_fee', 0))
    symbol = data.get('symbol', '').strip().upper()

    avg_cost = None
    if market == 'TW' and trade_type == 'sell' and symbol:
        existing_buys = Trade.query.filter_by(
            user_id=current_user.id, symbol=symbol, market='TW', trade_type='buy'
        ).all()
        if existing_buys:
            total_cost = sum(t.price * t.shares for t in existing_buys)
            total_shares = sum(t.shares for t in existing_buys)
            if total_shares > 0:
                avg_cost = total_cost / total_shares

    fees = get_fee_breakdown(
        market=market, trade_type=trade_type, price=price, shares=shares,
        broker_fee_usd=broker_fee, discount=current_user.commission_discount,
        avg_cost=avg_cost
    )
    return jsonify(fees)


@app.route('/api/portfolio/summary')
@login_required
def api_portfolio_summary():
    """Get holdings summary with market values and P&L."""
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date).all()

    # Build holdings by symbol
    holdings = {}
    for t in trades:
        key = f"{t.symbol}_{t.market}"
        if key not in holdings:
            holdings[key] = {'symbol': t.symbol, 'market': t.market, 'buys': [], 'sells': []}
        trade_dict = {
            'id': t.id, 'price': t.price, 'shares': t.shares,
            'trade_date': t.trade_date, 'total_fees': t.total_fees,
            'trade_type': t.trade_type, 'commission': t.commission,
        }
        if t.trade_type == 'buy':
            holdings[key]['buys'].append(trade_dict)
        else:
            holdings[key]['sells'].append(trade_dict)

    # Calculate remaining shares via FIFO
    result = []
    total_market_value = 0
    total_cost = 0

    for key, h in holdings.items():
        buy_lots = []
        for b in sorted(h['buys'], key=lambda x: x['trade_date']):
            buy_lots.append({
                'price': b['price'],
                'shares': b['shares'],
                'remaining': b['shares'],
                'date': b['trade_date'],
                'fees_per_share': b['total_fees'] / b['shares'] if b['shares'] > 0 else 0,
            })

        for s in sorted(h['sells'], key=lambda x: x['trade_date']):
            rem = s['shares']
            while rem > 0 and buy_lots:
                lot = buy_lots[0]
                take = min(rem, lot['remaining'])
                lot['remaining'] -= take
                rem -= take
                if lot['remaining'] <= 0:
                    buy_lots.pop(0)

        # Remaining holdings
        total_shares = sum(l['remaining'] for l in buy_lots)
        if total_shares <= 0:
            continue

        avg_cost = 0
        total_cost_this = 0
        earliest_date = None
        for l in buy_lots:
            if l['remaining'] > 0:
                cost = l['price'] * l['remaining'] + l['fees_per_share'] * l['remaining']
                total_cost_this += cost
                if earliest_date is None or l['date'] < earliest_date:
                    earliest_date = l['date']
        avg_cost = total_cost_this / total_shares if total_shares > 0 else 0

        # Get current price
        quote = get_quote(h['symbol'], h['market'])
        current_price = quote['price'] if quote else 0
        market_value = current_price * total_shares
        unrealized_pnl = market_value - total_cost_this

        # Dividend yield estimation
        div_yield = 0
        annual_dividend = 0
        try:
            import yfinance as yf
            ticker = yf.Ticker(yf_symbol(h['symbol'], h['market']))
            info = ticker.info
            div_yield = info.get('dividendYield', 0) or 0
            div_yield *= 100
            dps = info.get('dividendRate', 0) or 0
            annual_dividend = dps * total_shares
        except:
            pass

        result.append({
            'symbol': h['symbol'],
            'market': h['market'],
            'shares': total_shares,
            'avg_cost': round(avg_cost, 4),
            'current_price': current_price,
            'market_value': round(market_value, 4),
            'total_cost': round(total_cost_this, 4),
            'unrealized_pnl': round(unrealized_pnl, 4),
            'unrealized_pnl_pct': round((unrealized_pnl / total_cost_this) * 100, 2) if total_cost_this > 0 else 0,
            'dividend_yield': round(div_yield, 2),
            'annual_dividend': round(annual_dividend, 2),
            'earliest_buy_date': str(earliest_date) if earliest_date else '',
        })

        total_market_value += market_value
        total_cost += total_cost_this

    return jsonify({
        'holdings': result,
        'total_market_value': round(total_market_value, 4),
        'total_cost': round(total_cost, 4),
        'total_unrealized_pnl': round(total_market_value - total_cost, 4),
        'total_unrealized_pnl_pct': round(((total_market_value - total_cost) / total_cost) * 100, 2) if total_cost > 0 else 0,
        'holdings_count': len(result),
    })


@app.route('/api/portfolio/anniversaries')
@login_required
def api_portfolio_anniversaries():
    """US stock holding anniversary countdown."""
    trades = Trade.query.filter_by(user_id=current_user.id, market='US').order_by(Trade.trade_date).all()

    holdings = {}
    for t in trades:
        if t.symbol not in holdings:
            holdings[t.symbol] = []
        holdings[t.symbol].append({
            'trade_type': t.trade_type,
            'shares': t.shares,
            'trade_date': t.trade_date,
        })

    result = []
    today = date.today()

    for symbol, trade_list in holdings.items():
        buy_lots = []
        for t in sorted(trade_list, key=lambda x: x['trade_date']):
            if t['trade_type'] == 'buy':
                buy_lots.append({'shares': t['shares'], 'remaining': t['shares'], 'date': t['trade_date']})
            else:
                rem = t['shares']
                for lot in buy_lots:
                    take = min(rem, lot['remaining'])
                    lot['remaining'] -= take
                    rem -= take
                    if rem <= 0:
                        break

        for lot in buy_lots:
            if lot['remaining'] > 0:
                anniversary = lot['date'] + timedelta(days=365)
                days_left = (anniversary - today).days
                result.append({
                    'symbol': symbol,
                    'buy_date': str(lot['date']),
                    'anniversary_date': str(anniversary),
                    'days_left': days_left,
                    'shares': lot['remaining'],
                    'status': 'done' if days_left <= 0 else ('warning' if days_left <= 30 else 'normal'),
                })

    result.sort(key=lambda x: x['days_left'])
    return jsonify(result)


@app.route('/api/portfolio/concentration')
@login_required
def api_portfolio_concentration():
    """Check position concentration."""
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date).all()

    # Build net holdings
    net = {}
    for t in trades:
        key = f"{t.symbol}_{t.market}"
        if key not in net:
            net[key] = {'symbol': t.symbol, 'market': t.market, 'shares': 0}
        if t.trade_type == 'buy':
            net[key]['shares'] += t.shares
        else:
            net[key]['shares'] -= t.shares

    # Get market values
    total_value = 0
    items = []
    for key, h in net.items():
        if h['shares'] <= 0:
            continue
        quote = get_quote(h['symbol'], h['market'])
        price = quote['price'] if quote else 0
        mv = price * h['shares']
        items.append({'symbol': h['symbol'], 'market': h['market'], 'market_value': mv})
        total_value += mv

    threshold = current_user.concentration_threshold
    alerts = []
    for item in items:
        pct = (item['market_value'] / total_value * 100) if total_value > 0 else 0
        item['percentage'] = round(pct, 2)
        if pct >= threshold:
            alerts.append(item)

    return jsonify({
        'items': items,
        'alerts': alerts,
        'threshold': threshold,
        'total_value': round(total_value, 4),
    })


@app.route('/api/accounts')
@login_required
def api_accounts():
    """Get user's used account names."""
    trades = Trade.query.filter_by(user_id=current_user.id).filter(Trade.account != '').all()
    accounts = list(set(t.account for t in trades))
    return jsonify(sorted(accounts))


# ══════════════════════════════════════════════════════════
#  Watchlist API
# ══════════════════════════════════════════════════════════

@app.route('/api/watchlist', methods=['GET'])
@login_required
def api_get_watchlist():
    items = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.added_at.desc()).all()
    result = []
    for w in items:
        result.append({
            'id': w.id,
            'symbol': w.symbol,
            'market': w.market,
        })
    return jsonify(result)


@app.route('/api/watchlist', methods=['POST'])
@login_required
def api_add_watchlist():
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    market = data.get('market', '')
    # Smart market detection: digits = TW, letters = US
    if not market:
        import re
        market = 'TW' if re.search(r'\d', symbol) else 'US'
    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400

    existing = Watchlist.query.filter_by(user_id=current_user.id, symbol=symbol, market=market).first()
    if existing:
        return jsonify({'error': 'Already in watchlist'}), 400

    w = Watchlist(user_id=current_user.id, symbol=symbol, market=market)
    db.session.add(w)
    db.session.commit()
    return jsonify({'success': True, 'id': w.id})


@app.route('/api/watchlist/<int:item_id>', methods=['DELETE'])
@login_required
def api_remove_watchlist(item_id):
    w = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(w)
    db.session.commit()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════
#  Analytics API
# ══════════════════════════════════════════════════════════

@app.route('/api/analytics/overview')
@login_required
def api_analytics_overview():
    """Win rate, heatmap, scatter, FX — all in one response."""
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date).all()
    trades_list = [{
        'id': t.id, 'symbol': t.symbol, 'market': t.market,
        'trade_type': t.trade_type, 'price': t.price, 'shares': t.shares,
        'trade_date': t.trade_date, 'total_fees': t.total_fees,
        'reason_tag': t.reason_tag, 'account': t.account,
    } for t in trades]

    # Group by symbol and FIFO match
    by_symbol = {}
    for t in trades_list:
        if t['symbol'] not in by_symbol:
            by_symbol[t['symbol']] = []
        by_symbol[t['symbol']].append(t)

    all_matched = []
    for symbol, tlist in by_symbol.items():
        all_matched.extend(fifo_match(tlist))

    # Overall win rate
    total = len(all_matched)
    wins = sum(1 for m in all_matched if m['realized_pnl'] > 0)
    losses = sum(1 for m in all_matched if m['realized_pnl'] <= 0)
    win_rate = round((wins / total) * 100, 2) if total > 0 else 0

    avg_win = 0
    avg_loss = 0
    win_trades = [m for m in all_matched if m['realized_pnl'] > 0]
    loss_trades = [m for m in all_matched if m['realized_pnl'] <= 0]
    if win_trades:
        avg_win = round(sum(m['return_pct'] for m in win_trades) / len(win_trades), 2)
    if loss_trades:
        avg_loss = round(sum(m['return_pct'] for m in loss_trades) / len(loss_trades), 2)

    profit_factor = round(
        sum(m['realized_pnl'] for m in win_trades) / abs(sum(m['realized_pnl'] for m in loss_trades)), 2
    ) if loss_trades and sum(m['realized_pnl'] for m in loss_trades) != 0 else 0

    # Win rate by market
    tw_matched = [m for m in all_matched if m.get('market') == 'TW']
    us_matched = [m for m in all_matched if m.get('market') == 'US']
    tw_win_rate = round(sum(1 for m in tw_matched if m['realized_pnl'] > 0) / len(tw_matched) * 100, 2) if tw_matched else 0
    us_win_rate = round(sum(1 for m in us_matched if m['realized_pnl'] > 0) / len(us_matched) * 100, 2) if us_matched else 0

    # Monthly P&L heatmap
    monthly = {}
    for m in all_matched:
        month_key = m['sell_date'][:7]  # YYYY-MM
        if month_key not in monthly:
            monthly[month_key] = 0
        monthly[month_key] += m['realized_pnl']
    heatmap = [{'month': k, 'pnl': round(v, 2)} for k, v in sorted(monthly.items())]

    # Holding days scatter
    scatter = [{
        'hold_days': m['hold_days'],
        'return_pct': m['return_pct'],
        'symbol': m['symbol'],
        'win': m['realized_pnl'] > 0,
    } for m in all_matched]

    # Hold days buckets
    buckets = [
        {'label': '0-7d', 'min': 0, 'max': 7},
        {'label': '8-30d', 'min': 8, 'max': 30},
        {'label': '31-90d', 'min': 31, 'max': 90},
        {'label': '91-365d', 'min': 91, 'max': 365},
        {'label': '>365d', 'min': 366, 'max': 99999},
    ]
    bucket_stats = []
    for b in buckets:
        items = [m for m in all_matched if b['min'] <= m['hold_days'] <= b['max']]
        if items:
            bucket_wins = sum(1 for m in items if m['realized_pnl'] > 0)
            bucket_stats.append({
                'label': b['label'],
                'count': len(items),
                'win_rate': round(bucket_wins / len(items) * 100, 2),
                'avg_return': round(sum(m['return_pct'] for m in items) / len(items), 2),
            })
        else:
            bucket_stats.append({'label': b['label'], 'count': 0, 'win_rate': 0, 'avg_return': 0})

    # FX rate
    fx_rate = None
    try:
        import yfinance as yf
        ticker = yf.Ticker('TWD=X')
        hist = ticker.history(period='5d')
        if not hist.empty:
            closes = hist['Close'].dropna()
            if not closes.empty:
                fx_rate = round(float(closes.iloc[-1]), 4)
    except Exception:
        pass

    return jsonify({
        'total_trades': total,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'tw_win_rate': tw_win_rate,
        'us_win_rate': us_win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'heatmap': heatmap,
        'scatter': scatter,
        'bucket_stats': bucket_stats,
        'matched_trades': all_matched,
        'fx_rate': fx_rate,
    })


@app.route('/api/analytics/reason_winrate')
@login_required
def api_reason_winrate():
    """Win rate analysis by trade reason tag."""
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date).all()
    trades_list = [{
        'id': t.id, 'symbol': t.symbol, 'market': t.market,
        'trade_type': t.trade_type, 'price': t.price, 'shares': t.shares,
        'trade_date': t.trade_date, 'total_fees': t.total_fees,
        'reason_tag': t.reason_tag, 'account': t.account,
    } for t in trades]

    by_symbol = {}
    for t in trades_list:
        if t['symbol'] not in by_symbol:
            by_symbol[t['symbol']] = []
        by_symbol[t['symbol']].append(t)

    all_matched = []
    for symbol, tlist in by_symbol.items():
        all_matched.extend(fifo_match(tlist))

    # Group by reason tag
    by_reason = {}
    for m in all_matched:
        tag = m.get('reason_tag', '') or 'untagged'
        if tag not in by_reason:
            by_reason[tag] = []
        by_reason[tag].append(m)

    result = []
    for tag, items in by_reason.items():
        wins = sum(1 for m in items if m['realized_pnl'] > 0)
        result.append({
            'reason_tag': tag,
            'total': len(items),
            'wins': wins,
            'win_rate': round(wins / len(items) * 100, 2),
            'avg_return': round(sum(m['return_pct'] for m in items) / len(items), 2),
            'avg_hold_days': round(sum(m['hold_days'] for m in items) / len(items), 1),
            'total_pnl': round(sum(m['realized_pnl'] for m in items), 2),
        })

    return jsonify(result)


@app.route('/api/report/realized')
@login_required
def api_report_realized():
    """Full realized P&L report with filters."""
    trades = Trade.query.filter_by(user_id=current_user.id).order_by(Trade.trade_date).all()
    trades_list = [{
        'id': t.id, 'symbol': t.symbol, 'market': t.market,
        'trade_type': t.trade_type, 'price': t.price, 'shares': t.shares,
        'trade_date': t.trade_date, 'total_fees': t.total_fees,
        'reason_tag': t.reason_tag, 'account': t.account,
    } for t in trades]

    by_symbol = {}
    for t in trades_list:
        if t['symbol'] not in by_symbol:
            by_symbol[t['symbol']] = []
        by_symbol[t['symbol']].append(t)

    all_matched = []
    for symbol, tlist in by_symbol.items():
        all_matched.extend(fifo_match(tlist))

    # Apply filters
    year = request.args.get('year', '')
    market = request.args.get('market', '')
    account = request.args.get('account', '')
    reason = request.args.get('reason_tag', '')
    profit_filter = request.args.get('profit', '')  # profit, loss, all

    filtered = all_matched
    if year:
        filtered = [m for m in filtered if m['sell_date'].startswith(year)]
    if market:
        filtered = [m for m in filtered if m.get('market') == market]
    if account:
        filtered = [m for m in filtered if m.get('account') == account]
    if reason:
        filtered = [m for m in filtered if m.get('reason_tag') == reason]
    if profit_filter == 'profit':
        filtered = [m for m in filtered if m['realized_pnl'] > 0]
    elif profit_filter == 'loss':
        filtered = [m for m in filtered if m['realized_pnl'] <= 0]

    # Summary by year
    by_year = {}
    for m in filtered:
        y = m['sell_date'][:4]
        if y not in by_year:
            by_year[y] = 0
        by_year[y] += m['realized_pnl']

    # Summary by account
    by_account = {}
    for m in filtered:
        a = m.get('account', '') or 'N/A'
        if a not in by_account:
            by_account[a] = 0
        by_account[a] += m['realized_pnl']

    # Summary by reason
    by_reason = {}
    for m in filtered:
        r = m.get('reason_tag', '') or 'untagged'
        if r not in by_reason:
            by_reason[r] = 0
        by_reason[r] += m['realized_pnl']

    total_pnl = sum(m['realized_pnl'] for m in filtered)

    return jsonify({
        'trades': filtered,
        'total_pnl': round(total_pnl, 2),
        'total_count': len(filtered),
        'by_year': {k: round(v, 2) for k, v in sorted(by_year.items())},
        'by_account': {k: round(v, 2) for k, v in by_account.items()},
        'by_reason': {k: round(v, 2) for k, v in by_reason.items()},
    })


@app.route('/api/market/overview')
@login_required
def api_market_overview():
    """Market barometer: SPY, QQQ, DIA, VIX, 0050, TWII, USD/TWD."""
    import yfinance as yf
    symbols = {
        'SPY': {'name': 'S&P 500', 'market': 'US'},
        'QQQ': {'name': 'Nasdaq', 'market': 'US'},
        'DIA': {'name': 'Dow Jones', 'market': 'US'},
        '^VIX': {'name': 'VIX', 'market': 'US'},
        '0050.TW': {'name': 'Taiwan 50', 'market': 'TW'},
        '^TWII': {'name': 'TAIEX', 'market': 'TW'},
        'TWD=X': {'name': 'USD/TWD', 'market': 'FX'},
    }

    result = []
    for sym, info in symbols.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='5d')
            if hist.empty:
                continue
            closes = hist['Close'].dropna()
            if closes.empty:
                continue
            current = round(float(closes.iloc[-1]), 2)
            prev = float(closes.iloc[-2]) if len(closes) >= 2 else current
            change = round(current - prev, 2)
            change_pct = round((change / prev) * 100, 2) if prev != 0 else 0
            result.append({
                'symbol': sym,
                'name': info['name'],
                'market': info['market'],
                'price': current,
                'change': change,
                'change_pct': change_pct,
            })
        except Exception:
            continue

    return jsonify(result)


# ══════════════════════════════════════════════════════════
#  Simulation API
# ══════════════════════════════════════════════════════════

@app.route('/api/simulate', methods=['POST'])
@login_required
def api_simulate():
    """Single-stock simulation (4 strategies)."""
    import yfinance as yf
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    market = data.get('market', 'US')
    strategy = data.get('strategy', 'fixed_shares')  # fixed_shares, fixed_amount, dca, custom
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    shares = float(data.get('shares', 0))
    amount = float(data.get('amount', 0))
    frequency = int(data.get('frequency', 30))
    custom_trades = data.get('custom_trades', [])

    if not symbol or not start_date or not end_date:
        return jsonify({'error': 'Missing required fields'}), 400

    # Get history
    ticker = yf.Ticker(yf_symbol(symbol, market))
    hist = ticker.history(start=start_date, end=end_date)
    if hist.empty:
        return jsonify({'error': 'No data available'}), 404

    # Benchmark
    bench_sym = 'SPY' if market == 'US' else '0050.TW'
    bench_ticker = yf.Ticker(bench_sym)
    bench_hist = bench_ticker.history(start=start_date, end=end_date)

    # Simulate
    sim_trades = []
    total_shares = 0
    total_cost = 0

    if strategy == 'fixed_shares':
        # Buy once at start
        first_price = float(hist['Close'].iloc[0])
        fees = get_fee_breakdown(market, 'buy', first_price, shares,
                                  discount=current_user.commission_discount)
        total_shares = shares
        total_cost = fees['net_amount']
        sim_trades.append({
            'date': hist.index[0].strftime('%Y-%m-%d'),
            'price': first_price, 'shares': shares, 'type': 'buy', 'fees': fees['total_fees'],
        })

    elif strategy == 'fixed_amount':
        # Buy at intervals
        dates = list(hist.index)
        i = 0
        while i < len(dates):
            price = float(hist['Close'].iloc[i])
            buy_shares = int(amount / price) if market == 'TW' else round(amount / price, 4)
            if buy_shares > 0:
                fees = get_fee_breakdown(market, 'buy', price, buy_shares,
                                          discount=current_user.commission_discount)
                total_shares += buy_shares
                total_cost += fees['net_amount']
                sim_trades.append({
                    'date': dates[i].strftime('%Y-%m-%d'),
                    'price': price, 'shares': buy_shares, 'type': 'buy', 'fees': fees['total_fees'],
                })
            i += frequency

    elif strategy == 'dca':
        # DCA: regular interval buying
        dates = list(hist.index)
        i = 0
        while i < len(dates):
            price = float(hist['Close'].iloc[i])
            buy_shares = int(amount / price) if market == 'TW' else round(amount / price, 4)
            if buy_shares > 0:
                fees = get_fee_breakdown(market, 'buy', price, buy_shares,
                                          discount=current_user.commission_discount)
                total_shares += buy_shares
                total_cost += fees['net_amount']
                sim_trades.append({
                    'date': dates[i].strftime('%Y-%m-%d'),
                    'price': price, 'shares': buy_shares, 'type': 'buy', 'fees': fees['total_fees'],
                })
            i += frequency

    elif strategy == 'custom':
        for ct in custom_trades:
            ct_date = ct.get('date', '')
            ct_type = ct.get('type', 'buy')
            ct_shares = float(ct.get('shares', 0))
            # Find closest trading day
            try:
                target = datetime.strptime(ct_date, '%Y-%m-%d')
                idx = hist.index.get_indexer([target], method='nearest')[0]
                price = float(hist['Close'].iloc[idx])
                actual_date = hist.index[idx].strftime('%Y-%m-%d')
                fees = get_fee_breakdown(market, ct_type, price, ct_shares,
                                          discount=current_user.commission_discount)
                if ct_type == 'buy':
                    total_shares += ct_shares
                    total_cost += fees['net_amount']
                else:
                    total_shares -= ct_shares
                    total_cost -= fees['net_amount']
                sim_trades.append({
                    'date': actual_date, 'price': price, 'shares': ct_shares,
                    'type': ct_type, 'fees': fees['total_fees'],
                })
            except:
                continue

    # Final value
    _closes = hist['Close'].dropna()
    last_price = float(_closes.iloc[-1]) if not _closes.empty else 0
    sell_fees = get_fee_breakdown(market, 'sell', last_price, total_shares,
                                   discount=current_user.commission_discount)
    final_value = sell_fees['net_amount']
    net_pnl = final_value - total_cost
    gross_pnl = last_price * total_shares - total_cost
    total_return_pct = round((net_pnl / total_cost) * 100, 2) if total_cost > 0 else 0
    gross_return_pct = round((gross_pnl / total_cost) * 100, 2) if total_cost > 0 else 0

    # CAGR
    try:
        sd = datetime.strptime(start_date, '%Y-%m-%d')
        ed = datetime.strptime(end_date, '%Y-%m-%d')
        years = (ed - sd).days / 365.25
        cagr = round(((final_value / total_cost) ** (1 / years) - 1) * 100, 2) if years > 0 and total_cost > 0 else 0
    except:
        cagr = 0

    # Max drawdown
    equity_curve = []
    running_shares = 0
    running_cost = 0
    trade_idx = 0
    sorted_trades = sorted(sim_trades, key=lambda x: x['date'])

    for i, (idx, row) in enumerate(hist.iterrows()):
        date_str = idx.strftime('%Y-%m-%d')
        while trade_idx < len(sorted_trades) and sorted_trades[trade_idx]['date'] <= date_str:
            st = sorted_trades[trade_idx]
            if st['type'] == 'buy':
                running_shares += st['shares']
                running_cost += st['price'] * st['shares'] + st['fees']
            else:
                running_shares -= st['shares']
            trade_idx += 1

        mv = float(row['Close']) * running_shares
        equity_curve.append({
            'date': date_str,
            'market_value': round(mv, 2),
            'cost': round(running_cost, 2),
        })

    # Calculate max drawdown from equity curve
    peak = 0
    max_dd = 0
    for ec in equity_curve:
        if ec['market_value'] > peak:
            peak = ec['market_value']
        if peak > 0:
            dd = (peak - ec['market_value']) / peak * 100
            if dd > max_dd:
                max_dd = dd

    # Benchmark comparison
    bench_return = 0
    if not bench_hist.empty:
        _bc = bench_hist['Close'].dropna()
        bench_first = float(_bc.iloc[0]) if not _bc.empty else 0
        bench_last = float(_bc.iloc[-1]) if not _bc.empty else 0
        bench_return = round(((bench_last - bench_first) / bench_first) * 100, 2)

    return jsonify({
        'symbol': symbol,
        'market': market,
        'strategy': strategy,
        'trades': sim_trades,
        'total_shares': total_shares,
        'total_cost': round(total_cost, 2),
        'final_value': round(final_value, 2),
        'net_pnl': round(net_pnl, 2),
        'gross_return_pct': gross_return_pct,
        'net_return_pct': total_return_pct,
        'cagr': cagr,
        'max_drawdown': round(max_dd, 2),
        'benchmark_symbol': bench_sym,
        'benchmark_return': bench_return,
        'vs_benchmark': round(total_return_pct - bench_return, 2),
        'equity_curve': equity_curve,
    })


@app.route('/api/simulate/compare', methods=['POST'])
@login_required
def api_simulate_compare():
    """Multi-stock comparison (up to 6)."""
    import yfinance as yf
    data = request.get_json()
    symbols = data.get('symbols', [])[:6]
    market = data.get('market', 'US')
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    mode = data.get('mode', 'fixed_shares')  # fixed_shares, fixed_amount, dca
    shares = float(data.get('shares', 100))
    amount = float(data.get('amount', 10000))
    frequency = int(data.get('frequency', 30))

    results = []
    for sym in symbols:
        sym = sym.strip().upper()
        ticker = yf.Ticker(yf_symbol(sym, market))
        hist = ticker.history(start=start_date, end=end_date)
        if hist.empty:
            continue

        # Standardize to base 100
        _hc = hist['Close'].dropna()
        if _hc.empty:
            continue
        first_price = float(_hc.iloc[0])
        if first_price == 0:
            continue
        curve = []
        for idx, val in _hc.items():
            curve.append({
                'date': idx.strftime('%Y-%m-%d'),
                'value': round(float(val) / first_price * 100, 2),
            })

        last_price = float(_hc.iloc[-1])
        total_return = round(((last_price - first_price) / first_price) * 100, 2)

        results.append({
            'symbol': sym,
            'total_return': total_return,
            'curve': curve,
        })

    # Rank
    results.sort(key=lambda x: x['total_return'], reverse=True)
    for i, r in enumerate(results):
        r['rank'] = i + 1

    return jsonify(results)


@app.route('/api/simulate/dca_drip', methods=['POST'])
@login_required
def api_simulate_dca_drip():
    """DCA vs DCA+DRIP comparison."""
    import yfinance as yf
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    market = data.get('market', 'US')
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    amount = float(data.get('amount', 10000))
    frequency = int(data.get('frequency', 30))

    ticker = yf.Ticker(yf_symbol(symbol, market))
    hist = ticker.history(start=start_date, end=end_date)
    if hist.empty:
        return jsonify({'error': 'No data'}), 404

    divs = ticker.dividends

    # Pure DCA
    dca_shares = 0
    dca_cost = 0
    dca_cash_dividends = 0
    dca_curve = []

    # DCA + DRIP
    drip_shares = 0
    drip_cost = 0
    drip_curve = []

    dates = list(hist.index)
    trade_days = set()
    i = 0
    while i < len(dates):
        trade_days.add(dates[i].strftime('%Y-%m-%d'))
        i += frequency

    for idx, row in hist.iterrows():
        date_str = idx.strftime('%Y-%m-%d')
        price = float(row['Close'])

        if date_str in trade_days:
            buy_shares = round(amount / price, 4) if market == 'US' else int(amount / price)
            if buy_shares > 0:
                dca_shares += buy_shares
                dca_cost += amount
                drip_shares += buy_shares
                drip_cost += amount

        # Check dividends
        if not divs.empty and idx in divs.index:
            div_amount = float(divs[idx])
            dca_cash_dividends += div_amount * dca_shares

            # DRIP: reinvest
            drip_reinvest_shares = round((div_amount * drip_shares) / price, 4)
            drip_shares += drip_reinvest_shares

        dca_mv = dca_shares * price + dca_cash_dividends
        drip_mv = drip_shares * price

        dca_curve.append({'date': date_str, 'value': round(dca_mv, 2), 'cost': round(dca_cost, 2)})
        drip_curve.append({'date': date_str, 'value': round(drip_mv, 2), 'cost': round(drip_cost, 2)})

    dca_final = dca_curve[-1]['value'] if dca_curve else 0
    drip_final = drip_curve[-1]['value'] if drip_curve else 0

    return jsonify({
        'symbol': symbol,
        'dca': {
            'final_value': dca_final,
            'total_cost': dca_cost,
            'shares': dca_shares,
            'cash_dividends': round(dca_cash_dividends, 2),
            'return_pct': round(((dca_final - dca_cost) / dca_cost) * 100, 2) if dca_cost > 0 else 0,
            'curve': dca_curve,
        },
        'drip': {
            'final_value': drip_final,
            'total_cost': drip_cost,
            'shares': round(drip_shares, 4),
            'return_pct': round(((drip_final - drip_cost) / drip_cost) * 100, 2) if drip_cost > 0 else 0,
            'curve': drip_curve,
        },
        'compound_diff': round(drip_final - dca_final, 2),
    })


# ══════════════════════════════════════════════════════════
#  Academy API
# ══════════════════════════════════════════════════════════

@app.route('/api/academy/articles', methods=['GET'])
@login_required
def api_academy_articles():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    tag = request.args.get('tag', '')

    query = Article.query.filter_by(published=True)

    if search:
        like = f'%{search}%'
        query = query.filter(
            (Article.title.ilike(like)) |
            (Article.content.ilike(like)) |
            (Article.summary.ilike(like)) |
            (Article.tags.ilike(like))
        )
    if category:
        query = query.filter_by(category=category)
    if tag:
        query = query.filter(Article.tags.ilike(f'%{tag}%'))

    articles = query.order_by(Article.sort_order, Article.created_at.desc()).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'summary': a.summary,
        'category': a.category,
        'tags': [t.strip() for t in a.tags.split(',') if t.strip()] if a.tags else [],
        'created_at': a.created_at.isoformat(),
    } for a in articles])


@app.route('/api/academy/articles/<int:article_id>', methods=['GET'])
@login_required
def api_academy_article(article_id):
    a = Article.query.get_or_404(article_id)
    return jsonify({
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'summary': a.summary,
        'category': a.category,
        'tags': [t.strip() for t in a.tags.split(',') if t.strip()] if a.tags else [],
        'published': a.published,
        'sort_order': a.sort_order,
        'created_at': a.created_at.isoformat(),
        'updated_at': a.updated_at.isoformat() if a.updated_at else '',
    })


@app.route('/api/academy/tags')
@login_required
def api_academy_tags():
    articles = Article.query.filter_by(published=True).all()
    tags = set()
    for a in articles:
        if a.tags:
            for t in a.tags.split(','):
                t = t.strip()
                if t:
                    tags.add(t)
    return jsonify(sorted(list(tags)))


@app.route('/api/academy/articles', methods=['POST'])
@admin_required
def api_academy_create():
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    summary = data.get('summary', '').strip()
    category = data.get('category', 'concept')
    tags = data.get('tags', '')
    published = data.get('published', True)

    if not title:
        return jsonify({'error': 'Title required'}), 400

    if not summary and content:
        # Auto-extract summary from content (strip HTML)
        import re
        text = re.sub(r'<[^>]+>', '', content)
        summary = text[:150].strip()

    if isinstance(tags, list):
        tags = ','.join(tags)

    article = Article(
        title=title, content=content, summary=summary,
        category=category, tags=tags, published=published
    )
    db.session.add(article)
    db.session.commit()
    return jsonify({'success': True, 'id': article.id})


@app.route('/api/academy/articles/<int:article_id>', methods=['PUT'])
@admin_required
def api_academy_update(article_id):
    article = Article.query.get_or_404(article_id)
    data = request.get_json()

    if 'title' in data:
        article.title = data['title'].strip()
    if 'content' in data:
        article.content = data['content'].strip()
    if 'summary' in data:
        article.summary = data['summary'].strip()
    elif 'content' in data and not article.summary:
        import re
        text = re.sub(r'<[^>]+>', '', data['content'])
        article.summary = text[:150].strip()
    if 'category' in data:
        article.category = data['category']
    if 'tags' in data:
        tags = data['tags']
        article.tags = ','.join(tags) if isinstance(tags, list) else tags
    if 'published' in data:
        article.published = data['published']

    article.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/academy/articles/<int:article_id>', methods=['DELETE'])
@admin_required
def api_academy_delete(article_id):
    article = Article.query.get_or_404(article_id)
    # Also delete related bookmarks
    Bookmark.query.filter_by(article_id=article_id).delete()
    db.session.delete(article)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/academy/articles/reorder', methods=['PUT'])
@admin_required
def api_academy_reorder():
    data = request.get_json()
    order = data.get('order', [])
    for i, aid in enumerate(order):
        article = Article.query.get(aid)
        if article:
            article.sort_order = i
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/academy/admin/articles')
@admin_required
def api_academy_admin_articles():
    articles = Article.query.order_by(Article.sort_order, Article.created_at.desc()).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'summary': a.summary,
        'category': a.category,
        'tags': [t.strip() for t in a.tags.split(',') if t.strip()] if a.tags else [],
        'published': a.published,
        'sort_order': a.sort_order,
        'created_at': a.created_at.isoformat(),
    } for a in articles])


@app.route('/api/academy/word_of_day')
@login_required
def api_word_of_day():
    """Today's word: deterministic selection based on day."""
    articles = Article.query.filter_by(published=True).filter(
        Article.category.in_(['abbreviation', 'glossary'])
    ).order_by(Article.id).all()

    if not articles:
        articles = Article.query.filter_by(published=True).order_by(Article.id).all()

    if not articles:
        return jsonify(None)

    today = date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    idx = seed % len(articles)
    a = articles[idx]

    return jsonify({
        'id': a.id,
        'title': a.title,
        'summary': a.summary,
        'category': a.category,
    })


# ══════════════════════════════════════════════════════════
#  Bookmark API
# ══════════════════════════════════════════════════════════

@app.route('/api/bookmarks/folders', methods=['GET'])
@login_required
def api_get_folders():
    folders = BookmarkFolder.query.filter_by(user_id=current_user.id).order_by(BookmarkFolder.created_at).all()
    result = []
    for f in folders:
        count = Bookmark.query.filter_by(folder_id=f.id).count()
        result.append({
            'id': f.id,
            'color': f.color,
            'count': count,
        })
    return jsonify(result)


@app.route('/api/bookmarks/folders', methods=['POST'])
@login_required
def api_create_folder():
    data = request.get_json()
    color = data.get('color', '')
    if not color:
        return jsonify({'error': 'Color required'}), 400

    existing = BookmarkFolder.query.filter_by(user_id=current_user.id, color=color).first()
    if existing:
        return jsonify({'error': 'Color already used'}), 400

    folder_count = BookmarkFolder.query.filter_by(user_id=current_user.id).count()
    if folder_count >= 10:
        return jsonify({'error': 'Maximum 10 folders'}), 400

    f = BookmarkFolder(user_id=current_user.id, color=color)
    db.session.add(f)
    db.session.commit()
    return jsonify({'success': True, 'id': f.id})


@app.route('/api/bookmarks/folders/<int:folder_id>', methods=['PUT'])
@login_required
def api_update_folder(folder_id):
    f = BookmarkFolder.query.filter_by(id=folder_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'color' in data:
        f.color = data['color']
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/bookmarks/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def api_delete_folder(folder_id):
    f = BookmarkFolder.query.filter_by(id=folder_id, user_id=current_user.id).first_or_404()
    Bookmark.query.filter_by(folder_id=f.id).delete()
    db.session.delete(f)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/bookmarks', methods=['GET'])
@login_required
def api_get_bookmarks():
    folder_id = request.args.get('folder_id', '')
    query = Bookmark.query.filter_by(user_id=current_user.id)
    if folder_id:
        query = query.filter_by(folder_id=int(folder_id))

    bookmarks = query.order_by(Bookmark.created_at.desc()).all()
    result = []
    for b in bookmarks:
        article = Article.query.get(b.article_id)
        result.append({
            'id': b.id,
            'article_id': b.article_id,
            'folder_id': b.folder_id,
            'note': b.note,
            'article_title': article.title if article else '',
            'article_summary': article.summary if article else '',
            'article_category': article.category if article else '',
        })
    return jsonify(result)


@app.route('/api/bookmarks/article/<int:article_id>')
@login_required
def api_bookmark_status(article_id):
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id, article_id=article_id).all()
    return jsonify([{
        'id': b.id,
        'folder_id': b.folder_id,
        'folder_color': BookmarkFolder.query.get(b.folder_id).color if BookmarkFolder.query.get(b.folder_id) else '',
    } for b in bookmarks])


@app.route('/api/bookmarks', methods=['POST'])
@login_required
def api_add_bookmark():
    data = request.get_json()
    article_id = data.get('article_id')
    folder_id = data.get('folder_id')

    if not article_id or not folder_id:
        return jsonify({'error': 'Missing fields'}), 400

    existing = Bookmark.query.filter_by(
        user_id=current_user.id, article_id=article_id, folder_id=folder_id
    ).first()
    if existing:
        return jsonify({'error': 'Already bookmarked'}), 400

    b = Bookmark(user_id=current_user.id, article_id=article_id, folder_id=folder_id)
    db.session.add(b)
    db.session.commit()
    return jsonify({'success': True, 'id': b.id})


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['PUT'])
@login_required
def api_update_bookmark(bookmark_id):
    b = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'note' in data:
        b.note = data['note']
    if 'folder_id' in data:
        b.folder_id = data['folder_id']
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@login_required
def api_delete_bookmark(bookmark_id):
    b = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first_or_404()
    db.session.delete(b)
    db.session.commit()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════
#  Journal API
# ══════════════════════════════════════════════════════════

@app.route('/api/journal', methods=['GET'])
@login_required
def api_get_journals():
    month = request.args.get('month', '')  # YYYY-MM
    query = Journal.query.filter_by(user_id=current_user.id)
    if month:
        query = query.filter(Journal.journal_date >= f'{month}-01')
        # End of month
        y, m = int(month[:4]), int(month[5:7])
        if m == 12:
            end = f'{y+1}-01-01'
        else:
            end = f'{y}-{m+1:02d}-01'
        query = query.filter(Journal.journal_date < end)

    journals = query.order_by(Journal.journal_date.desc()).all()
    return jsonify([{
        'id': j.id,
        'journal_date': j.journal_date.isoformat(),
        'mood': j.mood,
        'market_view': j.market_view,
        'content': j.content,
    } for j in journals])


@app.route('/api/journal/<string:date_str>')
@login_required
def api_get_journal_by_date(date_str):
    j = Journal.query.filter_by(user_id=current_user.id, journal_date=date_str).first()
    if j:
        return jsonify({
            'id': j.id,
            'journal_date': j.journal_date.isoformat(),
            'mood': j.mood,
            'market_view': j.market_view,
            'content': j.content,
        })
    return jsonify(None)


@app.route('/api/journal', methods=['POST'])
@login_required
def api_save_journal():
    data = request.get_json()
    journal_date = data.get('journal_date', '')
    mood = data.get('mood', '')
    market_view = data.get('market_view', '')
    content = data.get('content', '').strip()

    if not journal_date:
        return jsonify({'error': 'Date required'}), 400

    j = Journal.query.filter_by(user_id=current_user.id, journal_date=journal_date).first()
    if j:
        j.mood = mood
        j.market_view = market_view
        j.content = content
    else:
        j = Journal(
            user_id=current_user.id,
            journal_date=datetime.strptime(journal_date, '%Y-%m-%d').date(),
            mood=mood, market_view=market_view, content=content
        )
        db.session.add(j)

    db.session.commit()
    return jsonify({'success': True, 'id': j.id})


@app.route('/api/journal/<int:journal_id>', methods=['DELETE'])
@login_required
def api_delete_journal(journal_id):
    j = Journal.query.filter_by(id=journal_id, user_id=current_user.id).first_or_404()
    db.session.delete(j)
    db.session.commit()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════
#  Dividends API
# ══════════════════════════════════════════════════════════

@app.route('/api/dividends', methods=['GET'])
@login_required
def api_get_dividends():
    dividends = Dividend.query.filter_by(user_id=current_user.id).order_by(Dividend.ex_date.desc()).all()
    return jsonify([{
        'id': d.id,
        'symbol': d.symbol,
        'market': d.market,
        'ex_date': d.ex_date.isoformat(),
        'amount': d.amount,
        'remind_days': d.remind_days,
    } for d in dividends])


@app.route('/api/dividends', methods=['POST'])
@login_required
def api_add_dividend():
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    market = data.get('market', 'TW')
    ex_date = data.get('ex_date', '')
    amount = float(data.get('amount', 0))
    remind_days = int(data.get('remind_days', 7))

    if not symbol or not ex_date or amount <= 0:
        return jsonify({'error': 'Missing fields'}), 400

    d = Dividend(
        user_id=current_user.id, symbol=symbol, market=market,
        ex_date=datetime.strptime(ex_date, '%Y-%m-%d').date(),
        amount=amount, remind_days=remind_days
    )
    db.session.add(d)
    db.session.commit()
    return jsonify({'success': True, 'id': d.id})


@app.route('/api/dividends/<int:div_id>', methods=['PUT'])
@login_required
def api_update_dividend(div_id):
    d = Dividend.query.filter_by(id=div_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'remind_days' in data:
        d.remind_days = int(data['remind_days'])
    if 'amount' in data:
        d.amount = float(data['amount'])
    if 'ex_date' in data:
        d.ex_date = datetime.strptime(data['ex_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/dividends/<int:div_id>', methods=['DELETE'])
@login_required
def api_delete_dividend(div_id):
    d = Dividend.query.filter_by(id=div_id, user_id=current_user.id).first_or_404()
    db.session.delete(d)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/dividends/fetch', methods=['POST'])
@login_required
def api_fetch_dividends():
    """Auto-fetch dividend info from yfinance."""
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    market = data.get('market', 'TW')

    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400

    divs = get_dividend_info(symbol, market)
    return jsonify(divs)


# ══════════════════════════════════════════════════════════
#  Settings API
# ══════════════════════════════════════════════════════════

@app.route('/api/settings', methods=['GET'])
@login_required
def api_get_settings():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'default_market': current_user.default_market,
        'commission_discount': current_user.commission_discount,
        'concentration_threshold': current_user.concentration_threshold,
        'anniversary_enabled': current_user.anniversary_enabled,
    })


@app.route('/api/settings', methods=['PUT'])
@login_required
def api_update_settings():
    data = request.get_json()
    if 'default_market' in data:
        current_user.default_market = data['default_market']
    if 'commission_discount' in data:
        current_user.commission_discount = float(data['commission_discount'])
    if 'concentration_threshold' in data:
        current_user.concentration_threshold = float(data['concentration_threshold'])
    if 'anniversary_enabled' in data:
        current_user.anniversary_enabled = bool(data['anniversary_enabled'])
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/settings/password', methods=['PUT'])
@login_required
def api_change_password():
    data = request.get_json()
    current_pwd = data.get('current_password', '')
    new_pwd = data.get('new_password', '')
    confirm_pwd = data.get('confirm_password', '')

    if not check_password_hash(current_user.password_hash, current_pwd):
        return jsonify({'error': 'Current password incorrect'}), 400
    if len(new_pwd) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if new_pwd != confirm_pwd:
        return jsonify({'error': 'Passwords do not match'}), 400

    current_user.password_hash = generate_password_hash(new_pwd)
    db.session.commit()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════
#  Portfolio API
# ══════════════════════════════════════════════════════════

@app.route('/api/portfolios', methods=['GET'])
@login_required
def api_get_portfolios():
    portfolios = Portfolio.query.filter_by(user_id=current_user.id).order_by(Portfolio.created_at.desc()).all()
    result = []
    for p in portfolios:
        members = PortfolioMember.query.filter_by(portfolio_id=p.id).all()
        result.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'tags': json.loads(p.tags) if p.tags else [],
            'members': [{'id': m.id, 'symbol': m.symbol, 'market': m.market} for m in members],
            'member_count': len(members),
        })
    return jsonify(result)


@app.route('/api/portfolios', methods=['POST'])
@login_required
def api_create_portfolio():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    tags = data.get('tags', [])

    if not name:
        return jsonify({'error': 'Name required'}), 400

    p = Portfolio(
        user_id=current_user.id, name=name, description=description,
        tags=json.dumps(tags)
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'success': True, 'id': p.id})


@app.route('/api/portfolios/<int:pid>', methods=['GET'])
@login_required
def api_get_portfolio(pid):
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    members = PortfolioMember.query.filter_by(portfolio_id=p.id).all()
    return jsonify({
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'tags': json.loads(p.tags) if p.tags else [],
        'members': [{'id': m.id, 'symbol': m.symbol, 'market': m.market} for m in members],
    })


@app.route('/api/portfolios/<int:pid>', methods=['PUT'])
@login_required
def api_update_portfolio(pid):
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    data = request.get_json()
    if 'name' in data:
        p.name = data['name'].strip()
    if 'description' in data:
        p.description = data['description'].strip()
    if 'tags' in data:
        p.tags = json.dumps(data['tags'])
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/portfolios/<int:pid>', methods=['DELETE'])
@login_required
def api_delete_portfolio(pid):
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    PortfolioMember.query.filter_by(portfolio_id=p.id).delete()
    db.session.delete(p)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/portfolios/<int:pid>/members', methods=['POST'])
@login_required
def api_add_portfolio_member(pid):
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    data = request.get_json()
    symbol = data.get('symbol', '').strip().upper()
    market = data.get('market', 'US')

    # Must be in watchlist
    in_watchlist = Watchlist.query.filter_by(
        user_id=current_user.id, symbol=symbol, market=market
    ).first()
    if not in_watchlist:
        return jsonify({'error': 'Stock must be in watchlist first'}), 400

    existing = PortfolioMember.query.filter_by(
        portfolio_id=p.id, symbol=symbol, market=market
    ).first()
    if existing:
        return jsonify({'error': 'Already in portfolio'}), 400

    m = PortfolioMember(portfolio_id=p.id, symbol=symbol, market=market)
    db.session.add(m)
    db.session.commit()
    return jsonify({'success': True, 'id': m.id})


@app.route('/api/portfolios/<int:pid>/members/<int:mid>', methods=['DELETE'])
@login_required
def api_remove_portfolio_member(pid, mid):
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    m = PortfolioMember.query.filter_by(id=mid, portfolio_id=p.id).first_or_404()
    db.session.delete(m)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/portfolios/<int:pid>/quotes')
@login_required
def api_portfolio_quotes(pid):
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    members = PortfolioMember.query.filter_by(portfolio_id=p.id).all()
    result = []
    for m in members:
        quote = get_quote(m.symbol, m.market)
        if quote:
            result.append(quote)
    return jsonify(result)


@app.route('/api/portfolios/<int:pid>/history')
@login_required
def api_portfolio_history(pid):
    """Standardized history for all members (base 100)."""
    import yfinance as yf
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    members = PortfolioMember.query.filter_by(portfolio_id=p.id).all()
    period_raw = request.args.get('period', '6mo')
    _pm = {'1M': '1mo', '3M': '3mo', '6M': '6mo', '1Y': '1y', '5Y': '5y'}
    period = _pm.get(period_raw, period_raw)

    result = []
    for m in members:
        ticker = yf.Ticker(yf_symbol(m.symbol, m.market))
        hist = ticker.history(period=period)
        if hist.empty:
            continue
        first = float(hist['Close'].iloc[0])
        curve = []
        for idx, row in hist.iterrows():
            curve.append({
                'date': idx.strftime('%Y-%m-%d'),
                'value': round(float(row['Close']) / first * 100, 2),
            })
        result.append({'symbol': m.symbol, 'market': m.market, 'curve': curve})

    return jsonify(result)


@app.route('/api/portfolios/<int:pid>/news')
@login_required
def api_portfolio_news(pid):
    """Fetch news for all portfolio members."""
    import yfinance as yf
    p = Portfolio.query.filter_by(id=pid, user_id=current_user.id).first_or_404()
    members = PortfolioMember.query.filter_by(portfolio_id=p.id).all()

    result = []
    for m in members[:8]:  # Max 8 members
        try:
            ticker = yf.Ticker(yf_symbol(m.symbol, m.market))
            news = ticker.news or []
            for n in news[:5]:
                result.append({
                    'symbol': m.symbol,
                    'title': n.get('title', ''),
                    'link': n.get('link', ''),
                    'publisher': n.get('publisher', ''),
                    'published': n.get('providerPublishTime', 0),
                })
        except:
            continue

    result.sort(key=lambda x: x.get('published', 0), reverse=True)
    return jsonify(result[:40])


# ══════════════════════════════════════════════════════════
#  Admin API
# ══════════════════════════════════════════════════════════

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def api_admin_users():
    search = request.args.get('search', '').strip()
    query = User.query
    if search:
        like = f'%{search}%'
        query = query.filter((User.username.ilike(like)) | (User.email.ilike(like)))
    users = query.order_by(User.created_at.desc()).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'status': u.status,
        'created_at': u.created_at.isoformat(),
    } for u in users])


@app.route('/api/admin/users/<int:uid>/role', methods=['PUT'])
@login_required
def api_admin_change_role(uid):
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Superadmin only'}), 403
    if uid == current_user.id:
        return jsonify({'error': 'Cannot change own role'}), 400
    user = User.query.get_or_404(uid)
    data = request.get_json()
    user.role = data.get('role', 'member')
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/admin/users/<int:uid>/toggle', methods=['POST'])
@admin_required
def api_admin_toggle_user(uid):
    if uid == current_user.id:
        return jsonify({'error': 'Cannot toggle self'}), 400
    user = User.query.get_or_404(uid)
    user.status = 'disabled' if user.status == 'active' else 'active'
    db.session.commit()
    return jsonify({'success': True, 'status': user.status})


@app.route('/api/admin/users', methods=['POST'])
@login_required
def api_admin_create_user():
    if current_user.role not in ('admin', 'superadmin'):
        return jsonify({'error': '需要管理員權限'}), 403
    data = request.get_json()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    role = data.get('role', 'member')

    if not username or not email or len(password) < 8:
        return jsonify({'error': '請填寫帳號、信箱，密碼至少 8 字元'}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({'error': '帳號或信箱已被使用'}), 400

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        status='active'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'message': '用戶建立成功'})


@app.route('/api/admin/users/<int:uid>', methods=['DELETE'])
@login_required
def api_admin_delete_user(uid):
    if current_user.role != 'superadmin':
        return jsonify({'error': '需要超級管理員權限'}), 403
    if uid == current_user.id:
        return jsonify({'error': '無法刪除自己'}), 400
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': '用戶已刪除'})


# ══════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════

if __name__ == '__main__':
    os.makedirs('/data', exist_ok=True)
    with app.app_context():
        init_db()
    app.run(debug=True, port=6000, host='0.0.0.0')
