from django import forms


class PedigreeForm(forms.Form):

    breeder = forms.CharField(required=False)

    current_owner = forms.CharField(required=False)

    reg_no = forms.CharField(label='Registration Number', required=True)
    reg_no.widget.attrs['class'] = 'form-control'
    reg_no.widget.attrs['placeholder'] = 'R012345'

    tag_no = forms.CharField(label='Tag Number', required=False)
    tag_no.widget.attrs['class'] = 'form-control'
    tag_no.widget.attrs['placeholder'] = 'T012345'

    name = forms.CharField(label='Name', required=False)
    name.widget.attrs['class'] = 'form-control'

    date_of_registration = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    date_of_registration.widget.attrs['class'] = 'form-control'
    date_of_registration.widget.attrs['placeholder'] = 'dd/mm/yyyy'

    date_of_birth = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    date_of_birth.widget.attrs['class'] = 'form-control'

    STATUSES = (
        ('dead', 'Dead'),
        ('alive', 'Alive'),
        ('unknown', 'Unknown'),
    )

    status = forms.ChoiceField(choices=STATUSES,  widget=forms.RadioSelect(attrs={'class': 'radio radio-info'}), initial='unknown', required=True)

    GENDERS = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('castrated', 'Castrated'),
    ]
    sex = forms.ChoiceField(choices=GENDERS, widget=forms.RadioSelect(attrs={'class': 'radio radio-info'}), initial='female', required=True)

    BORNAS = (
        ('single', 'Single'),
        ('twin', 'Twin'),
        ('triplet', 'Triplet'),
        ('quad', 'Quad')
    )
    born_as = forms.ChoiceField(choices=BORNAS, widget=forms.RadioSelect(attrs={'class': 'radio radio-info'}), initial='single', required=True)

    father = forms.CharField(required=False)
    father_notes = forms.CharField(required=False)
    father_notes.widget.attrs['class'] = 'form-control'

    mother = forms.CharField(required=False)
    mother_notes = forms.CharField(required=False)
    mother_notes.widget.attrs['class'] = 'form-control'

    breed_group = forms.CharField(required=False)

    description = forms.CharField(widget=forms.Textarea, required=False)
    description.widget.attrs['class'] = 'form-control'

    date_of_death = forms.DateField(required=False, widget=forms.widgets.DateInput(attrs={'type': 'date'}))
    date_of_death.widget.attrs['class'] = 'form-control'
    date_of_death.widget.attrs['placeholder'] = 'dd/mm/yyyy'

    custom_fields = forms.CharField(widget=forms.Textarea, required=False)
    custom_fields.widget.attrs['class'] = 'form-control'

    breed = forms.CharField(required=True)

    sale_or_hire = forms.BooleanField(required=False)
    sale_or_hire.widget.attrs['class'] = 'form-control'


class ImagesForm(forms.Form):

    upload_images = forms.ImageField(required=False)
    upload_images.widget.attrs['class'] = 'form-control'
    upload_images.widget.attrs['multiple'] = ''

