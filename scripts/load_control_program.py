# flake8: noqa
import logging
import os
import sys

import numpy as np
import pandas as pd
from dotenv import dotenv_values
from sqlalchemy import create_engine

import django

sys.path.append("..")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joompa.settings")
django.setup()

from django.db import transaction

from apps.body_part.models import BodyPart
from apps.controlled.models import (
    ControlProgram,
    ControlProgramInjury,
    EquipmentCombination,
    EquipmentGroup,
    EquipmentRelation,
    Exercise,
    ExerciseRelationship,
    FirstEverCalc,
    ProgramDesign,
    SessionLength,
    WorkoutFlow,
)
from apps.equipment.models import Equipment, EquipmentOption
from apps.goal.models import Goal
from apps.injury.models import Injury, InjuryType
from apps.session.models import Session
from apps.variance.models import Variance

logger = logging.getLogger(__name__)

base_path = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_path, "../.env")
db_config = dotenv_values(env_path)

engine = create_engine(
    f'postgresql://{db_config["USER"]}:{db_config["PASSWORD"]}@{db_config["HOST"]}:{db_config["PORT"]}/{db_config["NAME"]}'
)

session_length = pd.read_excel("excel/programs.xlsx", sheet_name="session_length")
workout_flow = pd.read_excel("excel/programs.xlsx", sheet_name="workout_flow")
program_design = pd.read_excel("excel/programs.xlsx", sheet_name="program_design")
control_program = pd.read_excel("excel/programs.xlsx", sheet_name="control_program")
injuries = pd.read_excel("excel/programs.xlsx", sheet_name="injuries")
exercise_relation = pd.read_excel("excel/programs.xlsx", sheet_name="exercise_relation")
exercise_combination = pd.read_excel("excel/programs.xlsx", sheet_name="exercise_combination")
first_ever_set = pd.read_excel("excel/programs.xlsx", sheet_name="first_ever_set")
videos = pd.read_excel("excel/programs.xlsx", sheet_name="videos")

goals = Goal.objects.all().values("id", "name")
d_goals = {record["name"]: record["id"] for record in goals}
body_part = BodyPart.objects.all().values("id", "name")
d_body_parts = {record["name"]: record["id"] for record in body_part}
variance = Variance.objects.all().values("id", "name")
d_variance = {record["name"]: record["id"] for record in variance}
equipment_option = EquipmentOption.objects.all().values("id", "name")
d_equipment_option = {record["name"]: record["id"] for record in equipment_option}
injury = Injury.objects.all().values("id", "name")
d_injury = {record["name"]: record["id"] for record in injury}
injury_type = InjuryType.objects.all().values("id", "name")
d_injury_type = {record["name"]: record["id"] for record in injury_type}
equipment = Equipment.objects.all().values("id", "name")
d_equipment = {record["name"]: record["id"] for record in equipment}
session = Session.objects.all().values("id", "value")
d_session = {record["value"]: record["id"] for record in session}

sl_records = session_length.to_dict(orient="records")
session_length = session_length.replace({np.nan: None})
workout_flow = workout_flow.replace({np.nan: None})
program_design = program_design.replace({np.nan: None})
control_program = control_program.replace({np.nan: None})
injuries = injuries.replace({np.nan: None})
first_ever_set = first_ever_set.replace({np.nan: None})
exercise_combination = exercise_combination.replace({np.nan: None})
exercise_relation = exercise_relation.replace({np.nan: None})
videos = videos.replace({np.nan: None})
sl_codes = session_length.code.unique()
pd_record_list = []
wf_record_list = []
# for sl_code in sl_codes:
#     if workout_flow.name is None:
#         workout_flow.name = workout_flow.value
#     work_flows = workout_flow[workout_flow.code == sl_code]
#     pg_design = program_design[program_design.code == sl_code]
#     pd_days = pg_design["day"].unique()
#     workout_days = []
#     for pd_day in pd_days:
#         p_g_design = program_design[(program_design.day == pd_day) & (program_design.code == sl_code)].shape[0]
#         for i in range(p_g_design + 1, 8):
#             wf_record_list.append({"name": i, "value": None, "code": sl_code, "day": program_design.day})
#             pd_record_list.append(
#                 {
#                     "day": pd_day,
#                     "body_part_id": None,
#                     "body_part_classification_id": None,
#                     "variance_id": None,
#                     "session_per_week_id": 1,
#                     "code": sl_code,
#                 }
#             )

fake_wf = pd.DataFrame(wf_record_list)
fake_pd = pd.DataFrame(pd_record_list)
workout_flow = pd.concat([workout_flow, fake_wf], ignore_index=True)
program_design = pd.concat([program_design, fake_pd], ignore_index=True)

session_length = session_length.replace({np.nan: None})
workout_flow = workout_flow.replace({np.nan: None})
program_design = program_design.replace({np.nan: None})
control_program = control_program.replace({np.nan: None})
injuries = injuries.replace({np.nan: None})
first_ever_set = first_ever_set.replace({np.nan: None})
exercise_combination = exercise_combination.replace({np.nan: None})
exercise_relation = exercise_relation.replace({np.nan: None})
videos = videos.replace({np.nan: None})

try:
    with transaction.atomic():
        for sl_record in sl_records:
            sl_code = sl_record.pop("code")
            sl_record["equipment_option_id"] = d_equipment_option[sl_record["equipment_option_id"]]

            sl_record["goal_id"] = d_goals[sl_record["goal_id"]]
            sl = SessionLength.objects.create(**sl_record)
            logger.info(f"SessionLength created with {sl.id}")
            sl_workflow = workout_flow[workout_flow.code == sl_code]
            wf_records = sl_workflow.to_dict(orient="records")
            sl_program_design = program_design[program_design.code == sl_code]
            pd_records = sl_program_design.to_dict(orient="records")
            for wf_record, pd_record in zip(wf_records, pd_records):
                wf_record.pop("code")
                wf_record["session_length"] = sl
                wf_record["value"] = "" if wf_record["value"] is None else wf_record["value"]
                wf_record["name"] = wf_record["value"] if wf_record["name"] is None else wf_record["name"]
                wf = WorkoutFlow.objects.create(**wf_record)
                logger.info(f"WorkoutFlow created with {wf.id}")
                pd_record.pop("code")
                pd_record["session_per_week_id"] = d_session[pd_record["session_per_week_id"]]
                pd_record["sequence_flow"] = wf
                pd_record["body_part_id"] = (
                    d_body_parts[pd_record["body_part_id"].rstrip()] if pd_record["body_part_id"] is not None else None
                )
                if pd_record["body_part_classification_id"]:
                    try:
                        body_part_classification = BodyPart.objects.get(
                            name=pd_record["body_part_classification_id"], classification=pd_record["body_part_id"]
                        ).id
                    except:
                        logger.error(
                            f"Body Part Classification does not Exist against "
                            f"{pd_record['body_part_id'], pd_record['body_part_classification_id']}"
                        )
                else:
                    body_part_classification = None
                pd_record["body_part_classification_id"] = body_part_classification

                pd_record["variance_id"] = (
                    d_variance[pd_record["variance_id"].rstrip()] if pd_record["variance_id"] is not None else None
                )
                pd = ProgramDesign.objects.create(**pd_record)
                logger.info(f"ProgramDesign created with {pd.id}")

        # cp_records = control_program.to_dict(orient="records")
        # for cp_record in cp_records:
        #     exercise = cp_record.pop("exercise")
        #     ex = Exercise.objects.create(name=exercise)
        #     logger.info(f"Exercise created with {ex.id}")
        #     cp_record["exercise"] = ex
        #     cp_code = cp_record.pop("code")
        #     cp_record["equipment_option_id"] = d_equipment_option[cp_record["equipment_option_id"]]
        #     cp_record["body_part_id"] = d_body_parts[cp_record["body_part_id"]]
        #     cp_record["body_part_classification_id"] = d_body_parts[cp_record["body_part_classification_id"]]
        #     cp_record["variance_id"] = d_variance[cp_record["variance_id"]]
        #     cp = ControlProgram.objects.create(**cp_record)
        #     logger.info(f"ControlProgram created with {cp.id}")
        #     injury_records = injuries[injuries.code == cp_code].to_dict(orient="records")
        #     for injury_record in injury_records:
        #         injury_record.pop("code")
        #         injury_record["injury_id"] = d_injury[injury_record["injury_id"]]
        #         injury_record["injury_type_id"] = d_injury_type[injury_record["injury_type_id"]]
        #         injury_record["control_program"] = cp
        #         cp_injury = ControlProgramInjury.objects.create(**injury_record)
        #         logger.info(f"ControlProgramInjury created with {cp_injury.id}")

        #     ex_rel_records = exercise_relation[exercise_relation.code == cp_code].to_dict(orient="records")
        #     for ex_rel_record in ex_rel_records:
        #         ex_rel_record["control_program"] = cp
        #         ex_id = Exercise.objects.filter(name=ex_rel_record["exercise"])[0]
        #         ex_rel_record["exercise"] = ex_id
        #         # handle names with id here
        #         ex_rel_record.pop("code")
        #         ex_relationship = ExerciseRelationship.objects.create(**ex_rel_record)
        #         logger.info(f"ExerciseRelationship created with {ex_relationship.id}")

        #     fes_records = first_ever_set[first_ever_set.code == cp_code].to_dict(orient="records")
        #     for fes_record in fes_records:
        #         fes_record["control_program"] = cp
        #         fes_record["weight_formula_structure"] = "{}"
        #         fes_record["reps_formula_structure"] = "{}"
        #         fes_record.pop("code")
        #         first_ever_set_calc = FirstEverCalc.objects.create(**fes_record)
        #         logger.info(f"FirstEverCalc created with {first_ever_set_calc.id}")

        #     video_records = videos[videos.code == cp_code]
        #     for video_record in video_records:
        #         video_record.pop("code")
        #         video_record["control_program"] = cp
        #     ex_cb_records = exercise_combination[exercise_combination.code == cp_code]
        #     com_names = ex_cb_records.combination_name.unique()
        #     for com_name in com_names:
        #         com = EquipmentCombination.objects.create(name=com_name)
        #         logger.info(f"EquipmentCombination created with {com.id}")
        #         eq_relation = EquipmentRelation.objects.create(exercise_program=cp, equipment_combination=com)
        #         logger.info(f"EquipmentRelation created with {eq_relation.id}")
        #         equipment_group_df = exercise_combination[
        #             (exercise_combination.code == cp_code) & (com_name == exercise_combination.combination_name)
        #         ]
        #         equipment_groups = equipment_group_df.to_dict(orient="records")

        #         for equipment_group in equipment_groups:
        #             eq_id = d_equipment[equipment_group["equipment"]]
        #             eq_group = EquipmentGroup.objects.create(equipment_combination=com, equipment_id=eq_id)
        #             logger.info(f"EquipmentGroup created with {eq_group.id}")
except Exception as e:
    message = "Error occurred while updating the data in the database."
    logger.exception(f"{message}:  {str(e)}")
