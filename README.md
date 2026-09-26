# Campus Queue — Virtual Queue Management System

A full-stack Flask + SQLite web app that lets students generate a virtual
queue token for a campus office, track their live position, and lets staff
and admins manage the queue. Built specifically to be a strong subject for
**manual QA and Selenium + Python + Pytest automation**: every important
element has a stable `id`, forms use predictable field `name`s, and
success/error messages carry their own IDs.

---

## 1. Install dependencies

Requires Python 3.9+.

```bash
cd campus_queue
python -m venv venv           # optional but recommended
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Initialize the database

The database is created and seeded **automatically the first time you run
the app** — there's no separate migration step. If you ever want to reset
all data, just delete the file and restart the app:

```bash
rm database/campus_queue.db     # Windows: del database\campus_queue.db
python app.py
```

## 3. Run the application

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## 4. Demo login credentials

| Role    | Email               | Password      |
|---------|---------------------|---------------|
| Student | student@test.com    | Student@123   |
| Staff   | staff@test.com      | Staff@123     |
| Admin   | admin@test.com      | Admin@123     |

The staff account is pre-assigned to the **Scholarship Office**. New
students can self-register from the Register page; staff/admin accounts are
only created by an admin (directly in the database for now, or you can
extend `admin/users.html` with a "create user" form).

---

## 5. Available features

**Public:** Home, About, Contact (with a working form), Login, Registration.

**Student:** dashboard with current token summary, generate a token
(department → service), live queue position & estimated wait, cancel a
waiting token, full token history, profile page.

**Staff:** dashboard for the assigned department, call next token, skip the
current token, mark the current token completed, today's stats
(waiting / completed / skipped), queue history table.

**Admin:** campus-wide dashboard stats, user management (activate /
deactivate students & staff), department management (add / toggle),
service management (add / toggle, tied to a department), a searchable/
filterable table of all tokens, and a reports page (tokens by status, by
department, and average completion time per department).

**Access control:** every route is protected **server-side** with a
`role_required()` decorator — hiding a nav link is never the only defense.
Unauthorized access shows a proper "Access Denied" page (HTTP 403).

---

## 6. Project structure

```
campus_queue/
├── app.py                  # all Flask routes & business logic
├── database.py              # schema creation + demo data seeding
├── requirements.txt
├── README.md
├── database/
│   └── campus_queue.db      # created automatically on first run
├── templates/
│   ├── base.html             # public layout (navbar/footer)
│   ├── base_dashboard.html   # sidebar layout for student/staff/admin
│   ├── home.html / about.html / contact.html
│   ├── login.html / register.html / access_denied.html
│   ├── student/  (dashboard, generate_token, current_token, history, profile)
│   ├── staff/    (dashboard, queue, history)
│   └── admin/    (dashboard, users, departments, services, tokens, reports)
├── static/
│   ├── css/style.css         # design system (colors, type, components)
│   ├── js/script.js          # toast rendering, confirm dialogs, filters
│   └── images/
└── tests/
    └── README.md             # suggested Selenium/Pytest project layout
```

---

## 7. Important URLs / routes

| Area | Route | Method(s) |
|---|---|---|
| Home | `/` | GET |
| About | `/about` | GET |
| Contact | `/contact` | GET, POST |
| Login | `/login` | GET, POST |
| Logout | `/logout` | GET |
| Register | `/register` | GET, POST |
| Access denied | `/access-denied` | GET |
| Student dashboard | `/student/dashboard` | GET |
| Generate token | `/student/generate-token` | GET, POST |
| Current token | `/student/current-token` | GET |
| Cancel token | `/student/cancel-token/<id>` | POST |
| Token history | `/student/history` | GET |
| Profile | `/student/profile` | GET |
| Staff dashboard | `/staff/dashboard` | GET |
| Staff queue | `/staff/queue` | GET |
| Call next token | `/staff/call-next` | POST |
| Skip token | `/staff/skip/<id>` | POST |
| Complete token | `/staff/complete/<id>` | POST |
| Staff history | `/staff/history` | GET |
| Admin dashboard | `/admin/dashboard` | GET |
| User management | `/admin/users` | GET |
| Toggle user | `/admin/users/toggle/<id>` | POST |
| Department management | `/admin/departments` | GET, POST |
| Toggle department | `/admin/departments/toggle/<id>` | POST |
| Service management | `/admin/services` | GET, POST |
| Toggle service | `/admin/services/toggle/<id>` | POST |
| All tokens | `/admin/tokens` | GET (`?status=`) |
| Reports | `/admin/reports` | GET |

---

## 8. How to test it manually

A ready-to-use set of manual test IDs (TC001–TC026) covering Login,
Registration, Token generation, Queue actions, and Access control. Example
walkthrough:

1. **TC001 Valid login** — go to `/login`, use `student@test.com` /
   `Student@123`, confirm redirect to `/student/dashboard`.
2. **TC012 Generate token** — from the student dashboard click
   *Generate New Token*, pick "Scholarship Office" then a service, submit,
   and confirm a token like `SCH-001` appears.
3. **TC015 Prevent duplicate active token** — try generating a second token
   while the first is still `WAITING`; confirm the message *"You already
   have an active token."* appears (`#active-token-warning`).
4. **TC018 Staff calls next token** — log in as `staff@test.com`, go to
   *Current Queue*, click **Call Next Token**, confirm the token now shows
   status `CALLED`.
5. **TC023 Student cannot access admin** — while logged in as a student,
   navigate directly to `/admin/dashboard`; confirm you see the
   Access Denied page (HTTP 403), not the dashboard.

The full TC001–TC026 scenario list from the original spec is fully
supported by this build — every action listed can be exercised end to end.

### Stable element IDs (selected)

```
#email #password #login-button #login-error
#name #phone #confirm_password #register-button #registration-error
#department-select #service-select #generate-token-button
#token-error #token-success #active-token-warning
#cancel-token-button #queue-position #estimated-wait-time
#current-token-number #current-token-status
#next-token-button #skip-token-button #complete-token-button
#current-serving-token
#users-table #departments-table #services-table #all-tokens-table
```

Every table row also carries a predictable id such as
`#history-row-<id>`, `#user-row-<id>`, `#department-row-<id>`, and every
toggle button is `#toggle-user-<id>`, `#toggle-department-<id>`,
`#toggle-service-<id>` — handy for locating a specific row's action in
Selenium without relying on visible text.

---

## 9. How to automate it with Selenium + Python + Pytest

Suggested setup (see `tests/README.md` for the folder layout):

```bash
pip install selenium pytest webdriver-manager
```

A minimal Page Object + test, following the Page Object Model:

```python
# tests/pages/login_page.py
class LoginPage:
    URL = "http://127.0.0.1:5000/login"

    def __init__(self, driver):
        self.driver = driver

    def open(self):
        self.driver.get(self.URL)

    def login(self, email, password):
        self.driver.find_element("id", "email").send_keys(email)
        self.driver.find_element("id", "password").send_keys(password)
        self.driver.find_element("id", "login-button").click()
```

```python
# tests/test_cases/test_login.py
def test_tc001_valid_login(driver):
    page = LoginPage(driver)
    page.open()
    page.login("student@test.com", "Student@123")
    assert "/student/dashboard" in driver.current_url
```

Because the app never hides a restricted action with JavaScript alone —
every permission check happens on the backend — your access-control tests
(TC023–TC026) can safely assert on the final URL / page content after a
direct `driver.get()` to a protected route, without needing to click
through the UI first.

For regression testing, re-run the full TC001–TC026 suite after any code
change; because IDs are hard-coded and never regenerated dynamically, your
locators won't need to change between runs.
