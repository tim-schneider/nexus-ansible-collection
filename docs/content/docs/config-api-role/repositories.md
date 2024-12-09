---
title: Repositories
weight: 21
---

#### Docker

{{< tabs items="config_api,nexus_oss" >}}
  {{< tab >}}

  ```yaml
  - name: full-new-format-docker-hosted
    online: true
    storage:
      blobStoreName: default
      strictContentTypeValidation: true
    cleanup:
      policyNames:
        - docker_cleanup_config_api
        - docker_cleanup_nexus_oss
    docker:
      httpPort: 5000
      v1Enabled: false
      forceBasicAuth: true
  ```

  {{< /tab >}}
  {{< tab >}}

  ```yaml
  - name: docker-hosted
    blob_store: blob-docker
    strict_content_validation: true
    cleanup_policies:
      - docker_cleanup_weekly
    http_port: 5001
    v1_enabled: false
    force_basic_auth: true
  ```

  {{< /tab >}}
{{< /tabs >}}
