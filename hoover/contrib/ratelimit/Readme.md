`hoover.contrib.ratelimit` is an extension to hoover-search that limits the
number of requests by username (or other criteria) in a given time period.

### setup
* add 'hoover.contrib.ratelimit' to `INSTALLED_APPS`
* configure `HOOVER_RATELIMIT_USER` to a tuple of `(number, interval)` (number
  of requests per user per interval). Defaults to `(30, 60)` (30 requests per
  minute).
