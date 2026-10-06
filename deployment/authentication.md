# Future Authentication Evolution

Local development uses SQL Server authentication:

```text
.env
  -> SQL username and password
  -> SQL Server
```

The intended future Azure model is:

```text
App Service managed identity
  -> Microsoft Entra ID
  -> Azure SQL Database
```

Managed identity and Microsoft Entra authentication are future deployment
concerns. They are not implemented in the local application and no Azure SDK
dependency is included solely for them. Azure SQL authorization will eventually
require an Entra administrator plus least-privilege database users and roles for
the runtime and migration identities.