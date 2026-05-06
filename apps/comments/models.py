from django.db import models
from django.conf import settings


class Comments(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    post = models.ForeignKey(
        'main.Post', 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    parent = models.ForeignKey( # если parent NONE то это основной комент, но если этот комент будет ответом на какойто то в parent будет лежать ID того комента на который этот был написан 
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )

    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'
    
    @property
    def replies_count(self):
        return self.replies.filter(is_active=True).count()
    
    @property
    def is_reply(self):
        return self.replies is not None
    