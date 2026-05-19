from rest_framework import generics
from api.models import Vehicle
from api.serializers import VehicleSerializer


class VehicleListView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        qs = Vehicle.objects.filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param in ('active', 'inactive'):
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(user=self.request.user)
