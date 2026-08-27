import os
import sys
import shutil
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash


# ============================================================
# PROJECT DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'transport.db')


# ============================================================
# OPTIONAL DATABASE BACKUP BEFORE RESET
# ============================================================

def backup_existing_database():
    """
    Creates a backup of the current transport.db before a full reset.
    """

    if not os.path.exists(DATABASE_PATH):
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    backup_name = f'transport_backup_{timestamp}.db'
    backup_path = os.path.join(BASE_DIR, backup_name)

    shutil.copy2(
        DATABASE_PATH,
        backup_path
    )

    print(
        f"✅ Existing database backup created:\n"
        f"{backup_path}"
    )

    return backup_path


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def create_tables(reset=False):

    database_exists = (
        os.path.exists(DATABASE_PATH)
        and os.path.getsize(DATABASE_PATH) > 0
    )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if database_exists and not reset:

        print("⚠️ Existing transport.db detected.")
        print("✅ No existing data was changed or deleted.")
        print("")
        print(
            "If you intentionally want to create a completely "
            "fresh database, run:"
        )
        print("")
        print("python init_db.py --reset")

        return

    # --------------------------------------------------------
    # BACKUP BEFORE INTENTIONAL RESET
    # --------------------------------------------------------

    if database_exists and reset:

        print("⚠️ Full database reset requested.")

        backup_existing_database()

    # --------------------------------------------------------
    # DATABASE CONNECTION
    # --------------------------------------------------------

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    # --------------------------------------------------------
    # DROP TABLES ONLY WHEN --reset IS USED
    # --------------------------------------------------------

    if reset:

        print(
            "⚠️ Reset mode enabled. "
            "Creating fresh database tables..."
        )

        cursor.execute(
            'DROP TABLE IF EXISTS users'
        )

        cursor.execute(
            'DROP TABLE IF EXISTS tickets'
        )

        cursor.execute(
            'DROP TABLE IF EXISTS reviews'
        )

        cursor.execute(
            'DROP TABLE IF EXISTS admins'
        )

        cursor.execute(
            'DROP TABLE IF EXISTS trips'
        )

        cursor.execute(
            'DROP TABLE IF EXISTS operators'
        )

    # ========================================================
    # USERS TABLE
    # ========================================================

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS users
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            coins INTEGER DEFAULT 50
        )
        '''
    )

    # ========================================================
    # TICKETS TABLE
    # ========================================================

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS tickets
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            pnr TEXT NOT NULL,

            passenger_name TEXT NOT NULL,

            transport_type TEXT NOT NULL,

            operator TEXT NOT NULL,

            departure TEXT NOT NULL,

            destination TEXT NOT NULL,

            journey_date TEXT NOT NULL,

            dep_time TEXT NOT NULL,

            price INTEGER NOT NULL,

            seat_info TEXT NOT NULL,

            payment_method TEXT NOT NULL,

            status TEXT DEFAULT 'Confirmed',

            earned_coins INTEGER DEFAULT 0,

            used_coins INTEGER DEFAULT 0,

            payment_type TEXT DEFAULT 'Full Paid',

            due_amount INTEGER DEFAULT 0
        )
        '''
    )

    # ========================================================
    # REVIEWS TABLE
    # ========================================================

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS reviews
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_name TEXT NOT NULL,

            transport_type TEXT NOT NULL,

            rating INTEGER NOT NULL,

            comment TEXT NOT NULL
        )
        '''
    )

    # ========================================================
    # ADMINS TABLE
    # ========================================================

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS admins
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL
        )
        '''
    )

    # ========================================================
    # TRIPS TABLE
    # ========================================================

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS trips
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transport_type TEXT NOT NULL,

            operator TEXT NOT NULL,

            departure TEXT NOT NULL,

            destination TEXT NOT NULL,

            dep_time TEXT NOT NULL,

            price INTEGER NOT NULL,

            duration TEXT NOT NULL,

            dur_mins INTEGER NOT NULL,

            seats_available INTEGER DEFAULT 40,

            live_status TEXT DEFAULT 'Scheduled'
        )
        '''
    )

    # ========================================================
    # OPERATORS TABLE
    # ========================================================

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS operators
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            total_expenses INTEGER DEFAULT 0
        )
        '''
    )

    # ========================================================
    # OPTIONAL ADMIN ACCOUNT
    #
    # Credentials are NOT hard-coded in GitHub source code.
    #
    # Environment variables:
    #
    # JATRA_ADMIN_EMAIL
    # JATRA_ADMIN_PASSWORD
    # ========================================================

    admin_email = os.environ.get(
        'JATRA_ADMIN_EMAIL'
    )

    admin_password = os.environ.get(
        'JATRA_ADMIN_PASSWORD'
    )

    if admin_email and admin_password:

        existing_admin = cursor.execute(
            '''
            SELECT id
            FROM admins
            WHERE email = ?
            ''',
            (
                admin_email,
            )
        ).fetchone()

        if not existing_admin:

            cursor.execute(
                '''
                INSERT INTO admins
                (
                    email,
                    password
                )
                VALUES (?, ?)
                ''',
                (
                    admin_email,

                    generate_password_hash(
                        admin_password
                    )
                )
            )

            print(
                f"✅ Admin account created: "
                f"{admin_email}"
            )

        else:

            print(
                "ℹ️ Admin account already exists."
            )

    else:

        print("")
        print(
            "ℹ️ No default admin credentials "
            "were stored inside the source code."
        )

        print(
            "Set JATRA_ADMIN_EMAIL and "
            "JATRA_ADMIN_PASSWORD if you want "
            "to create an admin automatically."
        )

    # ========================================================
    # OPTIONAL DEFAULT OPERATOR
    #
    # Environment variables:
    #
    # JATRA_DEFAULT_OPERATOR_EMAIL
    # JATRA_DEFAULT_OPERATOR_PASSWORD
    # JATRA_DEFAULT_OPERATOR_COMPANY
    # ========================================================

    operator_email = os.environ.get(
        'JATRA_DEFAULT_OPERATOR_EMAIL'
    )

    operator_password = os.environ.get(
        'JATRA_DEFAULT_OPERATOR_PASSWORD'
    )

    operator_company = os.environ.get(
        'JATRA_DEFAULT_OPERATOR_COMPANY',
        'Hanif Enterprise'
    )

    if operator_email and operator_password:

        existing_operator = cursor.execute(
            '''
            SELECT id
            FROM operators
            WHERE email = ?
            ''',
            (
                operator_email,
            )
        ).fetchone()

        if not existing_operator:

            cursor.execute(
                '''
                INSERT INTO operators
                (
                    company_name,
                    email,
                    password,
                    total_expenses
                )
                VALUES (?, ?, ?, ?)
                ''',
                (
                    operator_company,

                    operator_email,

                    generate_password_hash(
                        operator_password
                    ),

                    0
                )
            )

            print(
                f"✅ Operator account created: "
                f"{operator_company}"
            )

        else:

            print(
                "ℹ️ Operator account already exists."
            )

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    conn.commit()
    conn.close()

    print("")
    print(
        "✅ JATRA APP BD database schema is ready."
    )

    print(
        f"📁 Database location: {DATABASE_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':

    reset_database = (
        '--reset' in sys.argv
    )

    create_tables(
        reset=reset_database
    )