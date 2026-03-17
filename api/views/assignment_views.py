from rest_framework import generics
from api.models import Assignment
from api.serializers import AssignmentSerializer


class AssignmentListView(generics.ListCreateAPIView):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        qs = Assignment.objects.filter(
            user=self.request.user
        ).select_related('driver', 'vehicle')
        route_date = self.request.query_params.get('route_date')
        if route_date:
            qs = qs.filter(route_date=route_date)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(
            user=self.request.user
        ).select_related('driver', 'vehicle')
