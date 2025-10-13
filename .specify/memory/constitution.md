<!--
SYNC IMPACT REPORT
===================
Version Change: [TEMPLATE] → 1.0.0
Modified Principles: Initial ratification - all principles newly defined
Added Sections:
  - Core Principles (5 principles)
    * I. Data Reliability & Accuracy
    * II. Real-Time Observability & Visualization
    * III. Test-First Development (NON-NEGOTIABLE, >80% coverage)
    * IV. Security & Data Integrity
    * V. Performance & Efficiency
  - Technology Standards (Python-focused)
  - Development Workflow
  - Governance

Templates Status:
  ✅ plan-template.md - compatible (Constitution Check section aligns)
  ✅ spec-template.md - compatible (requirements structure supports principles)
  ✅ tasks-template.md - compatible (test-first approach with coverage requirements)

Follow-up TODOs: None - all placeholders resolved

Rationale: Initial constitution for DDMS (Device Data Monitoring System) web
application. Establishes Python-first development with 80%+ test coverage, efficient
data collection/visualization, and safety-critical industrial monitoring principles
for factory/coalmine environments.
-->

# DDMS Constitution

## Core Principles

### I. Data Reliability & Accuracy

All device data MUST be accurate, timestamped, and traceable to source. Data loss is
unacceptable in industrial monitoring contexts. System MUST:
- Validate all incoming device data at ingestion boundaries
- Reject malformed data with explicit error logging
- Store raw data immutably with full audit trail
- Maintain data provenance (device ID, timestamp, collection method)
- Provide data quality metrics (completeness, timeliness, validity)

**Rationale**: Industrial environments depend on accurate data for safety decisions and
operational efficiency. Incorrect or missing data can lead to equipment damage, safety
incidents, or production losses.

### II. Real-Time Observability & Visualization

System MUST provide real-time visibility into device status through efficient
visualization. Every component (data collectors, processors, storage, alerts) MUST
expose:
- Health status and uptime metrics
- Processing latency (p50, p95, p99)
- Error rates and failure modes
- Queue depths and backpressure indicators
- Resource utilization (CPU, memory, network)

**Visualization Requirements**:
- Dashboards MUST render efficiently with minimal latency
- Data visualization MUST support real-time updates without page refresh
- Charts and graphs MUST handle high-frequency data streams
- UI MUST be responsive and accessible for operational use

All logs MUST be structured (JSON) and machine-parseable. Human-readable summaries
MUST be available for operators. Self-monitoring is mandatory.

**Rationale**: Factory and coalmine environments require immediate visibility into
device status and trends. Efficient visualization enables rapid decision-making and
incident response.

### III. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development is mandatory for all features. Minimum 80% unit test coverage
required. No exceptions.

**Process**:
1. Write tests that define expected behavior
2. Verify tests FAIL (red phase)
3. Implement minimum code to pass tests (green phase)
4. Refactor while keeping tests passing
5. No code review or merge without passing tests

**Coverage Requirements**:
- Unit test coverage MUST be >= 80% for all Python modules
- Integration tests: Device data pipelines, API endpoints, database operations
- Contract tests: All external integrations and API contracts
- End-to-end tests: Critical user journeys and alert workflows

**Testing Tools** (Python ecosystem):
- pytest for unit and integration testing
- pytest-cov for coverage measurement
- pytest-mock for mocking external dependencies
- Coverage reports MUST be generated on every CI run

**Rationale**: Industrial monitoring systems are safety-critical. Untested code risks
silent failures, data corruption, or missed alerts that could endanger workers or
equipment. The 80% threshold ensures comprehensive validation.

### IV. Security & Data Integrity

Industrial device data MUST be protected from unauthorized access and tampering.

**Security Requirements**:
- All API endpoints MUST require authentication and authorization
- Device connections MUST use encrypted protocols (TLS 1.3+)
- Sensitive data (credentials, personal info) MUST be encrypted at rest
- Role-based access control (RBAC) for all data access
- Audit logging for all administrative actions and data modifications

**Python Security Standards**:
- Use pip-audit for dependency vulnerability scanning
- Pin all dependencies with exact versions in requirements.txt
- Use virtual environments (venv) for isolation
- Follow OWASP Python security best practices
- Regular security updates for all dependencies

**Data Integrity**:
- Write operations MUST be transactional with rollback capability
- Data validation MUST occur before persistence
- Schema changes MUST include backward-compatible migrations
- Retention policies MUST comply with regulatory requirements
- Backups MUST be automated, encrypted, and regularly tested

**Rationale**: Factory and coalmine data may be subject to regulatory compliance.
Security breaches or data tampering could compromise safety systems or lead to legal
liability.

### V. Performance & Efficiency

System MUST handle high-volume device data streams with predictable performance and
efficient resource utilization.

**Performance Targets**:
- Data ingestion latency: p95 < 500ms, p99 < 2s
- Dashboard query response: p95 < 1s, p99 < 3s
- Visualization rendering: < 100ms for standard charts
- Alert delivery latency: p95 < 5s from threshold breach
- System handles 10,000+ devices with 1-minute collection intervals

**Python Performance Standards**:
- Use async/await for I/O-bound operations (asyncio, aiohttp)
- Leverage pandas/numpy for efficient data processing
- Use connection pooling for database operations
- Implement caching strategies (Redis, in-memory) for frequent queries
- Profile performance-critical code paths with cProfile or py-spy

**Resource Constraints**:
- Data collector agents: < 5% CPU, < 200MB memory per agent
- Backend services: Graceful degradation under load
- Database: Query optimization required for time-series data
- Storage: Efficient compression for historical data (target 10:1 ratio)

**Rationale**: Industrial environments may have thousands of sensors. System must scale
efficiently without performance degradation that could delay critical alerts.

## Technology Standards

### Python-First Development

Python is the primary programming language for DDMS. All backend services, data
processing, and API development MUST use Python unless a compelling technical reason
exists for an alternative.

**Python Version**: Python 3.11+ (leverage performance improvements and modern syntax)

**Core Technology Stack**:
- **Web Framework**: FastAPI or Flask for REST APIs
- **Data Processing**: pandas, numpy for data manipulation
- **Visualization Backend**: matplotlib, plotly for chart generation
- **Database**: SQLAlchemy ORM for database abstraction
- **Async Operations**: asyncio, aiohttp for concurrent I/O
- **Task Queue**: Celery or RQ for background jobs
- **Testing**: pytest ecosystem

**Frontend** (for web visualization):
- Modern JavaScript framework (React, Vue, or similar)
- Integration with Python backend via REST APIs
- Real-time updates via WebSocket or Server-Sent Events

**Code Quality Tools**:
- **Linting**: pylint, flake8 for code quality
- **Formatting**: black for consistent code style
- **Type Checking**: mypy for static type analysis
- **Documentation**: Sphinx for API documentation

**Dependency Management**:
- requirements.txt for production dependencies
- requirements-dev.txt for development dependencies
- Use pip-tools for reproducible builds

**Justification**: Python provides excellent libraries for data processing, scientific
computing, and rapid web development. The ecosystem is mature, well-documented, and
widely adopted in data-intensive applications.

## Development Workflow

### Code Quality Standards

- All Python code MUST pass linting (pylint/flake8) and formatting (black)
- Functions MUST have type hints for parameters and return values
- Complex logic MUST include docstrings explaining safety considerations
- Error handling MUST be explicit (no bare except clauses)
- All modules MUST maintain >= 80% unit test coverage

### Review & Deployment

- All changes MUST pass automated test suite before review
- Code reviews MUST verify constitution compliance
- Test coverage MUST not decrease (ratcheting upward encouraged)
- Breaking changes MUST include migration guide and backward compatibility plan
- Feature flags MUST be used for risky changes in production
- Deployments MUST be reversible with documented rollback procedures
- Production deployments require two-person approval for safety-critical components

### Documentation Requirements

- All API endpoints MUST have OpenAPI/Swagger documentation
- Device integration guides MUST include Python examples and troubleshooting
- Alert configuration MUST document threshold recommendations
- Architecture decisions MUST be recorded in ADR (Architecture Decision Records)
- All public functions/classes MUST have docstrings (Google or NumPy style)
- Runbooks MUST exist for common operational scenarios

### Testing Standards

- Unit tests MUST be fast (< 1s per test file) and independent
- Integration tests MUST use test databases/containers (Docker)
- Mock external dependencies (devices, third-party APIs) in unit tests
- CI pipeline MUST run all tests and generate coverage reports
- Performance benchmarks for critical paths (profiling results documented)

## Governance

This constitution supersedes all other development practices. All features, code reviews,
architectural decisions, and operational procedures MUST comply with these principles.

### Amendment Process

1. Proposed amendments MUST include written justification and impact analysis
2. Breaking changes MUST include migration plan for existing deployments
3. All amendments MUST be reviewed against dependent templates and documentation
4. Version number MUST follow semantic versioning:
   - **MAJOR**: Backward-incompatible governance changes or principle removals
   - **MINOR**: New principles added or material expansions to existing principles
   - **PATCH**: Clarifications, wording improvements, typo fixes
5. Amendments require approval from technical lead and product owner

### Compliance Verification

- All pull requests MUST include constitution compliance checklist
- Test coverage MUST be verified automatically in CI (>= 80% enforced)
- Complexity that violates simplicity principles MUST be justified in implementation plans
- Constitution compliance reviews occur:
  - At feature planning (spec/plan phase)
  - During code review
  - Quarterly architecture reviews
  - After any safety incidents or compliance audits

### Violation Handling

When a principle violation is necessary (rare):
1. Document in Complexity Tracking section of implementation plan
2. Explain why violation is required for industrial safety or operational needs
3. Document simpler alternatives considered and why they were rejected
4. Set review date (max 6 months) to revisit the decision
5. Obtain technical lead approval before implementation

### Constitution Evolution

This constitution is a living document. As DDMS evolves and industrial requirements
change, principles may be amended. However, the core commitment to safety, reliability,
data integrity, and test quality (>80% coverage) MUST remain unchanged.

**Version**: 1.0.0 | **Ratified**: 2025-10-10 | **Last Amended**: 2025-10-10
