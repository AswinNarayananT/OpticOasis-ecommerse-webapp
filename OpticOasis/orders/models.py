from django.db import models
from django.db import models
from accounts.models import *
from product.models import *
from userpanel.models import *

# Create your models here.


class OrderMain(models.Model):
    user = models.ForeignKey(User,  on_delete=models.SET_NULL, null=True)
    address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL,null=True)
    total_amount = models.FloatField(null=False)
    date = models.DateField(auto_now_add=True)
    order_status = models.CharField( max_length=100, default="Order Placed")
    payment_option = models.CharField(max_length=100, default="Cash_on_delivery")
    order_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    payment_status = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=50)
    
    
    
class OrderSub(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    main_order = models.ForeignKey(OrderMain, on_delete=models.CASCADE)
    variant = models.ForeignKey(Product_Variant, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=False, default=0)
    is_active = models.BooleanField(default=True)
    
    def total_cost(self):
        return self.quantity * self.variant.product.offer_price