from django.db import models

# Create your models here.

class LeaderModle(models.Model):
    email=models.EmailField(max_length=100)
    first_name=models.CharField(max_length=100)
    last_name=models.CharField(max_length=100)
    full_name=models.CharField(max_length=100)
    picture_url=models.URLField(max_length=200)
    is_paid=models.BooleanField(default=False)

class TeamModle(models.Model):
    team_name=models.CharField(max_length=100)
    Leader=models.ForeignKey(LeaderModle,on_delete=models.CASCADE)
    team_member1_name=models.CharField(max_length=100)
    team_member2_name=models.CharField(max_length=100)
    team_member1_email=models.EmailField(max_length=100)
    team_member2_email=models.EmailField(max_length=100)
