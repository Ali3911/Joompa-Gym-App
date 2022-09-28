import logging

from pyfcm import FCMNotification

from django.core.management.base import BaseCommand

from apps.const import notification_messages
from apps.mobile_api.v1.models import UserProfile
from apps.mobile_api.v1.views import get_current_date_missed_sessions, get_missed_sessions
from apps.notification.models import UserNotification

logger = logging.getLogger(__name__)

db_configs = {
    "FIREBASE_API_KEY": "AAAA_wgJtr8:APA91bGXL1gPp88l78ZHItJ2ht7AYBHkpg7Jn2FSgHsKCA38O3JvvT1zCKygk-dvRlSpxNEJmkH"
    "-oKwe54IWSWon78KPR6JGzeI6VG3Ahp3YVK2pf19E9Zs0AkHQPa219T7YLrCndUDj"
}


class Command(BaseCommand):
    help = "Send Notifications to users with cronjob"
    missed_session_dict = {
        "one_day_missed_list": [],
        "two_days_missed_list": [],
        "four_days_missed_list": [],
        "seven_days_missed_list": [],
        "fourteen_days_missed_list": [],
        "twenty_eight_days_missed_list": [],
        "daily_missed_list": [],
    }
    push_service = FCMNotification(api_key=db_configs["FIREBASE_API_KEY"])

    def send_notification(self):
        message_title = "Joompa - AI Trainer"
        extra_notification_kwargs = {"android_channel_id": 2}
        daily_sent_notification = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["daily_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["daily_message"],
        )
        logger.info(daily_sent_notification)
        one_day_sent_notifications = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["one_day_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["one_day_message"],
        )
        logger.info(one_day_sent_notifications)
        two_days_sent_notifications = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["two_days_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["two_day_message"],
        )
        logger.info(two_days_sent_notifications)
        four_days_sent_notifications = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["four_days_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["three_four_day_message"],
        )
        logger.info(four_days_sent_notifications)
        seven_days_sent_notifications = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["seven_days_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["five_seven_days_message"],
        )
        logger.info(seven_days_sent_notifications)
        fourteen_days_sent_notifications = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["fourteen_days_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["eight_fourteen_days_message"],
        )
        logger.info(fourteen_days_sent_notifications)
        twenty_eight_days_sent_notifications = self.push_service.notify_multiple_devices(
            registration_ids=self.missed_session_dict["twenty_eight_days_missed_list"],
            message_title=message_title,
            extra_notification_kwargs=extra_notification_kwargs,
            message_body=notification_messages["more_then_fourteen_days_message"],
        )
        logger.info(twenty_eight_days_sent_notifications)

    def get_message_from_missed_session(self, missed_sessions, registration_id):
        if missed_sessions == 1:
            self.missed_session_dict["one_day_missed_list"].append(registration_id)
        elif missed_sessions == 2:
            self.missed_session_dict["two_days_missed_list"].append(registration_id)
        elif missed_sessions == 4:
            self.missed_session_dict["four_days_missed_list"].append(registration_id)
        elif missed_sessions == 7:
            self.missed_session_dict["seven_days_missed_list"].append(registration_id)
        elif missed_sessions == 14:
            self.missed_session_dict["fourteen_days_missed_list"].append(registration_id)
        elif missed_sessions == 28:
            self.missed_session_dict["twenty_eight_days_missed_list"].append(registration_id)

    def handle(self, *args, **options):
        users = UserProfile.objects.all()
        for user_profile in users:
            try:
                user_notification = UserNotification.objects.get(user_profile_id=user_profile.id)
                user_today_missed_workout = get_current_date_missed_sessions(user_profile.id)
                if user_today_missed_workout:
                    logger.info(f"User today's missed session: {user_today_missed_workout}")
                    self.missed_session_dict["daily_missed_list"].append(user_notification.registration_id)
                missed_sessions, response = get_missed_sessions(user_profile.id)
                if missed_sessions > 0:
                    logger.info(f"Number of missed sessions for user {user_profile.id} are {missed_sessions} ")
                    self.get_message_from_missed_session(missed_sessions, user_notification.registration_id)
            except UserNotification.DoesNotExist:
                logger.info(f"User Notification object with the id: {user_profile.id} doesn't exist.")
                continue
        self.send_notification()
