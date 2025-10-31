from django.urls import path
from . import views

urlpatterns = [
    path(
        's/<int:pk>/',
        views.recipe_short_link_redirect,
        name='recipe-short-link'
    ),
]
