# Competency Assessment Template

## Instructions
Complete this assessment before starting any new feature. Copy this template and fill in the details for each feature you're assigned.

---

# Competency Assessment — [Agent-ID]

## Feature: [Feature ID] [Feature Name]

### Technical Area Assessment
- **Primary Technologies**: [List main technologies, frameworks, languages involved]
- **Relevant Experience**: [Describe your experience with similar features/technologies]
- **Strengths**: [Your key strengths that apply to this feature]
- **Knowledge Gaps**: [Areas where you may need additional research/learning]
- **Confidence Level**: [High/Medium/Low] - [Brief explanation]

### Risk Assessment
- **Technical Risks**: [Potential technical challenges and how you'll address them]
- **Timeline Risks**: [Schedule concerns and mitigation strategies]
- **Dependency Risks**: [External dependencies that could impact delivery]
- **Quality Risks**: [Testing, performance, security concerns]

### Execution Plan (High Level)
1. [First major step/milestone]
2. [Second major step/milestone]
3. [Third major step/milestone]
4. [Final validation and completion steps]

### Success Criteria
- [ ] [Specific, measurable outcome 1]
- [ ] [Specific, measurable outcome 2]
- [ ] [Specific, measurable outcome 3]
- [ ] All tests passing and documentation updated

### Resources Needed
- **Documentation**: [Links to relevant docs, APIs, specifications]
- **Tools**: [Development tools, testing frameworks, deployment tools]
- **Support**: [Team members or external resources you may need help from]

---

# Example: Competency Assessment — augment-02

## Feature: 1.4.MY Incremental mypy hardening for backend/ai/

### Technical Area Assessment
- **Primary Technologies**: Python typing, mypy configuration, test-driven development
- **Relevant Experience**: Implemented strict typing across AI provider/router stacks; authored DTOs and Protocols for model routing and provider abstractions.
- **Strengths**: SOLID design, clean architecture, incremental refactors with high test coverage.
- **Knowledge Gaps**: None significant for this feature scope
- **Confidence Level**: High - Have extensive experience with Python typing and mypy configuration

### Risk Assessment
- **Technical Risks**: Potential hidden dynamic behaviors in provider modules; will mitigate with targeted tests and incremental flags.
- **Timeline Risks**: Low risk - incremental approach allows for steady progress
- **Dependency Risks**: None - self-contained typing improvements
- **Quality Risks**: Could break existing functionality; mitigated by comprehensive test suite

### Execution Plan (High Level)
1. Start with base provider and model_router (already partially strict in mypy.ini) and ensure clean types.
2. Add DTOs/Protocols to clarify request/response shapes.
3. Expand to config_manager and provider modules; remove ignore_errors entries gradually.
4. Keep tests green at each step; update planning docs per protocol.

### Success Criteria
- [x] mypy strict flags enabled for 3+ backend/ai modules with 0 errors in those modules
- [ ] make test passes locally; CI green
- [ ] Implementation plan and sync updated with results and test table entries
- [ ] All tests passing and documentation updated

### Resources Needed
- **Documentation**: mypy documentation, existing codebase patterns
- **Tools**: mypy, pytest, IDE with type checking
- **Support**: None required for this feature

