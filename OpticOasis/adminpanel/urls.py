from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/',views.admin_login, name='admin_login'),
    path('admin-dashboard/',views.admin_dashboard, name='admin_dashboard'),
    path('sales-report/',views.sales_report,name='sales-report'),
    path('user-list',views.user_list,name='user_list'),
    path('users-create/',views.user_create, name='user_create'),
    path('users-block/<int:user_id>/',views.user_block, name='user_block'),
    path('users-unblock/<int:user_id>/',views.user_unblock, name='user_unblock'),
    path('users-delete/<int:user_id>/',views.user_delete, name='user_delete'),
    path('users-undelete/<int:user_id>/',views.user_undelete, name='user_undelete'),
    path('admin-logout/',views.admin_logout,name='admin-logout'),
]
