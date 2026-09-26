# Tests

This folder is where your Selenium + Python + Pytest automation suite will
live once you start automating Campus Queue.

Suggested structure (Page Object Model):

```
tests/
├── README.md
├── conftest.py            # pytest fixtures (driver setup/teardown, base_url)
├── pages/
│   ├── login_page.py
│   ├── register_page.py
│   ├── student_dashboard_page.py
│   ├── generate_token_page.py
│   ├── staff_queue_page.py
│   └── admin_users_page.py
└── test_cases/
    ├── test_login.py          # TC001–TC006
    ├── test_registration.py   # TC007–TC011
    ├── test_token.py          # TC012–TC017
    ├── test_queue.py          # TC018–TC022
    └── test_access_control.py # TC023–TC026
```

See the main project README.md for the full list of test IDs (TC001–TC026),
the stable element IDs available on every page, and demo login credentials.
