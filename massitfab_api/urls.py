from django.contrib import admin
from django.urls import path, re_path
from .views import *

app_name = 'mfApi'

urlpatterns = [
    re_path(r'^u/get/(?i)(?P<username>[a-z]+)/$', get_profile, name='get_profile'),
    path('u/update/', update_profile, name='update_profile'),
    
    path('content/create/', create_product, name='upload_content'),
    path('content/update/<int:id>/', update_product, name='update_content'),
    path('content/delete/<int:id>/', delete_product, name='delete_content'),
    path('content/get/<int:id>/', get_product_details, name='get_content_details'),
    path('content/get/', get_products, name='get_contents'),
    path('content/search/', search_products, name='search_products'),

    path('u/toggle/wishlist/', add_to_wishlist, name='toggle_wishlist'),
    path('u/wishlist/get/', get_wishlist, name='get_wishlist'),

    path('review/create/<int:product_id>/', create_review, name='create_review'),
    path('review/get/<int:product_id>/', get_reviews, name="get_reviews"),
    path('review/delete/<int:review_id>/', delete_review, name='delete_review'),
]
