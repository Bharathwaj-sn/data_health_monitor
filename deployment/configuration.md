# Configuration Boundary

Local development supplies database values through `.env`:

```text
.env
  -> Settings
  -> database configuration
```

The future Azure equivalent is:

```text
App Service Configuration + Key Vault references
  -> Settings
  -> database configuration
```

Application code consumes `Settings` and does not know the configuration
source. Server, port, database name, schema, driver, timeouts, pool settings,
and encryption options are ordinary configuration. SQL usernames and passwords
are secrets. A future managed-identity client identifier is an Azure-managed
value, not a browser or source-code setting.

Never commit `.env` files, connection strings, passwords, or Key Vault secret
values. `.env.example` documents the variable names with placeholders only.