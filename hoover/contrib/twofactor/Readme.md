`hoover.contrib.twofactor` is an extension to hoover-search that requires the
user to log in with a
[TOTP](https://en.wikipedia.org/wiki/Time-based_One-time_Password_Algorithm)
token. It works with phone apps like Google Authenticator and Duo Mobile.

### setup
* Add the following to `INSTALLED_APPS`:

   ```
        'hoover.contrib.twofactor',
        'django_otp',
        'django_otp.plugins.otp_totp',
   ```

* Add the following to `MIDDLEWARE_CLASSES`:

   ```
        'django_otp.middleware.OTPMiddleware',
        'hoover.contrib.twofactor.middleware.AutoLogout',
        'hoover.contrib.twofactor.middleware.RequireAuth',
   ```

* Set `HOOVER_BASE_URL` to the root URL of your website, no trailing slash>

* Set `HOOVER_TWOFACTOR_INVITATION_VALID` - how long should an invitation be
  valid, in minutes? Defaults to `30`.

* Set `HOOVER_TWOFACTOR_AUTOLOGOUT` if this number of minutes has passed since
  login, then automatically log out the user. Defaults to `120` (3 hours). If
  `None` or `0` then users can stay logged in indefinitely.

### inviting users
New users go through a setup process to configure their TOTP token. The process
begins with an invitation URL, generated from the command line:

```shell
./manage.py invite george --create
```

This will create a new Django user with username `george` and will print the
URL to a short-lived invitation.

If you want to help a user recover an existing account, omit the `--create`
flag.
