from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatSerializer
import openai
from drf_yasg.utils import swagger_auto_schema

class ChatView(APIView):
    @swagger_auto_schema(request_body=ChatSerializer)
    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            
            try:
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": message}
                    ]
                )
                response_text = completion.choices[0].message.content
                return Response({'response': response_text}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
