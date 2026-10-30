import os

path_models = r"c:\Users\user\OneDrive\Desktop\Website\smartsave-backend\innovation\models.py"
content = """from django.conf import settings
from django.db import models
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL

class InnovationIdea(models.Model):
    CATEGORY_CHOICES = [("technology","Technology"),("technique","Technique"),("sustainability","Sustainability"),("other","Other")]
    STATUS_CHOICES = [("draft","Draft"),("submitted","Submitted"),("under_review","Under Review"),("approved","Approved"),("rejected","Rejected"),("implemented","Implemented")]
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="innovation_ideas")
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    problem_solved = models.TextField(blank=True)
    expected_impact = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="other")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")
    attachments = models.FileField(upload_to="innovation/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    votes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["-created_at"]
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title); slug = base_slug; counter = 1
            while InnovationIdea.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"; counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    def __str__(self): return self.title

class InnovationVote(models.Model):
    idea = models.ForeignKey(InnovationIdea, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="innovation_votes")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ("idea", "voter")
    def __str__(self): return f"{self.voter.email} voted for {self.idea.title}"

class InnovationComment(models.Model):
    idea = models.ForeignKey(InnovationIdea, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="innovation_comments")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"Comment by {self.author.email} on {self.idea.title}"
"""
with open(path_models, "w", encoding="utf-8") as f:
    f.write(content)
print("models.py written")
