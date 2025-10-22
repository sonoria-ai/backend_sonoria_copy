from django.urls import path
from . import views

urlpatterns = [
    path('incoming-call/', views.incoming_call, name='assistant_incoming_call'),
    path('session-token/', views.get_session_token, name='assistant_session_token'),
    path('send-sms/', views.send_sms, name='assistant_send_sms'),
    path('get-prompt/', views.get_prompt, name='assistant_get_prompt'),
    path('transfer-call/', views.transfer_call, name='assistant_transfer_call'),
    path('status/', views.get_assistant_status, name='assistant_status'),
    path('create-assistant/', views.create_assistant_with_number, name='create_assistant_with_number'),
]
