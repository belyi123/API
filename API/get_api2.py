from flask import Flask, request, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "access_logs.db"


def init_db():
    """Створення таблиці для логів, якщо вона ще не існує."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_agent TEXT,
                path TEXT
            )
        ''')
        conn.commit()


def log_request(ip, user_agent, path):
    """Збереження даних про запит у базу даних."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO logs (ip_address, timestamp, user_agent, path) VALUES (?, ?, ?, ?)",
            (ip, now, user_agent, path)
        )
        conn.commit()


@app.route('/')
def home():
    # Отримання IP-адреси відвідувача.
    # Якщо сервер стоїть за проксі (Nginx/Cloudflare), використовується заголовок X-Forwarded-For
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')

    # Запис у базі даних
    log_request(ip_address, user_agent, request.path)

    return "<h1>Ласкаво просимо на сайт!</h1><p>Ваше відвідування зафіксовано в системних логах.</p>"


@app.route('/admin/logs')
def view_logs():
    """Маршрут для перегляду зібраних логів у вигляді таблиці."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, ip_address, timestamp, path, user_agent FROM logs ORDER BY id DESC")
        logs = cursor.fetchall()

    # Простий HTML-шаблон для відображення логів
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Панель логів сервера</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h2>Журнал відвідувань (Access Logs)</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>IP-адреса</th>
                <th>Час</th>
                <th>Шлях</th>
                <th>User-Agent</th>
            </tr>
            {% for log in logs %}
            <tr>
                <td>{{ log[0] }}</td>
                <td>{{ log[1] }}</td>
                <td>{{ log[2] }}</td>
                <td>{{ log[3] }}</td>
                <td>{{ log[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, logs=logs)


if __name__ == '__main__':
    init_db()
    # Запуск сервера на порту 5000
    app.run(host='0.0.0.0', port=5000, debug=True)