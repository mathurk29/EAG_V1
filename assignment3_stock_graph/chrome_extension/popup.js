// System prompt for the LLM
const SYSTEM_PROMPT = `
You are a stock market agent who solves problem in iteration.

Respond with EXACTLY ONE of these formats:

1. FUNCTION_CALL: python_function_name|input

You have the following tools at hand. You are supposed to complete the task only using the following tools. If these tools are not sufficient - advise what additional tools are required.

where python_function_name is one of the following:
1. get_stock_news(stock_name,from_date,to_date)
2. get_stock_price(date)
3. plot_graph

Task: Find the news about a particular stock and link it with its price changes (e.g. search news about Ola in the last 1 month and news date, then see how the stock moved on those dates, and then link this data)

DO NOT include multiple responses. Give ONE response at a time.
`;

let model = null;

// Load saved API key on popup open
document.addEventListener('DOMContentLoaded', async () => {
  const result = await chrome.storage.local.get(['geminiApiKey']);
  if (result.geminiApiKey) {
    document.getElementById('apiKey').value = result.geminiApiKey;
    initializeGemini(result.geminiApiKey);
  }
});

// Save API key
document.getElementById('saveKey').addEventListener('click', async () => {
  const apiKey = document.getElementById('apiKey').value.trim();
  if (!apiKey) {
    showMessage('Please enter an API key', 'error');
    return;
  }

  try {
    await chrome.storage.local.set({ geminiApiKey: apiKey });
    initializeGemini(apiKey);
    showMessage('API key saved successfully!', 'success');
  } catch (error) {
    showMessage(`Error saving API key: ${error.message}`, 'error');
  }
});

function initializeGemini(apiKey) {
  const client = new GoogleGenerativeAI(apiKey);
  model = client.getGenerativeModel({ model: "gemini-pro" });
}

function showMessage(message, type) {
  const resultDiv = document.getElementById('result');
  resultDiv.innerHTML = `<p class="${type}">${message}</p>`;
}

async function callFunction(funcName, params) {
  try {
    const response = await fetch('http://localhost:8000/call_function', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        func_name: funcName,
        params: params
      })
    });

    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    return data.result;
  } catch (error) {
    throw new Error(`Function call failed: ${error.message}`);
  }
}

async function processLLMResponse(responseText, stockName, fromDate, toDate) {
  if (responseText.startsWith("FUNCTION_CALL:")) {
    const [, functionInfo] = responseText.split(":", 1);
    const [funcName, paramsStr] = functionInfo.split("|").map(x => x.trim());
    const params = JSON.parse(paramsStr);

    // Add stock_name and dates if not present
    if (!params.stock_name) params.stock_name = stockName;
    if (!params.from_date) params.from_date = fromDate;
    if (!params.to_date) params.to_date = toDate;

    return await callFunction(funcName, params);
  } else {
    throw new Error("Invalid LLM response format");
  }
}

document.getElementById('analyze').addEventListener('click', async () => {
  const stockName = document.getElementById('stockName').value;
  const resultDiv = document.getElementById('result');
  
  if (!model) {
    showMessage('Please save your API key first', 'error');
    return;
  }
  
  if (!stockName) {
    showMessage('Please enter a stock symbol', 'error');
    return;
  }

  resultDiv.textContent = 'Analyzing...';

  try {
    const fromDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    const toDate = new Date().toISOString().split('T')[0];
    
    let currentIteration = 0;
    const maxIterations = 5;
    let lastResponse = null;
    const iterationResponses = [];

    while (currentIteration < maxIterations) {
      // Prepare the query
      let currentQuery;
      if (lastResponse === null) {
        currentQuery = `Analyze stock ${stockName} from ${fromDate} to ${toDate}`;
      } else {
        currentQuery = `Previous result: ${JSON.stringify(lastResponse)}. What should I do next?`;
      }

      // Get model's response
      const prompt = `${SYSTEM_PROMPT}\n\nQuery: ${currentQuery}`;
      const result = await model.generateContent(prompt);
      const responseText = result.response.text().trim();
      
      // Process the response
      try {
        const result = await processLLMResponse(responseText, stockName, fromDate, toDate);
        lastResponse = result;
        iterationResponses.push(`Iteration ${currentIteration + 1}: ${responseText}`);

        // If we got a plot, we're done
        if (typeof result === 'string' && result.startsWith('data:image')) {
          // Create HTML content
          let htmlContent = `
            <h3>Analysis Results for ${stockName}</h3>
            <div class="graph-container">
              <img src="data:image/png;base64,${result}" alt="Stock Price Graph" style="width: 100%;">
            </div>
            <div class="news-container">
              <h4>Analysis Steps</h4>
              ${iterationResponses.map(r => `<p>${r}</p>`).join('')}
            </div>
          `;
          resultDiv.innerHTML = htmlContent;
          break;
        }
      } catch (error) {
        throw new Error(`Error processing LLM response: ${error.message}`);
      }

      currentIteration++;
    }

    if (currentIteration >= maxIterations) {
      throw new Error("Maximum iterations reached without completion");
    }

  } catch (error) {
    showMessage(`Error: ${error.message}`, 'error');
  }
}); 