import copy


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


def merge_dict(source, destination):
    """
    Recursively merge `source` dictionary into `destination`.
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            merge_dict(value, destination[key])
        else:
            destination[key] = value
    return destination


def merge_defaults(repo, global_defaults, type_defaults, format_defaults, repo_type, repo_format, legacy_field_map):
    """
    Merge hierarchical defaults and normalize a repository configuration.
    """
    # Step 1: Start with global defaults
    normalized = copy.deepcopy(global_defaults)

    # Step 2: Add type-specific defaults
    normalized = merge_dict(copy.deepcopy(
        type_defaults.get(repo_type, {})), normalized)

    # Step 3: Add format-specific defaults
    normalized = merge_dict(copy.deepcopy(
        format_defaults.get(repo_format, {})), normalized)

    # Step 4: Normalize legacy attributes
    for legacy_key, normalized_key in legacy_field_map.items():
        value = get_nested_value(repo, legacy_key)
        if value is not None:
            set_nested_value(normalized, normalized_key, value)

    # Step 5: Add repository-specific attributes
    normalized = merge_dict(repo, normalized)

    # Step 6: Set authentication type based on defined attributes
    auth_block = get_nested_value(normalized, "httpClient.authentication", {})
    if auth_block:
        ntlm_host = auth_block.get("ntlmHost")
        ntlm_domain = auth_block.get("ntlmDomain")
        username = auth_block.get("username")
        password = auth_block.get("password")

        if ntlm_host and ntlm_domain and username and password:
            # Configure NTLM only if all required fields are present
            auth_block["type"] = "ntlm"
        elif username and password:
            # Configure username-based authentication if NTLM is incomplete
            auth_block["type"] = "username"
        elif ntlm_host or ntlm_domain:
            raise ValueError(
                f"Repository '{
                    repo.get('name', 'unknown')}' has incomplete NTLM authentication settings. "
                "username, password, ntlmHost, and ntlmDomain are all required for NTLM."
            )
        set_nested_value(normalized, "httpClient.authentication", auth_block)

    return normalized


def enhanced_cleanup_legacy_attributes(repo, legacy_field_map):
    """
    Explicitly remove legacy attributes from the repository data after normalization.
    """
    cleaned_repo = repo.copy()  # Work on a copy to avoid mutating the input directly
    for legacy_key in legacy_field_map.keys():
        if '.' in legacy_key:
            # Remove nested keys
            parent, child = legacy_key.rsplit('.', 1)
            nested_parent = get_nested_value(cleaned_repo, parent, {})
            if isinstance(nested_parent, dict) and child in nested_parent:
                nested_parent.pop(child, None)
        elif legacy_key in cleaned_repo:
            # Remove top-level keys
            cleaned_repo.pop(legacy_key, None)
    return cleaned_repo


def normalize_and_clean_repositories_with_explicit_cleanup(
    repo_data, global_defaults, type_defaults, format_defaults, repo_type, repo_format, legacy_field_map
):
    """
    Normalize repositories and ensure explicit removal of all legacy attributes.
    """
    normalized_repos = []
    for repo in repo_data:
        # Normalize the repository
        normalized = merge_defaults(
            repo, global_defaults, type_defaults, format_defaults, repo_type, repo_format, legacy_field_map
        )

        # Explicitly clean up all legacy attributes from the normalized repository
        normalized = enhanced_cleanup_legacy_attributes(
            normalized, legacy_field_map)

        # Append the cleaned, normalized repository to the list
        normalized_repos.append(normalized)

    return normalized_repos


class FilterModule:
    def filters(self):
        """
        Ansible filter module definition.
        Registers the 'normalize_repositories' filter for use in playbooks.
        """
        return {
            "normalize_repositories": normalize_and_clean_repositories_with_explicit_cleanup
        }
