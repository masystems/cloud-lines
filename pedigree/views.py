from django.shortcuts import render, HttpResponse, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.decorators.cache import never_cache
from django.utils.text import slugify
from io import BytesIO
from django.template.loader import get_template
from django.views.generic import View
from xhtml2pdf import pisa
from .models import Pedigree, PedigreeAttributes, PedigreeImage
from breed.models import Breed
from breeder.models import Breeder
from breeder.forms import BreederForm
from breed.forms import BreedForm
from breed_group.models import BreedGroup
from .forms import PedigreeForm, AttributeForm, ImagesForm
from django.db.models import Q

import json
from account.views import is_editor, get_main_account


@login_required(login_url="/account/login")
def search(request):
    attached_service = get_main_account(request.user)
    pedigrees = Pedigree.objects.filter(account=attached_service)[0:1000]
    return render(request, 'search.html', {'pedigrees': pedigrees})


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
        context['pedigrees'] = Pedigree.objects.filter(account=context['attached_service'])

        # get custom fields
        try:
            context['custom_fields'] = json.loads(context['lvl1'].attribute.custom_fields)
        except json.decoder.JSONDecodeError:
            context['custom_fields'] = {}
        except ObjectDoesNotExist:
            context['custom_fields'] = {}

        context = generate_hirearchy(context)
        inbreeding_calc(context['lvl1'])

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
        context['lvl1'] = Pedigree.objects.get(account=context['attached_service'], id=self.kwargs['pedigree_id'])
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
            content = "attachment; filename='%s'" % filename
            download = request.GET.get("download")
            if download:
                content = "attachment; filename='%s'" % filename
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


def generate_hirearchy(context):
    # lvl 2
    # 1
    try:
        context['lvl2_1'] = Pedigree.objects.get(reg_no=context['lvl1'].parent_mother)
    except:
        context['lvl2_1'] = ''
    # 2
    try:
        context['lvl2_2'] = Pedigree.objects.get(reg_no=context['lvl1'].parent_father)
    except:
        context['lvl2_2'] = ''

    # lvl 3
    # 1
    try:
        context['lvl3_1'] = Pedigree.objects.get(reg_no=context['lvl2_1'].parent_mother)
    except:
        context['lvl3_1'] = ''

    # 2
    try:
        context['lvl3_2'] = Pedigree.objects.get(reg_no=context['lvl2_1'].parent_father)
    except:
        context['lvl3_2'] = ''

    # 3
    try:
        context['lvl3_3'] = Pedigree.objects.get(reg_no=context['lvl2_2'].parent_mother)
    except:
        context['lvl3_3'] = ''

    # 4
    try:
        context['lvl3_4'] = Pedigree.objects.get(reg_no=context['lvl2_2'].parent_father)
    except:
        context['lvl3_4'] = ''

    # lvl 4
    # 1
    try:
        context['lvl4_1'] = Pedigree.objects.get(reg_no=context['lvl3_1'].parent_mother)
    except:
        context['lvl4_1'] = ''

    # 2
    try:
        context['lvl4_2'] = Pedigree.objects.get(reg_no=context['lvl3_1'].parent_father)
    except:
        context['lvl4_2'] = ''

    # 3
    try:
        context['lvl4_3'] = Pedigree.objects.get(reg_no=context['lvl3_2'].parent_mother)
    except:
        context['lvl4_3'] = ''

    # 4
    try:
        context['lvl4_4'] = Pedigree.objects.get(reg_no=context['lvl3_2'].parent_father)
    except:
        context['lvl4_4'] = ''
    # 5
    try:
        context['lvl4_5'] = Pedigree.objects.get(reg_no=context['lvl3_3'].parent_mother)
    except:
        context['lvl4_5'] = ''

    # 6
    try:
        context['lvl4_6'] = Pedigree.objects.get(reg_no=context['lvl3_3'].parent_father)
    except:
        context['lvl4_6'] = ''

    # 7
    try:
        context['lvl4_7'] = Pedigree.objects.get(reg_no=context['lvl3_4'].parent_mother)
    except:
        context['lvl4_7'] = ''

    # 8
    try:
        context['lvl4_8'] = Pedigree.objects.get(reg_no=context['lvl3_4'].parent_father)
    except:
        context['lvl4_8'] = ''

    return context


@login_required(login_url="/account/login")
def search_results(request):
    if request.POST:
        attached_service = get_main_account(request.user)
        search_string = request.POST['search']

        # lvl 1
        try:
            results = Pedigree.objects.filter(Q(account=attached_service,
                                                reg_no__icontains=search_string.upper()) | Q(account=attached_service,
                                                                                             name__icontains=search_string))[0:1000]
        except ObjectDoesNotExist:
            breeders = Breeder.objects
            error = "No pedigrees found using: "
            return render(request, 'search.html', {'breeders': breeders,
                                                   'error': error,
                                                   'search_string': search_string})


        if len(results) > 1:
            return render(request, 'multiple_results.html', {'search_string': search_string,
                                                             'results': results})
        else:
            try:
                lvl1 = Pedigree.objects.get(Q(account=attached_service, reg_no__icontains=search_string.upper()) | Q(account=attached_service, name__icontains=search_string))
            except ObjectDoesNotExist:
                breeders = Breeder.objects
                error = "No pedigrees found using: "
                return render(request, 'search.html', {'breeders': breeders,
                                                       'error': error,
                                                       'search_string': search_string})

        return redirect('pedigree', pedigree_id=lvl1.id)


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
@never_cache
def new_pedigree_form(request):
    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    attributes_form = AttributeForm(request.POST or None, request.FILES or None)
    image_form = ImagesForm(request.POST or None, request.FILES or None)
    pre_checks = True
    attached_service = get_main_account(request.user)
    try:
        custom_fields = json.loads(attached_service.custom_fields)
    except json.decoder.JSONDecodeError:
        custom_fields = {}

    if request.method == 'POST':
        # check whether it's valid:
        if Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['reg_no'].value()).exists():
            pedigree_form.add_error('reg_no', 'Selected reg number already exists')
            pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['breeder'].value()).exists() and pedigree_form['breeder'].value() not in ['Breeder', '', 'None', None]:
            pedigree_form.add_error('breeder', 'Selected breeder does not exist')
            pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['current_owner'].value()).exists() and pedigree_form['current_owner'].value() not in ['Current Owner', '', 'None', None]:
            pedigree_form.add_error('current_owner', 'Selected owner does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['mother'].value()).exists() and pedigree_form['mother'].value() not in ['Mother', '', 'None', None]:
            pedigree_form.add_error('mother', 'Selected mother does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['father'].value()).exists() and pedigree_form['father'].value() not in ['Father', '', 'None', None]:
            pedigree_form.add_error('father', 'Selected father does not exist')
            pre_checks = False
        if not BreedGroup.objects.filter(account=attached_service, group_name=pedigree_form['breed_group'].value()).exists() and pedigree_form['breed_group'].value() not in ['Group pedigree was born from', '', 'None', None]:
            pedigree_form.add_error('breed_group', 'Selected breed group does not exist')
            pre_checks = False
        if not Breed.objects.filter(account=attached_service, breed_name=attributes_form['breed'].value()).exists() and attributes_form['breed'].value() not in ['Breed', '', 'None', None]:
            attributes_form.add_error('breed', 'Selected breed does not exist')
            pre_checks = False

        if pedigree_form.is_valid() and attributes_form.is_valid() and image_form.is_valid() and pre_checks:
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
            new_pedigree.reg_no = pedigree_form['reg_no'].value()
            new_pedigree.tag_no = pedigree_form['tag_no'].value()
            new_pedigree.name = pedigree_form['name'].value()
            try:
                new_pedigree.date_of_registration = pedigree_form['date_of_registration'].value() or None
            except:
                pass
            try:
                new_pedigree.dob = pedigree_form['date_of_birth'].value() or None
            except:
                pass
            new_pedigree.sex = pedigree_form['sex'].value()
            try:
                new_pedigree.dod = pedigree_form['date_of_death'].value() or None
            except:
                pass

            ### mother ###
            try:
                new_pedigree.parent_mother = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['mother'].value())
            except ObjectDoesNotExist:
                new_pedigree.breed_group = pedigree_form['breed_group'].value() or None
            try:
                new_pedigree.parent_mother_notes = pedigree_form['mother_notes'].value() or None
            except:
                pass

            ### father ###
            try:
                new_pedigree.parent_father = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['father'].value())
            except ObjectDoesNotExist:
                pass
            try:
                new_pedigree.parent_father_notes = pedigree_form['father_notes'].value() or None
            except:
                pass

            new_pedigree.description = pedigree_form['description'].value()
            new_pedigree.account = attached_service
            new_pedigree.save()

            new_pedigree_attributes = PedigreeAttributes()
            new_pedigree_attributes.reg_no = Pedigree.objects.get(account=attached_service, reg_no=new_pedigree.reg_no)

            breed = Breed.objects.get(account=attached_service, breed_name=request.POST.get('breed'))
            new_pedigree_attributes.breed = breed

            try:
                custom_fields = json.loads(attached_service.custom_fields)

                for id, field in custom_fields.items():
                    custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])
            except json.decoder.JSONDecodeError:
                pass

            new_pedigree_attributes.custom_fields = json.dumps(custom_fields)
            new_pedigree_attributes.save()

            files = request.FILES.getlist('upload_images')

            for file in files:
                upload = PedigreeImage(account=attached_service, image=file, reg_no=new_pedigree)
                upload.save()

            new_pedigree.save()
            return redirect('pedigree', new_pedigree.id)
    else:
        pedigree_form = PedigreeForm()

    return render(request, 'new_pedigree_form_base.html', {'pedigree_form': pedigree_form,
                                                           'attributes_form': attributes_form,
                                                           'image_form': image_form,
                                                           'pedigrees': Pedigree.objects.filter(account=attached_service),
                                                           'breeders': Breeder.objects.filter(account=attached_service),
                                                           'breeds': Breed.objects.filter(account=attached_service),
                                                           'breed_groups': BreedGroup.objects.filter(account=attached_service),
                                                           'custom_fields': custom_fields,
                                                           'breeder_form': BreederForm(),
                                                           'breed_form': BreedForm()})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
@never_cache
def edit_pedigree_form(request, id):
    attached_service = get_main_account(request.user)
    pedigree = Pedigree.objects.get(account=attached_service, id__exact=int(id))

    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    attributes_form = AttributeForm(request.POST or None, request.FILES or None)
    image_form = ImagesForm(request.POST or None, request.FILES or None)
    pre_checks = True

    try:
        # get custom fields
        custom_fields = json.loads(pedigree.attribute.custom_fields)
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
            pedigree.delete()
            return redirect('pedigree_search')

        # check whether it's valid:
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['breeder'].value()).exists() and pedigree_form['breeder'].value() not in ['Breeder', '', 'None', None]:
            pedigree_form.add_error('breeder', 'Selected breeder does not exist')
            pre_checks = False
        if not Breeder.objects.filter(account=attached_service, breeding_prefix=pedigree_form['current_owner'].value()).exists() and pedigree_form['current_owner'].value() not in ['Current Owner', '', 'None', None]:
            pedigree_form.add_error('current_owner', 'Selected owner does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['mother'].value()).exists() and pedigree_form['mother'].value() not in ['Mother', '', 'None', None]:
            pedigree_form.add_error('mother', 'Selected mother does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(account=attached_service, reg_no=pedigree_form['father'].value()).exists() and pedigree_form['father'].value() not in ['Father', '', 'None', None]:
            pedigree_form.add_error('father', 'Selected father does not exist')
            pre_checks = False
        if not BreedGroup.objects.filter(account=attached_service, group_name=pedigree_form['breed_group'].value()).exists() and pedigree_form['breed_group'].value() not in ['Group pedigree was born from', '', 'None', None]:
            pedigree_form.add_error('breed_group', 'Selected breed group does not exist')
            pre_checks = False
        if not Breed.objects.filter(account=attached_service, breed_name=attributes_form['breed'].value()).exists() and attributes_form['breed'].value() not in ['Breed', '', 'None', None]:
            attributes_form.add_error('breed', 'Selected breed does not exist')
            pre_checks = False

        if pedigree_form.is_valid() and attributes_form.is_valid() and image_form.is_valid() and pre_checks:
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

            pedigree.reg_no = pedigree_form['reg_no'].value()
            pedigree.tag_no = pedigree_form['tag_no'].value()
            pedigree.name = pedigree_form['name'].value()

            try:
                pedigree.date_of_registration = pedigree_form['date_of_registration'].value() or None
            except:
                pass

            try:
                pedigree.dob = pedigree_form['date_of_birth'].value() or None
            except:
                pass

            pedigree.sex = pedigree_form['sex'].value()

            try:
                pedigree.dod = pedigree_form['date_of_death'].value() or None
            except:
                pass

            try:
                if pedigree_form['mother'].value() == '':
                    pedigree.parent_mother = None
                else:
                    pedigree.parent_mother = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['mother'].value())
            except ObjectDoesNotExist:
                pedigree.breed_group = pedigree_form['breed_group'].value() or None
            try:
                pedigree.parent_mother_notes = pedigree_form['mother_notes'].value() or None
            except:
                pass

            try:
                if pedigree_form['father'].value() == '':
                    pedigree.parent_father = None
                else:
                    pedigree.parent_father = Pedigree.objects.get(account=attached_service, reg_no=pedigree_form['father'].value())
            except ObjectDoesNotExist:
                pass
            try:
                pedigree.parent_father_notes = pedigree_form['father_notes'].value() or None
            except:
                pass

            pedigree.breed_group = pedigree_form['breed_group'].value()

            pedigree.description = pedigree_form['description'].value()

            pedigree.save()

            pedigree_attributes, created = PedigreeAttributes.objects.get_or_create(reg_no=pedigree)

            pedigree_attributes.breed = Breed.objects.get(account=attached_service, breed_name=attributes_form['breed'].value())

            try:
                custom_fields = json.loads(pedigree_attributes.custom_fields)
            except json.decoder.JSONDecodeError:
                custom_fields = {}
            for id, field in custom_fields.items():
                custom_fields[id]['field_value'] = request.POST.get(custom_fields[id]['fieldName'])

            pedigree_attributes.custom_fields = json.dumps(custom_fields)

            files = request.FILES.getlist('upload_images')
            #fs = FileSystemStorage()

            for image in PedigreeImage.objects.filter(account=attached_service):
                img = request.POST.get('{}-{}'.format(pedigree.id, image.id))
                if img:
                    image.delete()

            for file in files:
                upload = PedigreeImage(account=attached_service, image=file, reg_no=pedigree)
                upload.save()

            pedigree.save()
            pedigree_attributes.save()

            return redirect('pedigree', pedigree.id)
    else:
        pedigree_form = PedigreeForm()

    return render(request, 'edit_pedigree_form.html', {'pedigree_form': pedigree_form,
                                                       'attributes_form': attributes_form,
                                                       'image_form': image_form,
                                                       'pedigree': pedigree,
                                                       'pedigrees': Pedigree.objects.filter(account=attached_service),
                                                       'breeders': Breeder.objects.filter(account=attached_service),
                                                       'breeds': Breed.objects.filter(account=attached_service),
                                                       'breed_groups': BreedGroup.objects.filter(account=attached_service),
                                                       'custom_fields': custom_fields})


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

        child.save()

    return redirect('pedigree', pedigree_id)


def inbreeding_calc(pedigree):
    pass
#     parents = []
#     unsorted_parents = [get_parents(pedigree)]
#     while True:
#         tmp_parents = unsorted_parents
#         for parent in tmp_parents:
#             parents.append(get_parents(parent))
#             tmp_parents = []
#
#
# def get_parents(pedigree):
#     try:
#         a = Pedigree.objects.get(id=pedigree.parent_mother.id)
#     except AttributeError:
#         a = None
#
#     try:
#         b = Pedigree.objects.get(id=pedigree.parent_father.id)
#     except AttributeError:
#         b = None
#
#     return a, b