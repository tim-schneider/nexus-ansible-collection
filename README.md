# Ansible Collection - cloudkrafter.nexus

[![Dynamic JSON Badge](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fgalaxy.ansible.com%2Fapi%2Fv3%2Fplugin%2Fansible%2Fcontent%2Fpublished%2Fcollections%2Findex%2Fcloudkrafter%2Fnexus%2F&query=%24.download_count&label=Galaxy%20Downloads)](https://galaxy.ansible.com/ui/repo/published/cloudkrafter/nexus/)

### Installing

`ansible-galaxy collection install cloudkrafter.nexus`

### Initial setup and using the nexus_oss role

```yaml
- name: Provisioning Playbook (former fork of thoteam/nexus_oss role)
  hosts: all
  collections:
    - cloudkrafter.nexus
  roles:
    - role: cloudkrafter.nexus.nexus_oss
```

### Running desired-state configurations

#### Important note on repository defaults
The `config_api` role uses a different approach to set defaults. If you override the `_nexus_repos_maven_defaults` variable for example, make sure you apply the same defaults to the `nexus_repos_global_defaults`, `nexus_repos_type_defaults` and `nexus_repos_format_defaults` dictionaries! See role defaults for the full dictionaries.


Once you have a working Nexus instance, you can also execute configuration tasks without rebooting your Nexus instance:
**Note:** this role will ensure a desired state. For example repositories not defined in `nexus_repos_*_*` will be **DELETED** in your Nexus instance. If you dont want this, stick with the **nexus_oss** role.

```yaml
- name: Run Desired state config
  hosts: all
  collections:
    - cloudkrafter.nexus
  roles:
    - role: cloudkrafter.nexus.config_api
```

You can also use both roles in one play:

```yaml
- name: Playbook
  hosts: all
  vars:
    # Disables the creation and modification of assets such as repos using the nexus_oss role
    nexus_run_provisionning: false
  collections:
    - cloudkrafter.nexus
  roles:
    - role: cloudkrafter.nexus.nexus_oss # Still ensuring the Nexus server configs
    - role: cloudkrafter.nexus.config_api # Creating, updating or deleting assets such as LDAP servers
```

### Using tags for a execution strategy

All tasks are tagged to allow certain parts to be executed.

available tags:
- license
- security-anonymous-access
- user-tokens
- ssl-truststore
- ldap
- security-realms
- cleanup-policies
- routing-rules
- content-selectors
- blobstores
- roles (depends on repositories)
- users (depends on roles)
- repositories (always needed when using with repo specific tags)
- maven-hosted
- maven-proxy
- maven (will execute tasks for all type maven repos)
**Note:** there are no `*-group` tags! Groups are always depending on either hosted or proxy repos. Therefore group repos can be configured using the format tag of tour group, for example `maven`.

#### Examples for execution strategies
```bash
# Only configure cleanup policies
ansible-playbook -i all --tags cleanup-policies playbook.yml
