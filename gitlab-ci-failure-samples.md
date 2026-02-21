# GitLab CI Failure Samples for CI·RCA System

Sample `.gitlab-ci.yml` files that trigger each of the 6 failure categories the RCA system knows about.

---

## 1. Misconfiguration — Terraform Format Error

```yaml
# .gitlab-ci.yml
stages:
  - validate

terraform-fmt-check:
  stage: validate
  image: hashicorp/terraform:1.5.0
  script:
    - cd terraform/
    - terraform fmt -check -recursive
  # FAILS if any .tf file is not properly formatted
  # RCA detects: TerraformFormatError → Misconfiguration
```

**Trigger failure — put this in `terraform/main.tf`:**

```hcl
resource "aws_instance" "example" {
ami           = "ami-0c55b159cbfafe1f0"
instance_type =    "t2.micro"
  tags = {
    Name = "example"
  }
}
```

**Log output:**

```
Error: Files in the working directory are not formatted.
  terraform/main.tf
  Run `terraform fmt` to fix formatting issues.
```

---

## 2. Auth — Vault Namespace Mismatch

```yaml
# .gitlab-ci.yml
stages:
  - secrets

fetch-vault-secrets:
  stage: secrets
  image: vault:1.13.0
  variables:
    VAULT_ADDR: "https://vault.company.com"
    VAULT_NAMESPACE: "ubs/wrong-team"
    VAULT_TOKEN: $CI_VAULT_TOKEN
  script:
    - vault login -method=token token=$VAULT_TOKEN
    - vault kv get -namespace=$VAULT_NAMESPACE secret/myapp/db-password
    - vault kv get -namespace=$VAULT_NAMESPACE secret/myapp/api-key
  # FAILS: namespace claim does not match configured namespace
  # RCA detects: VaultNamespaceMismatch → Auth
```

**Log output:**

```
Error making API request.
URL: PUT https://vault.company.com/v1/auth/token/lookup-self
Code: 403. Errors:
* 1 error occurred: namespace not authorized: ubs/wrong-team
```

---

## 3. Auth — Vault Token Expired

```yaml
# .gitlab-ci.yml
stages:
  - deploy

deploy-with-vault:
  stage: deploy
  image: alpine:3.18
  variables:
    VAULT_ADDR: "https://vault.company.com"
    VAULT_TOKEN: $VAULT_TOKEN
  script:
    - apk add --no-cache curl jq
    - |
      SECRET=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
        $VAULT_ADDR/v1/secret/data/myapp/credentials | jq -r '.data.data.password')
    - echo "Deploying with credentials..."
    - ./deploy.sh --password=$SECRET
  # FAILS: token TTL has expired
  # RCA detects: VaultTokenExpired → Auth
```

**Log output:**

```
Error making API request.
* permission denied
* Code: 403
* Token is expired
```

---

## 4. Dependency — Nexus Permission Denied

```yaml
# .gitlab-ci.yml
stages:
  - build
  - publish

build:
  stage: build
  image: maven:3.9.4-eclipse-temurin-17
  script:
    - mvn clean package -DskipTests

publish-to-nexus:
  stage: publish
  image: maven:3.9.4-eclipse-temurin-17
  script:
    - mvn deploy -s settings.xml
  # FAILS: team does not have write permission to Nexus repo
  # RCA detects: NexusPermissionDenied → Dependency
```

**`settings.xml`:**

```xml
<settings>
  <servers>
    <server>
      <id>nexus-releases</id>
      <username>${NEXUS_USER}</username>
      <password>${NEXUS_PASSWORD}</password>
    </server>
  </servers>
</settings>
```

**`pom.xml` distributionManagement:**

```xml
<distributionManagement>
  <repository>
    <id>nexus-releases</id>
    <url>https://nexus.company.com/repository/maven-releases/</url>
  </repository>
</distributionManagement>
```

**Log output:**

```
[ERROR] Failed to execute goal org.apache.maven.plugins:maven-deploy-plugin
[ERROR] Failed to deploy artifacts:
Could not transfer artifact com.company:myapp:jar:1.0.0
Return code is: 403, ReasonPhrase: Forbidden.
```

---

## 5. Dependency — Maven Dependency Not Found

```yaml
# .gitlab-ci.yml
stages:
  - build

build-java:
  stage: build
  image: maven:3.9.4-eclipse-temurin-17
  variables:
    MAVEN_OPTS: "-Dmaven.repo.local=.m2/repository"
  cache:
    paths:
      - .m2/repository/
  script:
    - mvn clean package
  # FAILS: artifact version does not exist in Nexus
  # RCA detects: MavenDependencyNotFound → Dependency
```

**Bad dependency in `pom.xml`:**

```xml
<dependency>
  <groupId>com.company.internal</groupId>
  <artifactId>shared-utils</artifactId>
  <version>9.9.9-SNAPSHOT</version>
</dependency>
```

**Log output:**

```
[ERROR] Failed to execute goal on project myapp
[ERROR] Could not resolve dependencies for project com.company:myapp:jar:1.0.0
[ERROR] Could not find artifact com.company.internal:shared-utils:jar:9.9.9-SNAPSHOT
  in nexus (https://nexus.company.com/repository/maven-public/)
```

---

## 6. Infrastructure — Docker Pull Timeout

```yaml
# .gitlab-ci.yml
stages:
  - build

docker-build:
  stage: build
  image: docker:24.0
  services:
    - docker:24.0-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_REGISTRY: "registry.company.com"
  script:
    - docker login -u $REGISTRY_USER -p $REGISTRY_PASSWORD $DOCKER_REGISTRY
    - docker pull $DOCKER_REGISTRY/base-images/java17:latest
    - docker build -t $DOCKER_REGISTRY/myapp:$CI_COMMIT_SHA .
    - docker push $DOCKER_REGISTRY/myapp:$CI_COMMIT_SHA
  timeout: 10m
  # FAILS: registry unreachable or runner network issue
  # RCA detects: DockerPullTimeout → Infrastructure
```

**Log output:**

```
Pulling from registry.company.com/base-images/java17
error pulling image configuration:
  Get https://registry.company.com/v2/...: net/http: request canceled
  while waiting for connection (Client.Timeout exceeded while awaiting headers)
```

---

## 7. Infrastructure — Out of Memory (OOM)

```yaml
# .gitlab-ci.yml
stages:
  - build

heavy-build:
  stage: build
  image: gradle:8.3-jdk17
  variables:
    GRADLE_OPTS: "-Xmx8g -XX:MaxMetaspaceSize=512m"
  script:
    - gradle clean build --no-daemon --parallel
  # FAILS: runner OOM killed
  # RCA detects: OutOfMemory → Infrastructure
```

**Log output:**

```
OpenJDK 64-Bit Server VM warning: INFO: os::commit_memory(0x...) failed
  in GrowHeap for request 1073741824 bytes
# There is insufficient memory for the Java Runtime Environment to continue.
# Native memory allocation (mmap) failed to map 1073741824 bytes
Killed
ERROR: Job failed: exit code 137
```

---

## 8. Test — JUnit Assertion Failure

```yaml
# .gitlab-ci.yml
stages:
  - test

unit-tests:
  stage: test
  image: maven:3.9.4-eclipse-temurin-17
  script:
    - mvn test
  artifacts:
    when: always
    reports:
      junit:
        - target/surefire-reports/TEST-*.xml
    paths:
      - target/surefire-reports/
    expire_in: 7 days
  # FAILS: unit test assertion error
  # RCA detects: JUnitAssertionFailure → Test
```

**Sample failing test:**

```java
// src/test/java/com/company/OrderServiceTest.java
@Test
public void testCalculateTotal() {
    OrderService service = new OrderService();
    double result = service.calculateTotal(100.0, 0.2);
    assertEquals(80.0, result, 0.01);  // fails if method returns 120.0
}
```

**Log output:**

```
[ERROR] Tests run: 5, Failures: 1, Errors: 0, Skipped: 0
[ERROR] testCalculateTotal(com.company.OrderServiceTest)
  Time elapsed: 0.123 s  <<< FAILURE!
  org.opentest4j.AssertionFailedError:
  expected: <80.0> but was: <120.0>
```

---

## 9. Runner — Job Timeout

```yaml
# .gitlab-ci.yml
stages:
  - e2e

e2e-tests:
  stage: e2e
  image: cypress/included:13.0.0
  timeout: 5m
  script:
    - npm ci
    - npx cypress run --browser chrome --spec "cypress/e2e/**/*.cy.js"
  artifacts:
    when: always
    paths:
      - cypress/screenshots/
      - cypress/videos/
  # FAILS: runner timeout exceeded
  # RCA detects: RunnerJobTimeout → Runner
```

**Log output:**

```
ERROR: Job failed: execution took longer than 5m0s seconds
```

---

## 10. Misconfiguration — YAML Syntax Error

```yaml
# .gitlab-ci.yml  ← this file itself is broken
stages:
  - build
  - test

build:
  stage: build
  script:
    - mvn clean package

test:
  stage: test
  script
    - mvn test
  only:
    - main
    - develop
```

**What GitLab shows:**

```
yaml invalid: jobs:test:script config should be a string or an array of strings
```

---

## Quick Reference Table

| # | Job Name | Failure | Category | Known Pattern |
|---|----------|---------|----------|---------------|
| 1 | terraform-fmt-check | Bad `.tf` formatting | Misconfiguration | TerraformFormatError |
| 2 | fetch-vault-secrets | Wrong namespace | Auth | VaultNamespaceMismatch |
| 3 | deploy-with-vault | Token expired | Auth | VaultTokenExpired |
| 4 | publish-to-nexus | 403 Forbidden | Dependency | NexusPermissionDenied |
| 5 | build-java | Artifact not in Nexus | Dependency | MavenDependencyNotFound |
| 6 | docker-build | Registry timeout | Infrastructure | DockerPullTimeout |
| 7 | heavy-build | OOM / exit code 137 | Infrastructure | OutOfMemory |
| 8 | unit-tests | AssertionFailedError | Test | JUnitAssertionFailure |
| 9 | e2e-tests | Execution timeout | Runner | RunnerJobTimeout |
| 10 | *(pipeline start)* | YAML parse error | Misconfiguration | YAMLSyntaxError |

---

## Testing Without GitLab

Copy any log output block above into the **Manual Analyze** form in the frontend.
Fill in the fields like this:

| Field | Example Value |
|-------|--------------|
| Pipeline ID | `123456` |
| Project Name | `my-service` |
| Job Name | match the job name from the sample |
| Stage | `build` / `test` / `deploy` etc. |
| Job Status | `failed` |
| Raw Log | paste the log output block |
