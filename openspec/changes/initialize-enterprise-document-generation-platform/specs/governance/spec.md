# Capability: Governance

## ADDED Requirements

### Requirement: Enforce Maker-Checker Workflow

The platform SHALL enforce a Maker-Checker approval workflow for all template changes.

#### Scenario: Submit template for approval

**Given**
a template is in Draft status

**When**
the Maker submits the template

**Then**
the template SHALL move to Submitted status

**And**
be assigned to a Checker for review.

#### Scenario: Prevent self approval

**Given**
the Maker created the template

**When**
the same user attempts approval

**Then**
the platform SHALL reject the approval request.

---

### Requirement: Review Template Changes

The platform SHALL allow Checkers to review pending template versions.

#### Scenario: Review template

**Given**
a Submitted template

**When**
the Checker opens the review

**Then**
the platform SHALL display the pending version

**And**
the previous published version for comparison.

---

### Requirement: Compare Template Versions

The platform SHALL compare template versions before approval.

#### Scenario: Compare versions

**Given**
two template versions

**When**
comparison is requested

**Then**
the platform SHALL identify

- Content Changes
- Style Changes
- Variable Changes
- Rule Changes
- Component Changes.

---

### Requirement: Approve Template

The platform SHALL publish approved templates.

#### Scenario: Approve template

**Given**
a Submitted template

**When**
the Checker approves

**Then**
the template SHALL become Published

**And**
the previous version SHALL become Archived.

---

### Requirement: Reject Template

The platform SHALL reject invalid templates.

#### Scenario: Reject template

**Given**
a Submitted template

**When**
the Checker rejects the template

**Then**
the template SHALL return to Draft

**And**
review comments SHALL be stored.

---

### Requirement: Request Rework

The platform SHALL support rework requests.

#### Scenario: Needs rework

**Given**
a Submitted template

**When**
the Checker requests rework

**Then**
the template SHALL return to the Maker

**And**
all review comments SHALL be preserved.

---

### Requirement: Maintain Workflow History

The platform SHALL maintain workflow history.

#### Scenario: Workflow action

**Given**
a workflow action

**When**
the action completes

**Then**
the platform SHALL record

- User
- Action
- Timestamp
- Remarks
- Status.

---

### Requirement: Create Immutable Snapshots

The platform SHALL create immutable snapshots for every generated document.

#### Scenario: Generate snapshot

**Given**
a document is generated

**When**
generation completes

**Then**
an immutable snapshot SHALL be stored.

---

### Requirement: Preserve Historical Documents

The platform SHALL preserve historical documents independently of template versions.

#### Scenario: Template updated

**Given**
a new template version is published

**When**
previous documents are viewed

**Then**
the original generated documents SHALL remain unchanged.

---

### Requirement: Maintain Audit Trail

The platform SHALL record all business activities.

#### Scenario: Audit event

**Given**
a platform operation

**When**
the operation completes

**Then**
an audit record SHALL be created.

---

### Requirement: Capture Audit Information

The platform SHALL record audit metadata.

#### Scenario: Store audit

**Given**
an audit event

**When**
the event is stored

**Then**
the platform SHALL record

- Event Type
- User
- Timestamp
- Entity
- Entity Identifier
- Action
- Status
- Before Value
- After Value.

---

### Requirement: Search Audit Records

The platform SHALL support audit search.

#### Scenario: Search audit

**Given**
audit records exist

**When**
filters are applied

**Then**
matching audit records SHALL be returned.

---

### Requirement: Support Compliance Reporting

The platform SHALL generate compliance reports.

#### Scenario: Compliance report

**Given**
an administrator

**When**
a compliance report is requested

**Then**
audit information SHALL be available.

---

### Requirement: Support Rollback

The platform SHALL support rollback of published templates.

#### Scenario: Rollback template

**Given**
multiple published versions

**When**
rollback is initiated

**Then**
the selected version SHALL become active

**And**
the rollback SHALL be audited.

---

### Requirement: Retain Governance Records

The platform SHALL retain governance records according to enterprise retention policies.

#### Scenario: Retain records

**Given**
audit and snapshot records

**When**
retention policies are evaluated

**Then**
records SHALL remain available until the configured retention period expires.

---

### Requirement: Expose Governance APIs

The platform SHALL expose REST APIs for governance services.

#### Scenario: Retrieve workflow history

**Given**
a valid request

**When**
the Workflow History API is invoked

**Then**
workflow history SHALL be returned.

#### Scenario: Retrieve audit history

**Given**
a valid request

**When**
the Audit API is invoked

**Then**
audit records SHALL be returned.

#### Scenario: Retrieve snapshot

**Given**
a generated document

**When**
the Snapshot API is invoked

**Then**
the immutable document SHALL be returned.