from django.db import models

class CodeforcesProblem(models.Model):
    contest_id = models.IntegerField()
    index = models.CharField(max_length=5)
    name = models.CharField(max_length=255)
    rating = models.IntegerField(null=True, blank=True)
    url = models.URLField()
    division = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.contest_id}{self.index} - {self.name}"


class CodeforcesUser(models.Model):
    handle = models.CharField(max_length=100, unique=True)
    solved_problems = models.ManyToManyField(CodeforcesProblem, blank=True)

    def __str__(self):
        return self.handle
