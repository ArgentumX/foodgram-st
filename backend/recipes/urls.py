from django.urls import path
from . import views

urlpatterns = [
    path(
        's/<int:pk>/',
        views.RecipeShortLinkRedirectView.as_view(),
        name='recipe-short-link'
    ),
]
