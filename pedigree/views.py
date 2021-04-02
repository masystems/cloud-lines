from django.shortcuts import render, HttpResponse, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.decorators.cache import never_cache
from django.utils.text import slugify
from django.core import serializers
from io import BytesIO
from django.template.loader import get_template
from django.views.generic import View
from xhtml2pdf import pisa
from .models import Pedigree, PedigreeImage
from breed.models import Breed
from breeder.models import Breeder
from breeder.forms import BreederForm
from breed.forms import BreedForm
from breed_group.models import BreedGroup
from .forms import PedigreeForm, ImagesForm
from .functions import get_site_pedigree_column_headings
from django.db.models import Q
import re
import json
from account.views import is_editor, get_main_account
from approvals.models import Approval
import dateutil.parser


@login_required(login_url="/account/login")
def search(request):
    attached_service = get_main_account(request.user)
    columns, column_data = get_site_pedigree_column_headings(attached_service)
    pedigrees = Pedigree.objects.filter(account=attached_service).exclude(state='unapproved').values('id', *columns)[:500]
    return render(request, 'search.html', {'pedigrees': pedigrees,
                                           'columns': columns,
                                           'column_data': column_data})


class PedigreeBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['attached_service'] = get_main_account(self.request.user)

        context['lvl1'] = Pedigree.objects.get(account=context['attached_service'], id=self.kwargs['pedigree_id'])

        # get any children
        context['children'] = Pedigree.objects.filter(Q(parent_father=context['lvl1'], account=context['attached_service']) | Q(parent_mother=context['lvl1'], account=context['attached_service']))

        # get attached groups
        context['groups'] = BreedGroup.objects.filter(group_members=context['lvl1'].id)

        # get all pedigrees for typeahead fields
        context['pedigrees'] = Pedigree.objects.filter(account=context['attached_service']).exclude(state='unapproved')

        # get custom fields
        try:
            context['custom_fields'] = json.loads(context['lvl1'].custom_fields)
        except json.decoder.JSONDecodeError:
            context['custom_fields'] = {}
        except ObjectDoesNotExist:
            context['custom_fields'] = {}

        context = generate_hirearchy(context)

        return context


class ShowPedigree(PedigreeBase):
    template_name = 'pedigree.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        context = {}
        context['attached_service'] = get_main_account(request.user)
        context['lvl1'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], id=self.kwargs['pedigree_id'])
        context = generate_hirearchy(context)

        pdf_filename = "{date}-{name}{pedigree}-certificate".format(
            date=context['lvl1'].date_added.strftime('%Y-%m-%d'),
            name=slugify(context['lvl1'].name),
            pedigree=context['lvl1'].reg_no,
        )

        pdf = render_to_pdf('certificate.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "%s.pdf" % pdf_filename
            content = "attachment; filename=%s" % filename
            download = request.GET.get("download")
            if download:
                content = "attachment; filename=%s" % filename
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


def generate_hirearchy(context):
    # lvl 2
    # 1
    try:
        context['lvl2_1'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl1'].parent_father)
    except ObjectDoesNotExist:
        context['lvl2_1'] = ''


    # 2
    try:
        if context['lvl1'].parent_mother:
            context['lvl2_2'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl1'].parent_mother)
        elif context['lvl1'].breed_group:
            context['lvl2_2_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl1'].breed_group)
    except:
        context['lvl2_2'] = ''

    # lvl 3
    # 1
    try:
        context['lvl3_1'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'],
                                                                             reg_no=context['lvl2_1'].parent_father)
    except :
        context['lvl3_1'] = ''
    # try:
    #     if context['lvl2_1'].parent_father:
    #         context['lvl3_1'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl2_1'].parent_father)
    # except KeyError:
    #     try:
    #         if context['lvl2_2_grp']:
    #             for pedigree in context['lvl2_2_grp'].group_members.all():
    #                 if pedigree.sex == 'male':
    #                     context['lvl3_1'] = pedigree
    #         else:
    #             context['lvl3_1'] = ''
    #     except KeyError:
    #         context['lvl3_1'] = ''
    # except ObjectDoesNotExist:
    #     context['lvl3_1'] = ''

    # 2
    try:
        if context['lvl2_1'].parent_mother:
            context['lvl3_2'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl2_1'].parent_mother)
        elif context['lvl2_1'].breed_group:
            context['lvl3_2_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl2_1'].breed_group)
    except:
        context['lvl3_2'] = ''

    # 3
    try:
        context['lvl3_3'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl2_2'].parent_father)
    except:
        context['lvl3_3'] = ''

    # 4
    try:
        if context['lvl2_2'].parent_mother:
            context['lvl3_4'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl2_2'].parent_mother)
        elif context['lvl2_2'].breed_group:
            context['lvl3_4_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl2_2'].breed_group)
    except:
        context['lvl3_4'] = ''

    # lvl 4
    # 1
    try:
        context['lvl4_1'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_1'].parent_father)
    except:
        context['lvl4_1'] = ''

    # 2
    try:
        if context['lvl3_1'].parent_mother:
            context['lvl4_2'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_1'].parent_mother)
        elif context['lvl3_1'].breed_group:
            context['lvl4_2_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl3_1'].breed_group)
    except:
        context['lvl4_1'] = ''

    # 3
    try:
        context['lvl4_3'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_2'].parent_father)
    except:
        context['lvl4_3'] = ''

    # 4
    try:
        if context['lvl3_2'].parent_mother:
            context['lvl4_4'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_2'].parent_mother)
        elif context['lvl3_2'].breed_group:
            context['lvl4_4_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl3_2'].breed_group)
    except:
        context['lvl4_4'] = ''

    # 5
    try:
        context['lvl4_5'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_3'].parent_father)
    except:
        context['lvl4_5'] = ''

    # 6
    try:
        if context['lvl3_3'].parent_mother:
            context['lvl4_6'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_3'].parent_mother)
        elif context['lvl3_3'].breed_group:
            context['lvl4_6_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl3_3'].breed_group)
    except:
        context['lvl4_6'] = ''

    # 7
    try:
        context['lvl4_7'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_4'].parent_father)
    except:
        context['lvl4_7'] = ''

    # 8
    try:
        if context['lvl3_4'].parent_mother:
            context['lvl4_8'] = Pedigree.objects.exclude(state='unapproved').get(account=context['attached_service'], reg_no=context['lvl3_4'].parent_mother)
        elif context['lvl3_4'].breed_group:
            context['lvl4_8_grp'] = BreedGroup.objects.get(account=context['attached_service'], group_name=context['lvl3_4'].breed_group)
    except:
        context['lvl4_8'] = ''

    return context


@login_required(login_url="/account/login")
def search_results(request):
    if request.POST:
        attached_service = get_main_account(request.user)
        search_string = request.POST['search']

        columns, column_data = get_site_pedigree_column_headings(attached_service)

        # lvl 1
        try:
            pedigrees = Pedigree.objects.filter(Q(account=attached_service,
                                                reg_no__icontains=search_string.upper()) | Q(account=attached_service,
                                                                      name__icontains=search_string)).exclude(state='unapproved').values('id', *columns)[:500]

        except ObjectDoesNotExist:
            breeders = Breeder.objects
            error = "No pedigrees found using: "
            return render(request, 'search.html', {'breeders': breeders,
                                                   'error': error,
                                                   'search_string': search_string})

        if len(pedigrees) > 1:
            return render(request, 'multiple_results.html', {'search_string': search_string,
                                                             'pedigrees': pedigrees,
                                                             'columns': columns,
                                                             'column_data': column_data})
        else:
            try:
                lvl1 = Pedigree.objects.exclude(state='unapproved').get(Q(account=attached_service,
                                                                          reg_no__icontains=search_string.upper()) | Q(account=attached_service,
                                                                                                                      name__icontains=search_string))
            except ObjectDoesNotExist:
                breeders = Breeder.objects
                error = "No pedigrees found using: "
                return render(request, 'search.html', {'breeders': breeders,
                                                       'error': error,
                                                       'search_string': search_string,
                                                       'columns': columns,
                                                       'column_data': column_data})

        return redirect('pedigree', pedigree_id=lvl1.id)


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
@never_cache
def new_pedigree_form(request):
    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    pre_checks = True
    attached_service = get_main_account(request.user)
    try:
        custom_fields = json.loads(attached_service.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}

    if request.method == 'POST':
        # check whether it's valid:
        if Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['reg_no'].value().strip()).exists():
            pedigree_form.add_error('reg_no', 'Selected reg number already exists')
            pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['breeder'].value()).exists() and pedigree_form['breeder'].value() not in ['Breeder', '', 'None', None]:
            pedigree_form.add_error('breeder', 'Selected breeder does not exist')
            pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['current_owner'].value()).exists() and pedigree_form['current_owner'].value() not in ['Current Owner', '', 'None', None]:
            pedigree_form.add_error('current_owner', 'Selected owner does not exist')
            pre_checks = False
        try:
            if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['mother'].value().strip()).exists() and pedigree_form['mother'].value().strip() not in ['Mother', '', 'None', None]:
                pedigree_form.add_error('mother', 'Selected mother does not exist')
                pre_checks = False
        except AttributeError:
            # ends up here if a breed group is added, so pedigree_form['mother'] doesn't exist in the post request
            pass
        if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['father'].value().strip()).exists() and pedigree_form['father'].value() not in ['Father', '', 'None', None]:
            pedigree_form.add_error('father', 'Selected father does not exist')
            pre_checks = False
        if not BreedGroup.objects.filter(account=attached_service, group_name=pedigree_form['breed_group'].value()).exists() and pedigree_form['breed_group'].value() not in ['Group pedigree was born from', '', 'None', None]:
            pedigree_form.add_error('breed_group', 'Selected breed group does not exist')
            pre_checks = False
        if not Breed.objects.filter(account=attached_service, breed_name=pedigree_form['breed'].value()).exists() and pedigree_form['breed'].value() not in ['Breed', '', 'None', None]:
            pedigree_form.add_error('breed', 'Selected breed does not exist')
            pre_checks = False

        if pedigree_form.is_valid() and pre_checks:
            new_pedigree = Pedigree()
            new_pedigree.creator = request.user
            try:
                new_pedigree.breeder = Breeder.objects.get(account=attached_service, breeding_prefix=pedigree_form['breeder'].value())
            except ObjectDoesNotExist:
                pass
            try:
                new_pedigree.current_owner = Breeder.objects.get(account=attached_service, breeding_prefix=pedigree_form['current_owner'].value())
            except ObjectDoesNotExist:
                pass
            new_pedigree.reg_no = pedigree_form['reg_no'].value().strip()
            new_pedigree.tag_no = pedigree_form['tag_no'].value().strip()
            new_pedigree.name = pedigree_form['name'].value()
            try:
                new_pedigree.date_of_registration = pedigree_form['date_of_registration'].value() or None
            except:
                pass
            try:
                new_pedigree.dob = pedigree_form['date_of_birth'].value() or None
            except:
                pass
            new_pedigree.status = pedigree_form['status'].value()
            new_pedigree.sex = pedigree_form['sex'].value()
            new_pedigree.born_as = pedigree_form['born_as'].value()
            try:
                new_pedigree.dod = pedigree_form['date_of_death'].value() or None
            except:
                pass

            ### mother ###
            try:
                new_pedigree.parent_mother = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['mother'].value().strip())

            except (ObjectDoesNotExist, AttributeError):
                new_pedigree.breed_group = pedigree_form['breed_group'].value()

            try:
                new_pedigree.parent_mother_notes = pedigree_form['mother_notes'].value() or ''
            except:
                pass

            ### father ###
            try:
                new_pedigree.parent_father = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['father'].value().strip())
            except ObjectDoesNotExist:
                pass
            try:
                new_pedigree.parent_father_notes = pedigree_form['father_notes'].value() or ''
            except:
                pass

            new_pedigree.description = pedigree_form['description'].value()
            new_pedigree.account = attached_service

            breed = Breed.objects.get(account=attached_service, breed_name=request.POST.get('breed'))
            new_pedigree.breed = breed

            try:
                custom_fields = json.loads(attached_service.custom_fields)

                for id, field in custom_fields.items():
                    custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])
            except json.decoder.JSONDecodeError:
                pass

            new_pedigree.custom_fields = json.dumps(custom_fields)

            if request.user in attached_service.contributors.all():
                new_pedigree.state = 'unapproved'
                new_pedigree.save()
                create_approval(request, new_pedigree, attached_service, state='unapproved', type='new')

            else:
                new_pedigree.save()


            # for key, file in request.FILES.items():
            #     upload = PedigreeImage(account=attached_service, image=file, reg_no=new_pedigree)
            #     upload.save()


            new_pedigree.save()
            return redirect('pedigree', new_pedigree.id)
    else:
        pedigree_form = PedigreeForm()

    # get next available reg number
    try:
        latest_added = Pedigree.objects.filter(account=attached_service).latest('reg_no')
        latest_reg = latest_added.reg_no
        reg_ints_re = re.search("[0-9]+", latest_reg)
        suggested_reg = latest_reg.replace(str(reg_ints_re.group(0)), str(int(reg_ints_re.group(0))+1).zfill(len(reg_ints_re.group(0))))
    except Pedigree.DoesNotExist:
        suggested_reg = 'REG123456'

    return render(request, 'new_pedigree_form_base.html', {'pedigree_form': pedigree_form,
                                                           'pedigrees': Pedigree.objects.filter(account=attached_service),
                                                           'breeders': Breeder.objects.filter(account=attached_service),
                                                           'breeds': Breed.objects.filter(account=attached_service),
                                                           'breed_groups': BreedGroup.objects.filter(account=attached_service),
                                                           'custom_fields': custom_fields,
                                                           'breeder_form': BreederForm(),
                                                           'breed_form': BreedForm(),
                                                           'suggested_reg': suggested_reg})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
@never_cache
def edit_pedigree_form(request, id):
    attached_service = get_main_account(request.user)
    pedigree = Pedigree.objects.get(account=attached_service, id__exact=int(id))

    # if state is edited make sure to show edited information
    if pedigree.state == 'edited':
        approval = Approval.objects.get(pedigree=pedigree)
        for obj in serializers.deserialize("yaml", approval.data):
            obj.object.state = 'edited'
            pedigree = obj.object

    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    image_form = ImagesForm(request.POST or None, request.FILES or None)
    pre_checks = True

    try:
        # get custom fields
        custom_fields = json.loads(pedigree.custom_fields)
    except json.decoder.JSONDecodeError:
        try:
            # get custom fields template
            custom_fields = json.loads(attached_service.custom_fields)
        except json.decoder.JSONDecodeError:
            custom_fields = {}
    except ObjectDoesNotExist:
        custom_fields = {}

    if request.method == 'POST':
        if 'delete' in request.POST:
            if request.user in attached_service.contributors.all():
                # contributors are not allowed to delete pedigrees!
                pass
            else:
                pedigree.delete()
                # delete any existed approvals
                approvals = Approval.objects.filter(pedigree=pedigree)
                for approval in approvals:
                    approval.delete()
            return redirect('pedigree_search')

        # check whether it's valid:
        if pedigree_form['reg_no'].value().strip() != pedigree.reg_no:
            if Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['reg_no'].value().strip()).exists():
                pedigree_form.add_error('reg_no', 'Selected reg number already exists')
                pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['breeder'].value()).exists() and pedigree_form['breeder'].value() not in ['Breeder', '', 'None', None]:
            pedigree_form.add_error('breeder', 'Selected breeder does not exist')
            pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['current_owner'].value()).exists() and pedigree_form['current_owner'].value() not in ['Current Owner', '', 'None', None]:
            pedigree_form.add_error('current_owner', 'Selected owner does not exist')
            pre_checks = False
        try:
            if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['mother'].value().strip()).exists() and pedigree_form['mother'].value() not in ['Mother', '', 'None', None]:
                pedigree_form.add_error('mother', 'Selected mother does not exist')
                pre_checks = False
        except AttributeError:
            # ends up here if a breed group is added, so pedigree_form['mother'] doesn't exist in the post request
            pass
        if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['father'].value().strip()).exists() and pedigree_form['father'].value() not in ['Father', '', 'None', None]:
            pedigree_form.add_error('father', 'Selected father does not exist')
            pre_checks = False
        if not BreedGroup.objects.filter(account=attached_service, group_name=pedigree_form['breed_group'].value()).exists() and pedigree_form['breed_group'].value() not in ['Group pedigree was born from', '', 'None', None]:
            pedigree_form.add_error('breed_group', 'Selected breed group does not exist')
            pre_checks = False
        if not Breed.objects.filter(account=attached_service, breed_name=pedigree_form['breed'].value()).exists() and pedigree_form['breed'].value() not in ['Breed', '', 'None', None]:
            pedigree_form.add_error('breed', 'Selected breed does not exist')
            pre_checks = False

        if pedigree_form.is_valid() and image_form.is_valid() and pre_checks:
            try:
                if pedigree_form['breeder'].value() == '':
                    pedigree.breeder = None
                else:
                    pedigree.breeder = Breeder.objects.get(account=attached_service, breeding_prefix=pedigree_form['breeder'].value())
            except ObjectDoesNotExist:
                pedigree.breeder = None

            try:
                if pedigree_form['current_owner'] == '':
                    pedigree.current_owner = None
                else:
                    pedigree.current_owner = Breeder.objects.get(account=attached_service, breeding_prefix=pedigree_form['current_owner'].value())
            except ObjectDoesNotExist:
                pass

            pedigree.reg_no = pedigree_form['reg_no'].value().strip()
            pedigree.tag_no = pedigree_form['tag_no'].value().strip() or ""
            pedigree.name = pedigree_form['name'].value()

            try:
                pedigree.date_of_registration = pedigree_form['date_of_registration'].value() or None
            except:
                pass

            try:
                pedigree.dob = pedigree_form['date_of_birth'].value() or None
            except:
                pass
            pedigree.status = pedigree_form['status'].value()
            pedigree.sex = pedigree_form['sex'].value()
            pedigree.born_as = pedigree_form['born_as'].value()

            try:
                pedigree.dod = pedigree_form['date_of_death'].value() or None
            except:
                pass

            try:
                if pedigree_form['mother'].value() in ('', None):
                    pedigree.parent_mother = None
                else:
                    try:
                        pedigree.parent_mother = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['mother'].value().strip())
                    except (ObjectDoesNotExist, AttributeError):
                        pedigree.breed_group = pedigree_form['breed_group'].value()

            except:
                pass

            try:
                pedigree.parent_mother_notes = pedigree_form['mother_notes'].value() or ''
            except:
                pass

            try:
                if pedigree_form['father'].value() in ('', None):
                    pedigree.parent_father = None
                else:
                    pedigree.parent_father = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['father'].value().strip())
            except ObjectDoesNotExist:
                pass
            try:
                pedigree.parent_father_notes = pedigree_form['father_notes'].value() or ''
            except:
                pass

            try:
                pedigree.breed_group = pedigree_form['breed_group'].value()
            except:
                pass

            pedigree.description = pedigree_form['description'].value()

            pedigree.breed = Breed.objects.get(account=attached_service, breed_name=pedigree_form['breed'].value())

            try:
                custom_fields = json.loads(pedigree.custom_fields)
            except json.decoder.JSONDecodeError:
                custom_fields = {}
            for id, field in custom_fields.items():
                custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])

            pedigree.custom_fields = json.dumps(custom_fields)

            if request.user in attached_service.contributors.all():
                if not Approval.objects.filter(pedigree=pedigree).exists():
                    create_approval(request, pedigree, attached_service, state='edited', type='edit')
            else:
                # delete any existed approvals
                approvals = Approval.objects.filter(pedigree=pedigree)
                for approval in approvals:
                    approval.delete()
                pedigree.state = 'approved'
                pedigree.save()

            for image in PedigreeImage.objects.filter(account=attached_service):
                img = request.POST.get('{}-{}'.format(pedigree.id, image.id))
                if img:
                    if request.user in attached_service.contributors.all():
                        image.state = 'edited'
                        image.save()
                    else:
                        image.delete()

            return redirect('pedigree', pedigree.id)
    else:
        pedigree_form = PedigreeForm()

    return render(request, 'edit_pedigree_form.html', {'pedigree_form': pedigree_form,
                                                       'image_form': image_form,
                                                       'pedigree': pedigree,
                                                       'pedigrees': Pedigree.objects.filter(account=attached_service),
                                                       'breeders': Breeder.objects.filter(account=attached_service),
                                                       'breeds': Breed.objects.filter(account=attached_service),
                                                       'breed_groups': BreedGroup.objects.filter(account=attached_service),
                                                       'custom_fields': custom_fields})


def image_upload(request, id):
    attached_service = get_main_account(request.user)
    pedigree = Pedigree.objects.get(account=attached_service, id__exact=int(id))

    image = request.FILES['file[0]']
    from PIL import Image
    from django.core.files.base import ContentFile
    import pyheif
    from io import BytesIO
    from os import path

    filename, file_extension = path.splitext(str(request.FILES['file[0]']))
    if file_extension == ".HEIC":
        img_io = BytesIO()
        heif_file = pyheif.read(request.FILES['file[0]'])
        image = Image.frombytes(mode=heif_file.mode, size=heif_file.size, data=heif_file.data)
        image.save(img_io, format='JPEG', quality=100)
        image = ContentFile(img_io.getvalue(), f"{filename}.jpeg")

    if request.user in attached_service.contributors.all():
        upload = PedigreeImage(account=attached_service, state='unapproved', image=image, reg_no=pedigree)
        upload.save()
    else:
        upload = PedigreeImage(account=attached_service, image=image, reg_no=pedigree)
        upload.save()
    return HttpResponse('')


def add_existing(request, pedigree_id):
    attached_service = get_main_account(request.user)
    pedigree = Pedigree.objects.get(account=attached_service, id=pedigree_id)

    if request.method == 'POST':
        child_reg = request.POST.get('reg_no')
        child = Pedigree.objects.get(account=attached_service, reg_no=child_reg)
        if pedigree.sex == 'male':
            child.parent_father = pedigree
        elif pedigree.sex == 'female':
            child.parent_mother = pedigree

        if request.user in attached_service.contributors.all():
            create_approval(request, child, attached_service, state='edited', type='edit')
        else:
            child.save()

    return redirect('pedigree', pedigree_id)


def add_existing_parent(request, pedigree_id):
    attached_service = get_main_account(request.user)
    pedigree = Pedigree.objects.get(account=attached_service, id=pedigree_id)

    if request.method == 'POST':
        parent_reg = request.POST.get('reg_no')
        parent = Pedigree.objects.get(account=attached_service, reg_no=parent_reg)
        if parent.sex == 'male':
            pedigree.parent_father = parent
        elif parent.sex == 'female':
            pedigree.parent_mother = parent

        if request.user in attached_service.contributors.all():
            create_approval(request, pedigree, attached_service, state='edited', type='edit')
        else:
            pedigree.save()

    return redirect('pedigree', pedigree_id)


def create_approval(request, pedigree, attached_service, state, type):
    if state == 'edited':
        Pedigree.objects.filter(id=pedigree.id).update(state=state)

    try:
        pedigree.dob = dateutil.parser.parse(pedigree.dob)
    except TypeError:
        pass
    try:
        pedigree.dod = dateutil.parser.parse(pedigree.dod)
    except TypeError:
        pass
    try:
        pedigree.date_of_registration = dateutil.parser.parse(pedigree.date_of_registration)
    except TypeError:
        pass
    data = serializers.serialize('yaml', [pedigree])
    Approval.objects.create(account=attached_service,
                            user=request.user,
                            type=type,
                            pedigree=pedigree,
                            data=data)
