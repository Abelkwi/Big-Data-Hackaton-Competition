from django import forms

from .models import Product, ProductImage, Review

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):

    widget = MultipleFileInput

    def clean(self, data, initial=None):

        if not data:
            return []

        if not isinstance(data, (list, tuple)):
            data = [data]

        cleaned_files = []

        for file in data:
            cleaned_files.append(super().clean(file, initial))

        return cleaned_files

class ProductForm(forms.ModelForm):
    gallery_images = MultipleFileField(
    required=False,
    label="Gallery Images"
    )

    class Meta:
        model = Product
        exclude = [
            "farmer",
            "verification_status",
            "availability_status",
            "created_at",
            "updated_at",
            ]

    widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Product name"
            }),

            "category": forms.Select(attrs={
                "class": "form-select"
            }),

            "variety": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Variety (Optional)"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

            "main_image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),

            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),

            "unit": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "minimum_order": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),

            "price_per_unit": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01"
            }),

            "province": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "district": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "sector": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "cell": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "village": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "harvest_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "expiry_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "organic": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        minimum_order = cleaned_data.get("minimum_order")
        harvest_date = cleaned_data.get("harvest_date")
        expiry_date = cleaned_data.get("expiry_date")

        if quantity is not None and quantity <= 0:
            self.add_error("quantity", "Quantity must be greater than zero.")

        if minimum_order is not None and minimum_order <= 0:
            self.add_error("minimum_order", "Minimum order must be greater than zero.")

        if (
            quantity is not None
            and minimum_order is not None
            and minimum_order > quantity
        ):
            self.add_error(
                "minimum_order",
                "Minimum order cannot exceed available quantity."
            )

        if (
            harvest_date
            and expiry_date
            and expiry_date < harvest_date
        ):
            self.add_error(
                "expiry_date",
                "Expiry date cannot be earlier than harvest date."
            )

        return cleaned_data
    
    def clean_gallery_images(self):
        images = self.cleaned_data.get("gallery_images", [])

        if len(images) > 10:
            raise forms.ValidationError(
                "You can upload a maximum of 10 gallery images."
            )

        for image in images:

            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Each image must be smaller than 5 MB."
                )

        return images

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review

        fields = [
            "rating",
            "comment",
        ]

        widgets = {

            "rating": forms.Select(attrs={
                "class": "form-select"
            }),

            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Share your experience with this product..."
            }),
        }

    def clean_rating(self):

        rating = self.cleaned_data["rating"]

        if rating not in [1, 2, 3, 4, 5]:
            raise forms.ValidationError(
                "Rating must be between 1 and 5."
            )

        return rating

    def clean_comment(self):

        comment = self.cleaned_data.get(
            "comment",
            ""
        ).strip()

        if comment and len(comment) < 5:
            raise forms.ValidationError(
                "Review is too short."
            )

        return comment