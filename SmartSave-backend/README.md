
git add .
git commit -m "Trigger fresh render sync"
git push origin main

## Secure administrator access

Set `ADMIN_LOGIN_EMAIL` in the backend deployment environment to the one
administrator email that may use the admin console. Do not put this setting or
an administrator password in frontend files or source control. With that
environment variable configured, provision or rotate the administrator account
on the backend using:

```powershell
python manage.py provision_admin
```

The command prompts for a password without echoing it and stores it using
Django's password hashers. The dedicated administrator login endpoint accepts
only that active, verified staff account, and admin dashboard APIs reject other
staff accounts. Administrator sign-in is rate-limited to five attempts per
minute. Configure the environment variable in the hosting provider before
provisioning; leaving it unset disables administrator dashboard access.
