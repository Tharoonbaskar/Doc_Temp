from django.db import models


class StatusChoices(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    DRAFT = "DRAFT", "Draft"
    FOR_REVIEW = "FOR_REVIEW", "For Review"
    APPROVED = "APPROVED", "Approved"
    ARCHIVED = "ARCHIVED", "Archived"


class TemplateStatusChoices(models.TextChoices):
    """Status choices specifically for Template approval workflow"""
    DRAFT = "DRAFT", "Draft"
    FOR_REVIEW = "FOR_REVIEW", "For Review"
    APPROVED = "APPROVED", "Approved"
    ARCHIVED = "ARCHIVED", "Archived"


class LifecycleStatusChoices(models.TextChoices):
    """Lifecycle status for templates based on effective date"""
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class VersionStatusChoices(models.TextChoices):
    """Status choices for template versions"""
    DRAFT = "DRAFT", "Draft"
    FOR_REVIEW = "FOR_REVIEW", "For Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ChangeTypeChoices(models.TextChoices):
    """Types of changes in version diff"""
    ADDED = "ADDED", "Added"
    MODIFIED = "MODIFIED", "Modified"
    DELETED = "DELETED", "Deleted"


class DocumentTypeChoices(models.TextChoices):
    LETTER = "LETTER", "Letter"
    REPORT = "REPORT", "Report"
    FORM = "FORM", "Form"
    CONTRACT = "CONTRACT", "Contract"
    CERTIFICATE = "CERTIFICATE", "Certificate"


class OutputFormatChoices(models.TextChoices):
    PDF = "PDF", "PDF"
    DOCX = "DOCX", "DOCX"
    HTML = "HTML", "HTML"
    TXT = "TXT", "Text"
    JSON = "JSON", "JSON"


class ConnectorTypeChoices(models.TextChoices):
    DATABASE = "DATABASE", "Database"
    API = "API", "API"
    FILE = "FILE", "File"
    QUEUE = "QUEUE", "Queue"
    WEBHOOK = "WEBHOOK", "Webhook"


class AuthenticationTypeChoices(models.TextChoices):
    NONE = "NONE", "None"
    BASIC = "BASIC", "Basic"
    API_KEY = "API_KEY", "API Key"
    BEARER_TOKEN = "BEARER_TOKEN", "Bearer Token"
    OAUTH2 = "OAUTH2", "OAuth2"


class RuleTypeChoices(models.TextChoices):
    VALIDATION = "VALIDATION", "Validation"
    TRANSFORMATION = "TRANSFORMATION", "Transformation"
    ELIGIBILITY = "ELIGIBILITY", "Eligibility"
    CALCULATION = "CALCULATION", "Calculation"
    ROUTING = "ROUTING", "Routing"


class WorkflowActionChoices(models.TextChoices):
    SUBMIT = "SUBMIT", "Submit"
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"
    RETURN = "RETURN", "Return"
    ESCALATE = "ESCALATE", "Escalate"


class LanguageChoices(models.TextChoices):
    ENGLISH = "en", "English"
    TAMIL = "ta", "Tamil"
    HINDI = "hi", "Hindi"


class OrientationChoices(models.TextChoices):
    PORTRAIT = "PORTRAIT", "Portrait"
    LANDSCAPE = "LANDSCAPE", "Landscape"


class PageSizeChoices(models.TextChoices):
    A4 = "A4", "A4"
    A3 = "A3", "A3"
    LETTER = "LETTER", "Letter"
    LEGAL = "LEGAL", "Legal"


class TemplateTypeChoices(models.TextChoices):
    STATIC = "STATIC", "Static"
    DYNAMIC = "DYNAMIC", "Dynamic"
    COMPOSITE = "COMPOSITE", "Composite"


class DataTypeChoices(models.TextChoices):
    STRING = "STRING", "String"
    INTEGER = "INTEGER", "Integer"
    DECIMAL = "DECIMAL", "Decimal"
    BOOLEAN = "BOOLEAN", "Boolean"
    DATE = "DATE", "Date"
    DATETIME = "DATETIME", "DateTime"
    JSON = "JSON", "JSON"


class SourceTypeChoices(models.TextChoices):
    STATIC = "STATIC", "Static"
    INPUT = "INPUT", "Input"
    CONNECTOR = "CONNECTOR", "Connector"
    DERIVED = "DERIVED", "Derived"
    RULE = "RULE", "Rule"