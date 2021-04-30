from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.index, name="ShopHome"),
    path("about/", views.about, name="AboutUs"),
    path("contact/", views.contact, name="ContactUs"),
    path("profile/", views.profile, name="profile"),
    path("tracker/", views.tracker, name="TrackingStatus"),
    path("search/", views.search, name="Search"),
    path("products/<int:myid>", views.productView, name="ProductView"),
    path("checkout/", views.checkout, name="Checkout"),
    path("handlerequest/", views.handlerequest, name="HandleRequest"),


    path('signup/', views.signup, name="signup"),  
    path('activate/<uidb64>/<token>/',views.activate, name='activate'),
    

    path("login/", auth_views.LoginView.as_view(template_name='shop/login.html', redirect_authenticated_user=True),name='login'),
    path("logout/", auth_views.LogoutView.as_view(next_page='/'),name='logout'),
    path("password_reset/", auth_views.PasswordResetView.as_view(template_name='shop/password_reset.html'),name='password_reset'),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'),name='password_reset_done'),
    path("password_reset_confirm/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'),name='password_reset_confirm'),
    path("password_reset_complete/", auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'),name='password_reset_complete'),
    
]

