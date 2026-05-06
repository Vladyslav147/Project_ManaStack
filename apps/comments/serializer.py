from rest_framework import serializers
from . models import Comments
from apps.main.models import Post



class CommentSerializer(serializers.ModelSerializer):
    author_info = serializers.SerializerMethodField()
    replies_count = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()

    class Meta:
        model = Comments
        fields = ['id', 'author', 'post', 'parent', 'content', 'is_active', 'created_at', 'updated_at', 'author_info', 'replies_count', 'is_reply']
        read_only_fields = ['id', 'author', 'is_active', 'created_at']
    
    def get_author_info(self, obj):
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'full_name': obj.author.full_name,
            'avatar': obj.author.avatar.url if obj.author.avatar else None,
        }
    


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Comments
        fields = ['post', 'parent', 'content']

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id, status='published').exists():
            raise serializers.ValidationError('Пост не найден')
        return value
        
    def validate_parent(self, value):
            # 1. Достаем ID поста из JSON-запроса Postman
            request_post_id = self.initial_data.get('post')
            
            # 2. Если есть и родитель, и ID поста
            if value and request_post_id:
                # value.post_id — это цифра из базы (выгоднее писать post_id, чтобы не дергать базу лишний раз)
                # int(request_post_id) — превращаем данные из Postman точно в число
                if value.post_id != int(request_post_id):
                    raise serializers.ValidationError('Коментарий должен относится к той же публикации')
                    
            return value
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
    


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ['content']   



class CommentDetailSerializer(CommentSerializer):
    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.filter(is_active=True).order_by('created_at')
            return CommentSerializer(replies, many=True, context=self.context).data
        return []