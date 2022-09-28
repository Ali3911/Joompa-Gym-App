from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.body_part.models import BodyPart
from apps.equipment.models import Equipment, EquipmentOption
from apps.goal.models import Goal
from apps.injury.models import Injury, InjuryType
from apps.session.models import Session
from apps.variance.models import Variance


class SessionLength(models.Model):
    total_session_length = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    equipment_option = models.ForeignKey(EquipmentOption, on_delete=models.CASCADE)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    total_sets = models.IntegerField(validators=[MinValueValidator(1)])
    workout_time = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    rest_time = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    warm_up_time = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "total_session_length": self.total_session_length,
            "goal": self.goal.id,
            "equipment_option": self.equipment_option.id,
            "total_sets": self.total_sets,
            "workout_time": self.workout_time,
            "rest_time": self.rest_time,
            "warm_up_time": self.warm_up_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    class Meta:
        ordering = ["-created_at"]
        #  TODO: needs to add unique constraint along with the session days
        # unique_together = (
        #     "total_session_length",
        #     "equipment_option",
        #     "goal",
        #     "total_sets",
        #     "workout_time",
        #     "rest_time",
        #     "warm_up_time",
        # )


class WorkoutFlow(models.Model):
    name = models.CharField(max_length=250)
    value = models.CharField(max_length=250, blank=True)
    session_length = models.ForeignKey(
        SessionLength, related_name="workout_flows", on_delete=models.CASCADE, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class ProgramDesign(models.Model):
    session_per_week = models.ForeignKey(Session, related_name="sessions", on_delete=models.CASCADE)
    sequence_flow = models.ForeignKey(WorkoutFlow, on_delete=models.CASCADE, related_name="sequences_flow")
    day = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)], null=True, blank=True
    )
    body_part = models.ForeignKey(BodyPart, related_name="body_parts", on_delete=models.CASCADE, null=True, blank=True)
    body_part_classification = models.ForeignKey(
        BodyPart, related_name="body_part_classifications", on_delete=models.CASCADE, null=True, blank=True
    )
    variance = models.ForeignKey(Variance, on_delete=models.CASCADE, related_name="variances", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "session_per_week",
            "sequence_flow",
            "day",
            "body_part",
            "body_part_classification",
            "variance",
        )


class Exercise(models.Model):
    name = models.CharField(max_length=250, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class ControlProgram(models.Model):
    equipment_option = models.ForeignKey(
        EquipmentOption, on_delete=models.CASCADE, related_name="cp_equipment_options"
    )
    body_part = models.ForeignKey(BodyPart, related_name="cp_body_parts", on_delete=models.CASCADE)
    body_part_classification = models.ForeignKey(
        BodyPart, related_name="cp_body_part_classifications", on_delete=models.CASCADE, null=True, blank=True
    )
    variance = models.ForeignKey(
        Variance, on_delete=models.CASCADE, related_name="cp_variances", null=True, blank=True
    )
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="cp_exercises")
    is_two_sided = models.BooleanField(default=False, null=True, blank=True)
    reps = models.DecimalField(max_digits=6, decimal_places=3)
    weight = models.DecimalField(max_digits=6, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class ControlProgramInjury(models.Model):
    control_program = models.ForeignKey(ControlProgram, related_name="cp_injuries", on_delete=models.CASCADE)
    injury = models.ForeignKey(Injury, related_name="cpi_injury", on_delete=models.CASCADE)
    injury_type = models.ForeignKey(InjuryType, related_name="cpi_injury_type", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class FirstEverCalc(models.Model):
    FORMULA_CHOICES = (
        ("Baseline", "Baseline"),
        ("FSC", "FSC"),
    )
    weight_formula_string = models.CharField(max_length=100)
    weight_formula_structure = models.JSONField()
    reps_formula_string = models.CharField(max_length=100)
    reps_formula_structure = models.JSONField()
    type = models.CharField(max_length=8, choices=FORMULA_CHOICES)
    control_program = models.ForeignKey(ControlProgram, related_name="fec_control_programs", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ExerciseRelationship(models.Model):
    control_program = models.ForeignKey(ControlProgram, related_name="control_programs", on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, related_name="exercises", on_delete=models.CASCADE)
    multi_weight = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("exercise", "multi_weight")


class Video(models.Model):
    url = models.CharField(max_length=250)
    control_program = models.ForeignKey(ControlProgram, related_name="cp_videos", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EquipmentCombination(models.Model):
    name = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class EquipmentRelation(models.Model):
    exercise_program = models.ForeignKey(ControlProgram, related_name="equipment_relations", on_delete=models.CASCADE)
    equipment_combination = models.ForeignKey(
        EquipmentCombination, related_name="equipment_combinations", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "control_program": self.exercise_program,
        }


class EquipmentGroup(models.Model):
    equipment_combination = models.ForeignKey(
        EquipmentCombination, related_name="equipment_combination_groups", on_delete=models.CASCADE
    )
    equipment = models.ForeignKey(Equipment, related_name="equipment_groups", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "equipment_id": self.equipment.id,
            "equipment_name": self.equipment.name,
        }
