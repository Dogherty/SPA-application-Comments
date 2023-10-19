from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from .forms import CommentForm
from bleach import clean
from django.conf import settings
from lxml import etree
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CommentSerializer, PostSerializer, ClientInfoSerializer
import json
from rest_framework import pagination
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import datetime
from django.views import View
from django_user_agents.utils import get_user_agent
from django.http import JsonResponse
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

# Задаем разрешенные теги и атрибуты для очистки текста
BLEACH_ALLOWED_TAGS = settings.BLEACH_ALLOWED_TAGS
BLEACH_ALLOWED_ATTRIBUTES = settings.BLEACH_ALLOWED_ATTRIBUTES

# Функция для генерации и отправки CAPTCHA
def get_captcha(request):
    if request.method == 'GET':
        captcha = CaptchaStore.generate_key()
        image_url = captcha_image_url(captcha)
        request.session['expected_captcha'] = captcha
        response_data = {
            'key': captcha,
            'image_url': image_url
        }
        return JsonResponse(response_data)

# Класс APIView для работы с комментариями
class CommentAPIView(APIView):
    # Метод GET для получения комментариев к посту
    def get(self, request, year, month, day, post_id):
        post = get_object_or_404(Post, id=post_id, status='published', publish__year=year, publish__month=month,
                                 publish__day=day)

        # Извлекаем параметры сортировки и порядка
        sort_by = request.GET.get('sort_by')
        order = request.GET.get('order', 'asc')

        # Выбор сортировки в зависимости от параметра sort_by
        if sort_by == 'user_name':
            if order == 'desc':
                comments = Comment.objects.filter(post=post).order_by('-user_name')
            else:
                comments = Comment.objects.filter(post=post).order_by('user_name')
        elif sort_by == 'email':
            if order == 'desc':
                comments = Comment.objects.filter(post=post).order_by('-email')
            else:
                comments = Comment.objects.filter(post=post).order_by('email')
        elif sort_by == 'date_added':
            if order == 'desc':
                comments = Comment.objects.filter(post=post).order_by('-created_at')
            else:
                comments = Comment.objects.filter(post=post).order_by('created_at')
        else:
            comments = Comment.objects.filter(post=post).select_related('post', 'parent_comment').order_by('-created_at')

        # Преобразование комментариев в словарь
        comments_dict = {comment.id: CommentSerializer(comment).data for comment in comments}

        # Группируем дочерние комментарии в соответствии с родительскими комментариями
        parent_to_children = {}
        for comment in comments_dict.values():
            comment['created_at'] = datetime.strptime(comment['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M %d.%m.%Y")
            parent_comment = comment.get('parent_comment')
            if parent_comment:
                parent_id = parent_comment
                parent_to_children.setdefault(parent_id, []).append(comment)

        # Выделение корневых комментариев и добавление дочерних к ним
        root_comments = [comment for comment in comments_dict.values() if not comment.get('parent_comment')]

        def add_children_to_parent(comment):
            children = parent_to_children.get(comment['id'], [])
            comment['children'] = children
            for child in children:
                add_children_to_parent(child)

        for comment in root_comments:
            add_children_to_parent(comment)

        # Пагинация результатов
        paginator = pagination.PageNumberPagination()
        paginator.page_size = 25
        page = paginator.paginate_queryset(root_comments, request)

        # Сериализация поста и возврат результата
        post_serializer = PostSerializer(post)
        result = {
            'post': post_serializer.data,
            'comments': page,
            'page': request.GET.get('page', 1),
            'total_pages': paginator.page.paginator.num_pages,
        }
        return Response(result)

    # Метод POST для создания нового комментария
    def post(self, request, year, month, day, post_id):
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Метод не поддерживается'}, status=405)
        try:
            data = request.data
            print(data)
            c_key = data.get('captcha_key', '')
            captcha_stores = CaptchaStore.objects.filter(hashkey=c_key)
            captcha_store = captcha_stores.first()
            c_value = data.get('captcha_value', '')
            print(c_key + ' value: ' + c_value + ' ожидаем: ' + captcha_store.response)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Ошибка при разборе JSON'}, status=400)

        # Создание формы комментария
        form = CommentForm(data, request.FILES)

        if form.is_valid():
            # Проверка CAPTCHA
            if captcha_store.response != c_value:
                return JsonResponse({'success': False, 'message': 'Неправильная CAPTCHA'}, status=400)

            parent_id = data.get('parent_comment')
            post = get_object_or_404(Post, id=post_id)
            parent_comment = get_object_or_404(Comment, id=parent_id) if parent_id else None

            comment = form.save(commit=False)
            comment.post = post
            comment.parent_comment = parent_comment

            # Сериализация информации о пользователе
            serializer = ClientInfoSerializer(data={
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': str(get_user_agent(request)),
                'user_name': comment.user_name
            })

            if serializer.is_valid():
                print('YES')
                client_info = serializer.save()
                comment.client_info = client_info
            else:
                print('NO')
                print(serializer.errors)

            # Очистка текста комментария от нежелательных тегов
            cleaned_text = clean(comment.text, tags=BLEACH_ALLOWED_TAGS, attributes=BLEACH_ALLOWED_ATTRIBUTES)
            comment.text = cleaned_text

            # Проверка валидности XHTML разметки
            if not validate_xhtml(comment.text):
                return JsonResponse({'success': False, 'message': 'Invalid XHTML markup'}, status=400)

            # Обработка изображения
            try:
                image_tmp_file = request.FILES.get('image')
                if image_tmp_file:

                    valid_formats = ['image/jpeg', 'image/png', 'image/gif']
                    if image_tmp_file.content_type not in valid_formats:
                        return JsonResponse({'success': False, 'message': 'Недопустимый формат изображения'},
                                            status=400)

                    img = Image.open(image_tmp_file)
                    width, height = img.size
                    max_size = (320, 240)
                    if width > max_size[0] or height > max_size[1]:
                        img = img.resize(max_size)
                        output_buffer = BytesIO()

                        img.save(output_buffer, format=image_tmp_file.content_type.split('/')[-1].upper())

                        image_tmp_file = InMemoryUploadedFile(output_buffer, 'ImageField', f'{image_tmp_file.name}',
                                                              image_tmp_file.content_type, output_buffer.tell, None)

                    comment.image = image_tmp_file

            except Exception as e:
                print(f"Ошибка при сохранении изображения: {e}")

            # Обработка текстового файла
            try:
                file_tmp_file = request.FILES.get('file')
                if file_tmp_file:
                    if not file_tmp_file.name.endswith('.txt'):
                        return JsonResponse(
                            {'success': False, 'message': 'Недопустимый формат файла. Разрешены только .txt файлы.'},
                            status=400)
                    if file_tmp_file.size > 102400:  # 100 КБ
                        return JsonResponse({'success': False, 'message': 'Файл слишком большой'}, status=400)

                    comment.text_file = file_tmp_file
                    new_name = comment.text_file.name.split('/')[-1]
                    comment.text_file.name = new_name
            except Exception as e:
                print(f"Ошибка при сохранении файла: {e}")

            comment.save()
            return JsonResponse({'success': True, 'comment_id': comment.id})
        else:
            errors = form.errors.as_json()
            errors_dict = json.loads(errors)  # Преобразуем JSON-строку в словарь
            message = errors_dict["image"][0]["message"]
            return JsonResponse({'success': False, 'message': message}, status=400)

# Класс View для отображения списка постов
class PostListView(View):
    def get(self, request):
        posts = Post.objects.all()
        for post in posts:
            post.formatted_date = post.publish.strftime('%Y/%m/%d')
        return render(request, 'comments/index.html', {'posts': posts})

# Класс View для отображения деталей поста
class PostDetailView(View):
    def get(self, request, year, month, day, post_id):
        post = get_object_or_404(Post, id=post_id, status='published', publish__year=year, publish__month=month, publish__day=day)
        return render(request, 'comments/detail.html', {
            'post': post,
            'comment_form': CommentForm(),
            'post_id': post.id,
            'year': post.publish.year,
            'month': post.publish.month,
            'day': post.publish.day
        })

# Функция для валидации XHTML разметки
def validate_xhtml(text):
        try:
            etree.fromstring("<root>" + text + "</root>")
            return True
        except etree.XMLSyntaxError:
            return False
