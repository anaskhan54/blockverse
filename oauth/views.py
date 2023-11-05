from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import urllib
from django.http.response import HttpResponseRedirect
import requests,json,razorpay,jwt
from .models import LeaderModle,TeamModle
# Create your views here.
data={'email':''}

class LandingPageView(APIView):
    def get(self,request):
        return render(request,'oauth/landing_page.htmml')
class GoogleOauthView(APIView):
    def get(self,request):
        auth_url='https://accounts.google.com/o/oauth2/v2/auth'
        redirect_uri = 'http://gauth-blockverse.com:8000/oauth/'
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
            redirect_uri = 'http://gauth-blockverse.com:8000/oauth/'

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

                jwt_data={'email':data['email']}
                token=jwt.encode(jwt_data,settings.SECRET_KEY,algorithm='HS256')
                response=HttpResponseRedirect('/register/')
                response.set_cookie('jwt_token',token)
                return response
        else:
            return Response({'error': 'Something went wrong'})

class RegisterView(APIView):
    def get(self,request):
        global data
        if LeaderModle.objects.filter(email=data['email']).exists():
            return Response({'message':'user already exists'})
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
        global data
        team_data=request.data
        TeamModle.objects.create(
            team_name=team_data['team_name'],
            Leader=LeaderModle.objects.get(email=data['email']),
            team_member1_name=team_data['member1'],
            team_member2_name=team_data['member2'],
            team_member1_email=team_data['email1'],
            team_member2_email=team_data['email2'],
        )
        return HttpResponseRedirect('/dashboard/')

class DashBoardView(APIView):
    def get(self,request):
        global data
        if LeaderModle.objects.filter(email=data['email']).exists():
            Leader=LeaderModle.objects.get(email=data['email'])
            teams=TeamModle.objects.filter(Leader=Leader)
            return render(request,'oauth/dashboard.html',context={'teams':teams,
                                                                  'Leader':Leader})
        else:
            return Response({'message':'user does not exists'})
        
class PaymentView(APIView):
    def get(self,request):
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
        global data
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



