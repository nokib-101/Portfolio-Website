from django.shortcuts import render, redirect
from django.contrib import messages
from Base.models import Contact


def contact(request):
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        content = request.POST.get('content', '').strip()
        number = request.POST.get('number', '').strip()

        if not 2 <= len(name) <= 40:
            messages.error(request, 'Name should be between 2 and 40 characters.')
        elif not 3 <= len(email) <= 40:
            messages.error(request, 'Please enter a valid email address.')
        elif not content or len(content) > 400:
            messages.error(request, 'Message should be between 1 and 400 characters.')
        elif len(number) > 15:
            messages.error(request, 'Phone number is too long.')
        else:
            Contact.objects.create(name=name, email=email, content=content, number=number)
            messages.success(request, "Thanks for reaching out! I'll get back to you soon.")

        # Post/Redirect/Get so refreshing doesn't resubmit the form
        return redirect('/#contact')

    return render(request, 'home.html')
