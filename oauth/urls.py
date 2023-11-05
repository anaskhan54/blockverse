from django.urls import path
from . import views
urlpatterns = [
    path('',views.LandingPageView.as_view(),name='landing_page'),
    path('googleOauth/',views.GoogleOauthView.as_view(),name='oauth'),
    path('oauth/',views.CallBackHandlerView.as_view(),name='callback'),
    path('register/',views.RegisterView.as_view(),name='register_team'),
    path('dashboard/',views.DashBoardView.as_view(),name='dashboard'),
    path('payment/',views.PaymentView.as_view(),name='paymanet'),
    path('payment/callback/',views.PaymentCallBackView.as_view(),name='callback_payment'),
]