from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/',views.admin_login, name='admin_login'),
    path('admin-dashboard/',views.admin_dashboard, name='admin_dashboard'),
    path('sales-report/',views.sales_report,name='sales-report'),
    path('sales-report/filter/',views.order_date_filter, name='order_date_filter'),
    path('user-list',views.user_list,name='user_list'),
    path('users-create/',views.user_create, name='user_create'),
    path('users-block/<int:user_id>/',views.user_block, name='user_block'),
    path('users-unblock/<int:user_id>/',views.user_unblock, name='user_unblock'),
    path('users-delete/<int:user_id>/',views.user_delete, name='user_delete'),
    path('users-undelete/<int:user_id>/',views.user_undelete, name='user_undelete'),
    path('best-selling-products/',views.best_selling_products, name='best-products'),
    path('best-selling-categories/',views.best_selling_categories, name='best-categories'),
    path('best-selling-brands/',views.best_selling_brands, name='best-brands'),
    path('admin-logout/',views.admin_logout,name='admin-logout'),
]
