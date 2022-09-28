from django.urls import path

# from apps.notification.views import get_id, index, send, showFirebaseJS
from apps.notification.views import NotificationView

urlpatterns = [
    path("notifications/", NotificationView.as_view()),
    # path("get-registration-id/", index),
    # path("get_id/", get_id),
    # path("send/", send),
    # path("firebase-messaging-sw.js", showFirebaseJS, name="show_firebase_js"),
]
