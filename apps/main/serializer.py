from rest_framework import serializers
from django.utils.text import slugify
from .models import Tag, Category, Post

class TagShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'title', 'slug']



class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'title', 'description', 'icon', 'slug', 'post_count']
        read_only_fields = ['id', 'slug']

    def get_post_count(self, obj):
        return obj.posts.filter(status='published').count()
    
    def create(self, validated_data):
        validated_data['slig'] = slugify(validated_data['title'])
        return super().create(validated_data)
    


class PostListSerializer(serializers.ModelSerializer):
    comment_count = serializers.ReadOnlyField()
    author = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    tag = TagShortSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'image', 'status', 'slug', 'comment_count', 'category', 'created_at', 'views_count', 'author', 'tag']
        read_only_fields = ['id', 'author', 'slug', 'views_count']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if len(data['description']) > 200:
            data['description'] = data['description'][:200] + '...'
        return data
    

class PostDetailSerializer(serializers.ModelSerializer):
    author_info = serializers.SerializerMethodField()
    category_info = serializers.SerializerMethodField()
    # can_pin = serializers.SerializerMethodField()
    comment_count = serializers.ReadOnlyField()
    tag = TagShortSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'image', 'status', 'slug', 'comment_count',
                'category_info', 'created_at', 'views_count', 'tag', 'author_info']
        read_only_fields = ['id', 'slug', 'comment_count', 'created_at', 'views_count']

    def get_author_info(self, obj):
        author = obj.author
        return {
            'id': author.id,
            'username': author.username,
            'full_name': author.full_name,
            'avatar': author.avatar.url if author.avatar else None,
        }

    def get_category_info(self, obj):
        if obj.category:
            category = obj.category
            return {
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
            }
        return None
    
    # def get_can_pin(self, obj):
    #     request = self.context.get('request')
    #     if not request or  not request.user.is_authenticated:
    #         return False
    #     return obj.can_be_pinned_by(request.user)
    


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    tag = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'image', 'status', 'category', 'tag']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['slug'] = slugify(validated_data['title'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'title' in validated_data:
            validated_data['slug'] = slugify(validated_data['title'])
        return super().update(instance, validated_data)


class TagListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'title', 'slug']
        read_only_fields = ['id', 'slug']