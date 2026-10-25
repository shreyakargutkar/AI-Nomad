from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
import uuid
from datetime import datetime, timezone

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(DATA_DIR, "journals.db")


def get_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS journals (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            destination TEXT,
            owner_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS collaborators (
            journal_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role TEXT DEFAULT 'editor',
            added_at TEXT NOT NULL,
            PRIMARY KEY (journal_id, user_id),
            FOREIGN KEY (journal_id) REFERENCES journals(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            journal_id TEXT NOT NULL,
            author_id TEXT NOT NULL,
            author_name TEXT,
            title TEXT,
            body TEXT NOT NULL,
            image_data TEXT,
            entry_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (journal_id) REFERENCES journals(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def user_can_access(conn, journal_id, user_id):
    row = conn.execute("SELECT owner_id FROM journals WHERE id = ?", (journal_id,)).fetchone()
    if not row:
        return False, None
    if row["owner_id"] == user_id:
        return True, row
    collab = conn.execute(
        "SELECT 1 FROM collaborators WHERE journal_id = ? AND user_id = ?",
        (journal_id, user_id),
    ).fetchone()
    return collab is not None, row


def journal_to_dict(row, entries=None, collaborators=None):
    data = {
        "id": row["id"],
        "title": row["title"],
        "destination": row["destination"],
        "owner_id": row["owner_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if entries is not None:
        data["entries"] = entries
    if collaborators is not None:
        data["collaborators"] = collaborators
    return data


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "journal"})


@app.route("/api/journals", methods=["GET"])
def list_journals():
    user_id = request.headers.get("X-User-Id") or request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    conn = get_db()
    rows = conn.execute(
        """
        SELECT DISTINCT j.* FROM journals j
        LEFT JOIN collaborators c ON j.id = c.journal_id
        WHERE j.owner_id = ? OR c.user_id = ?
        ORDER BY j.updated_at DESC
        """,
        (user_id, user_id),
    ).fetchall()
    conn.close()
    return jsonify({"journals": [journal_to_dict(r) for r in rows]})


@app.route("/api/journals", methods=["POST"])
def create_journal():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    journal_id = str(uuid.uuid4())
    now = utc_now()
    destination = (data.get("destination") or "").strip()

    conn = get_db()
    conn.execute(
        "INSERT INTO journals (id, title, destination, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (journal_id, title, destination, user_id, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM journals WHERE id = ?", (journal_id,)).fetchone()
    conn.close()
    return jsonify(journal_to_dict(row)), 201


@app.route("/api/journals/<journal_id>", methods=["GET"])
def get_journal(journal_id):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    conn = get_db()
    ok, row = user_can_access(conn, journal_id, user_id)
    if not ok:
        conn.close()
        return jsonify({"error": "Journal not found or access denied"}), 404

    entries = conn.execute(
        "SELECT * FROM entries WHERE journal_id = ? ORDER BY entry_date DESC, created_at DESC",
        (journal_id,),
    ).fetchall()
    collaborators = conn.execute(
        "SELECT user_id, role, added_at FROM collaborators WHERE journal_id = ?",
        (journal_id,),
    ).fetchall()
    conn.close()

    entry_list = [
        {
            "id": e["id"],
            "journal_id": e["journal_id"],
            "author_id": e["author_id"],
            "author_name": e["author_name"],
            "title": e["title"],
            "body": e["body"],
            "has_image": bool(e["image_data"]),
            "image_data": e["image_data"],
            "entry_date": e["entry_date"],
            "created_at": e["created_at"],
        }
        for e in entries
    ]
    collab_list = [
        {"user_id": c["user_id"], "role": c["role"], "added_at": c["added_at"]} for c in collaborators
    ]
    return jsonify(journal_to_dict(row, entries=entry_list, collaborators=collab_list))


@app.route("/api/journals/<journal_id>/entries", methods=["POST"])
def add_entry(journal_id):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "body is required"}), 400

    conn = get_db()
    ok, _ = user_can_access(conn, journal_id, user_id)
    if not ok:
        conn.close()
        return jsonify({"error": "Journal not found or access denied"}), 404

    entry_id = str(uuid.uuid4())
    now = utc_now()
    entry_date = data.get("entry_date") or now[:10]
    image_data = data.get("image_data")

    conn.execute(
        """
        INSERT INTO entries (id, journal_id, author_id, author_name, title, body, image_data, entry_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            journal_id,
            user_id,
            data.get("author_name", ""),
            (data.get("title") or "").strip(),
            body,
            image_data,
            entry_date,
            now,
        ),
    )
    conn.execute("UPDATE journals SET updated_at = ? WHERE id = ?", (now, journal_id))
    conn.commit()
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    conn.close()

    return jsonify(
        {
            "id": row["id"],
            "journal_id": row["journal_id"],
            "author_id": row["author_id"],
            "author_name": row["author_name"],
            "title": row["title"],
            "body": row["body"],
            "has_image": bool(row["image_data"]),
            "image_data": row["image_data"],
            "entry_date": row["entry_date"],
            "created_at": row["created_at"],
        }
    ), 201


@app.route("/api/journals/<journal_id>/collaborators", methods=["POST"])
def add_collaborator(journal_id):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"error": "X-User-Id header required"}), 401

    data = request.get_json() or {}
    partner_id = (data.get("user_id") or "").strip()
    if not partner_id:
        return jsonify({"error": "user_id (partner explorer ID) is required"}), 400

    conn = get_db()
    row = conn.execute("SELECT owner_id FROM journals WHERE id = ?", (journal_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Journal not found"}), 404
    if row["owner_id"] != user_id:
        conn.close()
        return jsonify({"error": "Only the journal owner can invite collaborators"}), 403

    try:
        conn.execute(
            "INSERT INTO collaborators (journal_id, user_id, role, added_at) VALUES (?, ?, ?, ?)",
            (journal_id, partner_id, data.get("role", "editor"), utc_now()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Collaborator already added"}), 409

    conn.close()
    return jsonify({"message": "Collaborator added", "user_id": partner_id}), 201


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5008)
