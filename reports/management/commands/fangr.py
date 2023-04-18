from django.core.management.base import BaseCommand
from pedigree.views import generate_hirearchy
from pedigree.models import Pedigree
from account.models import AttachedService

class Command(BaseCommand):
    help = "Calculate the FAnGR report"

    def add_arguments(self, parser):
        # Add any command line arguments if required
        parser.add_argument('-as', '--attached_service', type=int, help='Attached Service')
        parser.add_argument('-y', '--year', type=str, help='Year to run report on')

        #context['attached_service']
        pass

    def handle(self, *args, **options):
        # set up vars
        number_of_females_this_year = 0
        number_of_males_this_year = 0
        total_females = []
        female_reg_numbers = []
        total_males = []
        male_reg_numbers = []
        total_breeders = []

        context = {}
        context['attached_service'] = AttachedService.objects.get(id=options.get('attached_service', None))
        current_year = options.get('year', None)

        for pedigree in Pedigree.objects.filter(account=context['attached_service'], id=51744):
            capture_parent_breeder_count = False
            break_outer_loop = False
            context['lvl1'] = pedigree
            print(generate_hirearchy(context))
            for key, value in generate_hirearchy(context).items():
                if value in ['', None]:
                    # not a FULL pedigree
                    break_outer_loop = True
                    break
            if break_outer_loop:
                break
            # FULL pedigree, can add to calculations
            try:
                context['lvl1'].date_of_registration.year
            except AttributeError:
                # dob field empty
                continue
            if str(context['lvl1'].date_of_registration.year) == str(current_year):
                # Q1
                if context['lvl1'].sex == 'female':
                    number_of_females_this_year += 1
                    capture_parent_breeder_count = True
                    female_reg_numbers.append(context['lvl1'].reg_no)
                # Q1
                elif context['lvl1'].sex == 'male':
                    number_of_males_this_year += 1
                    capture_parent_breeder_count = True
                    male_reg_numbers.append(context['lvl1'].reg_no)

                if capture_parent_breeder_count:
                    if context['lvl1'].parent_mother not in total_females:
                        total_females.append(context['lvl1'].parent_mother)
                    if context['lvl1'].parent_father not in total_males:
                        total_males.append(context['lvl1'].parent_father)
                    if context['lvl1'].breeder not in total_breeders:
                        total_breeders.append(context['lvl1'].breeder)

        # create json stdout
        output = {"females_this_year": number_of_females_this_year,
                  "males_this_year": number_of_males_this_year,
                  "total_females": len(total_females),
                  "female_reg_numbers": female_reg_numbers,
                  "total_males": len(total_males),
                  "male_reg_numbers": male_reg_numbers,
                  "total_breeders": len(total_breeders)}
        self.stdout.write(self.style.SUCCESS(output))
