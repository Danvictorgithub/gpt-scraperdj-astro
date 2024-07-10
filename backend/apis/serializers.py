from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    server_url = serializers.URLField(max_length=200)
    server_url_2 = serializers.URLField(max_length=200,required=False)
    max_prompt = serializers.IntegerField(max_value=70,default=70)
    initial_message = serializers.CharField(max_length=4096,
                                            required=False,
                                            default=
                                            "Lets pretend to have a basic conversation like a human, you can also pretend to have emotion, I would like you to limit the length of your response to small paragraphs, I will do the same. I repeat respond with short paragraph, respond in less than 4096 characters")
    