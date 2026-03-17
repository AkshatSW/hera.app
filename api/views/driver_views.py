from rest_framework import generics
from api.models import Driver
from api.serializers import DriverSerializer


class DriverListView(generics.ListCreateAPIView):
    serializer_class = DriverSerializer

    def get_queryset(self):
        return Driver.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DriverSerializer

    def get_queryset(self):
        return Driver.objects.filter(user=self.request.user)
