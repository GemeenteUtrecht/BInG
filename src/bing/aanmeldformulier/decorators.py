from functools import wraps

from django.shortcuts import redirect

from bing.projects.models import Project

from .constants import PROJECT_SESSION_KEY


def project_required(func):
    @wraps(func)
    def _wrapped_view(request, *args, **kwargs):
        project_id = request.session.get(PROJECT_SESSION_KEY)
        if not Project.objects.filter(id=project_id).exists():
            return redirect("aanmeldformulier:info")
        return func(request, *args, **kwargs)

    return _wrapped_view
