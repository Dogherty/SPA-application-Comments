"""
ASGI config for spa project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from django.urls import path
from django.core.asgi import get_asgi_application
from spa.comments.consumers import YourConsumerpy


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spa.settings')

application = get_asgi_application()


django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws', YourConsumer.as_asgi())
        ])
    )
})