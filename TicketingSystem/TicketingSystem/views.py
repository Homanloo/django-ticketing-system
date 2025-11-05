from django.shortcuts import render
from django.conf import settings
import os


def index(request):
    """Serve the frontend index.html"""
    static_dir = settings.BASE_DIR / 'static'
    index_path = static_dir / 'index.html'
    
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        from django.http import HttpResponse
        return HttpResponse(content, content_type='text/html')
    else:
        from django.http import HttpResponseNotFound
        return HttpResponseNotFound('Frontend not found')

