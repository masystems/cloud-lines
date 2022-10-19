from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from django.conf import settings
from account.views import is_editor, get_main_account, send_mail, get_stripe_secret_key
from account.models import AttachedBolton
from urllib.parse import urljoin
import requests
import stripe
from json.decoder import JSONDecodeError
from json import dumps


# Create your views here.
class MembershipBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['attached_service'] = get_main_account(self.request.user)

        return context


class Membership(MembershipBase):
    template_name = 'membership/membership.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def change_bolton_state(request, bolton_id, req_state):
    # security checks
    # ensure user is superadmin or owner
    attached_service = get_main_account(request.user)
    if request.user.id is not attached_service.user.user.id:
        return redirect('settings')
    # ensure account is != small tier

    # get bolton from API
    try:
        bolton = requests.get(urljoin(settings.BOLTON_API_URL, str(bolton_id))).json()
    except:
        return redirect('settings')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # if activation request
    if req_state == "enable":
        # ensure bolton is not already active
        if attached_service.boltons.filter(bolton=bolton['id'], active=True).exists():
            return redirect('settings')
        else:
            stripe.api_key = get_stripe_secret_key(request)
            if request.META['HTTP_HOST'] in settings.TEST_STRIPE_DOMAINS:
                price = bolton['test_stripe_price_id']
            else:
                price = bolton['stripe_price_id']

            new_bolton = AttachedBolton.objects.create(bolton=bolton['id'],
                                          active=False)

            # create session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        "price": price,
                        "quantity": 1
                    }
                ],
                mode='subscription',
                customer=attached_service.user.stripe_id,
                success_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/birth_notification/enable_bn/{new_bolton.id}",
                cancel_url=f"{settings.HTTP_PROTOCOL}://{request.META['HTTP_HOST']}/account/settings",
            )
            new_bolton.stripe_payment_token=session['id']
            new_bolton.save()
            return redirect(session.url, code=303)

    # if deactivation request
    elif req_state == "disable":
        attached_bolton = AttachedBolton.objects.get(bolton=bolton['id'], active=True)
        # ensure bolton is deactivated
        attached_bolton.active = False
        attached_bolton.save()

        # cancel subscription in strip
        stripe.Subscription.delete(attached_bolton.stripe_sub_id)
    # disable bolton
    return redirect('settings')


@login_required(login_url="/accounts/login")
def validate_card(request, attached_service):
    # get strip secret key

    if request.user.is_superuser:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    stripe_id = attached_service.user.stripe_id

    # add payment token to user
    if not stripe_id:
        return {'result': 'fail',
                'feedback': "There has been a problem with this Stripe payment, you have not been charged, please try again. If this problem persists, email contact@masys.co.uk"}
    try:
        payment_method = stripe.Customer.modify(
            stripe_id,
            source=request.POST.get('token[id]')
        )
        return {'result': 'success',
                'feedback': payment_method}

    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}

    except Exception as e:
        # Something else happened, completely unrelated to Stripe
        feedback = send_payment_error(e)
        return {'result': 'fail',
                'feedback': feedback}


def send_payment_error(error):
    body = error.json_body
    err = body.get('error', {})

    feedback = "<strong>Status is:</strong> %s" % error.http_status
    feedback += "<br><strong>Type is:</strong> %s" % err.get('type')
    feedback += "<br><strong>Code is:</strong> %s" % err.get('code')
    feedback += "<br><strong>Message is:</strong> <span class='text-danger'>%s</span>" % err.get('message')
    return feedback