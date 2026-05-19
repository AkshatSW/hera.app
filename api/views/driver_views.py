from rest_framework import generics
from api.models import Driver
from api.serializers import DriverSerializer


class DriverListView(generics.ListCreateAPIView):
    serializer_class = DriverSerializer

    def get_queryset(self):
        qs = Driver.objects.filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param in ('active', 'inactive'):
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DriverSerializer

    def get_queryset(self):
        return Driver.objects.filter(user=self.request.user)
