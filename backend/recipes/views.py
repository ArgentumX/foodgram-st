from django.http import Http404
from django.shortcuts import redirect
from .models import Recipe


def recipe_short_link_redirect(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404("Recipe not found")
    return redirect(f"/recipes/{pk}/")
