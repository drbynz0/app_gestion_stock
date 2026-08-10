from django.db import models # type: ignore

class InternalOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('toPay', 'To Pay'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('virement', 'Virement'),
        ('cheque', 'Cheque'),
    ]
    TYPE_ORDER_CHOICES = [
        ('online', 'online'),
        ('inStore', 'inStore'),
    ]

    order_num = models.CharField(max_length=100, unique=True)
    client_id = models.IntegerField(null=False, blank=True)
    client_name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_ORDER_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'internalorders_internalorder'
    
    def update_payment_status(self):
        """Met à jour le statut de la commande en fonction des paiements"""
        if self.remaining_price <= 0:
            self.status = 'completed'
        elif self.total_paid > 0:
            self.status = 'toPay'
        else:
            self.status = 'pending'
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(InternalOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    product_ref = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    product_image = models.URLField(blank=True, null=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        db_table = 'internalorders_orderitem'
    
class Payment(models.Model):
    order = models.ForeignKey(InternalOrder, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=InternalOrder.PAYMENT_METHOD_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'internalorders_payment'

    def __str__(self):
        return f"Payment of {self.amount} for Order {self.order.order_num}"
    
    def save(self, *args, **kwargs):
        """Surcharge de save pour mettre à jour les totaux de la commande"""
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        if is_new:
            self.order.total_paid += self.amount
            self.order.remaining_price = self.order.total_price - self.order.total_paid
            self.order.update_payment_status()
            self.order.save()