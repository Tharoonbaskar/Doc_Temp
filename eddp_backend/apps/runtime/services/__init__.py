from __future__ import annotations

from importlib import import_module

_LAZY_EXPORTS = {
    "RuntimeAuthorizationService": ".authorization",
    "ConnectorExecutionService": ".connector_engine",
    "DOCXGeneratorService": ".docx_generator",
    "FileStorageService": ".file_storage",
    "GenerationService": ".generation_service",
    "HTMLBuilderService": ".html_builder",
    "PDFGeneratorService": ".pdf_generator",
    "RuleExecutionService": ".rule_engine",
    "RuntimeService": ".runtime_service",
    "TemplateRenderingService": ".template_renderer",
    "VariableResolverService": ".variable_resolver",
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str):
    """Lazy-load runtime services to avoid importing unused dependencies at package import time."""
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
