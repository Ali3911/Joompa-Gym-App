import datetime
import enum
import json as JSON
import logging
from string import Formatter

from drf_yasg.openapi import IN_QUERY, Parameter
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import IntegrityError, transaction

from apps.config.models import Config
from apps.const import TOTAL_PROGRAM_DESIGN_WEEKS
from apps.controlled.models import (
    ControlProgram,
    EquipmentGroup,
    FirstEverCalc,
    ProgramDesign,
    SessionLength,
    WorkoutFlow,
)
from apps.controlled.serializers import ProgramDesignSerializer
from apps.equipment.models import EquipmentOption
from apps.goal.models import Goal
from apps.injury.models import Injury
from apps.mobile_api.v1.models import (
    UserEquipment,
    UserFeedback,
    UserInjury,
    UserProfile,
    UserProgramDesign,
    UserStandardVariable,
)
from apps.mobile_api.v1.serializers import (
    SwaggerUserFeedbackSerializer,
    SwaggerUserProfileSerializer,
    UserEquipmentSerializer,
    UserFeedbackSerializer,
    UserInjurySerializer,
    UserProfileSerializer,
    UserProgramDesignSerializer,
    UserProgramDesignSwaggerSerializer,
    UserStandardVariableSerializer,
    UserWorkoutProgramSerializer,
)
from apps.reps_in_reserve.models import RepsInReserve, RepsRange, RepsRating
from apps.session.models import Session
from apps.standard_variable.models import StandardVariable
from apps.utils import response_json

logger = logging.getLogger(__name__)


class UserSession(enum.Enum):
    preponeone = 1
    preponeall = 2
    postponeall = 3
    rescheduleall = 4


def get_current_date_missed_sessions(user_profile_id):
    user_profile = UserProfile.objects.get(pk=user_profile_id)
    is_personalized = user_profile.is_personalized

    # get current date
    current_date = datetime.datetime.now()

    todays_workouts = UserProgramDesign.objects.filter(
        user=user_profile_id, workout_date__date=current_date, is_complete=False, is_personalized=is_personalized
    )

    if todays_workouts.exists():
        return True


def get_missed_sessions(user_profile_id):

    user_profile = UserProfile.objects.get(pk=user_profile_id)
    is_personalized = user_profile.is_personalized

    missed_sessions = 0
    response_data = {"can_reschedule": True}

    # get current date
    current_date = datetime.datetime.now()

    # get all previous in-complete programs
    in_complete_programs = UserProgramDesign.objects.filter(
        workout_date__date__lt=current_date,
        is_complete=False,
        user=user_profile_id,
        is_personalized=is_personalized,
    ).order_by("workout_date")

    incomplete_programs_count = in_complete_programs.count()

    if incomplete_programs_count > 0:
        # missed sessions
        missed_sessions = incomplete_programs_count

        # calculate date difference for first incomplete workout
        difference = abs((in_complete_programs.first().workout_date.replace(tzinfo=None) - current_date).days)
        if difference > 14:
            # send can_reschedule indicator in response to hide continue button in app
            response_data["can_reschedule"] = False

        # get most recent workout
        recent_workout = UserProgramDesign.objects.filter(
            user=user_profile_id,
            workout_date__date__lt=current_date,
            is_personalized=is_personalized,
        ).order_by("workout_date")

        recent_workout = recent_workout[recent_workout.count() - 1]
        starting_date = recent_workout.start_date

        # ignore the whole scenario if last workout is completed
        if recent_workout.is_complete is True:
            missed_sessions = 0
            response_data["can_reschedule"] = True
            pass
        else:
            # logic to calculate missed sessions between last completed session and current day
            recent_complete_workout = UserProgramDesign.objects.filter(
                user=user_profile_id,
                workout_date__date__lt=current_date,
                is_complete=True,
                start_date=starting_date,
                is_personalized=is_personalized,
            ).order_by("workout_date")

            if recent_complete_workout.exists():

                recent_complete_workout = recent_complete_workout[recent_complete_workout.count() - 1]
                recent_complete_workout_date = recent_complete_workout.workout_date
                missed_sessions = UserProgramDesign.objects.filter(
                    workout_date__date__range=[
                        recent_complete_workout_date,
                        current_date + datetime.timedelta(days=-1),
                    ],
                    user=user_profile_id,
                    is_personalized=is_personalized,
                ).count()
                # subtract first completed session
                missed_sessions = missed_sessions - 1
                # check if date difference is more than 14
                difference = abs((recent_complete_workout_date.replace(tzinfo=None) - current_date).days)
                if difference > 14:
                    # send can_reschedule indicator in response to hide continue button in app
                    response_data["can_reschedule"] = False

    return missed_sessions, response_data


def get_pd_dates(session_per_week):
    days = {1: "1:6", 2: "1:2", 3: "1:1", 4: "2:1", 5: "3:1", 6: "3:1"}
    no_of_workouts = int(days.get(session_per_week).split(":")[0])
    gaps = int(days.get(session_per_week).split(":")[1])

    today_date = datetime.datetime.now()
    count = gaps + 1
    dates = []

    for i in range(1, 7):
        difference = datetime.timedelta(days=i)
        if count <= gaps:
            count += 1
        else:
            dates.append(today_date + difference)
            if count <= no_of_workouts:
                count += 1
            else:
                count = 1
    return dates


def save_user_program_designs(user, session_per_week, goal_id, is_personalized, data):
    no_of_sessions = Session.objects.get(pk=int(session_per_week)).value
    workout_dates = get_pd_dates(no_of_sessions)
    weeks = TOTAL_PROGRAM_DESIGN_WEEKS
    system_rir_data = RepsInReserve.objects.get(goal=goal_id, fitness_level=user.fitness_level.id).weeks
    start_date = datetime.datetime.now()
    end_date_gap = datetime.timedelta(days=(weeks - 1) * 7)

    if no_of_sessions == 1:
        end_date = workout_dates[0] + end_date_gap

    elif no_of_sessions > 1:
        end_date = workout_dates[len(workout_dates) - 1] + end_date_gap

    for i in range(weeks):

        for counter, value in enumerate(workout_dates):
            day = counter + 1
            if day in data:
                program_design = data[day]
            else:
                program_design = []

            workout_date = value + datetime.timedelta(days=i * 7)
            system_rir = system_rir_data[i]["rir"]
            for exercise_counter, exercise in enumerate(program_design):
                exercise["id"] = exercise_counter + 1
            UserProgramDesign.objects.create(
                user=user,
                day=day,
                program_design=program_design,
                workout_date=workout_date,
                week=i + 1,
                is_personalized=is_personalized,
                system_rir=system_rir,
                start_date=start_date,
                end_date=end_date,
            )


def re_schedule_user_program_designs(user_id, session_per_week, is_personalized, data, starting_date):
    with transaction.atomic():
        # get userprofile
        user = UserProfile.objects.get(pk=user_id)

        # get goal ID
        if is_personalized:
            goal_id = user.goal.id
        else:
            goal_id = Goal.objects.get(pk=Config.objects.filter(key="goal")[0].value).id

        # create new workout data
        workout_dates = get_pd_dates(session_per_week)
        weeks = TOTAL_PROGRAM_DESIGN_WEEKS
        system_rir_data = RepsInReserve.objects.get(goal=goal_id, fitness_level=user.fitness_level.id).weeks
        start_date = datetime.datetime.now()
        end_date_gap = datetime.timedelta(days=(weeks - 1) * 7)
        if session_per_week == 1:
            end_date = workout_dates[0] + end_date_gap
        elif session_per_week > 1:
            end_date = workout_dates[len(workout_dates) - 1] + end_date_gap

        # delete previous data
        old_user_programs = UserProgramDesign.objects.filter(
            user=user_id, start_date=starting_date, is_personalized=is_personalized
        )
        old_user_programs = old_user_programs.delete()
        logger.info(f"Total UserPrograms deleted : {old_user_programs[0]} for Userprofile: {user_id}")

        newly_created_user_program_ids = []
        # create and save new workouts
        for i in range(weeks):
            for counter, value in enumerate(workout_dates):
                day = counter + 1
                program_design = data[counter]
                workout_date = value + datetime.timedelta(days=i * 7)
                system_rir = system_rir_data[i]["rir"]
                new_user_program_design = UserProgramDesign.objects.create(
                    user=user,
                    day=day,
                    program_design=program_design,
                    workout_date=workout_date,
                    week=i + 1,
                    is_personalized=is_personalized,
                    system_rir=system_rir,
                    start_date=start_date,
                    end_date=end_date,
                )
                newly_created_user_program_ids.append(new_user_program_design.id)

        user.is_pd_exist = True
        user.save()
        logger.info(f"UserPrograms created with IDs: {newly_created_user_program_ids} for Userprofile: {user_id}")


def adjust_weights_reps_warm_up(
    exercise_reps: float,
    exercise_weight: float,
    calculated_reps: int,
    calculated_weight: int,
    required_weight: int,
):
    weight_difference = required_weight - calculated_weight  # -5 = 5 - 10
    reps = weight_difference * exercise_reps // exercise_weight  # -10 = -5 * 2 / 1
    return calculated_reps - reps  # 10 - (-10)


def find_closest_weight(weight_list: list, calculated_weight: int):
    return min(weight_list, key=lambda x: abs(x - calculated_weight))


def fetch_reps_list(goal):
    reps_values = RepsRange.objects.filter(goal=goal).values_list("value", flat=True)
    reps_values = list(reps_values)
    if len(reps_values) == 0:
        raise Exception(f"RepsRange not exist against goal id: {goal}")
    _max = max(reps_values)
    for value in range(_max + 1, _max + 10, 1):
        reps_values.insert(len(reps_values), value)

    return reps_values


def validate_reps_range(rep: int, reps_list: list):
    return rep in reps_list


class UserWorkoutProgramsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def __user_equipment_list(self, user_profile: UserProfile):
        equipment_list = user_profile.user_profile_equipments.all().values_list("equipment", flat=True)
        return list(set(equipment_list))

    def __validate_equipment(self, control_program: ControlProgram, user_profile: UserProfile):

        equipment_list = self.__user_equipment_list(user_profile)
        combination_list = control_program.equipment_relations.all().values_list("equipment_combination", flat=True)
        for combination in combination_list:
            cp_equipments = set(
                EquipmentGroup.objects.filter(equipment_combination_id=combination).values_list("equipment", flat=True)
            )
            if cp_equipments.issubset(set(equipment_list)):
                return True, combination
        return False, 0

    def __populate_default_values(self, query_parameters: dict, user_profile):
        configurations = query_parameters.copy()
        keys = query_parameters.keys()
        default_config = None
        if not configurations["is_personalized"]:
            default_config = Config.objects.filter(
                key__in=["goal", "total_session_length", "session_per_week"]
            ).values("key", "value")
            for record in default_config:
                if record["key"] not in keys:
                    configurations[record["key"]] = record["value"]
        else:
            configurations = {
                "goal": user_profile.goal.id,
                "session_per_week": user_profile.session.id,
                "total_session_length": user_profile.max_session_length,
                "is_personalized": True,
            }

        return configurations

    def __variables_list(self, string: str):
        return [fn for _, fn, _, _ in Formatter().parse(string) if fn is not None]

    def __calculate_weight_fsc(self, first_ever: FirstEverCalc, user_profile: UserProfile):
        actual = first_ever.weight_formula_string
        variable = StandardVariable.objects.filter(name="Weight")
        if not variable.exists():
            raise Exception("Standard Variable `Weight` doesn't exist in the database")
        user_standard_variable = UserStandardVariable.objects.filter(
            user_profile=user_profile, standard_variable_id=variable[0]
        )
        if not user_standard_variable.exists():
            raise Exception(f"User Standard Variable `Weight` doesn't exist in the db against {user_profile.user_id}")
        body_weight = user_standard_variable[0].value
        formula = actual.format(Weight=body_weight, fitness_level=user_profile.fitness_level.fitness_level)
        return int(eval(formula))

    def __calculate_reps_fsc(self, first_ever: FirstEverCalc, user_profile: UserProfile):
        actual = first_ever.reps_formula_string
        if actual.isdigit():
            return int(actual)
        else:
            variable = StandardVariable.objects.filter(name="Weight")
            if not variable.exists():
                raise Exception("Standard Variable `Weight` doesn't exist in the database")
            user_standard_variable = UserStandardVariable.objects.filter(
                user_profile=user_profile, standard_variable_id=variable[0]
            )
            if not user_standard_variable.exists():
                raise Exception(
                    f"User Standard Variable `Weight` doesn't exist in the database against {user_profile.user_id}"
                )
            body_weight = user_standard_variable[0].value
            formula = actual.format(Weight=body_weight, fitness_level=user_profile.fitness_level.fitness_level)
            return int(eval(formula))

    def __calculate_weight_baseline(self, first_ever: FirstEverCalc, user_profile: UserProfile):
        objects = user_profile.baseline_assessment
        if objects is None:
            return 0
        string_formula = first_ever.weight_formula_string
        variable_list = self.__variables_list(string_formula)
        variable_dict = self.__populate_formulas_variables(user_profile, variable_list)
        for json in objects:
            if json["question"] in variable_list:
                variable_dict[json["question"]] = json["value"]
        keys = variable_dict.keys()
        for variable in variable_list:
            if variable not in keys:
                variable_dict[variable] = 0
        formula = string_formula.format(**variable_dict)
        return int(eval(formula))

    def __calculate_reps_baseline(self, first_ever: FirstEverCalc, user_profile: UserProfile):
        objects = user_profile.baseline_assessment
        reps_formula_string = first_ever.reps_formula_string
        variable_list = self.__variables_list(reps_formula_string)
        variable_dict = self.__populate_formulas_variables(user_profile, variable_list)
        for json in objects:
            if json["question"] in variable_list:
                variable_dict[json["question"]] = json["value"]
        keys = variable_dict.keys()
        for variable in variable_list:
            if variable not in keys:
                variable_dict[variable] = 0
        formula = reps_formula_string.format(**variable_dict)
        return int(eval(formula))

    def __populate_formulas_variables(self, user_profile: UserProfile, variables: list) -> dict:
        standard_variables = UserStandardVariable.objects.filter(user_profile=user_profile)
        sv_dict = {
            sv.standard_variable_id.name: sv.value
            for sv in standard_variables
            if sv.standard_variable_id.name in variables
        }

        return sv_dict

    def __adjust_weights_reps(
        self, control_program: ControlProgram, calculated_reps: int, calculated_weight: int, required_weight: int
    ):
        logger.info(
            f"control_program id: {control_program.id}, calculated_reps: {calculated_reps}, calculated_weight: "
            f"{calculated_weight}, closest_weight: {required_weight}"
        )
        logger.info(f"difference: {(required_weight - calculated_weight)}")
        weight_difference = (required_weight - calculated_weight) // 2.5  # -5 = 5 - 10
        logger.info(f"weight_difference: {weight_difference}")
        reps = weight_difference * float(control_program.reps) // float(control_program.weight)  # -10 = -5 * 2 / 1
        logger.info(f"reps: {reps}, updated_reps: {calculated_reps - reps}")
        return calculated_reps - reps  # 10 - (-10)

    def __validate_injuries(self, user_profile, control_program):
        program_injuries = set(control_program.cp_injuries.all().values_list("injury", flat=True))
        user_injuries = set(user_profile.user_profile_injuries.all().values_list("injury", flat=True))
        result = program_injuries.intersection(user_injuries)
        if len(result) > 0:
            # replace id within name to display injuries name in message
            return True, {injury.name for injury in Injury.objects.filter(id__in=result)}
        else:
            return False, result

    def __calculate_index(self, session, day):
        if day <= session:
            return day
        else:
            day % session + 1

    def __filter_control_programs(self, variance, body_part, body_part_classification, equip_op_list):
        return ControlProgram.objects.filter(
            variance=variance,
            body_part=body_part,
            body_part_classification=body_part_classification,
            equipment_option__in=equip_op_list,
        ).order_by("created_at")

    def __get_RepsInReserve(self, goal, fitness_level):
        reps_in_reserve = RepsInReserve.objects.filter(goal=goal, fitness_level=fitness_level)
        if reps_in_reserve.exists():
            rir_list = reps_in_reserve[0].weeks
            for rir in rir_list:
                if "week" not in rir.keys() or "rir" not in rir.keys():
                    raise Exception(f"Invalid format found in RepsInReserve against record id {reps_in_reserve[0].id}")
                if rir["week"] == 1 or rir["week"] == "1":
                    return rir["rir"]
        return 0

    def __user_weight_list(self, user_profile: UserProfile):
        user_weight_list = list()
        for equipment in user_profile.user_profile_equipments.all():
            if equipment.weights is not None:
                user_weight_list.extend([float(key) for key in dict(equipment.weights).keys()])
        return user_weight_list

    def __repeat_sets(self, data, user_weight_list):
        for key, records in data.items():
            position = 1
            for record in records:
                if record["checked"]:
                    continue
                for i in range(record["total_sets"]):
                    if i == 0:
                        record["set"] = str(i + 1)
                        record["checked"] = True
                        warm_up = record.copy()
                        warm_up["set"] = str(i)
                        if warm_up["system_calculated_weight"] != 0:
                            new_weight = warm_up["system_calculated_weight"] * 0.7
                            closest_weight = find_closest_weight(user_weight_list, new_weight)
                            warm_up["system_calculated_weight"] = closest_weight
                            warm_up["system_calculated_reps"] = adjust_weights_reps_warm_up(
                                float(warm_up["reps"]),
                                float(warm_up["weight"]),
                                warm_up["system_calculated_reps"],
                                new_weight,
                                closest_weight,
                            )
                        else:
                            new_reps = round(warm_up["system_calculated_reps"] * 0.7)
                            warm_up["system_calculated_reps"] = new_reps

                        data[key].insert(position - 1, warm_up)
                    if i > 0:
                        temp = record.copy()
                        temp["set"] = str(i + 1)
                        data[key].insert(position, temp)
                    position += 1
        return data

    def __generate_userprograms(self, request_data, user_profile):
        equip_op_list = []
        user_profile = user_profile[0]
        data = {}
        exercise_list = []
        skipped_pd = []  # temp variable
        configurations = self.__populate_default_values(query_parameters=request_data, user_profile=user_profile)
        logger.info(f"user_profile {user_profile.id} configurations data: {configurations}")
        all_equipment_options = EquipmentOption.objects.all().values("id", "name")
        _equipment_options = {record["name"]: record["id"] for record in all_equipment_options}
        user_equipment_options = {}
        equipment_options = user_profile.user_profile_equipments.all()
        if equipment_options:
            logger.info(f"user_profile {user_profile.id} equipment_options data: {equipment_options.values('id')}")
            for _equipment_option in equipment_options:
                user_equipment_options[_equipment_option.equipment_option.name] = _equipment_option.equipment_option.id
            if "2 weights" in user_equipment_options.keys():
                configurations["equipment_option"] = _equipment_options["2 weights"]
                equip_op_list = list(_equipment_options.values())
            elif "1 weight" in user_equipment_options.keys():
                configurations["equipment_option"] = _equipment_options["1 weight"]
                equip_op_list = [_equipment_options["1 weight"], _equipment_options["None"]]
            elif "None" in user_equipment_options.keys():
                configurations["equipment_option"] = _equipment_options["None"]
                equip_op_list = [_equipment_options["None"]]
            else:
                response_json(status=False, data=None, message="User has not selected Equipment yet")
        else:
            configurations["equipment_option"] = _equipment_options["None"]
            equip_op_list = [_equipment_options["None"]]
        logger.info(f"user_profile {user_profile.id} configurations with equipment_option data: {configurations}")
        reps_list = fetch_reps_list(configurations["goal"])
        reps_in_reserve = self.__get_RepsInReserve(configurations["goal"], user_profile.fitness_level)
        user_weight_list = self.__user_weight_list(user_profile)

        logger.info(
            f"user_profile id: {user_profile.id} \n reps_list data: {reps_list} \n reps_in_reserve data: "
            f"{reps_in_reserve} \n user_weight_list: {user_weight_list}"
        )

        message = {}
        session_ = Session.objects.filter(id=configurations["session_per_week"])
        if not session_.exists():
            message = f"Session object against id {configurations['session_per_week']} doesn't exist!"
            logger.info(message)
            return Response(response_json(status=False, data=None, message=message))
        session_value = session_[0].value
        for i in range(1, session_value + 1):
            data[i] = []
            message[i] = []
        for session_length in SessionLength.objects.filter(
            equipment_option=configurations["equipment_option"],
            goal=configurations["goal"],
            total_session_length=configurations["total_session_length"],
        ).order_by("created_at"):
            logger.info(
                f"Fetching session_length: {session_length.id} for user_profile {user_profile.id}"
                f" against equipment_option: {configurations['equipment_option']} goal: {configurations['goal']}"
                f" session_length: {configurations['total_session_length']}"
            )
            for workout in (
                WorkoutFlow.objects.filter(session_length=session_length.id).exclude(value="").order_by("created_at")
            ):
                logger.info(
                    f"Fetching workout {workout.id} for user_profile {user_profile.id}"
                    f" against session_length: {session_length.id}"
                )
                for program_design in ProgramDesign.objects.filter(
                    sequence_flow=workout.id, session_per_week=configurations["session_per_week"]
                ).order_by("created_at"):
                    logger.info(
                        f"Fetching program_design {program_design.id} for user_profile {user_profile.id} "
                        f"against workout: {workout.id}-{workout.value} session_per_week: "
                        f"{configurations['session_per_week']}"
                    )
                    control_programs = self.__filter_control_programs(
                        program_design.variance,
                        program_design.body_part,
                        program_design.body_part_classification,
                        equip_op_list,
                    )
                    if not control_programs.exists():
                        pd_data = ProgramDesignSerializer(program_design, many=False).data
                        skipped_pd.append(pd_data)
                        classification = (
                            program_design.body_part_classification.id
                            if program_design.body_part_classification is not None
                            else None
                        )
                        message[self.__calculate_index(session_value, program_design.day)].append(
                            f"Control Program not found against program design  parameters variance = "
                            f"{program_design.variance.id if program_design.variance is not None else None}, "
                            f"body part id = {program_design.body_part.id}, body_part_name = "
                            f"{program_design.body_part.name}"
                            f"body_part_classification = "
                            f"{classification} and equipment option = "
                            f"{_equipment_options.keys()}, pd_id={program_design.id}, workflow_id= {workout.id}"
                        )
                        logger.info(f"Skipped Control Programs for user_profile {user_profile.id}: {len(message)}")
                    logging.info(
                        f"Valid Control Programs for user_profile: {user_profile.id}: {control_programs.count()} "
                        f"against program_design: {program_design.id}"
                    )
                    index = self.__calculate_index(program_design.session_per_week.value, program_design.day)
                    for control_program in control_programs:
                        logger.info(
                            f"Fetching control_program {control_program.id} for exercise: "
                            f"{control_program.exercise.name}"
                        )
                        if control_program.exercise.name not in exercise_list:
                            exercise_list.append(control_program.exercise.name)
                            # skip validation for equipment option None
                            if _equipment_options["None"] == control_program.equipment_option.id:
                                valid_eq, com_id = True, 0

                            else:
                                valid_eq, com_id = self.__validate_equipment(control_program, user_profile)

                            if not valid_eq:
                                message[self.__calculate_index(session_value, program_design.day)].append(
                                    f"Equipment {set(self.__user_equipment_list(user_profile))} combination against"
                                    f" control_program id {control_program.id} does not exist!!"
                                )
                                logger.info(f"Invalid equipment for user_profile {user_profile.id}: {message}")
                                continue
                            valid_injuries = self.__validate_injuries(user_profile, control_program)
                            if valid_injuries[0] and configurations["is_personalized"]:
                                message[self.__calculate_index(session_value, program_design.day)].append(
                                    f"Equipment {set(self.__user_equipment_list(user_profile))} Combination against"
                                    f" control program id {control_program.id} does not exist"
                                )
                                logger.info(f"Invalid equipment for user_profile {user_profile.id}: {message}")
                                continue
                            valid_injuries = self.__validate_injuries(user_profile, control_program)
                            if valid_injuries[0] and configurations["is_personalized"]:
                                message[self.__calculate_index(session_value, program_design.day)].append(
                                    f"Equipment {set(self.__user_equipment_list(user_profile))} Combination against"
                                    f" control program id {control_program.id} does not exist"
                                )
                                logger.info(f"Invalid equipment for user_profile {user_profile.id}: {message}")
                                continue
                            valid_injuries = self.__validate_injuries(user_profile, control_program)
                            if valid_injuries[0] and configurations["is_personalized"]:
                                message[self.__calculate_index(session_value, program_design.day)].append(
                                    f"{control_program.exercise.name} skipped due to {valid_injuries[1]}"
                                )
                                logger.info(f"Invalid injury for user_profile {user_profile.id}: {message}")
                                continue
                            calculated_weight = 0
                            calculated_reps = 0
                            user_calculated_reps = (0,)
                            user_calculated_weight = (0,)
                            system_calculated_reps = (0,)
                            system_calculated_weight = (0,)
                            logger.info(
                                f"Before Calculation for control_program: {control_program.id} user_calculated_reps: "
                                f"{user_calculated_reps}, user_calculated_weight: {user_calculated_weight}, "
                                f"system_calculated_reps: {system_calculated_reps}, system_calculated_weight: "
                                f"{system_calculated_weight}"
                            )
                            if configurations["is_personalized"]:
                                first_ever = control_program.fec_control_programs.filter(type="Baseline")
                                if not first_ever.exists():
                                    logger.info(
                                        f"Baseline Formula against control program: {control_program.id}"
                                        f" exercise: {control_program.exercise.name} doesn't exist"
                                    )
                                else:
                                    try:
                                        # If equipment option is none weight calculation will be skipped
                                        if _equipment_options["None"] != control_program.equipment_option.id:
                                            calculated_weight = self.__calculate_weight_baseline(
                                                first_ever[0], user_profile
                                            )
                                        calculated_reps = self.__calculate_reps_baseline(first_ever[0], user_profile)
                                    except Exception as e:
                                        logger.exception(
                                            f"Error occurred due to invalid Baseline formula format : {e.args[0]} "
                                            f"against control program: {control_program.id} exercise: "
                                            f"{control_program.exercise.name}"
                                        )
                            if (
                                calculated_weight == 0
                                and configurations["is_personalized"]
                                # If equipment option is none weight calculation will be skipped
                                and _equipment_options["None"] != control_program.equipment_option.id
                            ) or (not configurations["is_personalized"]):
                                first_ever = control_program.fec_control_programs.filter(type="FSC")
                                if not first_ever.exists():
                                    logger.info(
                                        f"FSC Formula against control program: {control_program.id}"
                                        f" exercise: {control_program.exercise.name} doesn't exist"
                                    )
                                    # if configurations["is_personalized"]:
                                    #     message = f"Baseline and FSC Formulas against control program: {control_program.id}  \  # noqa: E501
                                    #         exercise: {control_program.exercise.name} don't exist"
                                    # else:
                                    #     message = f"FSC Formulas against control program: {control_program.id} \
                                    #         exercise: {control_program.exercise.name} don't exist"
                                    # return Response(response_json(status=False, data=None, message=message))
                                else:
                                    try:
                                        # If equipment option is none weight calculation will be skipped
                                        if _equipment_options["None"] != control_program.equipment_option.id:
                                            calculated_weight = self.__calculate_weight_fsc(
                                                first_ever[0], user_profile
                                            )
                                        calculated_reps = self.__calculate_reps_fsc(first_ever[0], user_profile)
                                    except Exception as e:
                                        logger.exception(
                                            f"Error Occur due to invalid FSC formula format : {e.args[0]} "
                                            f" against control program: {control_program.id} exercise: "
                                            f" {control_program.exercise.name}"
                                        )
                            if (
                                calculated_weight <= 0
                                # If equipment option is none weight calculation will be skipped
                                and _equipment_options["None"] != control_program.equipment_option.id
                            ):
                                message[self.__calculate_index(session_value, program_design.day)].append(
                                    f"Calculated Weight against {control_program.exercise.name} is: \
                                        {calculated_weight}"
                                )
                                continue
                            logger.info(
                                f"After Formula for control_program: {control_program.id}: user_calculated_reps: "
                                f"{user_calculated_reps}, user_calculated_weight: {user_calculated_weight}, "
                                f"system_calculated_reps: {system_calculated_reps}, system_calculated_weight: "
                                f"{system_calculated_weight} calculated_weight: {calculated_weight} "
                                f"calculated_reps: {calculated_reps}"
                            )

                            calculated_reps -= reps_in_reserve

                            logger.info(
                                f"After minus reps_in_reserve: reps_in_reserve: {reps_in_reserve} "
                                f"calculated_weight: {calculated_weight} calculated_reps: {calculated_reps}"
                            )
                            if calculated_weight in user_weight_list:
                                if not validate_reps_range(calculated_reps, reps_list):
                                    message[self.__calculate_index(session_value, program_design.day)].append(
                                        f"Calculated Rep {calculated_reps} for {control_program.exercise.name} against"
                                        f" {session_length.goal.name} does not exist"
                                    )
                                    continue
                                user_calculated_reps = calculated_reps
                                user_calculated_weight = calculated_weight
                                system_calculated_reps = calculated_reps
                                system_calculated_weight = calculated_weight
                                logger.info(
                                    f"Weight is in user_weight_list and Reps Range valid: user_calculated_reps: "
                                    f"{user_calculated_reps}, user_calculated_weight: {user_calculated_weight}, "
                                    f"system_calculated_reps: {system_calculated_reps}, system_calculated_weight: "
                                    f"{system_calculated_weight}"
                                )
                            elif _equipment_options["None"] == control_program.equipment_option.id:

                                if not validate_reps_range(calculated_reps, reps_list):
                                    message[self.__calculate_index(session_value, program_design.day)].append(
                                        f"Calculated Rep {calculated_reps} for {control_program.exercise.name} against"
                                        f" {session_length.goal.name} does not exist"
                                    )
                                    continue
                                user_calculated_reps = calculated_reps
                                user_calculated_weight = calculated_weight
                                system_calculated_reps = calculated_reps
                                system_calculated_weight = 0
                                logger.info(
                                    f"Weight NOT in user_weight_list and Reps Range valid: user_calculated_reps: "
                                    f"{user_calculated_reps}, user_calculated_weight: {user_calculated_weight}, "
                                    f"system_calculated_reps: {system_calculated_reps}, system_calculated_weight: "
                                    f"{system_calculated_weight}"
                                )

                            else:

                                closest_weight = find_closest_weight(user_weight_list, calculated_weight)
                                adjusted_reps = self.__adjust_weights_reps(
                                    control_program=control_program,
                                    calculated_reps=calculated_reps,
                                    calculated_weight=calculated_weight,
                                    required_weight=closest_weight,
                                )
                                logger.info(f"Closest weight: {closest_weight}, Adjusted Reps: {adjusted_reps}")
                                if adjusted_reps <= 0:
                                    message[self.__calculate_index(session_value, program_design.day)].append(
                                        f"Adjusted Reps for {control_program.exercise.name}is: {adjusted_reps}"
                                    )
                                    continue
                                elif not validate_reps_range(adjusted_reps, reps_list):
                                    message[self.__calculate_index(session_value, program_design.day)].append(
                                        f"Calculated Reps {adjusted_reps} for {control_program.exercise.name} against "
                                        f"{session_length.goal.name} does not exist!!!"
                                    )
                                    continue

                                user_calculated_reps = calculated_reps
                                user_calculated_weight = calculated_weight
                                system_calculated_weight = closest_weight
                                system_calculated_reps = adjusted_reps
                            equipments = [
                                (_eq.equipment)
                                for _eq in EquipmentGroup.objects.filter(equipment_combination_id=com_id)
                            ]
                            eq_option = None
                            if equipments:
                                eq_option = UserEquipment.objects.get(
                                    equipment_id=equipments[0].id, user_profile_id=user_profile.id
                                ).equipment_option.name
                            record = {
                                "pd_id": str(program_design.id),
                                "workout_id": workout.id,
                                "session_id": session_length.id,
                                "checked": False,
                                "goal": str(session_length.goal.name),
                                "total_sets": session_length.total_sets,
                                "workout_time": str(session_length.workout_time),
                                "rest_time": str(session_length.rest_time),
                                "warm_up_time": str(session_length.warm_up_time),
                                "name": str(workout.name),
                                "value": str(workout.value),
                                "equipment_types": [
                                    eq.weight_type
                                    for eq in user_profile.user_profile_equipments.all().distinct("weight_type")
                                ],
                                "session_per_week": str(program_design.session_per_week.value),
                                "equipment_option": eq_option,
                                "exercise": str(control_program.exercise.name),
                                "is_two_sided": control_program.is_two_sided,
                                "reps": str(control_program.reps),
                                "weight": str(control_program.weight),
                                "equipments": [str(equipments[0].name)] if equipments else [],
                                "total_session_length": str(session_length.total_session_length),
                                "user_calculated_reps": str(user_calculated_reps),
                                "user_calculated_weight": str(user_calculated_weight),
                                "system_calculated_reps": system_calculated_reps,
                                "system_calculated_weight": system_calculated_weight,
                                "created_at": str(control_program.created_at),
                                "updated_at": str(control_program.updated_at),
                                "videos": [{"url": str(video.url)} for video in control_program.cp_videos.all()],
                            }
                            # handle index on runtime w.r.t sessions if session is 2 and 3 day comes then it will
                            # put at day one
                            index = self.__calculate_index(program_design.session_per_week.value, program_design.day)
                            data[index].append(record)
                            break  # skip remaining cp against one pd
                        else:
                            logging.info(f"Exercise: {control_program.exercise.name} already added")
        data = self.__repeat_sets(data, user_weight_list)
        # add skipped days in log
        for key in data.keys():
            if len(data[key]) == 0:  # day will be empty
                logger.info(f"day {key} exercise missed due to {str(message[key])}")
        for key in data.keys():
            data[key] = sorted(data[key], key=lambda d: d["value"])

        return data, message, configurations

    @swagger_auto_schema(
        request_body=UserWorkoutProgramSerializer,
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def post(self, request, *args, **kwargs):
        try:

            request_data = request.data
            serializer = UserWorkoutProgramSerializer(data=request_data)
            if not serializer.is_valid():
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=serializer.errors,
                    ),
                    status=status.HTTP_200_OK,
                )
            user_profile = UserProfile.objects.filter(user_id=request.user.id)
            if not user_profile.exists():
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=f"Application did not find any record against {request.user}",
                    ),
                    status=status.HTTP_200_OK,
                )

            # generate user programs
            data, message, configurations = self.__generate_userprograms(request_data, user_profile)

            # save user programs in db
            save_user_program_designs(
                user_profile[0],
                configurations["session_per_week"],
                configurations["goal"],
                configurations["is_personalized"],
                data,
            )

            logger.info(f"User profile {user_profile[0].id}: \n \n data: {data} \n \n message: {message}")

            user_profile = user_profile.first()
            # update userprofile programdesign exists indicator
            user_profile.is_pd_exist = True
            user_profile.save()

            return Response(response_json(status=True, data=data, message=message), status=status.HTTP_201_CREATED)

        except Exception as e:
            messages = f"Error {e.args[0]} occurred while fetching the data from the database."
            logger.exception(f"{messages}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=messages), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView(APIView):
    """UserProfileView class

    This view contains GET, POST and PUT request for current user.

    Parameters
    ----------
    APIView : rest_framework.views
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=SwaggerUserProfileSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):
        """post function
        A HTTP api endpoint that Add user's data.

        ```
        Request body format:
        {
            "equipment_exist": "yes",
            "fitness_level":90,
            "gym_type":"home",
            "longitude":45.4703983,
            "lattitude":90.2750666,
            "equipments":
                [
                    {
                    "equipment":396,
                    "equipment_type": null,
                    "weights":
                        [
                           {"2":1},
                           {"4":2}
                        ],

                    "equipment_option": "1 Weight",
                    "weight_type": "kg"
                    }
                ],
            "standard_variables":
                [
                    {
                        "standard_variable_id": 64,
                        "value": "70"
                    }
                ]
        }
        ```

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns success message if user's data successfully inserts, error message otherwise
        """
        message = "Error occurred while saving the data into the database."
        try:
            with transaction.atomic():
                standard_variables = []
                equipments = []
                user = self.get_user_profile_object(request.user.id, "email")
                if user:
                    return Response(
                        response_json(status=False, data=None, message="User Already Exist"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                data = request.data
                data["user_id"] = request.user.id
                if "equipments" in data.keys():
                    equipments = data.pop("equipments")
                if "standard_variables" in data.keys():
                    standard_variables = data.pop("standard_variables")
                user_serializer = UserProfileSerializer(data=data)
                if user_serializer.is_valid():
                    user_profile = user_serializer.save()
                    for std in standard_variables:
                        std["user_profile"] = user_profile.id
                    for equipment in equipments:
                        equipment["user_profile"] = user_profile.id
                        equipment_option_id = EquipmentOption.objects.filter(
                            name__iexact=equipment["equipment_option"]
                        )[0].id
                        equipment["equipment_option"] = equipment_option_id
                    standard_variable_serializer = UserStandardVariableSerializer(data=standard_variables, many=True)
                    equipment_serializer = UserEquipmentSerializer(data=equipments, many=True)
                    if standard_variable_serializer.is_valid():
                        standard_variable_serializer.save()
                        if equipment_serializer.is_valid():
                            equipment_serializer.save()
                            return Response(
                                response_json(
                                    status=True,
                                    data=UserProfileSerializer(user_profile).data,
                                    message="User profile has saved successfully",
                                ),
                                status=status.HTTP_201_CREATED,
                            )
                        else:
                            raise IntegrityError(equipment_serializer.errors)
                    else:
                        raise IntegrityError(standard_variable_serializer.errors)
                else:
                    raise IntegrityError(user_serializer.errors)
        except IntegrityError as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=SwaggerUserProfileSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    def patch(self, request):
        """patch function
        A HTTP api endpoint that edit user's data.

        ```
        Request body format:
        {
            "goal":goal_id,
            "email":"user's email",
            "is_personalized":true,
            "baseline_assessment":[
                {"id":90,"question":"How many pull-ups can you do?","value":5},
                {"id":91,"question":"How many pushups can you do?","value":"30"},
                {"id":92,"question":"How many squats can you do?","value":"0"},
                {"id":102,"question":"How can I make my muscles more strong?","value":"0"},
                {"id":105,"question":"How many pull-ups can you do?","value":"0"}
            ],
            "session":session_id,
            "max_session_length":30,
            "injuries":
                [
                    {
                        "injury":injury_id,
                        "injury_type":injury_type_id
                    },
                    {
                        "injury":injury_id,
                        "injury_type":injury_type_id
                    }
                ],
            "standard_variables":
                [
                    {
                    "standard_variable_id": standard_variable_id,
                    "value": "190"
                    },
                    {
                    "standard_variable_id": standard_variable_id,
                    "value": "male"
                    },
                    {
                    "standard_variable_id": standard_variable_id,
                    "value": "10-10-1990"
                    }
                ],
                "equipments":[
                    {
                        "equipment":equipment_id,
                        "equipment_type":equipment_type_id,
                        "weights":
                            [
                               {"2":1},
                               {"4":2}
                            ],
                        "equipment_option": "1 Weight",
                        "weight_type": "kg"
                    },
                    {
                        "equipment":equipment_id,
                        "equipment_type":null,
                        "equipment_option": "None"
                    }
                ]
        }
        ```

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns success message if user's data successfully updates, error message otherwise
        """
        message = "Error occurred while updating the data in the database."
        if request.data["email"] == request.user.email:
            user = self.get_user_profile_object(user_id=request.user.id, email=request.data["email"])
            if user is None:
                return Response(
                    response_json(
                        status=False, data=None, message=f"User with the email: {request.data['email']} doesn't exist"
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                response_json(
                    status=False, data=None, message=f"User with the email: {request.data['email']} doesn't exist"
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            with transaction.atomic():
                injuries = []
                standard_variables = []
                equipments = []
                data = request.data
                data["user_id"] = request.user.id
                data.pop("email")
                if "injuries" in data.keys():
                    injuries = data.pop("injuries")
                if "standard_variables" in data.keys():
                    standard_variables = data.pop("standard_variables")
                if "equipments" in data.keys():
                    equipments = data.pop("equipments")

                user_serializer = UserProfileSerializer(user, data=data)
                if user_serializer.is_valid():
                    user_profile = user_serializer.save()
                    for std in standard_variables:
                        std["user_profile"] = user_profile.id
                        standard_variable_check = UserStandardVariable.objects.filter(
                            user_profile_id=std["user_profile"], standard_variable_id=std["standard_variable_id"]
                        )
                        if standard_variable_check.exists():
                            standard_variable_check.update(value=std["value"], unit=std["unit"])
                        else:
                            us_variable_serializer = UserStandardVariableSerializer(data=std)
                            if us_variable_serializer.is_valid():
                                us_variable_serializer.save()
                            else:
                                raise IntegrityError(us_variable_serializer.errors)

                    for injury in injuries:
                        injury["user_profile"] = user_profile.id
                        injury_check = UserInjury.objects.filter(
                            user_profile_id=injury["user_profile"],
                            injury_id=injury["injury"],
                            injury_type_id=injury["injury_type"],
                        )
                        if injury_check.exists():
                            injury_check.update(injury_id=injury["injury"], injury_type_id=injury["injury_type"])
                        else:
                            user_injury_serializer = UserInjurySerializer(data=injury)
                            if user_injury_serializer.is_valid():
                                user_injury_serializer.save()
                            else:
                                raise IntegrityError(user_injury_serializer.errors)

                    for equipment in equipments:
                        equipment["user_profile"] = user_profile.id
                        equipment_option_id = EquipmentOption.objects.filter(
                            name__iexact=equipment["equipment_option"]
                        )[0].id
                        equipment["equipment_option"] = equipment_option_id
                        equipment_check = UserEquipment.objects.filter(
                            user_profile_id=equipment.get("user_profile"),
                            equipment_id=equipment.get("equipment"),
                            equipment_type_id=equipment.get("equipment_type"),
                            equipment_option_id=equipment_option_id,
                        )
                        if equipment_check.exists():
                            equipment_check.update(
                                equipment_id=equipment.get("equipment"),
                                equipment_type_id=equipment.get("equipment_type"),
                                weights=equipment.get("weights"),
                                equipment_option=equipment_option_id,
                            )
                        else:
                            user_equipment_serializer = UserEquipmentSerializer(data=equipment)
                            if user_equipment_serializer.is_valid():
                                user_equipment_serializer.save()
                            else:
                                raise IntegrityError(user_equipment_serializer.errors)
                    return Response(
                        response_json(
                            status=True,
                            data=UserProfileSerializer(user_profile).data,
                            message="User profile updated successfully",
                        ),
                        status=status.HTTP_200_OK,
                    )
                else:
                    raise IntegrityError(user_serializer.errors)
        except IntegrityError as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
        manual_parameters=[
            Parameter("email", IN_QUERY, type="string"),
        ],
    )
    def get(self, request):
        """HTTP get request.
        A HTTP api endpoint that gets user's data from database.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for user's data objects, error message otherwise
        """
        try:
            email = request.GET.get("email", None)
            if email == request.user.email:
                user_profile = self.get_user_profile_object(user_id=request.user.id, email=email)
                if user_profile is None:
                    return Response(
                        response_json(
                            status=False,
                            data=None,
                            message=f"User with the email: {email} doesn't exist",
                        ),
                        status=status.HTTP_404_NOT_FOUND,
                    )
                user_profile_data = UserProfileSerializer(user_profile).data
                user_standard_variables = user_profile.user_profiles_std_var.all()
                standard_variables = []
                for user_standard_variable in user_standard_variables:
                    standard_variables.append(user_standard_variable.to_dict())
                user_profile_data["standard_variables"] = standard_variables
                user_equipments = user_profile.user_profile_equipments.all()
                equipments = []
                for user_equipment in user_equipments:
                    equipments.append(UserEquipmentSerializer(user_equipment).data)
                user_profile_data["equipments"] = equipments
                user_injuries = user_profile.user_profile_injuries.all()
                injuries = []
                for user_injury in user_injuries:
                    injuries.append(user_injury.to_dict())
                user_profile_data["injuries"] = injuries
                return Response(response_json(status=True, data=user_profile_data), status=status.HTTP_200_OK)
            else:
                return Response(
                    response_json(status=False, data=None, message=f"User with the email: {email} doesn't exist"),
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={200: "OK", 400: "Bad Request", 500: "Internal Server Error"},
    )
    def delete(self, request):
        user_id = request.data["user_id"]
        try:
            user = UserProfile.objects.get(user_id=user_id)
            user.delete()
            return Response(
                response_json(
                    status=True,
                    data=None,
                    message="User profile deleted successfully",
                ),
                status=status.HTTP_200_OK,
            )
        except UserProfile.DoesNotExist:
            logger.info(f"User with the user_id: {user_id} doesn't exist")
            message = logger.info(f"User with the email: {user_id} doesn't exist")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_user_profile_object(self, user_id, email):
        """get_user_profile_object function

        A function that gets user based on user_id from UserProfile table.

        Parameters
        ----------
        user_id : user's id

        Returns
        -------
        returns user object, None otherwise
        """
        try:
            user = UserProfile.objects.get(user_id=user_id)
            return user
        except UserProfile.DoesNotExist:
            logger.info(f"User with the email: {email} doesn't exist")
            return None


class UserFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=SwaggerUserFeedbackSerializer,
        responses={
            200: "OK",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    def post(self, request):

        """post function
        A HTTP api endpoint that Add user's Feedback data.

        ```
        Request body format:
        {
            "email": "user's email",
            "user_program_design": "user_program_design_id"
            "feedbacks":
                [
                    {
                        "feedback": feedback_id,
                        "value": user's answer
                    },
                    {
                        "feedback": feedback_id,
                        "value": user's answer
                    }
                ]
        }
        ```

        Parameters
        ----------
        request : django.http.request
        Returns
        -------
        rest_framework.response.Response
            returns success message if user's feedback successfully inserts, error message otherwise
        """
        message = "Error occurred while saving the data into the database."
        try:
            with transaction.atomic():
                user_profile = UserProfileView()
                if request.data["email"] == request.user.email:
                    user = user_profile.get_user_profile_object(user_id=request.user.id, email=request.data["email"])
                    if user is None:
                        return Response(
                            response_json(
                                status=False,
                                data=None,
                                message=f"User with the email: {request.data['email']} doesn't exist",
                            ),
                            status=status.HTTP_404_NOT_FOUND,
                        )
                else:
                    return Response(
                        response_json(
                            status=False,
                            data=None,
                            message=f"User with the email: {request.data['email']} doesn't exist",
                        ),
                        status=status.HTTP_404_NOT_FOUND,
                    )
                data = request.data
                if "feedbacks" in data.keys():
                    for feedback in data["feedbacks"]:
                        feedback["user_profile"] = user.id
                        feedback_check = UserFeedback.objects.filter(
                            user_profile=user.id,
                            feedback=feedback["feedback"],
                            user_program_design=feedback["user_program_design"],
                        )
                        if feedback_check.exists():
                            feedback_check.update(
                                feedback=feedback["feedback"],
                                value=feedback["value"],
                                user_program_design=feedback["user_program_design"],
                            )
                        else:
                            user_feedback_serializer = UserFeedbackSerializer(data=feedback)
                            if user_feedback_serializer.is_valid():
                                user_feedback_serializer.save()
                            else:
                                return Response(
                                    response_json(status=False, data=user_feedback_serializer.errors, message=message),
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                    return Response(
                        response_json(status=True, data=None, message="Feedback saved successfully."),
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    data.pop("email")
                    data["user_profile"] = user.id
                    feedback_check = UserFeedback.objects.filter(
                        user_profile=user.id,
                        feedback=data["feedback"],
                        user_program_design=data["user_program_design"],
                    )
                    if feedback_check.exists():
                        feedback_check.update(
                            feedback=data["feedback"],
                            value=data["value"],
                            user_program_design=data["user_program_design"],
                        )
                    else:
                        user_feedback_serializer = UserFeedbackSerializer(data=data)
                        if user_feedback_serializer.is_valid():
                            user_feedback_serializer.save()
                        else:
                            return Response(
                                response_json(status=False, data=user_feedback_serializer.errors, message=message),
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    return Response(
                        response_json(status=True, data=None, message="Feedback saved successfully."),
                        status=status.HTTP_201_CREATED,
                    )
        except IntegrityError as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=e.args[0]), status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
        manual_parameters=[
            Parameter("email", IN_QUERY, type="string"),
        ],
    )
    def get(self, request):
        """HTTP get request.
        A HTTP api endpoint that get all User's Feedbacks from database.

        Parameters
        ----------
        request : django.http.request

        Returns
        -------
        rest_framework.response.Response
            returns JSON object for all User's Feedback objects, error message otherwise
        """
        message = "Error occurred while saving the data into the database."
        try:
            email = request.GET.get("email", None)
            user_profile = UserProfileView()
            if email == request.user.email:
                user = user_profile.get_user_profile_object(user_id=request.user.id, email=email)
                if user is None:
                    return Response(
                        response_json(
                            status=False,
                            data=None,
                            message=f"User with the email: {email} doesn't exist",
                        ),
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    response_json(
                        status=False,
                        data=None,
                        message=f"User with the email: {email} doesn't exist",
                    ),
                    status=status.HTTP_404_NOT_FOUND,
                )
            feedbacks = UserFeedback.objects.filter(user_profile_id=user.id)
            data = []
            for feedback in feedbacks:
                data.append(
                    {
                        "value": feedback.value,
                        "id": feedback.id,
                        "name": feedback.feedback.name,
                        "fv_feedbacks": [
                            {"id": fv.id, "description": fv.description, "value": fv.value}
                            for fv in feedback.feedback.fv_feedbacks.all()
                        ],
                        "user_program_design": {
                            "id": feedback.user_program_design.id,
                            "day": feedback.user_program_design.day,
                            "program_design": feedback.user_program_design.program_design,
                            "workout_date": feedback.user_program_design.workout_date,
                            "is_complete": feedback.user_program_design.is_complete,
                            "week": feedback.user_program_design.week,
                            "is_personalized": feedback.user_program_design.is_personalized,
                            "system_rir": feedback.user_program_design.system_rir,
                        },
                    }
                )
            return Response(
                data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProgramDesignView(APIView):
    """UserProgramDesignView class

    This view contains GET method class UserProgramDesignView

    Parameters
    ----------
    APIView : rest_framework.views
    """

    permission_classes = [permissions.IsAuthenticated]

    def __get_user_programs(self, user_id, query_params):
        user_profile = UserProfile.objects.get(pk=user_id)
        is_personalized = user_profile.is_personalized
        default_session_length = Config.objects.filter(key="total_session_length")[0].value
        default_goal = Goal.objects.get(pk=Config.objects.filter(key="goal")[0].value).name
        if is_personalized:
            default_session_length = int(user_profile.max_session_length)
            default_session_length = str(default_session_length) + ".00"
            default_goal = user_profile.goal.name

        kwargs = {}
        kwargs["goal"] = default_goal
        kwargs["total_session_length"] = default_session_length
        start_date = None
        end_date = None

        for parameter in query_params:
            if parameter == "startdate":
                start_date = query_params["startdate"]
                start_date = datetime.datetime.fromisoformat(start_date)

            elif parameter == "endate":
                end_date = query_params["endate"]
                end_date = datetime.datetime.fromisoformat(end_date)

            else:
                value = query_params[parameter]
                if "[" in value:
                    kwargs[parameter] = JSON.loads(value)
                else:
                    kwargs[parameter] = value

        kwargs = [kwargs]
        user_programs = UserProgramDesign.objects.filter(
            user=user_id,
            program_design__contains=kwargs,
            workout_date__date__range=[start_date, end_date],
            is_personalized=is_personalized,
        )

        return user_programs

    def __get_user_sessions_per_week(self, user_profile_id):
        user_profile = UserProfile.objects.get(pk=user_profile_id)
        if user_profile.is_personalized:
            session_per_week = user_profile.session.value
        else:
            session_per_week = Session.objects.get(pk=Config.objects.filter(key="session_per_week")[0].value).value

        return session_per_week

    def __update_user_programs_dates(self, session, user_id):

        current_date = datetime.datetime.now()
        is_end_date_updated = False
        updated_end_date = None
        start_date = None
        is_personalized = UserProfile.objects.get(pk=user_id).is_personalized
        # scenario: no workout today,click on train today, prepone one day
        if session == UserSession.preponeone.name:

            # get all those userprograms where workout date is greater than current date
            user_programs = UserProgramDesign.objects.filter(
                user=user_id,
                workout_date__gt=current_date,
                is_complete=False,
                is_personalized=is_personalized,
            ).order_by("workout_date")
            if user_programs.count() > 0:
                # select next available userprogram
                selected_pd = user_programs[0]
                # assign current date to this userprogram
                selected_pd.workout_date = current_date
                selected_pd.save()

        # scenario: no workout today,click on train today, prepone whole program
        elif session == UserSession.preponeall.name:

            # get session per week from user profile
            session_per_week = self.__get_user_sessions_per_week(user_id)
            # get all those userprograms where workout date is greater than current date
            user_programs = UserProgramDesign.objects.filter(
                user=user_id,
                workout_date__gt=current_date,
                is_complete=False,
                is_personalized=is_personalized,
            ).order_by("workout_date")
            # initialize userprograms counter
            user_programs_counter = 0

            if user_programs.count() > 0:

                # define gaps for each session per week
                gaps = {1: 6, 2: 3, 3: 1, 4: 1, 5: 1, 6: 1}

                # select next available userprogram
                selected_pd = user_programs[user_programs_counter]
                # assign current date to this userprogram
                selected_pd.workout_date = current_date
                selected_pd.save()

                # set start date (same for all records)
                start_date = selected_pd.start_date

                # get day difference for session
                difference = gaps[session_per_week]

                while user_programs_counter < user_programs.count():
                    # select next  userprogram
                    selected_pd = user_programs[user_programs_counter]
                    # save end date
                    updated_end_date = selected_pd.workout_date + datetime.timedelta(days=difference * -1)
                    # prepone workout date by day difference
                    selected_pd.workout_date = selected_pd.workout_date + datetime.timedelta(days=difference * -1)
                    selected_pd.save()
                    # increment counter to get next userprogram
                    user_programs_counter = user_programs_counter + 1
                    # update end date in the end
                    is_end_date_updated = True

        # scenario: all workouts will increment by 1 day
        elif session == UserSession.postponeall.name:

            # get all those userprograms where workout date is greater than or equal to current date
            user_programs = UserProgramDesign.objects.filter(
                user=user_id,
                workout_date__date__gte=current_date,
                is_complete=False,
                is_personalized=is_personalized,
            ).order_by("workout_date")
            # loop all userprograms
            for program in user_programs:
                # postpone workout date by 1 day
                updated_end_date = program.workout_date + datetime.timedelta(days=1)
                program.workout_date = updated_end_date
                is_end_date_updated = True
                start_date = program.start_date
                program.save()

        # scenario: reschedule whole program upon missed sessions and delete previous one
        elif session == UserSession.rescheduleall.name:
            # initialize total days difference
            difference = None
            # get most recent workout
            recent_workout = UserProgramDesign.objects.filter(
                user=user_id,
                workout_date__date__lt=current_date,
                is_personalized=is_personalized,
            ).order_by("workout_date")

            if recent_workout.exists():
                # fetch last workout
                recent_workout = recent_workout.last()

                # get data from most recent workout
                is_personalized = recent_workout.is_personalized
                starting_date = recent_workout.start_date
                start_date_for_range = starting_date

                # check if most recent workout is complete
                if recent_workout.is_complete:
                    recent_complete_date = recent_workout.workout_date
                    # get number of days between last complete date and current date
                    difference = abs((recent_complete_date.replace(tzinfo=None) - current_date).days)
                    start_date_for_range = recent_complete_date

                else:
                    # check if any workout is complete inbetween
                    complete_workout = UserProgramDesign.objects.filter(
                        user=user_id,
                        start_date=starting_date,
                        is_complete=True,
                        workout_date__date__lt=current_date,
                        is_personalized=is_personalized,
                    ).order_by("workout_date")
                    if complete_workout.exists():
                        # fetch workout date of last completed workout
                        complete_workout_date = complete_workout.last().workout_date
                        # calculate difference
                        difference = abs((complete_workout_date.replace(tzinfo=None) - current_date).days)
                        start_date_for_range = complete_workout_date

                    else:
                        # fetch first incomplete session for current programdesign
                        first_missed_session_date = (
                            UserProgramDesign.objects.filter(
                                user=user_id,
                                start_date=starting_date,
                                is_complete=False,
                                workout_date__date__lt=current_date,
                                is_personalized=is_personalized,
                            )
                            .order_by("workout_date")
                            .first()
                            .workout_date
                        )
                        # calculate difference
                        difference = abs((first_missed_session_date.replace(tzinfo=None) - current_date).days)

                # case if total missed days are less than 14(reschedule missed and future sessions)
                if difference <= 14:

                    first_actual_missed_session = UserProgramDesign.objects.filter(
                        user=user_id,
                        start_date=starting_date,
                        is_complete=False,
                        workout_date__date__range=[start_date_for_range, current_date],
                        is_personalized=is_personalized,
                    ).order_by("workout_date")
                    if first_actual_missed_session.exists():
                        # fetch workout date of first actual missed session
                        first_actual_missed_session_date = first_actual_missed_session.first().workout_date
                        move_forward_gap = abs(
                            (first_actual_missed_session_date.replace(tzinfo=None) - current_date).days
                        )

                        # get all user programs where workout date is greater then actual missed date for current user
                        all_user_programs = UserProgramDesign.objects.filter(
                            user=user_id,
                            start_date=starting_date,
                            workout_date__date__gte=first_actual_missed_session_date,
                            is_personalized=is_personalized,
                        )
                        # update workout date according to calculated days gap
                        for user_pd in all_user_programs:
                            new_workout_date = user_pd.workout_date + datetime.timedelta(days=move_forward_gap)
                            user_pd.workout_date = new_workout_date
                            user_pd.save()
                else:
                    # get first week data and sessions from current user program to reset all workouts
                    user_programs = UserProgramDesign.objects.filter(
                        week=1,
                        user=user_id,
                        start_date=starting_date,
                        is_personalized=is_personalized,
                    ).values("program_design")
                    if user_programs.exists():
                        # get sessions per week
                        session_per_week = self.__get_user_sessions_per_week(user_id)
                        data = [pd["program_design"] for pd in user_programs]

                        # reschedule(reset) all programdesigns based on above data
                        re_schedule_user_program_designs(
                            user_id, session_per_week, is_personalized, data, starting_date
                        )

        if is_end_date_updated:
            UserProgramDesign.objects.filter(
                user=user_id,
                start_date=start_date,
                is_personalized=is_personalized,
            ).update(end_date=updated_end_date)

    def __update_user_rir(self, user_rir, execise_id, user_pd_id):
        user_pd = UserProgramDesign.objects.get(pk=user_pd_id)
        user_pd.program_design[execise_id - 1]["user_rir"] = user_rir
        user_pd.save()

    def __update_next_exercise(self, user_program_design, exercise_id, weight, rep):

        # current userprogram information
        day = user_program_design.day
        week = user_program_design.week
        # workout_date = user_program_design.workout_date
        current_pd = None
        for pd in user_program_design.program_design:
            if pd["id"] == exercise_id:
                current_pd = pd
        set = int(current_pd["set"]) + 1
        set = str(set)
        workout_name = current_pd["value"]
        exercise_name = current_pd["exercise"]

        # update exercise in same day
        for counter, pd in enumerate(user_program_design.program_design):
            if pd["set"] == set and pd["value"] == workout_name:
                user_program_design.program_design[counter]["system_calculated_reps"] = int(rep)
                user_program_design.program_design[counter]["system_calculated_weight"] = weight
                user_program_design.save()
                return

        # update exercise in next week
        set = "1"
        week = week + 1
        # new_date = workout_date + datetime.timedelta(days=7)
        next_user_pd = UserProgramDesign.objects.filter(
            user=user_program_design.user,
            week=week,
            day=day,
            is_complete=False,
            is_personalized=user_program_design.is_personalized,
        )
        if next_user_pd.exists():
            next_user_pd = next_user_pd[0]
            logger.info(f"checking in {next_user_pd.id}")
            for counter, exercise in enumerate(next_user_pd.program_design):
                if (
                    exercise["set"] == set
                    and exercise["value"] == workout_name
                    and exercise["exercise"] == exercise_name
                ):
                    next_user_pd.program_design[counter]["system_calculated_reps"] = int(rep)
                    next_user_pd.program_design[counter]["system_calculated_weight"] = weight
                    logger.info(
                        f"RIR updated in {next_user_pd.id}, set={set}, workout_name={workout_name}, "
                        f"exercise_name{exercise_name}"
                    )
                    next_user_pd.save()
                    return

    def __update_user_weight_reps(
        self, user_rir, system_rir, system_calculated_reps, system_calculated_weight, user_pd_id, exercise_id
    ):
        logger.info("********update_user_weight_reps function*********")
        logging.info(
            f"user_rir: {user_rir}, system_rir: {system_rir}, system_calculated_reps: {system_calculated_reps}, "
            f"system_calculated_weight: {system_calculated_weight}, user_pd_id: {user_pd_id}, exercise: {exercise_id}"
        )
        # calculate difference
        difference = int(user_rir - system_rir)
        # get user programdesign
        user_program_design = UserProgramDesign.objects.get(pk=user_pd_id)
        # get user profile
        user_profile = user_program_design.user
        # get goal
        if user_program_design.is_personalized:
            goal = user_profile.goal.id
        else:
            goal = Goal.objects.get(pk=Config.objects.filter(key="goal")[0].value).id

        # get exercise reps and weights
        exercise_reps = float(user_program_design.program_design[exercise_id - 1]["reps"])
        exercise_weight = float(user_program_design.program_design[exercise_id - 1]["weight"])

        # get reprange against goal and system calculated reps value, return if not found
        repsrange = None
        try:
            repsrange = RepsRange.objects.get(goal=goal, value=system_calculated_reps)
        except RepsRange.DoesNotExist:
            # get repsranges against goal
            reps_list = fetch_reps_list(goal)
            # validate if rep exists in reps_list
            is_valid_reps_range = validate_reps_range(system_calculated_reps, reps_list)
            logger.info(f"reps_list: {reps_list}, is_valid_reps_range: {is_valid_reps_range}")
            if is_valid_reps_range:
                # get the highest reps range value
                repsrange = RepsRange.objects.filter(goal=goal).order_by("value").last()
                logger.info(f"repsrange: {repsrange}")
            else:
                return "RepsRange invalid against goal:" + str(goal) + " and value:" + str(system_calculated_reps)

        # get values from reprating
        ratings = RepsRating.objects.filter(reps_range=repsrange.id)

        # check upper limit
        if difference > 3:
            ratings = ratings.filter(rating=3)
        # check lower limit
        elif difference < -3:
            ratings = ratings.filter(rating=-3)
        # get values based on difference
        else:
            ratings = ratings.filter(rating=difference)

        # get weight and reps from of resultant reprange row
        weight = ratings[0].weight
        reps = ratings[0].reps

        # calculate new weight and reps
        new_reps = int(system_calculated_reps) + reps
        new_weight = abs(int(system_calculated_weight) + (weight * 2.5))

        if int(system_calculated_weight) != 0:

            # get closest weight from user equipments
            user_weight_list = list()
            for equipment in user_profile.user_profile_equipments.all():
                if equipment.weights is not None:
                    user_weight_list.extend([float(key) for key in dict(equipment.weights).keys()])

            # new closest weight
            final_weight = find_closest_weight(user_weight_list, new_weight)
            # adjust reps according to closest weight
            final_reps = adjust_weights_reps_warm_up(
                exercise_reps, exercise_weight, new_reps, new_weight, final_weight
            )
            # get repsranges against goal
            reps_list = fetch_reps_list(goal)
            # validate if rep exists in reps_list
            validate_reps_range(new_reps, reps_list)
            self.__update_next_exercise(user_program_design, exercise_id, final_weight, final_reps)
            logging.info(f"Updated Weights/Reps: final_weight: {final_weight}, final_reps: {final_reps}")

        else:
            final_reps = adjust_weights_reps_warm_up(exercise_reps, exercise_weight, new_reps, new_weight, 0)
            self.__update_next_exercise(user_program_design, exercise_id, 0, final_reps)
            logging.info(f"Updated Weights/Reps: final_weight: 0, final_reps: {final_reps}")

        return "RIR Updated Successfully"

    def __edit_userprograms(self, request, user_profile):

        user_profile_id = user_profile.id
        response_message = ""

        # re-schedule workout case
        if "session" in request.data:
            self.__update_user_programs_dates(request.data["session"], user_profile_id)
            response_message = "Rescheduled workouts successfully against session:" + request.data["session"]

        # update rir case
        elif "user_rir" in request.data:
            user_rir = request.data["user_rir"]
            system_rir = request.data["system_rir"]
            exercise_id = request.data["exercise_id"]
            user_pd_id = request.data["user_program_design_id"]
            system_calculated_reps = request.data["system_calculated_reps"]
            system_calculated_weight = request.data["system_calculated_weight"]
            self.__update_user_rir(user_rir, exercise_id, user_pd_id)
            response_message = self.__update_user_weight_reps(
                user_rir, system_rir, system_calculated_reps, system_calculated_weight, user_pd_id, exercise_id
            )

        # execise complete case
        elif "user_program_design_id" in request.data:
            user_pd = UserProgramDesign.objects.get(pk=request.data["user_program_design_id"])
            user_pd.is_complete = True
            if user_pd.workout_date == user_pd.end_date:
                user_profile.is_pd_exist = False
                user_profile.save()
            user_pd.save()
            response_message = "Exercise marked completed successfully"

        return response_message

    @swagger_auto_schema(
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
        manual_parameters=[
            Parameter("goal", IN_QUERY, type="string"),
            Parameter("week", IN_QUERY, type="string"),
            Parameter("startdate", IN_QUERY, type="string"),
            Parameter("endate", IN_QUERY, type="string"),
            Parameter("total_session_length", IN_QUERY, type="string"),
        ],
    )
    def get(self, request, user_id):
        """HTTP GET request

        A HTTP endpoint that returns program designs for provided user_id
        Sample URL:
        localhost:8000/api/user-programs-designs/1/?goal=goal3&injuries=[{"name":"arm"},{"name":"leg"}]&total_session_length=45,week=2

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """

        try:
            user_profile_id = UserProfile.objects.get(user_id=request.user.id).id
            response_msg = ""
            optional_data = {}
            # check missed sessions
            missed_sessions, response_data = get_missed_sessions(user_profile_id)
            if missed_sessions != 0:
                response_msg = "You have missed " + str(missed_sessions) + " sessions."
                optional_data = response_data

            # return all userprograms for 1 week
            user_programs = self.__get_user_programs(user_profile_id, request.query_params)
            serializer = UserProgramDesignSerializer(user_programs, many=True)
            return Response(
                response_json(status=True, data=serializer.data, message=response_msg, optional_data=optional_data),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        request_body=UserProgramDesignSwaggerSerializer,
        responses={
            200: "OK",
            500: "Internal Server Error",
        },
        manual_parameters=[
            Parameter("goal", IN_QUERY, type="string"),
            Parameter("week", IN_QUERY, type="string"),
            Parameter("startdate", IN_QUERY, type="string"),
            Parameter("endate", IN_QUERY, type="string"),
            Parameter("total_session_length", IN_QUERY, type="string"),
        ],
    )
    def put(self, request, user_id):
        """HTTP GET request

        A HTTP endpoint that updates program designs for provided user_id

        Parameters
        ----------
        request : django.http.request

        pk : integer


        Returns
        -------
        rest_framework.response
            returns HTTP 200 status if data returned successfully,error message otherwise
        """

        try:
            user_profile = UserProfile.objects.get(user_id=request.user.id)
            user_profile_id = user_profile.id

            # edit userprograms
            response_message = self.__edit_userprograms(request, user_profile)

            # return all userprograms
            user_programs = self.__get_user_programs(user_profile_id, request.query_params)
            serializer = UserProgramDesignSerializer(user_programs, many=True)
            return Response(
                response_json(status=True, data=serializer.data, message=response_message), status=status.HTTP_200_OK
            )

        except Exception as e:
            message = "Error occurred while fetching the data from the database."
            logger.exception(f"{message}:  {str(e)}")
            return Response(
                response_json(status=False, data=None, message=message), status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
