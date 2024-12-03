def get_nested_value(data, key_path, default=None):
    """
    Retrieve a nested value from a dictionary using a dotted key path.
    Returns the default value if any key in the path is missing.
    """
    keys = key_path.split('.')
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data


def set_nested_value(data, key_path, value):
    """
    Set a nested value in a dictionary using a dotted key path.
    Creates intermediate dictionaries as needed.
    """
    keys = key_path.split('.')
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value


def normalize_repositories(repo_data, repo_type, repo_format, schemas):
    """
    Normalize repository configurations into API-compatible format.
    Handles mixed formats by merging legacy and normalized entries.

    Why this approach:
    - Ensures compatibility with the Nexus API by transforming input data into the required schema.
    - Supports legacy formats (method A) while allowing already normalized (method B) configurations.
    - Handles both flat and nested attributes dynamically using schema definitions.
    - Provides default values and validates required fields to avoid runtime API errors.

    Parameters:
    - repo_data: List of repository configurations (mixed formats supported).
    - repo_type: Type of repository (e.g., 'proxy', 'hosted', 'group').
    - repo_format: Format of the repository (e.g., 'maven', 'docker', 'npm').
    - schemas: Dictionary containing field mappings, default values, and required attributes.

    Returns:
    - A list of normalized repositories, ready for API consumption.
    """
    # Validate that the schema exists for the given repo type and format
    if repo_type not in schemas or repo_format not in schemas[repo_type]:
        raise ValueError(
            f"No schema defined for repository type '{
                repo_type}' and format '{repo_format}'"
        )

    # Load the schema for this repository type and format
    schema = schemas[repo_type][repo_format]
    normalized_repos = []  # Output list of normalized repositories

    for repo in repo_data:
        normalized = {}  # Start with an empty dictionary for the normalized repository

        # Map fields from source to target based on the schema
        for src_field, target_field in schema.get("field_map", {}).items():
            value = get_nested_value(repo, src_field)
            if value is not None:
                set_nested_value(normalized, target_field, value)

        # Merge existing nested structures (e.g., 'proxy', 'negativeCache') with defaults
        for key in ["proxy", "negativeCache", "httpClient", "storage", "maven"]:
            if key in repo:
                # Merge input structure with defaults (if any)
                normalized.setdefault(key, {}).update(repo[key])

        # Add default values for missing attributes
        for key, default_value in schema.get("default_values", {}).items():
            if get_nested_value(normalized, key) is None:
                set_nested_value(normalized, key, default_value)

        # Normalize httpClient.authentication.type
        auth_block = get_nested_value(
            normalized, "httpClient.authentication", {})
        if auth_block:
            username = auth_block.get("username")
            password = auth_block.get("password")
            ntlm_host = auth_block.get("ntlmHost")
            ntlm_domain = auth_block.get("ntlmDomain")

            if ntlm_host or ntlm_domain:
                # NTLM authentication requires all related fields
                if not (username and password and ntlm_host and ntlm_domain):
                    raise ValueError(
                        f"Repository '{
                            repo.get('name', 'unknown')}' is missing required fields "
                        "for NTLM authentication (username, password, ntlmHost, ntlmDomain)."
                    )
                auth_block["type"] = "ntlm"
            elif username or password:
                # Username-based authentication
                if not (username and password):
                    raise ValueError(
                        f"Repository '{
                            repo.get('name', 'unknown')}' is missing required fields "
                        "for username authentication (username and password)."
                    )
                auth_block["type"] = "username"

            # Update the normalized dictionary with the modified auth_block
            set_nested_value(
                normalized, "httpClient.authentication", auth_block)

        # Validate required attributes after processing
        for required_key in schema.get("required_fields", []):
            if get_nested_value(normalized, required_key) is None:
                raise ValueError(
                    f"Missing required field: {required_key} in repository '{
                        repo.get('name', 'unknown')}'"
                )

        # Append the fully normalized repository to the output list
        normalized_repos.append(normalized)

    return normalized_repos


class FilterModule:
    def filters(self):
        """
        Ansible filter module definition.
        Registers the 'normalize_repositories' filter for use in playbooks.
        """
        return {
            "normalize_repositories": normalize_repositories
        }
