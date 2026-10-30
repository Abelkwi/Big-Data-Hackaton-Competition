from django.shortcuts import render


def serve_static_page(request, page):
    return render(request, page)
