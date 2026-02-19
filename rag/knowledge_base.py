"""Sample knowledge base - past CI failures and fixes for RAG."""

KNOWLEDGE_BASE = [
    {
        "error_type": "TerraformFormatError",
        "category": "Misconfiguration",
        "description": "Terraform files contain formatting differences detected by terraform fmt",
        "fix": "Run `terraform fmt -recursive` in the project root, then commit the changes",
        "commands": ["cd terraform/", "terraform fmt -recursive", "git add .", "git commit -m 'fix: terraform formatting'"],
        "seen_count": 14
    },
    {
        "error_type": "VaultNamespaceMismatch",
        "category": "Auth",
        "description": "Vault namespace claim does not match the configured namespace in CI variables",
        "fix": "Update CI variable VAULT_NAMESPACE to match the correct namespace path (e.g., ubs/engineering/team)",
        "commands": ["Check GitLab CI/CD Settings > Variables", "Update VAULT_NAMESPACE value", "Retry pipeline"],
        "seen_count": 8
    },
    {
        "error_type": "NexusPermissionDenied",
        "category": "Dependency",
        "description": "Maven deploy stage fails with 403 Forbidden when pushing to Nexus repository",
        "fix": "Request write permission for Nexus repository via DevCloud ServiceNow ticket. Check pom.xml has correct repository URL",
        "commands": ["Verify repository URL in pom.xml <distributionManagement>", "Open ServiceNow: Nexus Write Access Request", "Add your team to repository permissions"],
        "seen_count": 12
    },
    {
        "error_type": "DockerPullTimeout",
        "category": "Infrastructure",
        "description": "GitLab runner fails to pull Docker image from registry within timeout",
        "fix": "Retry pipeline. If persists, check runner pool status in DevCloud dashboard or use a different runner tag",
        "commands": ["Retry pipeline", "Check runner availability: Settings > CI/CD > Runners", "Contact DevCloud team if issue persists"],
        "seen_count": 6
    },
    {
        "error_type": "YAMLSyntaxError",
        "category": "Misconfiguration",
        "description": "GitLab CI YAML file has syntax errors preventing pipeline from starting",
        "fix": "Use GitLab CI Lint to validate .gitlab-ci.yml. Common issues: wrong indentation, missing colons, duplicate keys",
        "commands": ["Go to CI/CD > Editor > Validate", "Fix YAML syntax errors", "Commit and push"],
        "seen_count": 9
    },
    {
        "error_type": "RunnerJobTimeout",
        "category": "Runner",
        "description": "Job exceeds maximum execution time configured for the runner",
        "fix": "Increase timeout in .gitlab-ci.yml with 'timeout' keyword, or optimize the job to run faster",
        "commands": ["Add 'timeout: 2h' to job definition", "Or optimize build steps (caching, parallel execution)", "Commit and retry"],
        "seen_count": 5
    },
    {
        "error_type": "JUnitAssertionFailure",
        "category": "Test",
        "description": "Unit test failed with assertion error",
        "fix": "Review test logs to identify which test failed. Fix the code or update the test if requirements changed",
        "commands": ["Check logs for test class and method name", "Run test locally: mvn test -Dtest=TestClassName", "Fix code or test"],
        "seen_count": 22
    },
    {
        "error_type": "MavenDependencyNotFound",
        "category": "Dependency",
        "description": "Maven cannot resolve dependency from configured repositories",
        "fix": "Check if artifact exists in Nexus. Verify repository URLs in pom.xml and settings.xml. Clear local cache if needed",
        "commands": ["Check artifact in Nexus search", "Verify <repositories> in pom.xml", "Run: mvn dependency:purge-local-repository"],
        "seen_count": 7
    },
    {
        "error_type": "VaultTokenExpired",
        "category": "Auth",
        "description": "Vault authentication token has expired during CI job execution",
        "fix": "Regenerate Vault token in GitLab CI variables. Ensure token TTL is sufficient for job duration",
        "commands": ["Go to GitLab Settings > CI/CD > Variables", "Update VAULT_TOKEN with new token", "Ensure token TTL > job duration"],
        "seen_count": 4
    },
    {
        "error_type": "OutOfMemory",
        "category": "Infrastructure",
        "description": "Job killed due to out of memory (OOM) on GitLab runner",
        "fix": "Request runner with more memory via runner tags, or optimize build to use less memory (e.g., lower Gradle max heap)",
        "commands": ["Use runner tag: 'large-memory'", "Or add to gradle.properties: org.gradle.jvmargs=-Xmx2g", "Retry pipeline"],
        "seen_count": 10
    }
]
