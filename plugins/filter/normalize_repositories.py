def normalize_repositories(repo_data, repo_type, repo_format, schemas):
    """
    Normalize repository configurations into API-compatible format.
    """
    if repo_type not in schemas or repo_format not in schemas[repo_type]:
        raise ValueError(f"No schema defined for type '{
                         repo_type}' and format '{repo_format}'")

    schema = schemas[repo_type][repo_format]
    normalized_repos = []

    for repo in repo_data:
        normalized = {}

        # Map fields from source to target based on the schema
        for src_field, target_field in schema.get("field_map", {}).items():
            if '.' in src_field:  # Handle nested keys
                keys = src_field.split('.')
                value = repo
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                if value is not None:
                    normalized[target_field] = value
            elif src_field in repo:
                normalized[target_field] = repo[src_field]

        # Add defaults for missing attributes
        for key, default_value in schema.get("default_values", {}).items():
            normalized.setdefault(key, default_value)

        # Include unmapped fields that are not excluded
        exclude_fields = schema.get("exclude_fields", [])
        for key, value in repo.items():
            if key not in schema.get("field_map", {}) and key not in exclude_fields:
                normalized[key] = value

        normalized_repos.append(normalized)

    return normalized_repos


class FilterModule:
    def filters(self):
        return {
            "normalize_repositories": normalize_repositories
        }
