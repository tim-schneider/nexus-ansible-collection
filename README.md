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

This is work in progress and is not -yet- compatible with the `nexus_repos_*_*` format used in the nexus_oss role.

For example, it won't work when your maven proxy repos are defined like the following, because that format is not compatible with the Nexus API.
```yaml
nexus_repos_maven_proxy:
  - name: maven-central
    remote_url: https://repo1.maven.org/maven2/
```

You can rewrite your repo definitions like this:
```yaml
nexus_repos_maven_proxy:
  - name: maven-central
    proxy:
      remoteUrl: https://repo1.maven.org/maven2/
      contentMaxAge: -1
      metadataMaxAge: 1440
    negativeCache:
      enabled: true
      timeToLive: 1440
    httpClient:
      blocked: false
      autoBlock: true
      connection:
        useTrustStore: true
```

Or you wait a bit for us to release a custom filter that would transform and normalize the nexus_oss format of `nexus_repos_*_*` to an API compatible format. Expected mid Dec 2024.


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
