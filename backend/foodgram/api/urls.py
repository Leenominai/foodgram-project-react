from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (TagViewSet, IngredientViewSet, RecipeViewSet, UserViewSet)

app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'users', UserViewSet, 'users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
