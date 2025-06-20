// System prompt for the LLM
const SYSTEM_PROMPT = `
You are a stock market agent who solves problem in iteration.

Respond in EXACTLY ONE of these formats:

1. FUNCTION_CALL: python_function_name|jsonified_parameter_string
2. TASK_COMPLETE: <task_complete_message>
3. INSUFFICIENT_TOOLS: <advise what additional tools are required>


You have the following tools at hand. You are supposed to complete the task only using the following tools.

where python_function_name is one of the following:
1. get_stock_news(stock_name,from_date,to_date):return news
2. get_stock_price(stock_name,from_date,to_date): return list of prices for the given stock name and date range in chronological ascending order
3. send_email(recipient_email,stock_name,body): return True if email is sent successfully, else return False


For example: if you are responding for getting stock news for stock named Ola for last 3 days, then you should return:
FUNCTION_CALL: get_stock_news|{"stock_name":"OLA","from_date":"2024-04-28","to_date":"2024-05-01"}

DO NOT include multiple responses. Give ONE response at a time.
DO NOT GIVE EXPLANATION OR REASONING. JUST RETURN THE RESPONSE IN THE SPECIFIED FORMAT.
DO NOT BREACH THE CONTRACT OF RESPONSE FORMAT!!!!!
`;

// Default query template for stock analysis
const DEFAULT_QUERY = (stockName, fromDate, toDate) => 
  `Find the news about ${stockName} and link it with its price changes from ${fromDate} to ${toDate} then see how the stock moved on those dates. Keep the analysis for a particular day within 50 words. Send the analysis to mathurk29@gmail.com`;

let model = null;

// Load saved API key on popup open
document.addEventListener('DOMContentLoaded', async () => {
  console.log('DOM Content Loaded - Initializing extension');
  try {
    const result = await chrome.storage.local.get(['geminiApiKey']);
    console.log('Retrieved API key from storage:', result.geminiApiKey ? '***' + result.geminiApiKey.slice(-4) : 'undefined');
    
    if (result.geminiApiKey) {
      document.getElementById('apiKey').value = result.geminiApiKey;
      console.log('Setting API key in input field');
      await initializeGemini(result.geminiApiKey);
    } else {
      console.log('No API key found in storage');
    }
  } catch (error) {
    console.error('Error in DOMContentLoaded:', error);
    showMessage('Error loading saved API key: ' + error.message, 'error');
  }
});

// Save API key
document.getElementById('saveKey').addEventListener('click', async () => {
  console.log('Save Key button clicked');
  const apiKey = document.getElementById('apiKey').value.trim();
  console.log('API Key from input:', apiKey ? '***' + apiKey.slice(-4) : 'undefined');
  
  if (!apiKey) {
    console.log('No API key provided');
    showMessage('Please enter an API key', 'error');
    return;
  }

  try {
    console.log('Saving API key to storage');
    await chrome.storage.local.set({ geminiApiKey: apiKey });
    console.log('API key saved to storage');
    
    console.log('Initializing Gemini with new API key');
    await initializeGemini(apiKey);
    showMessage('API key saved successfully!', 'success');
  } catch (error) {
    console.error('Error saving API key:', error);
    showMessage(`Error saving API key: ${error.message}`, 'error');
  }
});

async function initializeGemini(apiKey) {
  console.log('Initializing Gemini with API key:', apiKey ? '***' + apiKey.slice(-4) : 'undefined');
  try {
    model = new GeminiClient(apiKey);
    console.log('GeminiClient instance created');
    
    // Test the API key with a simple prompt
    console.log('Testing API key with simple prompt');
    const testResult = await model.generateContent('Hello');
    console.log('Test result:', testResult);
  } catch (error) {
    console.error('Error initializing Gemini:', error);
    throw new Error(`Failed to initialize Gemini: ${error.message}`);
  }
}

function showMessage(message, type) {
  console.log(`Showing message (${type}):`, message);
  const resultDiv = document.getElementById('result');
  resultDiv.innerHTML = `<p class="${type}">${message}</p>`;
}

async function callFunction(funcName, params) {
  console.log('Calling function:', funcName, 'with params:', params);
  try {
    const requestBody = {
      func_name: funcName,
      params: params
    };
    console.log('Request body:', JSON.stringify(requestBody, null, 2));

    const response = await fetch('http://localhost:8000/call_function', {
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
      throw new Error('Network response was not ok: ' + errorText);
    }

    const data = await response.json();
    console.log('Response data:', JSON.stringify(data, null, 2));
    return data.result;
  } catch (error) {
    console.error('Error in callFunction:', error);
    throw new Error(`Function call failed: ${error.message}`);
  }
}

async function processLLMResponse(responseText, stockName, fromDate, toDate) {
  console.log('Processing LLM response:', responseText);
  console.log('Context:', { stockName, fromDate, toDate });

  if (responseText.startsWith("FUNCTION_CALL:")) {
    console.log('Response is a function call');
    const functionInfo = responseText.split("FUNCTION_CALL:")[1].trim();
    console.log('Function info:', functionInfo);
    
    const [funcName, paramsStr] = functionInfo.split("|").map(x => x.trim());
    console.log('Parsed function name:', funcName);
    console.log('Parsed params string:', paramsStr);
    
    let params;
    try {
      // Parse parameters as JSON
      params = JSON.parse(paramsStr);
    } catch (e) {
      console.error('Failed to parse parameters as JSON:', e);
      throw new Error("Invalid parameter format in LLM response");
    }
    console.log('Parsed params:', params);

    return await callFunction(funcName, params);
  } 
  else if (responseText.startsWith("TASK_COMPLETE:")) {
    console.log('Response is a task complete message');
    const taskCompleteMessage = responseText.split("TASK_COMPLETE:")[1].trim();
    console.log('Task complete message:', taskCompleteMessage);
    return taskCompleteMessage;
  }
  else if (responseText.startsWith("INSUFFICIENT_TOOLS:")) {
    console.log('Response is an insufficient tools message');
    const insufficientToolsMessage = responseText.split("INSUFFICIENT_TOOLS:")[1].trim();
    console.log('Insufficient tools message:', insufficientToolsMessage);
    return insufficientToolsMessage;
  }
  else {
    console.error('Invalid response format:', responseText);
    throw new Error("Invalid LLM response format");
  }
}

document.getElementById('analyze').addEventListener('click', async () => {
  console.log('Analyze button clicked');
  const stockName = document.getElementById('stockName').value;
  console.log('Stock name:', stockName);
  const resultDiv = document.getElementById('result');
  
  if (!model) {
    console.log('No model initialized');
    showMessage('Please save your API key first', 'error');
    return;
  }
  
  if (!stockName) {
    console.log('No stock name provided');
    showMessage('Please enter a stock symbol', 'error');
    return;
  }

  resultDiv.textContent = 'Analyzing...';
  console.log('Starting analysis');

  try {
    const fromDate = new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const toDate = new Date().toISOString().split('T')[0];
    console.log('Date range:', { fromDate, toDate });
    
    let currentIteration = 0;
    const maxIterations = 10;
    const iterationHistory = [];
    let query = DEFAULT_QUERY(stockName, fromDate, toDate);
    let responseText = null;

    while (currentIteration < maxIterations) {
      console.log(`Starting iteration ${currentIteration + 1}`);
      
      // Check if we've reached maximum iterations
      if (currentIteration >= maxIterations - 1) {
        console.log('Maximum iterations reached');
        showMessage("Maximum iterations reached without completion", 'error');
        break;
      }

      // Prepare the query with history
      let currentQuery = query;
      if (iterationHistory.length > 0) {
        currentQuery += '\n\nPrevious iterations:';
        iterationHistory.forEach((history, index) => {
          currentQuery += `\n\nIteration ${index + 1}:`;
          currentQuery += `\nR${index + 1}: ${history.llmResponse}`;
          currentQuery += `\nS${index + 1}: ${JSON.stringify(history.serverResponse)}`;
        });
        currentQuery += '\n\nWhat should I do next?';
      }
      console.log('Current query:', currentQuery);

      // Get model's response
      const prompt = `${SYSTEM_PROMPT}\n\nQuery: ${currentQuery}`;
      console.log('Sending prompt to model');
      const result = await model.generateContent(prompt);
      responseText = result.response.text().trim();
      console.log('Model response:', responseText);
      
      // Process the response
      try {
        console.log('Processing model response');
        const serverResponse = await processLLMResponse(responseText, stockName, fromDate, toDate);
        console.log('Processed result:', serverResponse);
        
        // Store both LLM and server responses in history
        iterationHistory.push({
          llmResponse: responseText,
          serverResponse: serverResponse
        });
        console.log('Updated iteration history:', iterationHistory);

        // Break if we received a TASK_COMPLETE response
        if (responseText.startsWith("TASK_COMPLETE:")) {
          console.log('Received TASK_COMPLETE, ending analysis');
          let htmlContent = `
            <h3>Analysis Results for ${stockName}</h3>
            <div class="news-container">
              <h4>Analysis Steps</h4>
              ${iterationHistory.map((history, index) => `
                <div class="iteration-step">
                  <h5>Iteration ${index + 1}</h5>
                  <p><strong>R${index + 1}:</strong> ${history.llmResponse}</p>
                  <p><strong>S${index + 1}:</strong> ${JSON.stringify(history.serverResponse)}</p>
                </div>
              `).join('')}
            </div>
          `;
          resultDiv.innerHTML = htmlContent;
          break;
        }

        // If we got a plot, we're done
        if (typeof serverResponse === 'string' && serverResponse.startsWith('data:image')) {
          console.log('Received plot image, completing analysis');
          // Create HTML content
          let htmlContent = `
            <h3>Analysis Results for ${stockName}</h3>
            <div class="graph-container">
              <img src="data:image/png;base64,${serverResponse}" alt="Stock Price Graph" style="width: 100%;">
            </div>
            <div class="news-container">
              <h4>Analysis Steps</h4>
              ${iterationHistory.map((history, index) => `
                <div class="iteration-step">
                  <h5>Iteration ${index + 1}</h5>
                  <p><strong>R${index + 1}:</strong> ${history.llmResponse}</p>
                  <p><strong>S${index + 1}:</strong> ${JSON.stringify(history.serverResponse)}</p>
                </div>
              `).join('')}
              <div class="iteration-step">
                <h5>Final Step</h5>
                <p><strong>R${iterationHistory.length + 1}:</strong> ${responseText}</p>
                <p><strong>S${iterationHistory.length + 1}:</strong> Plot successfully generated</p>
              </div>
            </div>
          `;
          resultDiv.innerHTML = htmlContent;
          console.log('Analysis complete');
          break;
        }
      } catch (error) {
        console.error('Error processing LLM response:', error);
        throw new Error(`Error processing LLM response: ${error.message}`);
      }

      currentIteration++;
      console.log(`Completed iteration ${currentIteration}`);
    }

  } catch (error) {
    console.error('Error in analysis:', error);
    showMessage(`Error: ${error.message}`, 'error');
  }
});