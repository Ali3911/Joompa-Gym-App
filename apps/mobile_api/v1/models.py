"""Mobile API models file."""
from django.db import models

from apps.accounts.models import User
from apps.equipment.models import Equipment, EquipmentOption
from apps.feedback.models import Feedback
from apps.fitness_level.models import FitnessLevel
from apps.goal.models import Goal
from apps.injury.models import Injury, InjuryType
from apps.session.models import Session
from apps.standard_variable.models import StandardVariable


class UserProfile(models.Model):
    """UserProfile model class

    Parameters
    ----------
    models : django.db

    """

    GYM_CHOICES = (("home", "home"), ("condominium", "condominium"), ("commercial", "commercial"))
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_profiles")
    fitness_level = models.ForeignKey(
        FitnessLevel, on_delete=models.CASCADE, related_name="user_fitness_levels", null=True, blank=True
    )
    gym_type = models.CharField(max_length=12, choices=GYM_CHOICES, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=14, null=True, blank=True)
    lattitude = models.DecimalField(max_digits=20, decimal_places=14, null=True, blank=True)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="user_goals", null=True, blank=True)
    baseline_assessment = models.JSONField(null=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="user_sessions", null=True, blank=True)
    max_session_length = models.CharField(max_length=3, null=True, blank=True)
    is_personalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pd_exist = models.BooleanField(default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id.id,
            "username": self.user_id.username,
            "first_name": self.user_id.first_name,
            "last_name": self.user_id.last_name,
            "fitness_level": self.fitness_level.fitness_level,
            "gym_type": self.gym_type,
            "longitude": self.longitude,
            "lattitude": self.lattitude,
            "goal": self.goal.name,
            "baseline_assessment": self.baseline_assessment,
            "session": self.session.value,
            "max_session_length": self.max_session_length,
            "is_personalized": self.is_personalized,
        }


class UserStandardVariable(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_profiles_std_var")
    standard_variable_id = models.ForeignKey(
        StandardVariable, on_delete=models.CASCADE, related_name="user_standard_variable"
    )
    value = models.CharField(max_length=250)
    unit = models.CharField(max_length=250, blank=True, null=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_profile": self.user_profile.id,
            "standard_variable_id": self.standard_variable_id.name,
            "value": self.value,
            "unit": self.unit if self.unit else None,
        }

    class Meta:
        unique_together = ("user_profile", "standard_variable_id")


class UserInjury(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_profile_injuries")
    injury = models.ForeignKey(Injury, related_name="user_injury", on_delete=models.CASCADE)
    injury_type = models.ForeignKey(InjuryType, related_name="user_injury_type", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_profile": self.user_profile.id if self.user_profile else None,
            "injury": self.injury.name if self.injury else None,
            "injury_type": self.injury_type.name if self.injury_type else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    class Meta:
        unique_together = ("user_profile", "injury", "injury_type")


class UserEquipment(models.Model):
    weight_types = (
        ("kg", "kg"),
        ("lbs", "lbs"),
    )
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_profile_equipments")
    equipment = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name="user_equipments", null=True, blank=True
    )
    equipment_type = models.ForeignKey(
        Equipment, on_delete=models.CASCADE, related_name="user_equipment_types", null=True, blank=True
    )
    equipment_option = models.ForeignKey(
        EquipmentOption, on_delete=models.CASCADE, related_name="user_equipment_options", null=True, blank=True
    )
    weights = models.JSONField(null=True, blank=True)
    weight_type = models.CharField(max_length=5, choices=weight_types, default="kg")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_profile": self.user_profile.id if self.user_profile else None,
            "equipment": self.equipment.name if self.equipment else None,
            "equipment_type": self.equipment_type.name if self.equipment_type else None,
            "equipment_option": self.equipment_option.name if self.equipment_option else None,
            "weights": self.weights if self.weights else None,
            "weight_type": self.weight_type if self.weight_type else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class UserProgramDesign(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_programs")
    day = models.PositiveBigIntegerField()
    program_design = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    workout_date = models.DateTimeField()
    is_complete = models.BooleanField(default=False)
    week = models.PositiveBigIntegerField(blank=True, null=True)
    is_personalized = models.BooleanField(default=True)
    system_rir = models.IntegerField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)


class UserFeedback(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_profile_feedbacks")
    feedback = models.ForeignKey(
        Feedback, on_delete=models.CASCADE, related_name="user_feedbacks", null=True, blank=True
    )
    user_program_design = models.ForeignKey(
        UserProgramDesign, on_delete=models.CASCADE, related_name="user_program_design", null=True, blank=True
    )
    value = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user_profile", "feedback", "user_program_design")
