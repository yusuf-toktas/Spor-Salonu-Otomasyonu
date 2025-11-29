from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .models import User, MembershipPlan, UserSubscription, Message
from django.db.models import Q
import qrcode
import io
import base64
from datetime import timedelta, date

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    subscription = getattr(request.user, 'subscription', None)
    qr_code_img = None

    if subscription and subscription.is_active:
        # Generate QR Code
        qr_data = f"USER:{request.user.id}:VALID"
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_img = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'dashboard.html', {
        'subscription': subscription,
        'qr_code': qr_code_img
    })

@login_required
def plan_list(request):
    plans = MembershipPlan.objects.all()
    return render(request, 'plans.html', {'plans': plans})

@login_required
def subscribe(request, plan_id):
    if request.method != 'POST':
         # Ideally should be POST only, but for now we'll allow GET or implement a confirmation page.
         # But sticking to plan: Update start_date.
         pass

    plan = get_object_or_404(MembershipPlan, id=plan_id)
    # Check if user already has active subscription
    if hasattr(request.user, 'subscription'):
        sub = request.user.subscription
        sub.plan = plan
        sub.start_date = date.today()
        sub.end_date = date.today() + timedelta(days=plan.duration_days)
        sub.is_active = True
        sub.save()
    else:
        UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            end_date=date.today() + timedelta(days=plan.duration_days)
        )
    return redirect('dashboard')

@login_required
def inbox(request):
    # Filter users based on role
    if request.user.is_trainer:
        # Trainers can see everyone (or just members, but let's say everyone for now)
        users = User.objects.exclude(id=request.user.id)
    else:
        # Members can only see Trainers
        users = User.objects.filter(is_trainer=True).exclude(id=request.user.id)

    # Get latest messages (simplified)
    # A proper query would group by conversation partner
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')

    return render(request, 'inbox.html', {'users': users, 'messages': messages})

@login_required
def chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )
            return redirect('chat', user_id=user_id)

    return render(request, 'chat.html', {'other_user': other_user, 'messages': messages})
