from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('CEO', 'CEO'),
        ('MANAGER', 'Manager'),
        ('HR', 'HR'),
        ('EMPLOYEE', 'Employee')
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.role == 'CEO':
            if User.objects.filter(role='CEO').exclude(pk=self.pk).exists():
                raise ValueError("There can only be one CEO.")
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.price} - {self.quantity}"
    
class Sale(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.total_amount} - {self.created_at}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} - {self.price_at_sale}"


class Shift(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.username} - {self.date}"

class InventoryLog(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    adjustment = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.manager.username} adjusted {self.product.name}"