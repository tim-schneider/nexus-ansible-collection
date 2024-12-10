---
title: Roles
weight: 12
---

```yaml {filename="group_vars/all.yml"}
    nexus_roles:
    - id: "nx-admin"
        name: "nx-admin"
        description: "Administrator Role"
        privileges:
        - "nx-all"
        roles: []
    - id: "nx-anonymous"
        name: "nx-anonymous"
        description: "Anonymous Role"
        privileges:
        - "nx-healthcheck-read"
        - "nx-search-read"
        - "nx-repository-view-*-*-read"
        - "nx-repository-view-*-*-browse"
        roles: []
```
