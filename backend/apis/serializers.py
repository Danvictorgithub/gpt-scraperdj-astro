from rest_framework import serializers

class ChatRequestSerializer(serializers.Serializer):
    server_url = serializers.URLField(max_length=200)
    server_url_2 = serializers.URLField(max_length=200,required=False)
    max_prompt = serializers.IntegerField(max_value=70,default=30)
    initial_message = serializers.CharField(max_length=4096,
                                            required=False,
                                            default=
                                            "Lets pretend to have a basic conversation like a human with basic vocabulary, you can also pretend to have emotion, I would like you to limit the length of your response to small paragraphs, I will do the same. I repeat respond with short paragraph")
    topic = serializers.CharField(max_length=200,required=False,default="general")
    
class ChatRequestGeminiSeralizer(serializers.Serializer):
    max_prompt = serializers.IntegerField(max_value=70,default=30)
    initial_message = serializers.CharField(max_length=4096,
                                            required=False,
                                            default=
                                            "Lets pretend to have a basic conversation like a human with basic vocabulary, you can also pretend to have emotion, I would like you to limit the length of your response to small paragraphs, I will do the same. I repeat respond with short paragraph")
    topic = serializers.CharField(max_length=200,required=False,default="general")

class ChatRequestGeminiRandomSeralizer(serializers.Serializer):
    max_prompt = serializers.IntegerField(max_value=70,default=6)
    initial_message = serializers.CharField(max_length=4096,
                                            required=False,
                                            default=
                                            "Lets pretend to have a basic conversation like a human with basic vocabulary, you can also pretend to have emotion, I would like you to limit the length of your response to small paragraphs, I will do the same. I repeat respond with short paragraph, please limit to less than 300 character")
