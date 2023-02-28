from django.urls import path
from django.views.generic import TemplateView

app_name = 'mfApp'

urlpatterns = [
  path('', TemplateView.as_view(template_name="index.html")),
  # path('cards', card_list, name="cards"),
]