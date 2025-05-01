class GeminiClient {
  constructor(apiKey) {
    console.log('Initializing GeminiClient with API key:', apiKey ? '***' + apiKey.slice(-4) : 'undefined');
    this.apiKey = apiKey;
    this.baseUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';
  }

  async generateContent(prompt) {
    console.log('Generating content with prompt:', prompt);
    console.log('Using API URL:', this.baseUrl);
    
    try {
      const requestBody = {
        contents: [{
          parts: [{
            text: prompt
          }]
        }]
      };
      console.log('Request body:', JSON.stringify(requestBody, null, 2));

      const response = await fetch(`${this.baseUrl}?key=${this.apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response body:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      console.log('Response data:', JSON.stringify(data, null, 2));

      if (!data.candidates || !data.candidates[0] || !data.candidates[0].content || !data.candidates[0].content.parts || !data.candidates[0].content.parts[0]) {
        console.error('Unexpected response structure:', data);
        throw new Error('Unexpected response structure from Gemini API');
      }

      return {
        response: {
          text: () => data.candidates[0].content.parts[0].text
        }
      };
    } catch (error) {
      console.error('Error in generateContent:', error);
      throw new Error(`Failed to generate content: ${error.message}`);
    }
  }
} 