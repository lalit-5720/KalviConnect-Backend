from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardStatsView,
    StudentViewSet, 
    MarkViewSet, 
    FeeRecordViewSet, 
    AttendanceViewSet, 
    AnnouncementViewSet
)

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'marks', MarkViewSet, basename='mark')
router.register(r'fees', FeeRecordViewSet, basename='feerecord')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
