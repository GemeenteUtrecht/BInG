"""
Middleware to transform data from/to camunda.
"""
from django_camunda.interface import Variable


class ZaakVariable(Variable):
    object_type_name = "com.gemeenteutrecht.processplatform.domain.impl.ZaakImpl"


class DocumentListVariable(Variable):
    object_type_name = (
        "com.gemeenteutrecht.processplatform.domain.document.impl.DocumentImpl"
    )
