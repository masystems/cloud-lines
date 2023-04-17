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
        total_males = []
        total_breeders = []

        context = {}
        context['attached_service'] = AttachedService.objects.get(id=options.get('attached_service', None))
        current_year = options.get('year', None)

        for pedigree in Pedigree.objects.filter(account=context['attached_service']):
            capture_parent_breeder_count = False
            context['lvl1'] = pedigree
            for key, value in generate_hirearchy(context).items():
                if not value:
                    # not a FULL pedigree
                    break
            # FULL pedigree, can add to calculations
            try:
                context['lvl1'].dob.year
            except AttributeError:
                # dob field empty
                continue
            if context['lvl1'].dob.year == current_year:
                # Q1
                if context['lvl1'].sex == 'female':
                    number_of_females_this_year += 1
                    capture_parent_count = True
                # Q1
                elif context['lvl1'].sex == 'male':
                    number_of_males_this_year += 1
                    capture_parent_breeder_count = True

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
                  "total_males": len(total_males),
                  "total_breeders": len(total_breeders)}
        self.stdout.write(self.style.SUCCESS(output))
