from django.db import models
from django.contrib.auth.models import User

class Headline(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField(null = True, blank = True)
    url = models.TextField()
    content = models.TextField(null=True, blank=True)  # Fix here
    source = models.CharField(max_length=200,null = True,blank=True)

    def __str__(self):
        return self.title

class EHeadline(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField(null = True, blank = True)
    url = models.TextField()
    content = models.TextField(null=True, blank=True)  # Fix here
    source = models.CharField(max_length=200,null = True,blank=True)

    def __str__(self):
        return self.title

class SHeadline(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField(null = True, blank = True)
    url = models.TextField()
    content = models.TextField(null=True, blank=True)  # Fix here
    source = models.CharField(max_length=200,null = True,blank=True)

    def __str__(self):
        return self.title

class PHeadline(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField(null = True, blank = True)
    url = models.TextField()
    content = models.TextField(null=True, blank=True)  # Fix here
    source = models.CharField(max_length=200,null = True,blank=True)

    def __str__(self):
        return self.title

class LHeadline(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField(null = True, blank = True)
    url = models.TextField()
    content = models.TextField(null=True, blank=True)  # Add this line if it's missing
    source = models.CharField(max_length=200,null = True,blank=True)

    def __str__(self):
        return self.title

class ENHeadline(models.Model):
    title = models.CharField(max_length=200)
    image = models.URLField(null = True, blank = True)
    url = models.TextField()
    content = models.TextField(null=True, blank=True)
    source = models.CharField(max_length=200,null = True,blank=True)

    def __str__(self):
        return self.title

class Article(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    image = models.URLField()
    content = models.TextField(null=True, blank=True)  # Fix here
    source = models.CharField(max_length=255)
    likes = models.ManyToManyField(User, related_name='liked_articles', blank=True)
    dislikes = models.ManyToManyField(User, related_name='disliked_articles', blank=True)
    favorites = models.ManyToManyField(User, related_name='favorite_articles', blank=True)

    def total_likes(self):
        return self.likes.count()
    
    def total_dislikes(self):
        return self.dislikes.count()

    def is_favorite(self, user):
        return self.favorites.filter(id=user.id).exists()

    def __str__(self):
        return self.title