from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Category, UserProfile, Blood_Donation, Order


def is_admin(user):
    return user.is_authenticated and user.is_staff


def get_user_profile(user):
    """Helper to ensure a UserProfile always exists for an authenticated user."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def Home(request):
    return render(request, 'carousel.html')


def About(request):
    return render(request, 'about.html')


def Contact(request):
    if request.method == "POST":
        name = request.POST.get('Name', '').strip()
        messages.success(request, f"Thank you {name or ''}! Your message has been sent successfully.")
        return redirect('contact')
    return render(request, 'contact.html')


def Gallery(request):
    return render(request, 'gallery.html')


def Login_User(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('profile')

    if request.method == "POST":
        u = request.POST.get('uname', '').strip()
        p = request.POST.get('pwd', '').strip()
        user = authenticate(username=u, password=p)

        if user is not None:
            if not user.is_staff:
                login(request, user)
                messages.success(request, f"Welcome, {user.first_name or user.username}!")
                return redirect('profile')
            else:
                messages.error(request, "Staff / Admin accounts should log in via Admin Login.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html')


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_home')

    if request.method == "POST":
        u = request.POST.get('uname', '').strip()
        p = request.POST.get('pwd', '').strip()
        user = authenticate(username=u, password=p)

        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, "Logged in as Administrator.")
            return redirect('admin_home')
        else:
            messages.error(request, "Invalid admin credentials.")

    return render(request, 'admin_login.html')


def Signup_User(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        f = request.POST.get('fname', '').strip()
        l = request.POST.get('lname', '').strip()
        u = request.POST.get('uname', '').strip()
        e = request.POST.get('email', '').strip()
        p = request.POST.get('pwd', '').strip()
        d = request.POST.get('dob', '').strip()
        con = request.POST.get('contact', '').strip()
        add = request.POST.get('add', '').strip()
        group_id = request.POST.get('group', '').strip()
        im = request.FILES.get('image')

        if not u or not p:
            messages.error(request, "Username and password are required.")
            return render(request, 'register.html', {'cat': categories})

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists. Please choose a different username.")
            return render(request, 'register.html', {'cat': categories})

        if e and User.objects.filter(email=e).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'register.html', {'cat': categories})

        blood_group = Category.objects.filter(id=group_id).first() if group_id else None

        user = User.objects.create_user(username=u, email=e, password=p, first_name=f, last_name=l)
        UserProfile.objects.create(
            user=user,
            contact=con,
            address=add,
            image=im,
            dob=d or None,
            blood_group=blood_group
        )
        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'register.html', {'cat': categories})


def Logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')


@login_required(login_url='login')
def Change_Password(request):
    if request.method == "POST":
        old_pwd = request.POST.get('pwd3', '')
        new_pwd = request.POST.get('pwd1', '')
        confirm_pwd = request.POST.get('pwd2', '')

        if not request.user.check_password(old_pwd):
            messages.error(request, "Current password is incorrect.")
            return redirect('change_password')

        if new_pwd != confirm_pwd:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change_password')

        if len(new_pwd) < 6:
            messages.error(request, "New password must be at least 6 characters long.")
            return redirect('change_password')

        request.user.set_password(new_pwd)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Password changed successfully.")
        return redirect('home')

    return render(request, 'change_password.html')


@login_required(login_url='login')
def profile(request):
    pro = get_user_profile(request.user)
    return render(request, "profile.html", {'pro': pro})


@login_required(login_url='login')
def edit_profile(request, pid):
    data = get_object_or_404(UserProfile, id=pid)

    if not request.user.is_staff and data.user != request.user:
        messages.error(request, "You can only edit your own profile.")
        return redirect('profile')

    cat = Category.objects.all()

    if request.method == 'POST':
        f = request.POST.get('fname', '').strip()
        l = request.POST.get('lname', '').strip()
        e = request.POST.get('email', '').strip()
        con = request.POST.get('contact', '').strip()
        add = request.POST.get('add', '').strip()
        group_id = request.POST.get('group', '').strip()

        if 'image' in request.FILES:
            data.image = request.FILES['image']

        if data.user:
            data.user.first_name = f
            data.user.last_name = l
            data.user.email = e
            data.user.save()

        data.contact = con
        data.address = add

        if group_id:
            data.blood_group = Category.objects.filter(id=group_id).first()

        data.save()
        messages.success(request, "Profile updated successfully.")

        if request.user.is_staff:
            return redirect('view_user')
        else:
            return redirect('profile')

    return render(request, 'edit_profile.html', {'data': data, 'cat': cat})


@user_passes_test(is_admin, login_url='admin_login')
def view_user(request):
    data = UserProfile.objects.all().select_related('user', 'blood_group')
    return render(request, 'view_user.html', {'data': data})


@user_passes_test(is_admin, login_url='admin_login')
def delete_user(request, pid):
    profile = get_object_or_404(UserProfile, id=pid)
    user = profile.user
    if user:
        user.delete()
    else:
        profile.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('view_user')


@user_passes_test(is_admin, login_url='admin_login')
def add_category(request):
    if request.method == 'POST':
        n = request.POST.get('name', '').strip()
        if n:
            Category.objects.create(name=n)
            messages.success(request, "Category created successfully.")
            return redirect('view_category')
        else:
            messages.error(request, "Category name cannot be empty.")
    return render(request, 'add_category.html')


@user_passes_test(is_admin, login_url='admin_login')
def view_category(request):
    data = Category.objects.all()
    return render(request, 'view_category.html', {'data': data})


@user_passes_test(is_admin, login_url='admin_login')
def edit_category(request, pid):
    data = get_object_or_404(Category, id=pid)
    if request.method == 'POST':
        n = request.POST.get('name', '').strip()
        if n:
            data.name = n
            data.save()
            messages.success(request, "Category updated successfully.")
            return redirect('view_category')
        else:
            messages.error(request, "Category name cannot be empty.")
    return render(request, 'edit_category.html', {'data': data})


@user_passes_test(is_admin, login_url='admin_login')
def delete_category(request, pid):
    data = get_object_or_404(Category, id=pid)
    data.delete()
    messages.success(request, "Category deleted successfully.")
    return redirect('view_category')


@login_required(login_url='login')
def search_blood(request):
    userprofile = get_user_profile(request.user)
    data = Blood_Donation.objects.filter(status="Approved").exclude(purpose="Request for Blood", user=userprofile).select_related('user__user', 'blood_group')

    if request.method == "POST":
        bg = request.POST.get('group')
        place = request.POST.get('place', '').strip()
        cat = Category.objects.filter(id=bg).first() if bg else None
        Blood_Donation.objects.create(
            blood_group=cat,
            user=userprofile,
            purpose="Request for Blood",
            status="Pending",
            place=place
        )
        messages.success(request, "Blood request generated successfully.")
        return redirect('search_blood')

    all_cat = Category.objects.all()
    return render(request, 'search_blood.html', {'data': data, 'cat': all_cat})


@login_required(login_url='login')
def donate_blood(request):
    userprofile = get_user_profile(request.user)

    if request.method == "POST":
        bg = request.POST.get('group')
        place = request.POST.get('place', '').strip()
        cat = Category.objects.filter(id=bg).first() if bg else None
        Blood_Donation.objects.create(
            blood_group=cat,
            user=userprofile,
            purpose="Blood Donor",
            status="Pending",
            place=place
        )
        messages.success(request, "Thank you! Your donation details have been submitted.")
        return redirect('donate_blood')

    all_cat = Category.objects.all()
    return render(request, 'donate_blood.html', {'cat': all_cat})


@user_passes_test(is_admin, login_url='admin_login')
def request_blood(request):
    mydata = request.GET.get('action')
    data = Blood_Donation.objects.filter(purpose="Request for Blood").select_related('user__user', 'blood_group')
    if mydata:
        data = data.filter(status=mydata)

    if request.method == "POST":
        bg = request.POST.get('group')
        place = request.POST.get('place', '').strip()
        cat = Category.objects.filter(id=bg).first() if bg else None
        userprofile = get_user_profile(request.user)
        Blood_Donation.objects.create(
            blood_group=cat,
            user=userprofile,
            purpose="Request for Blood",
            status="Pending",
            place=place
        )
        messages.success(request, "Blood request registered successfully.")
        return redirect('request_blood')

    all_cat = Category.objects.all()
    return render(request, 'request_blood.html', {'data': data, 'cat': all_cat})


@user_passes_test(is_admin, login_url='admin_login')
def donator_blood(request):
    mydata = request.GET.get('action')
    data = Blood_Donation.objects.filter(purpose="Blood Donor").select_related('user__user', 'blood_group')
    if mydata:
        data = data.filter(status=mydata)
    return render(request, 'donator_blood.html', {'data': data})


@user_passes_test(is_admin, login_url='admin_login')
def change_status(request, pid):
    data = get_object_or_404(Blood_Donation, id=pid)
    url = request.GET.get('data')
    if data.status == "Approved":
        data.status = "Pending"
    else:
        data.status = "Approved"
    data.save()
    messages.success(request, f"Status updated to {data.status}.")
    return HttpResponseRedirect(url or '/donator_blood')


@user_passes_test(is_admin, login_url='admin_login')
def admin_home(request):
    total_users = UserProfile.objects.count()
    total_orders = Order.objects.count()
    total_donate = Blood_Donation.objects.filter(purpose="Blood Donor").count()
    total_req = Blood_Donation.objects.filter(purpose="Request for Blood").count()

    context = {
        'data': total_users,
        'order': total_orders,
        'req': total_req,
        'donate': total_donate
    }
    return render(request, 'admin_home.html', context)


@login_required(login_url='login')
def history(request):
    userprofile = get_user_profile(request.user)
    data = Blood_Donation.objects.filter(user=userprofile).select_related('blood_group')
    return render(request, "history.html", {'data': data})


@login_required(login_url='login')
def pay_now(request, pid):
    total = 2000
    userprofile = get_user_profile(request.user)
    blood = get_object_or_404(Blood_Donation, id=pid)

    if request.method == "POST" or request.GET.get('get') == "1":
        Order.objects.create(user=userprofile, blood_donation=blood, amount=str(total), status="Pending")
        messages.success(request, "Blood ordered successfully!")
        return redirect("my_order")

    return render(request, "payment2.html", {'total': total, 'blood': blood})


@login_required(login_url='login')
def my_order(request):
    userprofile = get_user_profile(request.user)
    data = Order.objects.filter(user=userprofile).select_related('blood_donation__blood_group')
    return render(request, "my_order.html", {'data': data})


@user_passes_test(is_admin, login_url='admin_login')
def all_order(request):
    data = Order.objects.all().select_related('user__user', 'blood_donation__blood_group')
    return render(request, "all_order.html", {'data': data})


@login_required(login_url='login')
def delete_order(request, pid):
    order = get_object_or_404(Order, id=pid)
    if request.user.is_staff:
        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect('all_order')
    else:
        if order.user and order.user.user == request.user:
            order.delete()
            messages.success(request, "Order deleted successfully.")
        else:
            messages.error(request, "You are not authorized to delete this order.")
        return redirect('my_order')


@user_passes_test(is_admin, login_url='admin_login')
def change_order_status(request, pid):
    order = get_object_or_404(Order, id=pid)
    if order.status == "Delivered":
        order.status = "Pending"
    else:
        order.status = "Delivered"
    order.save()
    messages.success(request, f"Order status changed to {order.status}.")
    return redirect('all_order')