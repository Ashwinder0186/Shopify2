from django.shortcuts import render , redirect
from .models import Product, Contact, Orders, userDetails, OrderUpdate
from math import ceil
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
from django.core.mail import EmailMessage,send_mail
from django.conf import settings 
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required



from django.shortcuts import render, redirect

#################
from django.contrib.sites.shortcuts import get_current_site

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
#new

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

UserModel = get_user_model()


UserModel = get_user_model()




MERCHANT_KEY = 'muAbf1DOStdDOzFl'

def index(request):
    if request.user.is_anonymous:
        return redirect("/shop/login")
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds':allProds}
    return render(request, 'shop/index.html', params)

def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    if request.user.is_anonymous:
        return redirect("/shop/login")
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]

        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg": ""}
    if len(allProds) == 0 or len(query)<4:
        params = {'msg': "no products found!"}
    return render(request, 'shop/search.html', params)


def about(request):
    if request.user.is_anonymous:
        return redirect("/shop/login")
    return render(request, 'shop/about.html')


def contact(request):
    if request.user.is_anonymous:
        return redirect("/shop/login")
    thank = False
    if request.method=="POST":
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True

        template1=render_to_string('shop/contactemail.html',{'name':name,})

        email = EmailMessage('your query is submitted', template1, to=[email])
        email.send()

    return render(request, 'shop/contact.html', {'thank': thank})


def tracker(request):
    if request.user.is_anonymous:
        return redirect("/shop/login")    
    if request.method=="POST":
        orderId = request.POST.get('orderId', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=orderId, email=email)
            if len(order)>0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps([updates, order[0].items_json], default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{}')
        except Exception as e:
            return HttpResponse('{}')

    return render(request, 'shop/tracker.html')




def productView(request, myid):
    if request.user.is_anonymous:
        return redirect("/shop/login")

    # Fetch the product using the id
    product = Product.objects.filter(id=myid)
    return render(request, 'shop/prodView.html', {'product':product[0]})


def checkout(request):
    if request.user.is_anonymous:
        return redirect("/shop/login")
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json, name=name, email=email, address=address, city=city,
                       state=state, zip_code=zip_code, phone=phone, amount=amount)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank':thank, 'id': id})
        # Request paytm to transfer the amount to your account after payment by user
        param_dict = {

                'MID': 'yPWbiG78870241339146',
                'ORDER_ID': str(order.order_id),
                'TXN_AMOUNT': str(amount),
                'CUST_ID': email,
                'INDUSTRY_TYPE_ID': 'Retail',
                'WEBSITE': 'WEBSTAGING',
                'CHANNEL_ID': 'WEB',
                'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',

        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')


@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            allproduct= Orders.objects.all()
            useremail=list(reversed(allproduct))[0].email
            username=list(reversed(allproduct))[0].name
            userid=list(reversed(allproduct))[0].order_id
            orderprice=list(reversed(allproduct))[0].amount
            template2=render_to_string('shop/orderemail.html',{'name':username,'orderid':userid,'amount':orderprice})
            email = EmailMessage('order succesfull', template2, to=[useremail])
            email.send()

            print('order successful')
            
        else:
            p= Orders.objects.all()
            q=OrderUpdate.objects.all()
            r=list(reversed(p))[0].delete()
            r=list(reversed(q))[0].delete()
            print('order was not successful because' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})







class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('shop/account_activation_email.html', {
                'user': user,
                'domain': '127.0.0.1:8000',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return render(request,'shop/home2.html')
    else:
        form = SignUpForm()
    return render(request, 'shop/signup1.html', {'form': form})






def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request,'shop/signup.html')
    else:
        return HttpResponse('Activation link is invalid!')





#profile
@login_required
def profile(request):
    if request.method =='POST':
        u_form= UserUpdate(request.POST,instance=request.user)
        p_form= ProfileUpdate(request.POST,request.FILES,instance=request.user.userdetails)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
    else:        
        u_form= UserUpdate(instance=request.user)
        p_form= ProfileUpdate(instance=request.user.userdetails)
    return render(request,'shop/profile.html',{'u_form':u_form,'p_form':p_form})


class UserUpdate(forms.ModelForm):
    class Meta:
        model= User
        fields=['first_name','last_name']


class ProfileUpdate(forms.ModelForm):
    class Meta:
        model=userDetails
        fields=['phone','image']



