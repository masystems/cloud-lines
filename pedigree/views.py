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
from datetime import datetime, timedelta
from .models import Pedigree, PedigreeAttributes, PedigreeImage
from breed.models import Breed
from breeder.models import Breeder
from breed_group.models import BreedGroup
from .forms import PedigreeForm, AttributeForm, ImagesForm
from django.db.models import Q
import csv
from account.models import SiteDetail


def is_editor(user):
    return user.groups.filter(name='editor').exists() or user.is_superuser


@login_required(login_url="/account/login")
def dashboard(request):

    editor = is_editor(request.user)
    total_pedigrees = Pedigree.objects.all().count()
    total_breeders = Breeder.objects.all().count()
    top_pedigrees = Pedigree.objects.all().order_by('-date_added')[:5]
    breed_groups = BreedGroup.objects.all().order_by('-date_added')[:5]
    top_breeders = Breeder.objects.all()

    current_month = datetime.now().month
    date = datetime.now()
    pedigree_chart = {}
    for month in range(0, 12):
        month_count = Pedigree.objects.filter(date_added__month=current_month-month).count()
        if month != 0:
            date = date.replace(day=1)
            date = date - timedelta(days=1)
        print(date.strftime("%B"))
        pedigree_chart[date.strftime("%Y-%m")] = {'pedigrees_added': month_count}

    breed_chart = {}
    for breed in Breed.objects.all():
        breed_chart[breed] = {'male': Pedigree.objects.filter(Q(attribute__breed__breed_name=breed) & Q(sex='male')).count(),
                               'female': Pedigree.objects.filter(Q(attribute__breed__breed_name=breed) & Q(sex='female')).count()}

    # breeders_totals = {}
    # for breeder in top_breeders:
    #     breeders_totals[breeder]['pedigree_count'] = Pedigree.objects.filter(breeder__prefix__exact=breeder).count()
    #     breeders_totals[breeder]['owned_count'] = Pedigree.objects.filter(current_owner__prefix__exact=breeder).count()

    return render(request, 'dashboard.html', {'total_pedigrees': total_pedigrees,
                                              'total_breeders': total_breeders,
                                              'top_pedigrees': top_pedigrees,
                                              'top_breeders': top_breeders,
                                              'breed_groups': breed_groups,
                                              'editor': editor,
                                              'breed_chart': breed_chart,
                                              'pedigree_chart': pedigree_chart})


@login_required(login_url="/account/login")
def search(request):
    editor = is_editor(request.user)
    pedigrees = Pedigree.objects.all()
    return render(request, 'search.html', {'pedigrees': pedigrees,
                                           'editor': editor})



class PedigreeBase(LoginRequiredMixin, TemplateView):
    login_url = '/account/login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context['editor'] = is_editor(self.request.user)
        except AttributeError:
            pass

        context['site_mode'] = SiteDetail.objects.all().first()

        context['lvl1'] = Pedigree.objects.get(id=self.kwargs['pedigree_id'])

        # get any children
        context['children'] = Pedigree.objects.filter(Q(parent_father=context['lvl1']) | Q(parent_mother=context['lvl1']))

        # get attached groups
        context['groups'] = BreedGroup.objects.filter(group_members=context['lvl1'].id)

        # get all pedigrees for typeahead fields
        context['pedigrees'] = Pedigree.objects.all()

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
        context['lvl1'] = Pedigree.objects.get(id=self.kwargs['pedigree_id'])
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
        context['lvl3_1'] = Pedigree.objects.get(name=context['lvl2_1'].parent_mother)
    except:
        context['lvl3_1'] = ''

    # 2
    try:
        context['lvl3_2'] = Pedigree.objects.get(name=context['lvl2_1'].parent_father)
    except:
        context['lvl3_2'] = ''

    # 3
    try:
        context['lvl3_3'] = Pedigree.objects.get(name=context['lvl2_2'].parent_mother)
    except:
        context['lvl3_3'] = ''

    # 4
    try:
        context['lvl3_4'] = Pedigree.objects.get(name=context['lvl2_2'].parent_father)
    except:
        context['lvl3_4'] = ''

    return context

@login_required(login_url="/account/login")
def search_results(request):
    if request.POST:
        editor = is_editor(request.user)
        search_string = request.POST['search']

        # lvl 1
        try:
            results = Pedigree.objects.filter(Q(reg_no__icontains=search_string.upper()) | Q(name__icontains=search_string))
        except ObjectDoesNotExist:
            breeders = Breeder.objects
            error = "No pedigrees found using: "
            return render(request, 'search.html', {'breeders': breeders,
                                                    'error': error,
                                                    'search_string': search_string,
                                                       'editor': editor})


        if len(results) > 1:
            return render(request, 'multiple_results.html', {'search_string': search_string,
                                                        'results': results,
                                                       'editor': editor})
        else:
            try:
                lvl1 = Pedigree.objects.get(Q(reg_no__icontains=search_string.upper()) | Q(name__icontains=search_string))
            except ObjectDoesNotExist:
                breeders = Breeder.objects
                error = "No pedigrees found using: "
                return render(request, 'search.html', {'breeders': breeders,
                                                       'error': error,
                                                       'search_string': search_string,
                                                       'editor': editor})

        return redirect('pedigree', pedigree_id=lvl1.id)


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
@never_cache
def new_pedigree_form(request):

    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    attributes_form = AttributeForm(request.POST or None, request.FILES or None)
    image_form = ImagesForm(request.POST or None, request.FILES or None)
    pre_checks = True

    if request.method == 'POST':
        # check whether it's valid:
        if not Breeder.objects.filter(prefix=pedigree_form['breeder'].value()).exists() and pedigree_form['breeder'].value() not in ['Breeder', '', 'None', None]:
            pedigree_form.add_error('breeder', 'Selected breeder does not exist')
            pre_checks = False
        if not Breeder.objects.filter(prefix=pedigree_form['current_owner'].value()).exists() and pedigree_form['current_owner'].value() not in ['Current Owner', '', 'None', None]:
            pedigree_form.add_error('current_owner', 'Selected owner does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(reg_no=pedigree_form['mother'].value()).exists() and pedigree_form['mother'].value() not in ['Mother', '', 'None', None]:
            pedigree_form.add_error('mother', 'Selected mother does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(reg_no=pedigree_form['father'].value()).exists() and pedigree_form['father'].value() not in ['Father', '', 'None', None]:
            pedigree_form.add_error('father', 'Selected father does not exist')
            pre_checks = False
        if not BreedGroup.objects.filter(group_name=pedigree_form['breed_group'].value()).exists() and pedigree_form['breed_group'].value() not in ['Group pedigree was born from', '', 'None', None]:
            pedigree_form.add_error('breed_group', 'Selected breed group does not exist')
            pre_checks = False
        if not Breed.objects.filter(breed_name=attributes_form['breed'].value()).exists() and attributes_form['breed'].value() not in ['Breed', '', 'None', None]:
            attributes_form.add_error('breed', 'Selected breed does not exist')
            pre_checks = False

        if pedigree_form.is_valid() and attributes_form.is_valid() and image_form.is_valid() and pre_checks:
            new_pedigree = Pedigree()
            try:
                new_pedigree.breeder = Breeder.objects.get(prefix=pedigree_form['breeder'].value())
            except ObjectDoesNotExist:
                pass
            try:
                new_pedigree.current_owner = Breeder.objects.get(prefix=pedigree_form['current_owner'].value())
            except ObjectDoesNotExist:
                pass
            new_pedigree.reg_no = pedigree_form['reg_no'].value()
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
            try:
                new_pedigree.parent_mother = Pedigree.objects.get(reg_no=pedigree_form['mother'].value())
            except ObjectDoesNotExist:
                new_pedigree.breed_group = pedigree_form['breed_group'].value() or None
            try:
                new_pedigree.parent_father = Pedigree.objects.get(reg_no=pedigree_form['father'].value())
            except ObjectDoesNotExist:
                pass
            new_pedigree.description = pedigree_form['description'].value()
            new_pedigree.note = pedigree_form['note'].value()
            new_pedigree.save()

            new_pedigree_attributes = PedigreeAttributes()
            new_pedigree_attributes.reg_no = Pedigree.objects.get(reg_no=new_pedigree.reg_no)
            try:
                new_pedigree_attributes.breed = Breed.objects.get(breed_name=attributes_form['breed'].value())
            except ObjectDoesNotExist:
                pass

            eggs = attributes_form['eggs_per_week'].value()
            new_pedigree_attributes.eggs_per_week = int(eggs)
            new_pedigree_attributes.prize_winning = attributes_form['prize_winning'].value()
            new_pedigree_attributes.save()

            files = request.FILES.getlist('upload_images')
            #fs = FileSystemStorage()

            for file in files:
                upload = PedigreeImage(image=file, reg_no=new_pedigree)
                upload.save()

            new_pedigree.save()
            return redirect('pedigree', new_pedigree.id)
    else:
        pedigree_form = PedigreeForm()


    return render(request, 'new_pedigree_form.html', {'pedigree_form': pedigree_form,
                                                      'attributes_form': attributes_form,
                                                      'image_form': image_form,
                                                      'pedigrees': Pedigree.objects.all,
                                                      'breeders': Breeder.objects.all,
                                                      'breeds': Breed.objects.all,
                                                      'breed_groups': BreedGroup.objects.all})


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
@never_cache
def edit_pedigree_form(request, id):
    pedigree = Pedigree.objects.get(id__exact=int(id))

    pedigree_form = PedigreeForm(request.POST or None, request.FILES or None)
    attributes_form = AttributeForm(request.POST or None, request.FILES or None)
    image_form = ImagesForm(request.POST or None, request.FILES or None)
    pre_checks = True

    if request.method == 'POST':
        if 'delete' in request.POST:
            pedigree.delete()
            return redirect('pedigree_search')

        # check whether it's valid:
        if not Breeder.objects.filter(prefix=pedigree_form['breeder'].value()).exists() and pedigree_form['breeder'].value() not in ['Breeder', '', 'None', None]:
            pedigree_form.add_error('breeder', 'Selected breeder does not exist')
            pre_checks = False
        if not Breeder.objects.filter(prefix=pedigree_form['current_owner'].value()).exists() and pedigree_form['current_owner'].value() not in ['Current Owner', '', 'None', None]:
            pedigree_form.add_error('current_owner', 'Selected owner does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(reg_no=pedigree_form['mother'].value()).exists() and pedigree_form['mother'].value() not in ['Mother', '', 'None', None]:
            pedigree_form.add_error('mother', 'Selected mother does not exist')
            pre_checks = False
        if not Pedigree.objects.filter(reg_no=pedigree_form['father'].value()).exists() and pedigree_form['father'].value() not in ['Father', '', 'None', None]:
            pedigree_form.add_error('father', 'Selected father does not exist')
            pre_checks = False
        if not BreedGroup.objects.filter(group_name=pedigree_form['breed_group'].value()).exists() and pedigree_form['breed_group'].value() not in ['Group pedigree was born from', '', 'None', None]:
            pedigree_form.add_error('breed_group', 'Selected breed group does not exist')
            pre_checks = False
        if not Breed.objects.filter(breed_name=attributes_form['breed'].value()).exists() and attributes_form['breed'].value() not in ['Breed', '', 'None', None]:
            attributes_form.add_error('breed', 'Selected breed does not exist')
            pre_checks = False

        if pedigree_form.is_valid() and attributes_form.is_valid() and image_form.is_valid() and pre_checks:
            try:
                pedigree.breeder = Breeder.objects.get(prefix=pedigree_form['breeder'].value())
            except ObjectDoesNotExist:
                pedigree.breeder = None
            try:
                pedigree.current_owner = Breeder.objects.get(prefix=pedigree_form['current_owner'].value())
            except ObjectDoesNotExist:
                pass
            pedigree.reg_no = pedigree_form['reg_no'].value()
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
                pedigree.parent_mother = Pedigree.objects.get(reg_no=pedigree_form['mother'].value())
            except ObjectDoesNotExist:
                pedigree.breed_group = pedigree_form['breed_group'].value() or None
            try:
                pedigree.parent_father = Pedigree.objects.get(reg_no=pedigree_form['father'].value())
            except ObjectDoesNotExist:
                pass
            pedigree.description = pedigree_form['description'].value()
            pedigree.note = pedigree_form['note'].value()
            pedigree.save()

            pedigree_attributes = PedigreeAttributes.objects.get(reg_no=pedigree)
            try:
                pedigree_attributes.breed = Breed.objects.get(breed_name=attributes_form['breed'].value())
            except ObjectDoesNotExist:
                pass

            eggs = attributes_form['eggs_per_week'].value()
            pedigree_attributes.eggs_per_week = int(eggs)
            pedigree_attributes.prize_winning = attributes_form['prize_winning'].value()

            files = request.FILES.getlist('upload_images')
            #fs = FileSystemStorage()

            for image in PedigreeImage.objects.all():
                img = request.POST.get('{}-{}'.format(id, image.id))
                if img:
                    image.delete()

            for file in files:
                upload = PedigreeImage(image=file, reg_no=pedigree)
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
                                                       'pedigrees': Pedigree.objects.all,
                                                       'breeders': Breeder.objects.all,
                                                       'breeds': Breed.objects.all,
                                                       'breed_groups': BreedGroup.objects.all})

def add_existing(request, pedigree_id):
    pedigree = Pedigree.objects.get(id=pedigree_id)

    if request.method == 'POST':
        child_reg = request.POST.get('reg_no')
        child = Pedigree.objects.get(reg_no=child_reg)
        if pedigree.sex == 'male':
            child.parent_father = pedigree
        elif pedigree.sex == 'female':
            child.parent_mother = pedigree

        child.save()

    return redirect('pedigree', pedigree_id)


@login_required(login_url="/account/login")
@user_passes_test(is_editor)
def export(request):
    if request.method == 'POST':
        fields = request.POST.getlist('fields')
        date = datetime.now()
        if request.POST['submit'] == 'xlsx':
            pass
        elif request.POST['submit'] == 'csv':
            # Create the HttpResponse object with the appropriate CSV header.
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="pedigree_db{}.csv"'.format(date.strftime("%Y-%m-%d"))

            writer = csv.writer(response)
            header = False

            for pedigree in Pedigree.objects.all():
                head = ''
                row = ''
                for key, val in pedigree.__dict__.items():
                    if not header:
                        if key != '_state':
                            head += '{},'.format(key)
                    if key in fields:
                        row += '{},'.format(val)
                if not header:
                    writer.writerow([head])
                    header = True
                writer.writerow([row])

            return response
        elif request.POST['submit'] == 'pdf':
            pass

    return render(request, 'export.html', {'fields': Pedigree._meta.get_fields(include_parents=False, include_hidden=False)})
