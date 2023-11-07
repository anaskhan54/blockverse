from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import urllib
from django.http.response import HttpResponseRedirect
import requests,json,razorpay,jwt
from .models import LeaderModle,TeamModle
from django.core.mail import send_mail
# Create your views here.
data={'email':''}

class LandingPageView(APIView):
    def get(self,request):
        return render(request,'oauth/landing_page.html')
class GoogleOauthView(APIView):
    def get(self,request):
        auth_url='https://accounts.google.com/o/oauth2/v2/auth'
        redirect_uri = 'http://ec2-3-109-124-174.ap-south-1.compute.amazonaws.com/oauth/'
        scope='openid email profile'
        state='random_state_value'
        params={
            'client_id':settings.GOOGLE_OAUTH2_CLIENT_ID,
            'redirect_uri':redirect_uri,
            'scope':scope,
            'state':state,  
            'response_type':'code',

        }
        url=f'{auth_url}?{urllib.parse.urlencode(params)}'

        
        return HttpResponseRedirect(url)
    
class CallBackHandlerView(APIView):
    def get(self, request):
        global data
        auth_code = request.GET.get('code')
        state = request.GET.get('state')
        
        if auth_code and state:
            token_url = 'https://oauth2.googleapis.com/token'
            redirect_uri = 'http://ec2-3-109-124-174.ap-south-1.compute.amazonaws.com/oauth/'

            params = {
                'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'code': auth_code,
            }

            response = requests.post(token_url, data=params)
            data=json.loads(response.text)
            if 'access_token' in data:
                access_token = data['access_token']
                user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }
                response = requests.get(user_info_url, headers=headers)
                 
                data= json.loads(response.text)

                jwt_data=data
                token=jwt.encode(jwt_data,settings.SECRET_KEY,algorithm='HS256')
                response=HttpResponseRedirect('/register/')
                response.set_cookie('jwt_token',token)
                return response
        else:
            return Response({'error': 'Something went wrong'})

class RegisterView(APIView):
    def get(self,request):
        if request.COOKIES.get('jwt_token'):
            token=request.COOKIES.get('jwt_token')
            data=jwt.decode(token,settings.SECRET_KEY,algorithms=['HS256'])
        else:
            return Response({'message':'user not authenticated'})
        if LeaderModle.objects.filter(email=data['email']).exists():
            if LeaderModle.objects.get(email=data['email']).is_paid:
                return HttpResponseRedirect('/dashboard/')
            elif TeamModle.objects.filter(Leader=LeaderModle.objects.get(email=data['email'])).exists():
                return HttpResponseRedirect('/dashboard/')
            else:
                return render(request,'oauth/register.html',context={'data':data})
        else:
            LeaderModle.objects.create(
                email=data['email'],
                first_name=data['given_name'],
                last_name=data['family_name'],
                full_name=data['name'],
                picture_url=data['picture'],
            )
            
            return render(request,'oauth/register.html',context={'data':data})
    def post(self,request):
        if request.COOKIES.get('jwt_token'):
            token=request.COOKIES.get('jwt_token')
            data=jwt.decode(token,settings.SECRET_KEY,algorithms=['HS256'])
        else:
            return Response({'message':'user not authenticated'})
        team_data=request.data
        try:
            TeamModle.objects.create(
                team_name=team_data['team_name'],
                Leader=LeaderModle.objects.get(email=data['email']),
                team_member1_name=team_data['member1'],
                team_member2_name=team_data['member2'],
                team_member1_email=team_data['email1'],
                team_member2_email=team_data['email2'],
            )
        except:
            return Response({"message":"same member can not be in 2 teams at the same time"})
        subject='Registration Successful'
        message=f'Hi {LeaderModle.objects.get(email=data["email"]).full_name},\n\nYou are one step behind the Registration.\n\nKindly Proceed with the payment of Amount INR 20 to proceed with the Registration\n \n\nRegards,\nTeam Blockverse\n\n'
        email_from='professor00333@gmail.com'
        email_to=[LeaderModle.objects.get(email=data['email']).email]
        send_mail(subject,message,email_from,email_to)
        return HttpResponseRedirect('/dashboard/')

class DashBoardView(APIView):
    def get(self,request):
        if request.COOKIES.get('jwt_token'):
            token=request.COOKIES.get('jwt_token')
            data=jwt.decode(token,settings.SECRET_KEY,algorithms=['HS256'])
        else:
            return Response({'message':'user not authenticated'})
        if LeaderModle.objects.filter(email=data['email']).exists()==False:
            return HttpResponseRedirect('/register/')
        if TeamModle.objects.filter(Leader=LeaderModle.objects.get(email=data['email'])).exists()==False:
            return HttpResponseRedirect('/register/')

        if LeaderModle.objects.filter(email=data['email']).exists():
            Leader=LeaderModle.objects.get(email=data['email'])
            teams=TeamModle.objects.filter(Leader=Leader)
            return render(request,'oauth/dashboard.html',context={'teams':teams,
                                                                  'Leader':Leader})
        else:
            return Response({'message':'user does not exists'})
        
class PaymentView(APIView):
    def get(self,request):
        
        if request.COOKIES.get('jwt_token'):
            token=request.COOKIES.get('jwt_token')
            data=jwt.decode(token,settings.SECRET_KEY,algorithms=['HS256'])
        else:
            return Response({'message':'user not authenticated'})
        if TeamModle.objects.filter(Leader=LeaderModle.objects.get(email=data['email'])).exists()==False:
            return HttpResponseRedirect('/register/')
        if LeaderModle.objects.get(email=data['email']).is_paid:
            return HttpResponseRedirect('/dashboard/')
        key=settings.RAZORPAY_API_KEY
        secret=settings.RAZORPAY_API_SECRET
        razorpay_client=razorpay.Client(auth=(key,secret))
        currency='INR'
        amount=2000
        razorpay_order=razorpay_client.order.create({
            'amount':amount,
            'currency':currency,
            'payment_capture':0
        })
        razorpay_order_id = razorpay_order['id']
        callback_url = '/payment/callback/'
        context = {}
        context['razorpay_order_id'] = razorpay_order_id
        context['razorpay_merchant_key'] = key
        context['razorpay_amount'] = amount
        context['currency'] = currency
        context['callback_url'] = callback_url
 
        return render(request, 'oauth/payment.html', context=context)
    
class PaymentCallBackView(APIView):
    def post(self,request):
        key=settings.RAZORPAY_API_KEY
        secret=settings.RAZORPAY_API_SECRET
        razorpay_client=razorpay.Client(auth=(key,secret))
        if request.COOKIES.get('jwt_token'):
            token=request.COOKIES.get('jwt_token')
            data=jwt.decode(token,settings.SECRET_KEY,algorithms=['HS256'])
        else:
            return Response({'message':'user not authenticated'})
        if TeamModle.objects.filter(Leader=LeaderModle.objects.get(email=data['email'])).exists()==False:
            return HttpResponseRedirect('/register/')
        if LeaderModle.objects.get(email=data['email']).is_paid:
            return HttpResponseRedirect('/dashboard/')
        try:
           
            # get the required parameters from post request.
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
 
            # verify the payment signature.
            result = razorpay_client.utility.verify_payment_signature(
                params_dict)
            if result is not None:
                amount = 2000 
                try:
 
                    # capture the payemt
                    razorpay_client.payment.capture(payment_id, amount)
                    user=LeaderModle.objects.get(email=data['email'])
                    user.is_paid=True
                    user.save()
                    subject='Payment Successful'
                    message=f'Hi {user.full_name},\n\nYour payment of Rs. 20 has been received successfully.\n \n\nRegards,\nTeam Blockverse\n\n'
                    email_from='professor00333@gmail.com'
                    email_to=[user.email]
                    send_mail(subject,message,email_from,email_to)
                    return HttpResponseRedirect('/dashboard/')
                except:
 
                    # if there is an error while capturing payment.
                    return Response({'message':'payment failed'})
            else:
 
                # if signature verification fails.
                return Response({'message':'payment failed'})
        except:
 
            # if we don't find the required parameters in POST data
            return Response({'message':'payment failed'})


class LogoutView(APIView):
    def get(self,request):
        response=HttpResponseRedirect('/')
        response.delete_cookie('jwt_token')
        return response
