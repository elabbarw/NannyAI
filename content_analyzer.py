import openai
import google.generativeai as genai
from utils.logger import get_logger
from PIL import Image
import io
import base64
import json

class ContentAnalyzer:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)

        # Set default provider
        self.provider = config.get('vision_provider', 'openai')

        # Initialize API clients with keys from config
        self._initialize_api_clients()

    def _initialize_api_clients(self):
        """Initialize API clients with current config"""
        try:
            # Initialize OpenAI client
            openai_key = self.config.get_api_key('openai')
            self.openai_client = openai.OpenAI(api_key=openai_key) if openai_key else None

            # Initialize Gemini client
            gemini_key = self.config.get_api_key('gemini')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel(
                    self.config.get_model_settings('gemini').get('selected_model', 'gemini-1.5-flash-8b')
                )
            else:
                self.gemini_model = None

        except Exception as e:
            self.logger.error(f"Failed to initialize API clients: {str(e)}")
            self.openai_client = None
            self.gemini_model = None

    def analyze_image(self, image):
        """Analyze image for inappropriate content"""
        try:
            # Validate API configuration
            if not self._validate_api_config():
                return False

            # Convert PIL Image to appropriate format
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # Get analysis based on selected provider
            if self.provider == 'openai':
                analysis = self._call_openai_api(img_byte_arr)
            elif self.provider == 'gemini':
                analysis = self._call_gemini_api(img_byte_arr)
            else:
                self.logger.error(f"Unknown provider: {self.provider}")
                return False


            # Check against configured thresholds
            return self._check_harmful_content(analysis)

        except Exception as e:
            self.logger.error(f"Content analysis failed: {str(e)}")
            return False

    def _validate_api_config(self):
        """Validate API configuration"""
        if self.provider == 'openai':
            if not self.openai_client:
                self._initialize_api_clients()  # Try to reinitialize
                if not self.openai_client:
                    self.logger.error("OpenAI API key not configured")
                    return False
            model_settings = self.config.get_model_settings('openai')
            if not model_settings.get('selected_model'):
                self.logger.error("OpenAI model not selected")
                return False
        elif self.provider == 'gemini':
            if not self.gemini_model:
                self._initialize_api_clients()  # Try to reinitialize
                if not self.gemini_model:
                    self.logger.error("Gemini API key not configured")
                    return False
            model_settings = self.config.get_model_settings('gemini')
            if not model_settings.get('selected_model'):
                self.logger.error("Gemini model not selected")
                return False
        return True

    def _call_openai_api(self, image_bytes):
        """Call OpenAI Vision API for content analysis"""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")

            base64_image = base64.b64encode(image_bytes).decode('utf-8')

            # Get selected model from config
            model_settings = self.config.get_model_settings('openai')
            model = model_settings.get('selected_model', 'gpt-4o-mini')

            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role":"system",
                        "content":"""You're NannyAI. A bot specialised in protecting children and minors from harmful content on the internet. You will be provided with screenshots to analyze for potentially harmful content. For each category (violence, adult, hate, drugs), provide a confidence score as a float between 0.0 and 1.0 .Return the results in a JSON format with these categories as keys using the following format: Example would be:
                        {
                                'violence': 0.0,
                                'adult': 0.0,
                                'hate': 0.0,
                                'drugs': 0.0,
                                'gambling': 0.0
                        }
                        """


                    },
                    {
                        "role":"system",
                        "content":"NannyAI, pay close attention to chats and emojis that might hint towards anything sexual or violent since a minor would be viewing them. They won't explicitly mention anything to trigger but the emojis and their order would implicitly mention this. For example: eggplant emoji with peach emoji, etc."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "NannyAI, please analyze this screenshot for potentially harmful content."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                response_format={ "type": "json_object" }
            )

            # Extract scores from response
            try:
                content = response.choices[0].message.content
                content = json.loads(response.choices[0].message.content) if isinstance(content, str) else content
                print(content)
                scores = {
                    'violence': 0.0,
                    'adult': 0.0,
                    'hate': 0.0,
                    'drugs': 0.0,
                    'gambling': 0.0
                }


                for key in scores.keys():
                    if key in content:
                        scores[key] += content[key]

                # Special case check for 'explicit' contributing to the 'adult' score
                if 'explicit' in content:
                    scores['adult'] += content['explicit']

                return scores

            except Exception as e:
                self.logger.error(f"Failed to parse OpenAI response: {str(e)}")
                return {"error": "Failed to parse response"}

        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {str(e)}")
            return {"error": str(e)}

    def _call_gemini_api(self, image_bytes):
        """Call Google Gemini Vision API for content analysis"""
        try:
            if not self.gemini_model:
                raise ValueError("Gemini client not initialized")

            # Convert bytes to PIL Image for Gemini
            image = Image.open(io.BytesIO(image_bytes))

            prompt = """
            You're NannyAI. A bot that specialised in protecting children and minors from harmful content on the internet. You will be provided with screenshots to analyze for potentially harmful content. For each category (violence, adult, hate, drugs), provide a confidence score as a float between 0.0 and 1.0. Return the results in a JSON format with these categories as keys. Example would be:
            {
                    'violence': 0.0,
                    'adult': 0.0,
                    'hate': 0.0,
                    'drugs': 0.0,
                    'gambling': 0.0
            }.
            NannyAI, pay close attention to chats and emojis that might hint towards anything sexual or violent since a minor would be viewing them. They won't explicitly mention anything to trigger but the emojis and their order would implicitly mention this. For example: eggplant emoji with peach emoji, etc.
            NannyAI, please analyze this image for potentially harmful content.
            """

            response = self.gemini_model.generate_content([prompt, image])

            # Extract scores from response
            try:
                content = response.text
                content = json.loads(response.text) if isinstance(content, str) else content
                scores = {
                    'violence': 0.0,
                    'adult': 0.0,
                    'hate': 0.0,
                    'drugs': 0.0,
                    'gambling': 0.0
                }


                for key in scores.keys():
                    if key in content:
                        scores[key] += content[key]

                # Special case check for 'explicit' contributing to the 'adult' score
                if 'explicit' in content:
                    scores['adult'] += content['explicit']

                return scores

            except Exception as e:
                self.logger.error(f"Failed to parse Gemini response: {str(e)}")
                return {"error": "Failed to parse response"}

        except Exception as e:
            self.logger.error(f"Gemini API call failed: {str(e)}")
            return {"error": str(e)}

    def _check_harmful_content(self, analysis):
        """Check if content is harmful based on configured thresholds"""
        if "error" in analysis:
            return False

        # Get configured thresholds
        thresholds = self.config.get('content_thresholds', {
            'violence': 0.7,
            'adult': 0.7,
            'hate': 0.7,
            'drugs': 0.7,
            'gambling': 0.7
        })

        # Get configured categories to monitor
        monitored_categories = self.config.get('monitored_categories', [
            'violence',
            'adult',
            'hate',
            'drugs',
            'gambling'
        ])

        # Check each monitored category against its threshold
        for category in monitored_categories:
            if category in analysis:
                score = float(analysis[category])
                threshold = thresholds.get(category, 0.7)

                if score >= threshold:
                    self.logger.warning(f"Harmful content detected: {category} ({score:.2f})")
                    return analysis

        return False