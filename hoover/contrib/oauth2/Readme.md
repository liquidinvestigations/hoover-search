### setup
* add `hoover.contrib.oauth2` to `INSTALLED_APPS`
* set `HOOVER_OAUTH_LIQUID_URL` to the URL of the liquid users app
* set `HOOVER_OAUTH_LIQUID_CLIENT_ID` and `HOOVER_OAUTH_LIQUID_CLIENT_SECRET`
  to the Client ID and Client Secret keys (see below)

### obtaining oauth2 client keys
The liquid-core app uses django-rest-framework to implement an oauth2 provider.
In order to obtain client keys, go to the admin site, "Home › Django OAuth
Toolkit › Applications", and create a new application. Select client type
"confidential", authorization grant type "authorization code", and
`http://hoover-search.example.com/accounts/oauth2-exchange/` as redirect URI
(replace `hoover-search.example.com` with the domain of your setup). Copy the
generated "client id" and "client secret" to `HOOVER_OAUTH_LIQUID_CLIENT_ID`
and `HOOVER_OAUTH_LIQUID_CLIENT_SECRET`.
