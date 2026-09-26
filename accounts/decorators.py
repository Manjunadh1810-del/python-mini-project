from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def candidate_required(view_func):
    """Allow access only to authenticated users with role='candidate'."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_candidate():
            messages.error(request, "This page is only accessible to candidates.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def recruiter_required(view_func):
    """Allow access only to authenticated users with role='recruiter'."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_recruiter():
            messages.error(request, "This page is only accessible to recruiters.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
