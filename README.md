# HeartLink – Cyber Dating Demo  
**BS Cyber Security Final Year Project**

Educational demonstration of how a dating-style website can harvest a visitor’s **precise geolocation** and **public IP address** after obtaining consent through a flirtatious (non-vulgar) social-engineering prompt.

---

## Features

| Feature | Description |
|---------|-------------|
| Main site | Attractive dating landing page with “Find my match tonight” CTA |
| Consent prompt | Lustful but non-vulgar language asking for location access |
| Location capture | Browser Geolocation API (lat / lon / accuracy) |
| IP logging | Server-side public IP of the visitor |
| Admin panel | Locked at `/admin` – shows every visitor’s IP + coordinates + maps link |
| Credentials | `identifier: shahmir` / `password: shahmir` |

---

## How to run

```bash
cd cyber-dating
python3 app.py
```

Then open:

- **Main site**  → http://127.0.0.1:5000/
- **Admin login** → http://127.0.0.1:5000/admin  
  Credentials: `shahmir` / `shahmir`

---

## Project structure

```
cyber-dating/
├── app.py                 # Flask backend
├── data/                  # visitors.json (auto-created)
├── static/
│   ├── style.css
│   └── app.js             # Geolocation + fetch logic
├── templates/
│   ├── index.html         # Dating landing page
│   ├── admin_login.html
│   └── admin_dashboard.html
└── README.md
```

---

## Security / Learning points (for your report)

1. **Social engineering** – users willingly grant location because the prompt is framed as “finding a match”.
2. **Geolocation API** – works only over HTTPS (or localhost). Accuracy can be within a few metres.
3. **IP address** – easily obtained server-side; combined with GPS it creates a powerful tracking vector.
4. **Session-based admin auth** – very basic; in a real system you would use proper authentication, rate-limiting, HTTPS, etc.
5. **Data persistence** – currently stored in a local JSON file (resets only when you clear it from the admin panel).

---

## Disclaimer

This project is strictly for educational purposes inside a controlled academic environment.  
Do **not** deploy it on a public server or use it to collect real users’ data without proper consent frameworks and legal compliance.
