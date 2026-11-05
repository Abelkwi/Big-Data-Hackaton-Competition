from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from blog.models import BlogComment, BlogPost
from marketplace.models import Product
from recovery.models import RecoveryListing

from .audit import record_event


User = get_user_model()


@receiver(post_save, sender=User)
def record_user_registration(sender, instance, created, raw, **kwargs):
    if created and not raw:
        record_event("registration", user=instance, description="Account registered")


@receiver(post_save, sender=Product)
def record_product_submission(sender, instance, created, raw, **kwargs):
    if created and not raw:
        record_event(
            "content_submit",
            user=instance.farmer,
            description="Agricultural product submitted for review",
            metadata={"content_type": "product", "content_id": instance.pk},
        )


@receiver(post_save, sender=BlogPost)
def record_blog_post_creation(sender, instance, created, raw, **kwargs):
    if created and not raw:
        record_event(
            "post_create",
            user=instance.author,
            description="Blog post created",
            metadata={"content_type": "blog_post", "content_id": instance.pk},
        )


@receiver(post_save, sender=BlogComment)
def record_pending_comment(sender, instance, created, raw, **kwargs):
    if created and not raw and not instance.is_approved:
        record_event(
            "content_submit",
            user=instance.author,
            description="Blog comment submitted for review",
            metadata={"content_type": "blog_comment", "content_id": instance.pk},
        )


@receiver(post_save, sender=RecoveryListing)
def record_recovery_listing(sender, instance, created, raw, **kwargs):
    if created and not raw:
        record_event(
            "content_submit",
            user=instance.donor,
            description="Food recovery listing created",
            metadata={"content_type": "recovery_listing", "content_id": instance.pk},
        )
