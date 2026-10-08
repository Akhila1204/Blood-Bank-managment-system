from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name or "Unnamed Category"

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    contact = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    blood_group = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    image = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.user.username if self.user else "Anonymous UserProfile"



class Blood_Donation(models.Model):
    status = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    blood_group = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    place = models.CharField(max_length=100, null=True, blank=True)
    purpose = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now=True,null=True)
    active = models.BooleanField(null=True, blank=True, default=False)

    def __str__(self):
        username = self.user.user.username if (self.user and self.user.user) else "Unknown"
        return f"{username} - {self.purpose or 'Blood Donation'}"

class Order(models.Model):
    status = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    blood_donation = models.ForeignKey(Blood_Donation, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now=True,null=True)

    def __str__(self):
        username = self.user.user.username if (self.user and self.user.user) else "Unknown"
        return f"{username} - Order #{self.id}"