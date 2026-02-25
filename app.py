from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "hireease_secret"

def init_db():
    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            contact TEXT,
            password TEXT,
            experience TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            district TEXT,
            required_skill TEXT,
            status TEXT,
            max_hires INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            district TEXT,
            availability TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            district TEXT,
            required_skill TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            worker_id INTEGER,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        role = request.form["role"].strip()
        contact = request.form["contact"].strip()
        password = generate_password_hash(request.form["password"])

        experience = None
        if role == "worker":
            experience = request.form["experience"].strip()

        conn = sqlite3.connect("hireease.db")
        c = conn.cursor()

        c.execute("INSERT INTO users (name, role, contact, password, experience) VALUES (?, ?, ?, ?, ?)",
                  (name, role, contact, password, experience))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        contact = request.form["contact"].strip()
        password = request.form["password"].strip()

        conn = sqlite3.connect("hireease.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE contact=?", (contact,))
        user = c.fetchone()

        conn.close()

        if user and check_password_hash(user[4], password):
            session["user_id"] = user[0]
            session["role"] = user[2]
            session["name"] = user[1]

            # 🔥 Admin redirect
            if user[2] == "admin":
                return redirect("/admin")

            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] == "worker":
        return render_template("worker_dashboard.html")
    else:
        return render_template("employer_dashboard.html")


@app.route("/post_skill", methods=["GET", "POST"])
def post_skill():
    if "user_id" not in session or session["role"] != "worker":
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        district = request.form["district"].strip()
        availability = request.form["availability"].strip()

        conn = sqlite3.connect("hireease.db")
        c = conn.cursor()
        c.execute("INSERT INTO skills (user_id, title, description, district, availability) VALUES (?, ?, ?, ?, ?)",
                  (session["user_id"], title, description, district, availability))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("post_skill.html")


@app.route("/search_skills", methods=["GET", "POST"])
def search_skills():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    query = "SELECT skills.title, skills.description, skills.district, skills.availability, users.name, users.contact FROM skills JOIN users ON skills.user_id = users.id"
    filters = []
    values = []

    skill_keyword = request.args.get("skill")
    district = request.args.get("district")

    if skill_keyword:
        filters.append("skills.title LIKE ?")
        values.append(f"%{skill_keyword}%")

    if district:
        filters.append("skills.district LIKE ?")
        values.append(f"%{district}%")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    c.execute(query, values)
    results = c.fetchall()

    conn.close()

    return render_template("search_skills.html", results=results)

@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if "user_id" not in session or session["role"] != "employer":
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        district = request.form["district"].strip()
        required_skill = request.form["required_skill"].strip()
        status = "Open"
        max_hires = int(request.form["max_hires"])

        conn = sqlite3.connect("hireease.db")
        c = conn.cursor()
        c.execute("INSERT INTO jobs (user_id, title, description, district, required_skill, status,max_hires) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (session["user_id"], title, description, district, required_skill, status,max_hires))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("post_job.html")

@app.route("/close_job/<int:job_id>")
def close_job(job_id):
    if "user_id" not in session or session["role"] != "employer":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()
    c.execute("UPDATE jobs SET status='Closed' WHERE id=? AND user_id=?", 
              (job_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect("/dashboard")
@app.route("/my_jobs")
def my_jobs():
    if "user_id" not in session or session["role"] != "employer":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()
    c.execute("SELECT id, title, status FROM jobs WHERE user_id=?", 
              (session["user_id"],))
    jobs = c.fetchall()
    conn.close()

    return render_template("my_jobs.html", jobs=jobs)
@app.route("/view_jobs", methods=["GET"])
def view_jobs():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    query = "SELECT id, title, description, district, required_skill, status FROM jobs WHERE status='Open'"
    filters = []
    values = []

    skill = request.args.get("skill")
    district = request.args.get("district")

    if skill:
        filters.append("required_skill LIKE ?")
        values.append(f"%{skill}%")

    if district:
        filters.append("district LIKE ?")
        values.append(f"%{district}%")

    if filters:
        query += " AND " + " AND ".join(filters)

    c.execute(query, values)
    jobs = c.fetchall()
    conn.close()

    return render_template("view_jobs.html", jobs=jobs)

@app.route("/my_skills")
def my_skills():
    if "user_id" not in session or session["role"] != "worker":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()
    c.execute("SELECT id, title, district, availability FROM skills WHERE user_id=?", 
              (session["user_id"],))
    skills = c.fetchall()
    conn.close()

    return render_template("my_skills.html", skills=skills)

@app.route("/delete_skill/<int:skill_id>")
def delete_skill(skill_id):
    if "user_id" not in session or session["role"] != "worker":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()
    c.execute("DELETE FROM skills WHERE id=? AND user_id=?", 
              (skill_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect("/my_skills")
@app.route("/apply/<int:job_id>")
def apply(job_id):
    if "user_id" not in session or session["role"] != "worker":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    # Check job status and capacity
    c.execute("SELECT status, max_applicants FROM jobs WHERE id=?", (job_id,))
    job = c.fetchone()

    if not job or job[0] == "Closed":
        conn.close()
        return redirect("/view_jobs")

    # Count current applications
    c.execute("SELECT COUNT(*) FROM applications WHERE job_id=?", (job_id,))
    count = c.fetchone()[0]

    if count >= job[1]:
        # Close job automatically
        c.execute("UPDATE jobs SET status='Closed' WHERE id=?", (job_id,))
        conn.commit()
        conn.close()
        return redirect("/view_jobs")

    # Prevent duplicate applications
    c.execute("SELECT * FROM applications WHERE job_id=? AND worker_id=?",
              (job_id, session["user_id"]))
    existing = c.fetchone()

    if not existing:
        c.execute("INSERT INTO applications (job_id, worker_id, status) VALUES (?, ?, ?)",
                  (job_id, session["user_id"], "Pending"))
        conn.commit()

    conn.close()
    return redirect("/view_jobs")

@app.route("/view_applicants/<int:job_id>")
def view_applicants(job_id):
    if "user_id" not in session or session["role"] != "employer":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    c.execute("""
        SELECT applications.id, users.name, users.contact, applications.status
        FROM applications
        JOIN users ON applications.worker_id = users.id
        WHERE applications.job_id=?
    """, (job_id,))

    applicants = c.fetchall()
    conn.close()

    return render_template("view_applicants.html", applicants=applicants)
@app.route("/update_application/<int:app_id>/<action>")
def update_application(app_id, action):
    if "user_id" not in session or session["role"] != "employer":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    # Get job_id from this application
    c.execute("SELECT job_id FROM applications WHERE id=?", (app_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        return redirect("/dashboard")

    job_id = result[0]

    if action == "accept":
        # Count already accepted
        c.execute("SELECT COUNT(*) FROM applications WHERE job_id=? AND status='Accepted'", (job_id,))
        accepted_count = c.fetchone()[0]

        # Get max_hires
        c.execute("SELECT max_hires FROM jobs WHERE id=?", (job_id,))
        max_hires = c.fetchone()[0]

        if accepted_count < max_hires:
            c.execute("UPDATE applications SET status='Accepted' WHERE id=?", (app_id,))

            # Recount after acceptance
            c.execute("SELECT COUNT(*) FROM applications WHERE job_id=? AND status='Accepted'", (job_id,))
            new_count = c.fetchone()[0]

            if new_count >= max_hires:
                c.execute("UPDATE jobs SET status='Closed' WHERE id=?", (job_id,))

    elif action == "reject":
        c.execute("UPDATE applications SET status='Rejected' WHERE id=?", (app_id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)

@app.route("/my_applications")
def my_applications():
    if "user_id" not in session or session["role"] != "worker":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    c.execute("""
        SELECT jobs.title, jobs.district, applications.status, users.contact
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN users ON jobs.user_id = users.id
        WHERE applications.worker_id=?
    """, (session["user_id"],))

    applications = c.fetchall()
    conn.close()

    return render_template("my_applications.html", applications=applications)

@app.route("/all_applications")
def all_applications():
    if "user_id" not in session or session["role"] != "employer":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    c.execute("""
        SELECT jobs.title, users.name, users.contact, applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN users ON applications.worker_id = users.id
        WHERE jobs.user_id=?
    """, (session["user_id"],))

    applications = c.fetchall()
    conn.close()

    return render_template("all_applications.html", applications=applications)

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    conn = sqlite3.connect("hireease.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE role='worker'")
    total_workers = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE role='employer'")
    total_employers = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM jobs WHERE status='Open'")
    open_jobs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM jobs WHERE status='Closed'")
    closed_jobs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM applications")
    total_applications = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM applications WHERE status='Accepted'")
    accepted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM applications WHERE status='Rejected'")
    rejected = c.fetchone()[0]

    conn.close()

    return render_template("admin_dashboard.html",
        total_users=total_users,
        total_workers=total_workers,
        total_employers=total_employers,
        total_jobs=total_jobs,
        open_jobs=open_jobs,
        closed_jobs=closed_jobs,
        total_applications=total_applications,
        accepted=accepted,
        rejected=rejected
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)