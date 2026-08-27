from flask import Flask, render_template, request, redirect, url_for, session, flash, \
    make_response  # 🟢 make_response: Backend theke PDF file download response pathanor jonno
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
import io
import os
import shutil
import secrets
import base64
import random
import socket
import re
import json
from datetime import datetime

# 🟢 PDF Generation Libraries (Backend theke original design-e PDF bananor jonno)
import pdfkit
import platform

app = Flask(__name__)


# 🟢 Project-relative paths so the same code works in PyCharm and on PythonAnywhere.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'transport.db')


# 🔐 Secure Flask secret key.
# Priority:
# 1) FLASK_SECRET_KEY environment variable (recommended for live server)
# 2) A private local .secret_key file (auto-created for local/PyCharm use)
SECRET_KEY_FILE = os.path.join(BASE_DIR, '.secret_key')
environment_secret = os.environ.get('FLASK_SECRET_KEY')

if environment_secret:
    app.secret_key = environment_secret
else:
    if not os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'w', encoding='utf-8') as secret_file:
            secret_file.write(secrets.token_hex(32))

    with open(SECRET_KEY_FILE, 'r', encoding='utf-8') as secret_file:
        app.secret_key = secret_file.read().strip()


# 🟢 Find wkhtmltopdf automatically on Windows/Linux.
# Optional override: set the WKHTMLTOPDF_PATH environment variable.
def get_wkhtmltopdf_path():
    configured_path = os.environ.get('WKHTMLTOPDF_PATH')

    if configured_path:
        return configured_path

    detected_path = shutil.which('wkhtmltopdf')
    if detected_path:
        return detected_path

    if os.name == 'nt':
        windows_candidates = [
            r'F:\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        ]

        for candidate in windows_candidates:
            if os.path.isfile(candidate):
                return candidate

        return windows_candidates[0]

    return '/usr/bin/wkhtmltopdf'


# 🟢 লোকাল আইপি বের করার ফাংশন, যাতে মোবাইল থেকে কিউআর কোড স্ক্যান করে ই-টিকিট দেখা যায়।
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


# 🟢 ডাটাবেস কানেকশন তৈরি করার ফাংশন।
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 🌟 BD CONTEXT ORIGINAL STATION & AIRPORT NAMES 🌟
def get_station_name(city, transport):
    if not city: return "Unknown Terminal"
    city_lower = city.lower()

    if transport == 'Air':
        if 'dhaka' in city_lower:
            return "Hazrat Shahjalal Int. Airport"
        elif 'chittagong' in city_lower:
            return "Shah Amanat Int. Airport"
        elif 'sylhet' in city_lower:
            return "Osmani Int. Airport"
        elif "cox" in city_lower:
            return "Cox's Bazar Airport"
        elif 'rajshahi' in city_lower:
            return "Shah Makhdum Airport"
        elif 'jessore' in city_lower:
            return "Jessore Airport"
        elif 'saidpur' in city_lower:
            return "Saidpur Airport"
        elif 'barisal' in city_lower:
            return "Barisal Airport"
        else:
            return f"{city} Airport"

    elif transport == 'Train':
        if 'dhaka' in city_lower:
            return "Kamalapur Railway Station"
        elif 'chittagong' in city_lower:
            return "Chittagong Railway Station"
        elif 'rajshahi' in city_lower:
            return "Rajshahi Railway Station"
        elif 'sylhet' in city_lower:
            return "Sylhet Railway Station"
        elif 'khulna' in city_lower:
            return "Khulna Railway Station"
        elif 'dinajpur' in city_lower:
            return "Dinajpur Railway Station"
        elif 'feni' in city_lower:
            return "Feni Railway Station"
        elif 'rajbari' in city_lower:
            return "Rajbari Railway Station"
        elif 'pabna' in city_lower:
            return "Pabna Railway Station"
        else:
            return f"{city} Railway Station"

    elif transport == 'Launch':
        if 'dhaka' in city_lower:
            return "Sadarghat Launch Terminal"
        elif 'barisal' in city_lower:
            return "Barisal River Port"
        elif 'chandpur' in city_lower:
            return "Chandpur River Port"
        elif 'bhola' in city_lower:
            return "Ilisha Ghat, Bhola"
        elif 'hatiya' in city_lower:
            return "Nalchira Ghat, Hatiya"
        elif 'kuakata' in city_lower:
            return "Kuakata River Port"
        elif 'patuakhali' in city_lower:
            return "Patuakhali River Port"
        elif 'munshiganj' in city_lower:
            return "Mawa Ghat, Munshiganj"
        elif 'madaripur' in city_lower:
            return "Kathalbari Ghat, Madaripur"
        elif 'shariatpur' in city_lower:
            return "Majhirghat, Shariatpur"
        else:
            return f"{city} River Port"

    else:  # For Bus
        if 'dhaka' in city_lower:
            return random.choice(["Gabtoli Bus Terminal", "Sayedabad Bus Terminal", "Mohakhali Bus Terminal"])
        elif 'chittagong' in city_lower:
            return "Dampara Bus Stand"
        elif 'sylhet' in city_lower:
            return "Kadamtali Bus Terminal"
        elif "cox" in city_lower:
            return "Dolphin Bus Stand"
        elif 'rajshahi' in city_lower:
            return "Shiroil Bus Terminal"
        elif 'khulna' in city_lower:
            return "Sonadanga Bus Terminal"
        elif 'barisal' in city_lower:
            return "Nathullabad Bus Terminal"
        elif 'rangpur' in city_lower:
            return "Kamargari Bus Stand"
        elif 'dinajpur' in city_lower:
            return "Dinajpur Central Bus Terminal"
        elif 'feni' in city_lower:
            return "Mohipal Bus Stand"
        elif 'rajbari' in city_lower:
            return "Rajbari Bus Terminal"
        elif 'bogura' in city_lower:
            return "Charmatha Bus Terminal"
        elif 'pabna' in city_lower:
            return "Pabna Bus Terminal"
        elif 'faridpur' in city_lower:
            return "Faridpur New Bus Stand"
        else:
            return f"{city} Central Bus Terminal"


@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_name = session.get('user_name')
    conn = get_db_connection()

    user_record = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not user_record:
        session.clear()
        return redirect(url_for('login'))

    confirmed_tickets = conn.execute(
        "SELECT journey_date, dep_time FROM tickets WHERE passenger_name = ? AND status LIKE 'Confirmed%'",
        (user_name,)).fetchall()

    completed_journeys = sum(
        1 for t in confirmed_tickets
        if datetime.strptime(
            f"{t['journey_date']} {t['dep_time']}",
            "%Y-%m-%d %I:%M %p"
        ) < datetime.now()
        if True
    )

    reviews_count = conn.execute(
        'SELECT COUNT(*) FROM reviews WHERE user_name = ?',
        (user_name,)
    ).fetchone()[0]

    pending_review = completed_journeys > reviews_count

    reviews = conn.execute(
        'SELECT * FROM reviews ORDER BY id DESC LIMIT 10'
    ).fetchall()

    conn.close()

    return render_template(
        'index.html',
        reviews=reviews,
        pending_review=pending_review
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    # 🟢 সিকিউরিটি আপডেট: ইউজার লগইন থাকলে আবার রেজিস্টার পেজে ঢুকতে পারবে না
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']

        password = generate_password_hash(
            request.form['password']
        )

        conn = get_db_connection()

        try:

            conn.execute(
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                (name, email, password)
            )

            conn.commit()

            flash(
                'Registration successful! You received 50 Jatra Coins! Please login.',
                'success'
            )

            return redirect(url_for('login'))

        except sqlite3.IntegrityError:

            flash(
                'Email already exists! Try logging in.',
                'danger'
            )

        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # 🟢 সিকিউরিটি আপডেট: ইউজার লগইন থাকলে আবার লগইন পেজে ঢুকতে পারবে না
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':

        conn = get_db_connection()

        user = conn.execute(
            'SELECT * FROM users WHERE email = ?',
            (request.form['email'],)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
                user['password'],
                request.form['password']
        ):

            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['coins'] = user['coins']

            flash(
                'Logged in successfully!',
                'success'
            )

            return redirect(url_for('index'))

        else:

            flash(
                'Invalid email or password!',
                'danger'
            )

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()

    flash(
        'You have been logged out.',
        'info'
    )

    return redirect(url_for('login'))


# 🟢 কোন রুটে কোন ট্রান্সপোর্ট চলবে, তার ভ্যালিডেশন লজিক (যেমন ভোলায় ট্রেন যাবে না)।
def get_valid_transports(departure, destination):
    valid_transports = ["Bus"]

    no_train = [
        "Barisal",
        "Bhola",
        "Patuakhali",
        "Kuakata",
        "Barguna",
        "Hatiya",
        "Bandarban",
        "Rangamati",
        "Khagrachari",
        "Pirojpur",
        "Jhalokati",
        "Madaripur",
        "Shariatpur",
        "Magura",
        "Narail",
        "Meherpur",
        "Lakshmipur",
        "Sherpur",
        "Satkhira"
    ]

    if not any(c in departure for c in no_train) and not any(
            c in destination for c in no_train
    ):
        valid_transports.append("Train")

    air_cities = [
        "Dhaka",
        "Chittagong",
        "Cox's Bazar",
        "Sylhet",
        "Saidpur",
        "Rajshahi",
        "Barisal",
        "Jessore"
    ]

    if any(c in departure for c in air_cities) and any(
            c in destination for c in air_cities
    ):
        valid_transports.append("Air")

    launch_hubs = [
        "Barisal",
        "Chandpur",
        "Bhola",
        "Patuakhali",
        "Barguna",
        "Hatiya",
        "Kuakata",
        "Pirojpur",
        "Jhalokati",
        "Shariatpur",
        "Madaripur",
        "Lakshmipur",
        "Munshiganj"
    ]

    if (
            "Dhaka" in departure and
            any(c in destination for c in launch_hubs)
    ) or (
            "Dhaka" in destination and
            any(c in departure for c in launch_hubs)
    ) or (
            any(c in departure for c in launch_hubs) and
            any(c in destination for c in launch_hubs)
    ):
        valid_transports.append("Launch")

    return valid_transports


def generate_and_save_trips(
        transport_type,
        dep,
        dest
):
    conn = get_db_connection()

    ops = []
    bp = 0
    dstr = ""
    dmins = 0

    if transport_type == "Bus":

        ops = [
            "Hanif Enterprise",
            "Ena Transport",
            "Green Line",
            "Shyamoli SP",
            "Desh Travels",
            "Royal Coach",
            "TR Travels",
            "Shohagh Paribahan",
            "S.Alam Service",
            "Saudia Coach",
            "Saintmartin Travels",
            "Relax Transport",
            "Tuba Line"
        ]

        bp = random.randint(500, 1800)

        dstr = "6h 30m"

        dmins = 390

    elif transport_type == "Train":

        ops = [
            "Subarna Express",
            "Sonar Bangla",
            "Teesta Express",
            "Parabat Express",
            "Turna Express",
            "Upaban Express",
            "Nilsagar Express",
            "Chitra Express",
            "Drutojan Express",
            "Cox's Bazar Express",
            "Silkcity Express",
            "Banalata Express",
            "Rupsha Express",
            "Mahanagar Express",
            "Jayantika Express"
        ]

        bp = random.randint(300, 1450)

        dstr = "5h 15m"

        dmins = 315

    elif transport_type == "Air":

        ops = [
            "Biman Bangladesh",
            "US-Bangla",
            "Novoair",
            "Air Astra"
        ]

        bp = random.randint(3500, 8500)

        dstr = "0h 55m"

        dmins = 55

    elif transport_type == "Launch":

        ops = [
            "MV Sundarban 10",
            "Green Line Water Ways",
            "MV Parabat 12",
            "MV Manjur",
            "MV Surabhi 9",
            "MV Tasrif",
            "MV Prince Awlad",
            "MV Kuakata"
        ]

        bp = random.randint(350, 3500)

        dstr = "9h 45m"

        dmins = 585

    for _ in range(
            random.randint(4, 7)
    ):
        t_data = (
            transport_type,
            random.choice(ops),
            dep,
            dest,

            random.choice([
                "07:30 AM",
                "09:00 AM",
                "10:30 AM",
                "02:15 PM",
                "04:00 PM",
                "08:30 PM",
                "11:30 PM"
            ]),

            bp + random.randint(-100, 500),

            dstr,

            dmins,

            random.randint(2, 40)
        )

        conn.execute(
            '''
            INSERT INTO trips
            (
                transport_type,
                operator,
                departure,
                destination,
                dep_time,
                price,
                duration,
                dur_mins,
                seats_available
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            t_data
        )

    conn.commit()

    conn.close()


def get_weather_forecast(
        city,
        date_str
):
    seed = sum(
        ord(c)
        for c in city + date_str
    )

    random.seed(seed)

    temp = random.randint(24, 34)

    conditions = [

        (
            "☀️",
            "Sunny & Clear",
            "Don't forget your sunglasses!"
        ),

        (
            "⛅",
            "Partly Cloudy",
            "Perfect weather for a journey!"
        ),

        (
            "🌧️",
            "Light Rain Expected",
            "Carry an umbrella with you!"
        ),

        (
            "⛈️",
            "Thunderstorms",
            "Expect possible delays due to weather."
        )

    ]

    icon, cond, advice = random.choice(
        conditions
    )

    random.seed()

    return (
        f"{icon} {city} Weather on {date_str}: "
        f"{temp}°C, {cond}. {advice}"
    )


@app.route(
    '/search_results',
    methods=['POST']
)
def search_results():
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    t_type = request.form.get(
        'transport_type'
    )

    dep = request.form.get(
        'departure'
    )

    dest = request.form.get(
        'destination'
    )

    date = request.form.get(
        'journey_date'
    )

    if dep == dest:
        flash(
            f'⚠️ Departure and Destination cannot be the same city ({dep}).',
            'danger'
        )

        return redirect(
            url_for('index')
        )

    v_trans = get_valid_transports(
        dep,
        dest
    )

    conn = get_db_connection()

    all_trips = []

    if t_type == "Compare All":

        for trans in v_trans:

            records = conn.execute(
                '''
                SELECT *
                FROM trips
                WHERE transport_type = ?
                AND departure = ?
                AND destination = ?
                ''',

                (
                    trans,
                    dep,
                    dest
                )
            ).fetchall()

            if not records:
                generate_and_save_trips(
                    trans,
                    dep,
                    dest
                )

                records = conn.execute(
                    '''
                    SELECT *
                    FROM trips
                    WHERE transport_type = ?
                    AND departure = ?
                    AND destination = ?
                    ''',

                    (
                        trans,
                        dep,
                        dest
                    )
                ).fetchall()

            all_trips.extend(
                records
            )

    else:

        if t_type not in v_trans:
            flash(
                f'⚠️ {t_type} service is not physically available '
                f'on the {dep} ➡️ {dest} route.',
                'danger'
            )

            return redirect(
                url_for('index')
            )

        records = conn.execute(
            '''
            SELECT *
            FROM trips
            WHERE transport_type = ?
            AND departure = ?
            AND destination = ?
            ''',

            (
                t_type,
                dep,
                dest
            )
        ).fetchall()

        if not records:
            generate_and_save_trips(
                t_type,
                dep,
                dest
            )

            records = conn.execute(
                '''
                SELECT *
                FROM trips
                WHERE transport_type = ?
                AND departure = ?
                AND destination = ?
                ''',

                (
                    t_type,
                    dep,
                    dest
                )
            ).fetchall()

        all_trips.extend(
            records
        )

    conn.close()

    formatted_trips = []

    for t in all_trips:

        base_price = t['price']

        final_price = base_price

        is_surge = False

        if t['seats_available'] <= 10:
            final_price = int(
                base_price * 1.15
            )

            is_surge = True

        formatted_trips.append({

            "id":
                t['id'],

            "type":
                t['transport_type'],

            "operator":
                t['operator'],

            "dep_time":
                t['dep_time'],

            "price":
                final_price,

            "is_surge":
                is_surge,

            "duration":
                t['duration'],

            "dur_mins":
                t['dur_mins'],

            "seats_available":
                t['seats_available'],

            "low_seat":
                t['seats_available'] < 6,

            "delay_msg":
                ""
        })

    ch = (
        min(
            formatted_trips,
            key=lambda x: x['price']
        )
        if formatted_trips
        else None
    )

    fa = (
        min(
            formatted_trips,
            key=lambda x: x['dur_mins']
        )
        if formatted_trips
        else None
    )

    bv = (
        min(
            formatted_trips,
            key=lambda x: x['price'] * x['dur_mins']
        )
        if formatted_trips
        else None
    )

    return render_template(

        'results.html',

        trips=formatted_trips,

        transport=t_type,

        frm=dep,

        to=dest,

        date=date,

        cheapest=ch,

        fastest=fa,

        best_value=bv
    )


@app.route(
    '/checkout',
    methods=['POST']
)
def checkout():
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    dest = request.form.get(
        'to'
    )

    date = request.form.get(
        'date'
    )

    transport = request.form.get(
        'transport'
    )

    operator = request.form.get(
        'operator'
    )

    frm = request.form.get(
        'frm'
    )

    dep_time = request.form.get(
        'dep_time'
    )

    price = request.form.get(
        'price'
    )

    trip_mode = request.form.get(
        'trip_mode'
    )

    return_date = request.form.get(
        'return_date'
    )

    weather_msg = get_weather_forecast(
        dest,
        date
    )

    conn = get_db_connection()

    booked_records = conn.execute(
        '''
        SELECT seat_info
        FROM tickets

        WHERE transport_type=?
        AND operator=?
        AND departure=?
        AND destination=?
        AND journey_date=?
        AND dep_time=?
        AND status NOT LIKE '%Cancelled%'
        ''',

        (
            transport,
            operator,
            frm,
            dest,
            date,
            dep_time
        )
    ).fetchall()

    trip_data = conn.execute(
        '''
        SELECT seats_available
        FROM trips

        WHERE transport_type=?
        AND operator=?
        AND departure=?
        AND destination=?
        AND dep_time=?
        ''',

        (
            transport,
            operator,
            frm,
            dest,
            dep_time
        )
    ).fetchone()

    seats_available_in_db = (
        trip_data['seats_available']
        if trip_data
        else 32
    )

    conn.close()

    booked_seats = []

    for r in booked_records:
        # 🟢 UPDATED: This regex ensures that A1, 10F, T40, C120 all are perfectly matched
        seats = re.findall(
            r'\b[A-Z]{1,3}\d+\b|\b\d+[A-Z]\b|\bT\d+-\d+\b|\bC\d+\b',
            r['seat_info']
        )
        booked_seats.extend(
            seats
        )

    booked_seats_json = json.dumps(
        booked_seats
    )

    frm_station = get_station_name(
        frm,
        transport
    )

    to_station = get_station_name(
        dest,
        transport
    )

    return render_template(

        'checkout.html',

        weather_msg=
        weather_msg,

        booked_seats_json=
        booked_seats_json,

        seats_available=
        seats_available_in_db,

        frm_station=
        frm_station,

        to_station=
        to_station,

        transport=
        transport,

        operator=
        operator,

        frm=
        frm,

        to=
        dest,

        date=
        date,

        dep_time=
        dep_time,

        price=
        price,

        trip_mode=
        trip_mode,

        return_date=
        return_date
    )


@app.route(
    '/confirm_booking',
    methods=['POST']
)
def confirm_booking():
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    passenger_phone = request.form.get(
        'passenger_phone'
    )

    if not passenger_phone or len(passenger_phone.strip()) < 11:
        flash(
            '⚠️ A valid Mobile Number is required to confirm the booking.',
            'danger'
        )
        return redirect(url_for('index'))

    transport_type = request.form.get(
        'transport'
    )

    operator_name = request.form.get(
        'operator'
    )

    departure = request.form.get(
        'frm'
    )

    destination = request.form.get(
        'to'
    )

    journey_date = request.form.get(
        'date'
    )

    dep_time = request.form.get(
        'dep_time'
    )

    payment_method = request.form.get(
        'payment_method'
    )

    passenger_name = request.form.get(
        'passenger_name'
    )

    class_type = request.form.get(
        'class_type',
        'Standard Class'
    )

    weather_msg = request.form.get(
        'weather_msg'
    )

    trip_mode = request.form.get(
        'trip_mode',
        'one_way'
    )

    return_date = request.form.get(
        'return_date',
        ''
    )

    selected_seats = request.form.get(
        'selected_seats_input',
        ''
    )

    if not selected_seats:
        selected_seats = (
            "Auto-Assigned"
        )

    original_base_price = int(
        request.form.get(
            'price'
        )
    )

    multiplier = 1.0

    if class_type == "Economy Class":

        multiplier = 0.85

    elif class_type == "Premium Class":

        multiplier = 1.25

    elif class_type == "VIP / Business":

        multiplier = 1.50

    actual_unit_price = round(
        original_base_price *
        multiplier
    )

    quantity = int(
        request.form.get(
            'quantity',
            1
        )
    )

    sub_total = (
            actual_unit_price *
            quantity
    )

    use_coins = request.form.get(
        'use_coins'
    )

    user_coins = session.get(
        'coins',
        0
    )

    discount = (
        user_coins
        if use_coins == "yes"
           and user_coins > 0
        else 0
    )

    if discount > sub_total:
        discount = sub_total

    final_payable_total = (
            sub_total -
            discount
    )

    payment_type = request.form.get(
        'payment_type',
        'full'
    )

    due_amount = 0

    actual_paid = (
        final_payable_total
    )

    ticket_status = (
        'Confirmed (100% Paid)'
    )

    if payment_type == 'partial':
        actual_paid = int(
            final_payable_total *
            0.50
        )

        due_amount = (
                final_payable_total -
                actual_paid
        )

        ticket_status = (
            'Reserved (Due: ৳{})'
            .format(
                due_amount
            )
        )

    earned_coins = int(
        actual_paid *
        0.05
    )

    new_coin_balance = (
                               user_coins -
                               discount
                       ) + earned_coins

    conn = get_db_connection()

    conn.execute(
        '''
        UPDATE users
        SET coins = ?
        WHERE id = ?
        ''',

        (
            new_coin_balance,
            session['user_id']
        )
    )

    session['coins'] = (
        new_coin_balance
    )

    pnr_number = (
        f"PNR-{random.randint(10000, 99999)}"
    )

    ticket_meta = {}

    ticket_meta['trip_mode'] = (
        trip_mode
    )

    ticket_meta['return_date'] = (
        return_date
        if trip_mode == 'round_way'
        else 'N/A'
    )

    if transport_type == "Train":

        ticket_meta['class_type'] = (
            class_type
        )

        ticket_meta['seat_no'] = (
            selected_seats
        )

        ticket_meta['contact'] = (
            f"Police: 01711-"
            f"{random.randint(100000, 999999)}"
        )

        seat_info = (
            f"{ticket_meta['class_type']} | "
            f"Seats: {ticket_meta['seat_no']} | "
            f"Return: {ticket_meta['return_date']} | "
            f"📞 {ticket_meta['contact']}"
        )

    elif transport_type == "Air":

        ticket_meta['flight_no'] = (
            f"BG-{random.randint(101, 999)}"
        )

        ticket_meta['seat_no'] = (
            selected_seats
        )

        ticket_meta['gate_no'] = (
            f"Gate {random.randint(1, 12)}"
        )

        ticket_meta['terminal'] = (
            "Domestic"
        )

        ticket_meta['baggage'] = (
            "20 KG"
        )

        ticket_meta['class_type'] = (
            class_type
        )

        ticket_meta['contact'] = (
            "Help: 13605"
        )

        seat_info = (
            f"Flight {ticket_meta['flight_no']} | "
            f"Seats: {ticket_meta['seat_no']} | "
            f"Return: {ticket_meta['return_date']} | "
            f"📞 {ticket_meta['contact']}"
        )

    elif transport_type == "Launch":

        ticket_meta['cabin_type'] = (
            class_type
        )

        ticket_meta['deck_floor'] = (
            "1st Deck"
        )

        ticket_meta['seat_no'] = (
            f"{selected_seats}"
        )

        ticket_meta['ghat_name'] = (
            get_station_name(
                departure,
                transport_type
            )
        )

        ticket_meta['master_name'] = (
            "Master Siraj"
        )

        ticket_meta['contact'] = (
            f"Master: 01819-"
            f"{random.randint(100000, 999999)}"
        )

        seat_info = (
            f"{ticket_meta['cabin_type']} | "
            f"Cabins: {ticket_meta['seat_no']} | "
            f"Return: {ticket_meta['return_date']} | "
            f"📞 {ticket_meta['contact']}"
        )

    else:

        ticket_meta['bus_model'] = (
            class_type
        )

        ticket_meta['seat_no'] = (
            selected_seats
        )

        ticket_meta['boarding_point'] = (
            get_station_name(
                departure,
                transport_type
            )
        )

        ticket_meta['supervisor'] = (
            "Supervisor Tarik"
        )

        ticket_meta['contact'] = (
            f"Super: 01712-"
            f"{random.randint(100000, 999999)}"
        )

        seat_info = (
            f"{class_type} | "
            f"Seats: {ticket_meta['seat_no']} | "
            f"Return: {ticket_meta['return_date']} | "
            f"📞 {ticket_meta['contact']}"
        )

    frm_station = get_station_name(
        departure,
        transport_type
    )

    to_station = get_station_name(
        destination,
        transport_type
    )

    conn.execute(

        '''
        INSERT INTO tickets
        (
            pnr,
            passenger_name,
            transport_type,
            operator,
            departure,
            destination,
            journey_date,
            dep_time,
            price,
            seat_info,
            payment_method,
            status,
            earned_coins,
            used_coins,
            payment_type,
            due_amount
        )

        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',

        (
            pnr_number,
            passenger_name,
            transport_type,
            operator_name,
            departure,
            destination,
            journey_date,
            dep_time,
            final_payable_total,
            seat_info,
            payment_method,
            ticket_status,
            earned_coins,
            discount,
            payment_type,
            due_amount
        )
    )

    conn.execute(

        '''
        UPDATE trips

        SET seats_available =
            seats_available - ?

        WHERE transport_type=?
        AND operator=?
        AND departure=?
        AND destination=?
        AND dep_time=?
        ''',

        (
            quantity,
            transport_type,
            operator_name,
            departure,
            destination,
            dep_time
        )
    )

    conn.commit()

    conn.close()

    # Build the QR URL from the current request host.
    # Works on local PyCharm and on the live PythonAnywhere domain.
    e_ticket_url = url_for(
        'e_ticket',
        pnr=pnr_number,
        _external=True
    )

    img = qrcode.make(
        e_ticket_url
    )

    buf = io.BytesIO()

    img.save(
        buf,
        format="PNG"
    )

    qr_base64 = (
        base64.b64encode(
            buf.getvalue()
        ).decode(
            'utf-8'
        )
    )

    issue_time = datetime.now().strftime(
        '%d %b %Y, %I:%M %p'
    )

    return render_template(

        'ticket.html',

        qr_code=
        qr_base64,

        pnr=
        pnr_number,

        meta=
        ticket_meta,

        frm_station=
        frm_station,

        to_station=
        to_station,

        name=
        passenger_name,

        total_price=
        final_payable_total,

        actual_paid=
        actual_paid,

        due_amount=
        due_amount,

        payment_type=
        payment_type,

        quantity=
        quantity,

        transport=
        transport_type,

        operator=
        operator_name,

        date=
        journey_date,

        dep_time=
        dep_time,

        payment=
        payment_method,

        earned_coins=
        earned_coins,

        frm=
        departure,

        to=
        destination,

        weather_msg=
        weather_msg,

        trip_mode=
        trip_mode,

        return_date=
        return_date,

        issue_time=
        issue_time
    )


@app.route('/e_ticket/<pnr>')
def e_ticket(pnr):
    conn = get_db_connection()

    ticket = conn.execute(
        'SELECT * FROM tickets WHERE pnr = ?',
        (pnr,)
    ).fetchone()

    conn.close()

    current_time = datetime.now().strftime(
        '%d %b %Y, %I:%M %p'
    )

    if ticket:
        return render_template(

            'e_ticket_view.html',

            ticket=ticket,

            frm_station=get_station_name(
                ticket['departure'],
                ticket['transport_type']
            ),

            to_station=get_station_name(
                ticket['destination'],
                ticket['transport_type']
            ),

            current_time=current_time
        )

    return (
        "<h3>❌ Invalid or Fake Ticket!</h3>",
        404
    )


@app.route('/download_ticket/<pnr>')
def download_ticket(pnr):
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    conn = get_db_connection()

    ticket = conn.execute(
        'SELECT * FROM tickets WHERE pnr = ?',
        (pnr,)
    ).fetchone()

    conn.close()

    if not ticket:
        return (
            "<h3>❌ Invalid or Fake Ticket!</h3>",
            404
        )

    current_time = datetime.now().strftime(
        '%d %b %Y, %I:%M %p'
    )

    rendered_html = render_template(

        'e_ticket_view.html',

        ticket=ticket,

        frm_station=get_station_name(
            ticket['departure'],
            ticket['transport_type']
        ),

        to_station=get_station_name(
            ticket['destination'],
            ticket['transport_type']
        ),

        current_time=current_time
    )

    options = {

        'page-size':
            'A4',

        'margin-top':
            '0.5in',

        'margin-right':
            '0.5in',

        'margin-bottom':
            '0.5in',

        'margin-left':
            '0.5in',

        'encoding':
            "UTF-8",

        'enable-local-file-access':
            ""
    }

    try:

        path_wkhtmltopdf = get_wkhtmltopdf_path()

        config = pdfkit.configuration(
            wkhtmltopdf=
            path_wkhtmltopdf
        )

        pdf = pdfkit.from_string(

            rendered_html,

            False,

            options=options,

            configuration=config
        )

        response = make_response(
            pdf
        )

        response.headers[
            'Content-Type'
        ] = (
            'application/pdf'
        )

        response.headers[
            'Content-Disposition'
        ] = (
            f'attachment; '
            f'filename=Smart_Ticket_Invoice_{pnr}.pdf'
        )

        return response

    except Exception as e:

        return (
            f"<h3>❌ PDF Generation Error: "
            f"{str(e)}</h3>"
            f"<p>Path checked: "
            f"{path_wkhtmltopdf}"
            f"</p>"
        )


@app.route('/download_professional_invoice/<pnr>')
def download_professional_invoice(pnr):

    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    conn = get_db_connection()

    ticket = conn.execute(

        '''
        SELECT *
        FROM tickets
        WHERE pnr = ?
        ''',

        (pnr,)
    ).fetchone()

    conn.close()

    if not ticket:
        return (
            "<h3>❌ Invalid or Fake Ticket!</h3>",
            404
        )

    current_time = datetime.now().strftime(
        '%d %b %Y, %I:%M %p'
    )

    # Build the QR verification URL from the current request host.
    # Works on local PyCharm and on the live PythonAnywhere domain.
    verification_url = url_for(
        'e_ticket',
        pnr=pnr,
        _external=True
    )

    qr_image = qrcode.make(
        verification_url
    )

    qr_buffer = io.BytesIO()

    qr_image.save(
        qr_buffer,
        format="PNG"
    )

    qr_base64 = (
        base64.b64encode(
            qr_buffer.getvalue()
        ).decode(
            'utf-8'
        )
    )

    rendered_html = render_template(

        'invoice_pdf.html',

        ticket=
        ticket,

        frm_station=
        get_station_name(
            ticket['departure'],
            ticket['transport_type']
        ),

        to_station=
        get_station_name(
            ticket['destination'],
            ticket['transport_type']
        ),

        current_time=
        current_time,

        qr_code=
        qr_base64,

        verification_url=
        verification_url
    )

    options = {

        'page-size':
            'A4',

        'margin-top':
            '0.35in',

        'margin-right':
            '0.35in',

        'margin-bottom':
            '0.35in',

        'margin-left':
            '0.35in',

        'encoding':
            'UTF-8',

        'enable-local-file-access':
            '',

        'print-media-type':
            '',

        'quiet':
            ''
    }

    try:

        path_wkhtmltopdf = get_wkhtmltopdf_path()

        config = pdfkit.configuration(
            wkhtmltopdf=
            path_wkhtmltopdf
        )

        pdf = pdfkit.from_string(

            rendered_html,

            False,

            options=
            options,

            configuration=
            config
        )

        response = make_response(
            pdf
        )

        response.headers[
            'Content-Type'
        ] = (
            'application/pdf'
        )

        response.headers[
            'Content-Disposition'
        ] = (

            f'attachment; '

            f'filename='
            f'Jatra_Professional_Invoice_{pnr}.pdf'
        )

        return response

    except Exception as e:

        return (

            f"<h3>"
            f"❌ Professional Invoice PDF Generation Error: "
            f"{str(e)}"
            f"</h3>"

            f"<p>"
            f"Path checked: "
            f"{path_wkhtmltopdf}"
            f"</p>"
        )


@app.route('/my_tickets')
def my_tickets():
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    conn = get_db_connection()

    tickets_raw = conn.execute(

        '''
        SELECT *
        FROM tickets
        WHERE passenger_name = ?
        ORDER BY id ASC
        ''',

        (
            session['user_name'],
        )
    ).fetchall()

    tickets = []

    for t in tickets_raw:

        t_dict = dict(t)

        try:

            trip = conn.execute(

                '''
                SELECT live_status
                FROM trips

                WHERE operator=?
                AND departure=?
                AND destination=?
                AND dep_time=?
                ''',

                (
                    t['operator'],
                    t['departure'],
                    t['destination'],
                    t['dep_time']
                )
            ).fetchone()

            t_dict['live_status'] = (
                trip['live_status']
                if trip
                else 'Scheduled'
            )

        except sqlite3.OperationalError:

            t_dict['live_status'] = (
                'Scheduled'
            )

        tickets.append(
            t_dict
        )

    conn.close()

    return render_template(
        'my_tickets.html',
        tickets=tickets
    )


@app.route(
    '/cancel_ticket/<pnr>',
    methods=['POST']
)
def cancel_ticket(pnr):
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    conn = get_db_connection()

    user_record = conn.execute(

        '''
        SELECT coins
        FROM users
        WHERE id = ?
        ''',

        (
            session['user_id'],
        )
    ).fetchone()

    if not user_record:
        session.clear()

        flash(
            'Database was reset! Please login again.',
            'danger'
        )

        return redirect(
            url_for('login')
        )

    current_coins = (
        user_record['coins']
    )

    ticket = conn.execute(

        '''
        SELECT *
        FROM tickets
        WHERE pnr = ?
        AND passenger_name = ?
        ''',

        (
            pnr,
            session['user_name']
        )
    ).fetchone()

    if not ticket or "Cancelled" in ticket['status']:
        flash(
            'Invalid request.',
            'danger'
        )

        return redirect(
            url_for('my_tickets')
        )

    try:

        hours_left = (

                             datetime.strptime(

                                 f"{ticket['journey_date']} "
                                 f"{ticket['dep_time']}",

                                 "%Y-%m-%d %I:%M %p"

                             ) -

                             datetime.now()

                     ).total_seconds() / 3600

    except ValueError:

        hours_left = 25

    actual_paid_amount = (

            ticket['price'] -
            ticket['due_amount']
    )

    refund_pct = (

        90
        if hours_left >= 48

        else (

            50
            if hours_left >= 24

            else (

                25
                if hours_left >= 12

                else 0
            )
        )
    )

    refund_amount = int(

        (
                actual_paid_amount *
                refund_pct
        ) / 100
    )

    earned = (
        ticket['earned_coins']
    )

    used = (
        ticket['used_coins']
    )

    new_coins = max(

        0,

        current_coins -
        earned +
        used
    )

    conn.execute(

        '''
        UPDATE users
        SET coins = ?
        WHERE id = ?
        ''',

        (
            new_coins,
            session['user_id']
        )
    )

    session['coins'] = (
        new_coins
    )

    new_status = (

        f'Cancelled '
        f'(Refund: ৳{refund_amount})'

        if refund_pct > 0

        else

        'Cancelled (No Refund)'
    )

    msg = (

        f'✅ Ticket Cancelled! '
        f'Refund BDT {refund_amount} '
        f'to {ticket["payment_method"]}. '
        f'({earned} Coins Deducted).'

        if refund_pct > 0

        else

        f'⚠️ Cancelled. '
        f'No refund (under 12 hrs). '
        f'({earned} Coins Deducted).'
    )

    conn.execute(

        '''
        UPDATE tickets
        SET status = ?
        WHERE pnr = ?
        ''',

        (
            new_status,
            pnr
        )
    )

    booked_seats = re.findall(

        r'\b[A-Z]{1,2}\d+\b|\b\d+[A-Z]\b|\bT\d+-\d+\b|\bC\d+\b',

        ticket['seat_info']
    )

    qty_to_restore = (

        len(booked_seats)

        if booked_seats

        else 1
    )

    conn.execute(

        '''
        UPDATE trips

        SET seats_available =
            seats_available + ?

        WHERE transport_type=?
        AND operator=?
        AND departure=?
        AND destination=?
        AND dep_time=?
        ''',

        (
            qty_to_restore,
            ticket['transport_type'],
            ticket['operator'],
            ticket['departure'],
            ticket['destination'],
            ticket['dep_time']
        )
    )

    conn.commit()

    conn.close()

    flash(

        msg,

        'success'
        if refund_pct > 0
        else 'danger'
    )

    return redirect(
        url_for('my_tickets')
    )


@app.route(
    '/submit_review',
    methods=['POST']
)
def submit_review():
    if 'user_id' not in session:
        return redirect(
            url_for('login')
        )

    conn = get_db_connection()

    conn.execute(

        '''
        INSERT INTO reviews
        (
            user_name,
            transport_type,
            rating,
            comment
        )

        VALUES (?, ?, ?, ?)
        ''',

        (
            session.get(
                'user_name'
            ),

            request.form.get(
                'transport_type'
            ),

            int(
                request.form.get(
                    'rating'
                )
            ),

            request.form.get(
                'comment'
            )
        )
    )

    user_record = conn.execute(

        '''
        SELECT coins
        FROM users
        WHERE id = ?
        ''',

        (
            session['user_id'],
        )
    ).fetchone()

    if user_record:
        current_coins = (
            user_record['coins']
        )

        conn.execute(

            '''
            UPDATE users
            SET coins = ?
            WHERE id = ?
            ''',

            (
                current_coins + 5,
                session['user_id']
            )
        )

        session['coins'] = (
                current_coins + 5
        )

    conn.commit()

    conn.close()

    flash(
        '✅ Review submitted successfully! You earned 5 Jatra Coins! 🎉',
        'success'
    )

    return redirect(
        url_for('index')
    )


@app.route(
    '/admin_login',
    methods=['GET', 'POST']
)
def admin_login():
    if 'user_id' in session:
        flash(
            '⚠️ Unauthorized Access! You do not have permission to view this page.',
            'danger'
        )

        return redirect(
            url_for('index')
        )

    if request.method == 'POST':

        conn = get_db_connection()

        admin = conn.execute(

            '''
            SELECT *
            FROM admins
            WHERE email = ?
            ''',

            (
                request.form['email'],
            )
        ).fetchone()

        conn.close()

        if admin and check_password_hash(
                admin['password'],
                request.form['password']
        ):
            session['admin_id'] = (
                admin['id']
            )

            return redirect(
                url_for(
                    'admin_dashboard'
                )
            )

        flash(
            'Invalid Admin Credentials!',
            'danger'
        )

    return render_template(
        'admin_login.html'
    )


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(
            url_for('admin_login')
        )

    conn = get_db_connection()

    total_users = conn.execute(
        'SELECT COUNT(*) FROM users'
    ).fetchone()[0]

    total_tickets = conn.execute(
        'SELECT COUNT(*) FROM tickets'
    ).fetchone()[0]

    revenue_data = conn.execute(

        '''
        SELECT SUM(price - due_amount)
        FROM tickets
        WHERE status NOT LIKE '%Cancelled%'
        '''

    ).fetchone()[0]

    total_revenue = (

        revenue_data
        if revenue_data
        else 0
    )

    trips = conn.execute(

        '''
        SELECT *
        FROM trips
        ORDER BY id DESC
        '''

    ).fetchall()

    tickets = conn.execute(

        '''
        SELECT *
        FROM tickets
        ORDER BY id DESC
        '''

    ).fetchall()

    reviews = conn.execute(

        '''
        SELECT *
        FROM reviews
        ORDER BY id DESC
        '''

    ).fetchall()

    operators_list = conn.execute(

        '''
        SELECT *
        FROM operators
        ORDER BY id DESC
        '''

    ).fetchall()

    conn.close()

    return render_template(

        'admin_dashboard.html',

        total_users=
        total_users,

        total_tickets=
        total_tickets,

        total_revenue=
        total_revenue,

        trips=
        trips,

        tickets=
        tickets,

        reviews=
        reviews,

        operators_list=
        operators_list
    )


@app.route(
    '/admin_add_trip',
    methods=['POST']
)
def admin_add_trip():
    if 'admin_id' not in session:
        return redirect(
            url_for('admin_login')
        )

    conn = get_db_connection()

    conn.execute(

        '''
        INSERT INTO trips
        (
            transport_type,
            operator,
            departure,
            destination,
            dep_time,
            price,
            duration,
            dur_mins,
            seats_available
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',

        (
            request.form['type'],

            request.form['operator'],

            request.form['dep'],

            request.form['dest'],

            request.form['time'],

            int(
                request.form['price']
            ),

            request.form['duration'],

            int(
                request.form['dur_mins']
            ),

            int(
                request.form['seats']
            )
        )
    )

    conn.commit()

    conn.close()

    flash(
        '✅ New Trip Added Successfully to Live Database!',
        'success'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.route(
    '/admin_add_operator',
    methods=['POST']
)
def admin_add_operator():
    if 'admin_id' not in session:
        return redirect(
            url_for('admin_login')
        )

    company_name = request.form[
        'company_name'
    ]

    email = request.form[
        'email'
    ]

    password = generate_password_hash(
        request.form['password']
    )

    conn = get_db_connection()

    try:

        conn.execute(

            '''
            INSERT INTO operators
            (
                company_name,
                email,
                password
            )

            VALUES (?, ?, ?)
            ''',

            (
                company_name,
                email,
                password
            )
        )

        conn.commit()

        flash(
            f'✅ Operator account for "{company_name}" created successfully!',
            'success'
        )

    except sqlite3.IntegrityError:

        flash(
            f'⚠️ An operator with email "{email}" already exists!',
            'danger'
        )

    finally:

        conn.close()

    return redirect(
        url_for('admin_dashboard')
    )


@app.route(
    '/admin_delete_trip/<int:id>'
)
def admin_delete_trip(id):
    if 'admin_id' not in session:
        return redirect(
            url_for('admin_login')
        )

    conn = get_db_connection()

    conn.execute(

        '''
        DELETE FROM trips
        WHERE id = ?
        ''',

        (
            id,
        )
    )

    conn.commit()

    conn.close()

    flash(
        '🗑️ Trip Deleted Successfully!',
        'danger'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.route(
    '/admin_cancel_ticket/<pnr>'
)
def admin_cancel_ticket(pnr):
    if 'admin_id' not in session:
        return redirect(
            url_for('admin_login')
        )

    conn = get_db_connection()

    conn.execute(

        '''
        UPDATE tickets
        SET status = ?
        WHERE pnr = ?
        ''',

        (
            'Cancelled by Admin',
            pnr
        )
    )

    conn.commit()

    conn.close()

    flash(
        f'🚫 Ticket {pnr} Force Cancelled by Admin!',
        'danger'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.route(
    '/admin_delete_review/<int:id>'
)
def admin_delete_review(id):
    if 'admin_id' not in session:
        return redirect(
            url_for('admin_login')
        )

    conn = get_db_connection()

    conn.execute(

        '''
        DELETE FROM reviews
        WHERE id = ?
        ''',

        (
            id,
        )
    )

    conn.commit()

    conn.close()

    flash(
        '🗑️ Review removed from website!',
        'warning'
    )

    return redirect(
        url_for('admin_dashboard')
    )


@app.route('/admin_logout')
def admin_logout():
    session.pop(
        'admin_id',
        None
    )

    return redirect(
        url_for('admin_login')
    )


@app.route(
    '/operator_login',
    methods=['GET', 'POST']
)
def operator_login():
    if 'user_id' in session:
        flash(
            '⚠️ Unauthorized Access! You do not have permission to view this page.',
            'danger'
        )

        return redirect(
            url_for('index')
        )

    if request.method == 'POST':

        conn = get_db_connection()

        operator = conn.execute(

            '''
            SELECT *
            FROM operators
            WHERE email = ?
            ''',

            (
                request.form['email'],
            )
        ).fetchone()

        conn.close()

        if operator and check_password_hash(
                operator['password'],
                request.form['password']
        ):
            session['operator_id'] = (
                operator['id']
            )

            session['operator_company'] = (
                operator['company_name']
            )

            flash(
                'Operator logged in successfully!',
                'success'
            )

            return redirect(
                url_for(
                    'operator_dashboard'
                )
            )

        flash(
            'Invalid Operator Credentials!',
            'danger'
        )

    return render_template(
        'operator_login.html'
    )


@app.route('/operator_dashboard')
def operator_dashboard():
    if 'operator_id' not in session:
        return redirect(
            url_for(
                'operator_login'
            )
        )

    company_name = (
        session[
            'operator_company'
        ]
    )

    conn = get_db_connection()

    tickets = conn.execute(

        '''
        SELECT *
        FROM tickets
        WHERE operator = ?
        ORDER BY id DESC
        ''',

        (
            company_name,
        )
    ).fetchall()

    revenue_data = conn.execute(

        '''
        SELECT SUM(price - due_amount)
        FROM tickets

        WHERE operator = ?
        AND status NOT LIKE '%Cancelled%'
        ''',

        (
            company_name,
        )
    ).fetchone()[0]

    total_revenue = (

        revenue_data
        if revenue_data
        else 0
    )

    due_data = conn.execute(

        '''
        SELECT SUM(due_amount)
        FROM tickets

        WHERE operator = ?
        AND status NOT LIKE '%Cancelled%'
        ''',

        (
            company_name,
        )
    ).fetchone()[0]

    total_dues = (

        due_data
        if due_data
        else 0
    )

    total_tickets = len(
        tickets
    )

    operator_data = conn.execute(

        '''
        SELECT total_expenses
        FROM operators
        WHERE id = ?
        ''',

        (
            session['operator_id'],
        )
    ).fetchone()

    total_expenses = (

        operator_data[
            'total_expenses'
        ]

        if operator_data
           and operator_data[
               'total_expenses'
           ]

        else 0
    )

    net_profit = (
            total_revenue -
            total_expenses
    )

    operator_trips = conn.execute(

        '''
        SELECT *
        FROM trips
        WHERE operator = ?
        ORDER BY id DESC
        ''',

        (
            company_name,
        )
    ).fetchall()

    op_transport = "Bus"

    if operator_trips:

        op_transport = operator_trips[0]['transport_type']

    else:

        c_lower = company_name.lower()

        if 'air' in c_lower or 'biman' in c_lower or 'novo' in c_lower:
            op_transport = "Air"

        elif 'mv ' in c_lower or 'water' in c_lower:
            op_transport = "Launch"

        elif 'express' in c_lower and 'hanif' not in c_lower:
            op_transport = "Train"

    today_date = datetime.now().strftime('%Y-%m-%d')
    booked_seats_dict = {}

    for trip in operator_trips:
        tickets_for_trip = conn.execute('''
            SELECT seat_info
            FROM tickets
            WHERE operator=? AND departure=? AND destination=? AND dep_time=? AND journey_date=? AND status NOT LIKE '%Cancelled%'
        ''', (company_name, trip['departure'], trip['destination'], trip['dep_time'], today_date)).fetchall()

        seats = []
        for t_rec in tickets_for_trip:
            # 🟢 DYNAMIC LAYOUT: Regex matches A1, 10F, T40, C120 accurately
            s_list = re.findall(r'\b[A-Z]{1,3}\d+\b|\b\d+[A-Z]\b|\bT\d+-\d+\b|\bC\d+\b', t_rec['seat_info'])
            seats.extend(s_list)

        booked_seats_dict[trip['id']] = seats

    booked_seats_json = json.dumps(booked_seats_dict)

    conn.close()

    return render_template(

        'operator_dashboard.html',

        company_name=
        company_name,

        tickets=
        tickets,

        total_revenue=
        total_revenue,

        total_expenses=
        total_expenses,

        net_profit=
        net_profit,

        total_dues=
        total_dues,

        total_tickets=
        total_tickets,

        operator_trips=
        operator_trips,

        booked_seats_json=
        booked_seats_json,

        op_transport=
        op_transport
    )


@app.route(
    '/operator_add_route',
    methods=['POST']
)
def operator_add_route():

    if 'operator_id' not in session:
        return redirect(
            url_for('operator_login')
        )

    company_name = (
        session['operator_company']
    )

    departure = request.form.get(
        'departure'
    )

    destination = request.form.get(
        'destination'
    )

    raw_time = request.form.get(
        'dep_time'
    )

    price = int(
        request.form.get('price')
    )

    duration = request.form.get(
        'duration'
    )

    dur_mins = int(
        request.form.get('dur_mins')
    )

    seats_available = int(
        request.form.get('seats_available')
    )

    if departure == destination:
        flash(
            '⚠️ Route Error: Departure and Destination cannot be the same city!',
            'danger'
        )
        return redirect(url_for('operator_dashboard'))

    try:
        time_obj = datetime.strptime(raw_time, '%H:%M')
        formatted_time = time_obj.strftime('%I:%M %p')
    except ValueError:
        formatted_time = raw_time

    conn = get_db_connection()

    op_trips = conn.execute(
        'SELECT transport_type FROM trips WHERE operator = ? LIMIT 1',
        (company_name,)
    ).fetchone()

    if op_trips:

        transport_type = op_trips['transport_type']

    else:

        c_lower = company_name.lower()

        if 'air' in c_lower or 'biman' in c_lower or 'novo' in c_lower:
            transport_type = "Air"

        elif 'mv ' in c_lower or 'water' in c_lower:
            transport_type = "Launch"

        elif 'express' in c_lower and 'hanif' not in c_lower:
            transport_type = "Train"

        else:
            transport_type = "Bus"


    conn.execute(
        '''
        INSERT INTO trips
        (
            transport_type,
            operator,
            departure,
            destination,
            dep_time,
            price,
            duration,
            dur_mins,
            seats_available
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            transport_type,
            company_name,
            departure,
            destination,
            formatted_time,
            price,
            duration,
            dur_mins,
            seats_available
        )
    )

    conn.commit()
    conn.close()

    flash(
        f'✅ New Route ({departure} ➔ {destination}) added successfully for {company_name}!',
        'success'
    )

    return redirect(
        url_for('operator_dashboard')
    )


@app.route(
    '/operator_update_price',
    methods=['POST']
)
def operator_update_price():
    if 'operator_id' not in session:
        return redirect(
            url_for(
                'operator_login'
            )
        )

    company_name = (
        session[
            'operator_company'
        ]
    )

    trip_id = request.form.get(
        'trip_id'
    )

    new_price = int(
        request.form.get(
            'new_price'
        )
    )

    class_type = request.form.get(
        'class_type',
        'Standard Class'
    )

    base_price = (
        new_price
    )

    if class_type == "Economy Class":

        base_price = int(
            new_price /
            0.85
        )

    elif class_type == "Premium Class":

        base_price = int(
            new_price /
            1.25
        )

    elif class_type == "VIP / Business":

        base_price = int(
            new_price /
            1.50
        )

    conn = get_db_connection()

    conn.execute(

        '''
        UPDATE trips
        SET price = ?

        WHERE id = ?
        AND operator = ?
        ''',

        (
            base_price,
            trip_id,
            company_name
        )
    )

    conn.commit()

    conn.close()

    flash(

        f'📈 {class_type} fare dynamically updated to '
        f'৳{new_price}! '
        f'(Base fare adjusted automatically)',

        'success'
    )

    return redirect(
        url_for(
            'operator_dashboard'
        )
    )


@app.route(
    '/operator_add_expense',
    methods=['POST']
)
def operator_add_expense():
    if 'operator_id' not in session:
        return redirect(
            url_for(
                'operator_login'
            )
        )

    expense_amount = int(
        request.form.get(
            'expense_amount'
        )
    )

    conn = get_db_connection()

    conn.execute(

        '''
        UPDATE operators

        SET total_expenses =
            total_expenses + ?

        WHERE id = ?
        ''',

        (
            expense_amount,
            session['operator_id']
        )
    )

    conn.commit()

    conn.close()

    flash(

        f'💸 Expense of ৳{expense_amount} recorded successfully. '
        f'Net Profit updated!',

        'warning'
    )

    return redirect(
        url_for(
            'operator_dashboard'
        )
    )


@app.route(
    '/operator_pos_booking',
    methods=['POST']
)
def operator_pos_booking():
    if 'operator_id' not in session:
        return redirect(
            url_for(
                'operator_login'
            )
        )

    company_name = (
        session[
            'operator_company'
        ]
    )

    trip_id = request.form.get(
        'trip_id'
    )

    passenger_name = request.form.get(
        'passenger_name'
    )

    passenger_phone = request.form.get(
        'passenger_phone',
        'No Number'
    )

    selected_seats = request.form.get(
        'selected_seats_input',
        ''
    )

    quantity = int(
        request.form.get(
            'quantity',
            1
        )
    )

    conn = get_db_connection()

    trip = conn.execute(

        '''
        SELECT *
        FROM trips

        WHERE id = ?
        AND operator = ?
        ''',

        (
            trip_id,
            company_name
        )
    ).fetchone()

    if not trip:
        flash(
            '⚠️ Invalid Trip Selected!',
            'danger'
        )

        conn.close()

        return redirect(
            url_for(
                'operator_dashboard'
            )
        )

    if trip['seats_available'] <= 0 or trip['seats_available'] < quantity:
        flash(
            f'⚠️ Booking Failed! No seats available for this trip (0 Left).',
            'danger'
        )

        conn.close()

        return redirect(
            url_for(
                'operator_dashboard'
            )
        )

    total_price = (
            trip['price'] *
            quantity
    )

    pnr_number = (
        f"PNR-{random.randint(10000, 99999)}"
    )

    if selected_seats:
        seat_info = (
            f"Counter Booking | "
            f"Seats: {selected_seats} | "
            f"📞 {passenger_phone} (Cash)"
        )
    else:
        seat_info = (
            f"Counter Booking | "
            f"Seats: Auto-Assigned ({quantity}) | "
            f"📞 {passenger_phone} (Cash)"
        )

    journey_date = (
        datetime.now().strftime(
            '%Y-%m-%d'
        )
    )

    conn.execute(

        '''
        INSERT INTO tickets
        (
            pnr,
            passenger_name,
            transport_type,
            operator,
            departure,
            destination,
            journey_date,
            dep_time,
            price,
            seat_info,
            payment_method,
            status,
            earned_coins,
            used_coins,
            payment_type,
            due_amount
        )

        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',

        (
            pnr_number,
            passenger_name,
            trip['transport_type'],
            company_name,
            trip['departure'],
            trip['destination'],
            journey_date,
            trip['dep_time'],
            total_price,
            seat_info,
            'Counter Cash',
            'Confirmed (100% Paid)',
            0,
            0,
            'full',
            0
        )
    )

    conn.execute(

        '''
        UPDATE trips

        SET seats_available =
            seats_available - ?

        WHERE id = ?
        ''',

        (
            quantity,
            trip_id
        )
    )

    conn.commit()

    conn.close()

    flash(

        f'✅ POS Offline Booking Successful! '
        f'PNR: {pnr_number} '
        f'(Collected ৳{total_price} Cash)',

        'success'
    )

    return redirect(
        url_for(
            'operator_dashboard'
        )
    )


@app.route(
    '/operator_clear_due/<pnr>'
)
def operator_clear_due(pnr):
    if 'operator_id' not in session:
        return redirect(
            url_for(
                'operator_login'
            )
        )

    company_name = (
        session[
            'operator_company'
        ]
    )

    conn = get_db_connection()

    ticket = conn.execute(

        '''
        SELECT *
        FROM tickets

        WHERE pnr = ?
        AND operator = ?
        ''',

        (
            pnr,
            company_name
        )
    ).fetchone()

    if ticket and ticket['due_amount'] > 0:

        new_status = (
            'Confirmed (100% Paid)'
        )

        conn.execute(

            '''
            UPDATE tickets

            SET due_amount = 0,
                status = ?

            WHERE pnr = ?
            ''',

            (
                new_status,
                pnr
            )
        )

        conn.commit()

        flash(

            f'✅ Due amount collected successfully! '
            f'Ticket {pnr} is now 100% Paid.',

            'success'
        )

    else:

        flash(
            '⚠️ Invalid request or due already cleared!',
            'danger'
        )

    conn.close()

    return redirect(
        url_for(
            'operator_dashboard'
        )
    )


@app.route(
    '/operator_update_status',
    methods=['POST']
)
def operator_update_status():
    if 'operator_id' not in session:
        return redirect(
            url_for(
                'operator_login'
            )
        )

    company_name = (
        session[
            'operator_company'
        ]
    )

    trip_id = request.form.get(
        'trip_id'
    )

    new_status = request.form.get(
        'live_status'
    )

    conn = get_db_connection()

    conn.execute(

        '''
        UPDATE trips

        SET live_status = ?

        WHERE id = ?
        AND operator = ?
        ''',

        (
            new_status,
            trip_id,
            company_name
        )
    )

    conn.commit()

    conn.close()

    flash(

        f'📡 Trip live status updated to: {new_status}',

        'info'
    )

    return redirect(
        url_for(
            'operator_dashboard'
        )
    )


@app.route('/operator_logout')
def operator_logout():
    session.pop(
        'operator_id',
        None
    )

    session.pop(
        'operator_company',
        None
    )

    flash(
        'Operator logged out successfully.',
        'info'
    )

    return redirect(
        url_for(
            'operator_login'
        )
    )


def setup_database_for_operator():
    conn = get_db_connection()

    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS operators
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        '''
    )

    try:

        conn.execute(
            '''
            ALTER TABLE operators
            ADD COLUMN total_expenses
            INTEGER DEFAULT 0
            '''
        )

    except sqlite3.OperationalError:

        pass

    # 🔐 Optional default operator setup.
    # Credentials are read from environment variables instead of being
    # published inside the source code. Existing operator accounts in
    # transport.db continue to work exactly as before.
    default_operator_email = os.environ.get(
        'JATRA_DEFAULT_OPERATOR_EMAIL'
    )

    default_operator_password = os.environ.get(
        'JATRA_DEFAULT_OPERATOR_PASSWORD'
    )

    default_operator_company = os.environ.get(
        'JATRA_DEFAULT_OPERATOR_COMPANY',
        'Hanif Enterprise'
    )

    if default_operator_email and default_operator_password:

        operator = conn.execute(

            '''
            SELECT *
            FROM operators
            WHERE email = ?
            ''',

            (
                default_operator_email,
            )
        ).fetchone()

        if not operator:
            conn.execute(

                '''
                INSERT INTO operators
                (
                    company_name,
                    email,
                    password
                )

                VALUES (?, ?, ?)
                ''',

                (
                    default_operator_company,

                    default_operator_email,

                    generate_password_hash(
                        default_operator_password
                    )
                )
            )

    try:

        conn.execute(

            '''
            ALTER TABLE trips
            ADD COLUMN live_status
            TEXT DEFAULT 'Scheduled'
            '''
        )

    except sqlite3.OperationalError:

        pass

    conn.commit()

    conn.close()


if __name__ == '__main__':
    setup_database_for_operator()

    app.run(
        debug=True,
        host='0.0.0.0'
    )
