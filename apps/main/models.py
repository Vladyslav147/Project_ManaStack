from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse

class Tag(models.Model):
    title = models.CharField(max_length=10, unique=True)
    slug = models.SlugField(max_length=30, unique=True, db_index=True)# db_index=True = нужно для того что бы когда будет вызов  по слагу к примеру, а в базе оч много записей а идет вызов по названию vuv-car то с db_index=True он бдуте не все записи просматривать что бы найти а которые начинаются с буквы v

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        db_table = 'tags' 

    def sava(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Category(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    icon = models.ImageField(upload_to='category/icon/', blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PostManager(models.Manager):
    def with_card_info(self):
        return self.select_related('category', 'pin_info').prefetch_related('author', 'author__inventary', 'author__inventary__subscription_card','tag')
    
class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='post/image/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    slug = models.SlugField(max_length=200, unique=True)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, blank=True, null=True, related_name='posts', on_delete=models.SET_NULL)
    tag = models.ManyToManyField(Tag, related_name='posts', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)

    objects = PostManager()

    class Meta:
        db_table = 'posts'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("model_detail", kwargs={"slug": self.slug})
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields = ['views_count'])

    @property
    def comments_count(self):
        return self.comments.filter(is_active = True).count()
    
    def can_be_pinned_by(self, user):
        if not user or not user.is_authenticated:
            return False
        
        if self.author != user:
            return False 
        
        return user.inventory.filter(subscription_card__type='premium', status='active').exists()
    
    @property
    def comment_count(self):
        return self.comments.filter(is_active=True).count()



