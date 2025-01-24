from django.urls import path
from . import views

app_name = 'guestbook'

urlpatterns = [
    path('', views.EventsView.as_view(), name='events'),
    path('<int:event_id>/message/', views.GuestbookView.as_view(), name='message'),
    path('<int:event_id>/messages/', views.MessagesView.as_view(), name='messages'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('api/events/search/', views.EventSearchView.as_view(), name='event_search'),

]